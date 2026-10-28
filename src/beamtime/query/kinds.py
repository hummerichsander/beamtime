"""One function per query kind, each returning the canonical JSON answer."""

import csv
import io
import json
import math
import posixpath
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from beamtime.format import constants as c
from beamtime.format.authored import newest, read_markdown_doc
from beamtime.format.ids import is_run_id
from beamtime.format.run import read_preview
from beamtime.format.tree import is_reserved
from beamtime.index.columns import TIME_KEY, Column, open_columns
from beamtime.index.index import Index
from beamtime.index.store import in_scope
from beamtime.query import models as m
from beamtime.query.fields import PROPOSAL as PROPOSAL_FIELDS
from beamtime.query.fields import Field, decode_cell, parse_field, sql
from beamtime.query.models import QueryError, closest
from beamtime.query.read import (
    bucket_means,
    downsample,
    ema,
    finite_range,
    from_preview,
    value_at,
    width_for,
    window_stat,
)
from beamtime.query.where import fields_of, matches, number

Caller = Literal["cli", "mcp", "view"]
DEFAULTS: dict[str, dict[str, int]] = {
    "cli": {"rows": 50, "points": 100, "entries": 30},
    "mcp": {"rows": 50, "points": 100, "entries": 30},
    "view": {"rows": 1000, "points": 1000, "entries": 200},
}
CHART_BUDGET = 30_000


@dataclass(kw_only=True)
class Context:
    """What a query runs against."""

    index: Index
    caller: Caller
    scope: str
    run_id: str | None
    now: float

    @property
    def defaults(self) -> dict[str, int]:
        """The caller's default limits."""
        return DEFAULTS[self.caller]


def resolve_from(index: Index, base: str, target: str) -> tuple[str, str | None]:
    """Resolve ``from`` to a group relative to the log dir, or to one run.

    :param index: The index.
    :param base: The group relative paths start from (a view's group; ``.`` for CLI).
    :param target: The ``from`` value: a group, a run id, or ``@remote/...``.
    :return: The group relative to the log dir, and the run id if one run was named."""
    if target.startswith("@"):
        raise QueryError(
            f"from {target!r}: remote sources come with remotes (milestone M8); "
            "query local groups for now"
        )
    name = target.rstrip("/").rsplit("/", 1)[-1]
    if is_run_id(name):
        if (path := index.run_path(name)) is None:
            index.catch_up(".", budget_s=0)
            path = index.run_path(name)
        if path is None:
            raise QueryError(f"no run {name!r} below the log dir", code="not_found")
        return path.relative_to(index.logdir).as_posix(), name
    rel = posixpath.normpath(posixpath.join(base, target.strip("/") or "."))
    if rel == ".." or rel.startswith("../"):
        raise QueryError(f"from {target!r} leaves the log dir")
    if rel != "." and any(is_reserved(part) for part in rel.split("/")):
        raise QueryError(
            f"from {target!r}: {rel!r} holds authored or machine files, not runs; "
            "name the group above it",
            code="not_found",
        )
    if not index.folder_path(rel).is_dir():
        parent = index.folder_path(posixpath.dirname(rel) or ".")
        options = [p.name for p in parent.iterdir() if p.is_dir()] if parent.is_dir() else []
        raise QueryError(
            f"no group {rel!r} below the log dir." + closest(posixpath.basename(rel), options),
            code="not_found",
        )
    return rel, None


def derived_status(status: str | None, heartbeat: float | None, now: float) -> str | None:
    """Derive ``lost`` for running runs with a stale heartbeat.

    :param status: The status from ``_run.json``.
    :param heartbeat: The modification time of ``_run.json``.
    :param now: The current time.
    :return: The status shown."""
    if status == "running" and heartbeat is not None and now - heartbeat > c.LOST_AFTER_S:
        return "lost"
    return status


class Columns:
    """Lazily opened column files of one run."""

    def __init__(self, *, index: Index, run_id: str) -> None:
        """Prepare access to a run's columns.

        :param index: The index.
        :param run_id: The run id."""
        self.dir = index.series / run_id
        self.manifest, self.entries = open_columns(self.dir)
        self.open: dict[str, Column] = {}

    def get(self, key: str) -> Column | None:
        """Open a key's column.

        :param key: The metric key or ``_t``.
        :return: The column, or ``None`` if the run has none for it."""
        if key not in self.open:
            if (e := self.entries.get(key)) is None:
                return None
            self.open[key] = Column.open(self.dir, e)
        return self.open[key]

    def close(self) -> None:
        """Close every opened column."""
        for col in self.open.values():
            col.close()


def known_keys(ctx: Context, what: Literal["metrics", "values", "config"]) -> set[str]:
    """List the metric, value or top-level config keys in scope.

    :param ctx: The query context.
    :param what: Which keys.
    :return: The keys."""
    cond, params = scope_condition(ctx)
    source = {"metrics": "card, '$.metrics'", "values": "card, '$.values'"}.get(what, "config")
    rows = ctx.index.store.db.execute(
        f"SELECT DISTINCT j.key FROM runs, json_each({source}) j WHERE {cond}", params
    )
    return {r[0] for r in rows}


def scope_condition(ctx: Context, depth: Any = "all") -> tuple[str, list[Any]]:
    """Build the SQL condition selecting the runs in scope.

    :param ctx: The query context.
    :param depth: ``all`` or how many levels below the scope to include.
    :return: The condition and its parameters."""
    if ctx.run_id is not None:
        return "runs.id = ?", [ctx.run_id]
    cond, params = in_scope("runs.folder", ctx.scope)
    if depth != "all":
        base = 0 if ctx.scope in (".", "") else ctx.scope.count("/") + 1
        cond += (
            " AND (CASE WHEN runs.folder = '.' THEN 0 ELSE "
            "length(runs.folder) - length(replace(runs.folder, '/', '')) + 1 END) < ?"
        )
        params.append(base + int(depth))
    return cond, params


def check_known(ctx: Context, fields: list[Field]) -> None:
    """Refuse fields naming keys that no run in scope has, with the closest matches.

    :param ctx: The query context.
    :param fields: The fields of the query."""
    for f in fields:
        what = {"metric": "metrics", "value": "values", "config": "config"}.get(f.ns)
        if what is None:
            continue
        cond, params = scope_condition(ctx)
        source = {"metrics": "card, '$.metrics'", "values": "card, '$.values'"}.get(what, "config")
        # one hit is enough; the full key list is only needed for suggestions.
        hit = ctx.index.store.db.execute(
            f"SELECT 1 FROM runs, json_each({source}) j WHERE {cond} AND j.key = ? LIMIT 1",
            [*params, f.key],
        ).fetchone()
        if hit:
            continue
        if known := known_keys(ctx, what):
            raise QueryError(
                f"{f.text!r}: no run in {ctx.scope!r} has {f.ns} key {f.key!r}."
                f"{closest(f.key, sorted(known))} See `beamtime keys {ctx.scope}`.",
                code="not_found",
            )


SQL_OPS = {"eq": "=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}


def prefilter(where: dict[str, Any], exprs: dict[Field, str]) -> tuple[str, list[Any]]:
    """Translate the simple top-level conditions into SQL, to narrow rows early.

    Only conditions where SQL and the Python evaluator agree exactly are translated:
    scalar comparisons on SQL-backed fields (a missing value fails both ways; a string
    never equals or orders against a number in either). The Python evaluator still
    checks every row that comes back.

    :param where: The condition.
    :param exprs: SQL expressions of the fields, by field.
    :return: `` AND …`` conditions and their parameters, or nothing."""
    by_text = {f.text: e for f, e in exprs.items()}
    parts, params = [], []
    for key, cond in where.items():
        if (expr := by_text.get(key)) is None or key == "run.tags":
            continue
        for op, value in cond.items() if isinstance(cond, dict) else [("eq", cond)]:
            if op not in SQL_OPS or isinstance(value, bool):
                continue
            if key == "run.status" and value in ("running", "lost"):
                continue
            sql_op = SQL_OPS[op]
            is_num = f"typeof({expr}) IN ('integer', 'real')"
            is_text = f"typeof({expr}) = 'text'"
            # mirror where.compare: numbers compare as numbers, strings as strings.
            if isinstance(value, (int, float)):
                parts.append(f"({is_num} AND {expr} {sql_op} ?)")
                params.append(value)
            elif isinstance(value, str) and (n := number(value)) is not value:
                parts.append(
                    f"(({is_num} AND {expr} {sql_op} ?) OR ({is_text} AND {expr} {sql_op} ?))"
                )
                params += [n, value]
            elif isinstance(value, str):
                parts.append(f"({is_text} AND {expr} {sql_op} ?)")
                params.append(value)
    return "".join(f" AND {p}" for p in parts), params


def select_runs(
    ctx: Context,
    sel: m.Selection,
    extra: list[str],
    *,
    config: bool = False,
    restrict: tuple[str, list[Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[Field]]:
    """Select runs in scope that match ``where``, with the values of the given fields.

    :param ctx: The query context.
    :param sel: The selection part of the query.
    :param extra: Further fields to fetch (``select``, ``sort``, ``by``).
    :param config: Whether to fetch whole configs (``seeds`` and ``keys`` need them).
    :param restrict: A further SQL condition and its parameters, e.g. proposal membership.
    :return: One dict per run (``_id``, ``_path``, ``_config`` and the field values),
        and the parsed fields."""
    texts = list(dict.fromkeys([*fields_of(sel.where), *extra]))
    fields = [parse_field(t) for t in texts]
    check_known(ctx, fields)
    exprs = [(f, e) for f in fields if (e := sql(f)) is not None]
    whole = "config" if config or sel.seeds else "NULL"
    cols = ", ".join(["id", "path", "status", "heartbeat", whole, *[e for _, e in exprs]])
    cond, params = scope_condition(ctx, sel.depth)
    if restrict is not None:
        cond, params = f"{cond} AND {restrict[0]}", [*params, *restrict[1]]
    pre, pre_params = prefilter(sel.where, dict(exprs))
    rows = ctx.index.store.db.execute(
        f"SELECT {cols} FROM runs WHERE {cond}{pre}", [*params, *pre_params]
    ).fetchall()
    windowed = [f for f in fields if f.window is not None]
    proposal = [f for f in fields if f.ns == "proposal"]
    out = []
    for row in rows:
        values: dict[str, Any] = {"_id": row[0], "_path": row[1], "_config": row[4]}
        for k, (f, _) in enumerate(exprs):
            values[f.text] = decode_cell(f, row[5 + k])
        for f in fields:
            if f.text == "run.status":
                values[f.text] = derived_status(row[2], row[3], ctx.now)
        if proposal:
            research = run_research(ctx, row[0], row[1])
            values |= {f.text: research[f.key] for f in proposal}
        if windowed:
            cols_ = Columns(index=ctx.index, run_id=row[0])
            for f in windowed:
                col = cols_.get(f.key)
                values[f.text] = (
                    None
                    if col is None
                    else window_stat(
                        col.steps, col.values, f.window, f.stat, nonfinite=col.nonfinite
                    )
                )
            cols_.close()
        if matches(sel.where, values):
            out.append(values)
    return out, fields


def run_research(ctx: Context, run_id: str, path: str) -> dict[str, Any]:
    """Derive the ``proposal.*`` fields of a run from its own proposal.

    :param ctx: The query context.
    :param run_id: The run id.
    :param path: The run path relative to the log dir.
    :return: ``status``, ``check``, ``progress`` and ``verdict``."""
    from beamtime.record.proposals import Target
    from beamtime.record.status import research_status

    return research_status(Target(index=ctx.index, rel=path, run_id=run_id))


def seed_groups(
    runs: list[dict[str, Any]], seeds: str
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """Group runs whose configs differ only in the seed key.

    :param runs: Selected runs with ``_config``.
    :param seeds: The seed field, e.g. ``config.seed``.
    :return: ``(config without the seed, runs)`` per group."""
    seed = parse_field(seeds)
    if seed.ns != "config" or len(seed.path) != 1:
        raise QueryError(f"seeds: {seeds!r} must be a top-level config field like config.seed")
    groups: dict[str, tuple[dict[str, Any], list]] = {}
    for r in runs:
        cfg = json.loads(r["_config"] or "{}")
        cfg.pop(seed.key, None)
        key = json.dumps(cfg, sort_keys=True)
        groups.setdefault(key, (cfg, []))[1].append(r)
    return list(groups.values())


def aggregate(values: list[Any]) -> Any:
    """Summarize a column over the seeds of a group.

    :param values: The values of the group's runs.
    :return: The common value, ``{mean, std, n}`` for differing numbers, or ``None``."""
    distinct = {json.dumps(v, sort_keys=True) for v in values}
    if len(distinct) == 1:
        return values[0]
    nums = [
        v
        for v in values
        if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
    ]
    if nums and len(nums) == len([v for v in values if v is not None]):
        mean = math.fsum(nums) / len(nums)
        std = (
            math.sqrt(math.fsum((x - mean) ** 2 for x in nums) / (len(nums) - 1))
            if len(nums) > 1
            else 0.0
        )
        return {"mean": mean, "std": std, "n": len(nums)}
    return None


def sort_rows(rows: list[dict[str, Any]], sort: list[str]) -> None:
    """Sort rows in place by several fields; missing values go last either way.

    :param rows: The rows, field name to value.
    :param sort: Fields, a leading ``-`` for descending."""

    def key(v: Any) -> Any:
        if isinstance(v, dict) and "mean" in v:
            v = v["mean"]
        return (0, v) if isinstance(v, (int, float)) and not isinstance(v, bool) else (1, str(v))

    for spec in reversed(sort):
        desc = spec.startswith("-")
        name = spec.lstrip("-")
        present = [r for r in rows if r.get(name) is not None]
        missing = [r for r in rows if r.get(name) is None]
        present.sort(key=lambda r: key(r[name]), reverse=desc)
        rows[:] = present + missing


def meta(ctx: Context, **kwargs: Any) -> dict[str, Any]:
    """Start an answer's meta.

    :param ctx: The query context.
    :param kwargs: Kind-specific entries.
    :return: The meta dict; freshness is added by ``run``."""
    return {"source": "local", "from": ctx.scope} | kwargs


def runs_kind(ctx: Context, q: m.Runs) -> dict[str, Any]:
    """Answer a run table.

    :param ctx: The query context.
    :param q: The query.
    :return: ``{columns, rows, meta}``."""
    select = q.select or default_columns(ctx)
    sort = [s.lstrip("-") for s in q.sort]
    runs, _ = select_runs(ctx, q, [*select, *sort])
    if q.seeds:
        rows = []
        for _, group in seed_groups(runs, q.seeds):
            row = {"runs": [r["_id"] for r in group]}
            for f in dict.fromkeys([*select, *sort]):
                row[f] = aggregate([r.get(f) for r in group])
            rows.append(row)
        columns = ["runs", *select]
    else:
        rows = [{"run.id": r["_id"]} | r for r in runs]
        columns = ["run.id", *[s for s in select if s != "run.id"]]
    sort_rows(rows, q.sort or ["-run.created_at"] if not q.seeds else q.sort)
    limit = q.limit if q.limit is not None else ctx.defaults["rows"]
    cut = len(rows) > limit
    shown = rows[:limit]
    return {
        "kind": "runs",
        "columns": columns,
        "rows": [[r.get(col) for col in columns] for r in shown],
        "meta": meta(
            ctx,
            matched=len(runs),
            means=len(rows) if q.seeds else None,
            shown=len(shown),
            cut=cut,
            hint="raise limit to see more" if cut else None,
        ),
    }


def default_columns(ctx: Context) -> list[str]:
    """Pick the default run table columns: name, status, steps and common metrics.

    :param ctx: The query context.
    :return: The fields."""
    cond, params = scope_condition(ctx)
    common = ctx.index.store.db.execute(
        "SELECT j.key, count(*) AS n FROM runs, json_each(card, '$.metrics') j "
        f"WHERE {cond} GROUP BY j.key ORDER BY n DESC, j.key LIMIT 3",
        params,
    )
    return [
        "run.name",
        "run.status",
        "run.steps",
        *[f"metric.{r[0]}.last" for r in common],
    ]


def keys_kind(ctx: Context, q: m.Keys) -> dict[str, Any]:
    """Answer what exists in a selection.

    :param ctx: The query context.
    :param q: The query.
    :return: Metrics, config keys, data keys, tags and run counts."""
    runs, _ = select_runs(ctx, q, ["run.status", "run.tags"], config=True)
    ids = [r["_id"] for r in runs]
    db = ctx.index.store.db
    marks = ", ".join("?" * len(ids))
    metrics = db.execute(
        "SELECT j.key, count(*), max(json_extract(j.value, '$.last_step')) "
        f"FROM runs, json_each(card, '$.metrics') j WHERE runs.id IN ({marks}) "
        "GROUP BY j.key ORDER BY j.key",
        ids,
    ).fetchall()
    metrics = with_live_keys(ctx, runs, metrics)
    data = db.execute(
        "SELECT key, kind, count(DISTINCT run_id), count(*) FROM data "
        f"WHERE run_id IN ({marks}) GROUP BY key, kind ORDER BY key",
        ids,
    ).fetchall()
    config: dict[str, list[Any]] = defaultdict(list)
    for r in runs:
        for key, value in flatten(json.loads(r["_config"] or "{}")).items():
            config[key].append(value)
    tags = Counter(t for r in runs for t in r["run.tags"])
    return {
        "kind": "keys",
        "runs": len(runs),
        "status": dict(Counter(r["run.status"] for r in runs)),
        "metrics": {
            "columns": ["key", "runs", "last_step"],
            "rows": [list(row) for row in metrics],
        },
        "config": {
            "columns": ["key", "runs", "values"],
            "rows": [[f"config.{k}", len(v), summarize(v)] for k, v in sorted(config.items())],
        },
        "data": {
            "columns": ["key", "kind", "runs", "entries"],
            "rows": [list(row) for row in data],
        },
        "tags": dict(tags.most_common()),
        "meta": meta(ctx, matched=len(runs)),
    }


def with_live_keys(
    ctx: Context, runs: list[dict[str, Any]], metrics: list[tuple[str, int, Any]]
) -> list[tuple[str, int, Any]]:
    """Add the metrics running runs logged since their card was last written.

    A run rewrites its card every few minutes, so a new run's keys are in its columns first.

    :param ctx: The query context.
    :param runs: The selected runs.
    :param metrics: ``(key, runs, last_step)`` from the cards.
    :return: The rows with the running runs' column keys merged in."""
    out = {key: [n, last] for key, n, last in metrics}
    for r in runs:
        if r["run.status"] != "running":
            continue
        carded = {k for (k,) in ctx.index.store.db.execute(
            "SELECT j.key FROM runs, json_each(card, '$.metrics') j WHERE runs.id = ?", (r["_id"],)
        )}  # fmt: skip
        manifest, entries = open_columns(ctx.index.series / r["_id"])
        for key in entries.keys() - carded - {TIME_KEY}:
            row = out.setdefault(key, [0, None])
            steps = [x for x in (row[1], manifest.last_step) if x is not None]
            row[0] += 1
            row[1] = max(steps) if steps else None
    return sorted((k, n, last) for k, (n, last) in out.items())


def flatten(config: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Flatten a nested config into dotted keys (keys with dots are quoted).

    :param config: The config.
    :param prefix: The path so far.
    :return: Dotted key to leaf value."""
    out = {}
    for k, v in config.items():
        name = f'["{k}"]' if "." in k else (f".{k}" if prefix else k)
        path = f"{prefix}{name}"
        if isinstance(v, dict) and v:
            out |= flatten(v, path)
        else:
            out[path] = v
    return out


def summarize(values: list[Any]) -> Any:
    """Describe the values of a config key: up to 10 distinct values, else a range.

    :param values: The values across runs.
    :return: A sorted list of distinct values or ``{min, max, distinct}``."""
    distinct = {json.dumps(v, sort_keys=True): v for v in values}
    if len(distinct) <= 10:
        return sorted(distinct.values(), key=lambda v: (type(v).__name__, str(v)))
    nums = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
    if nums:
        return {"min": min(nums), "max": max(nums), "distinct": len(distinct)}
    return {"distinct": len(distinct)}


def series_kind(ctx: Context, q: m.Series) -> dict[str, Any]:
    """Answer curves, per run or aggregated by fields or over seeds.

    :param ctx: The query context.
    :param q: The query.
    :return: ``{curves, meta}``."""
    by = list(q.by or [])
    fields = ["run.name", *[f"metric.{y}.count" for y in q.y], *by]
    runs, _ = select_runs(ctx, q, fields)
    if q.steps and len(q.steps) != 2:
        raise QueryError("series: steps is [first, last], e.g. [0, 5000]")
    window = (q.steps[0], q.steps[1]) if q.steps else (None, None)
    if q.x not in ("_step", TIME_KEY, "_elapsed"):
        check_known(ctx, [parse_field(f"metric.{q.x}.last")])
    points = q.points or ctx.defaults["points"]
    if q.by or q.seeds:
        groups = (
            [(cfg, rs) for cfg, rs in seed_groups(runs, q.seeds)]
            if q.seeds and not q.by
            else group_by(runs, by)
        )
        n_curves = max(1, len(groups) * len(q.y))
        per_curve = max(2, min(points, CHART_BUDGET // n_curves))
        curves = [
            grouped_curve(ctx, label, rs, y, window, per_curve, q)
            for label, rs in groups
            for y in q.y
        ]
    else:
        n_curves = max(1, len(runs) * len(q.y))
        per_curve = max(2, min(points, CHART_BUDGET // n_curves))
        curves = []
        for r in runs:
            cols = Columns(index=ctx.index, run_id=r["_id"])
            for y in q.y:
                if (curve := run_curve(ctx, r, cols, y, window, per_curve, q)) is not None:
                    curves.append(curve)
            cols.close()
    return {
        "kind": "series",
        "curves": curves,
        "meta": meta(
            ctx,
            matched=len(runs),
            curves=len(curves),
            points=per_curve,
            downsampled=any(not cv.get("raw", False) for cv in curves),
            from_preview=sum(cv.get("source") == "preview" for cv in curves),
        ),
    }


def run_curve(
    ctx: Context,
    run: dict[str, Any],
    cols: Columns,
    y: str,
    window: tuple[int | None, int | None],
    points: int,
    q: m.Series,
) -> dict[str, Any] | None:
    """Build one run's curve, from the preview when it suffices, else the columns.

    :param ctx: The query context.
    :param run: The selected run.
    :param cols: The run's columns.
    :param y: The metric key.
    :param window: The step window.
    :param points: The point budget of the curve.
    :param q: The query.
    :return: The curve, or ``None`` if the run has no such metric."""
    head = {"run": run["_id"], "name": run.get("run.name"), "metric": y}
    status = ctx.index.store.run(run["_id"])["status"]
    plain = q.x == "_step" and window == (None, None) and q.smooth is None
    if plain and status != "running":
        try:
            preview = read_preview(ctx.index.logdir / run["_path"]).metrics.get(y)
        except (OSError, ValueError):
            preview = None
        if preview is not None and (curve := from_preview(preview, points)) is not None:
            return head | {"source": "preview"} | curve
    col = cols.get(y)
    if col is None:
        return None
    steps, values = col.steps, col.values
    if q.smooth is not None:
        end = len(steps) if window[1] is None else col.window(None, window[1])[1]
        values = ema(values[:end], q.smooth.ema)
        steps = steps[:end]
    curve = downsample(steps, values, window=window, points=points, nonfinite=col.nonfinite)
    if q.x != "_step":
        xs = curve["x"] if curve["raw"] else curve["first"]
        curve["x"] = map_x(cols, q.x, xs)
    return head | {"source": "columns"} | curve


def map_x(cols: Columns, x: str, steps: list[int]) -> list[Any]:
    """Map steps to another x axis: wall time, elapsed time or a metric's value.

    :param cols: The run's columns.
    :param x: ``_t``, ``_elapsed`` or a metric key.
    :param steps: The steps to map.
    :return: The x values; ``None`` where unknown."""
    col = cols.get(TIME_KEY if x in (TIME_KEY, "_elapsed") else x)
    if col is None:
        return [None] * len(steps)
    out = [value_at(col.steps, col.values, s) for s in steps]
    if x == "_elapsed" and len(col.values):
        t0 = col.values[0]
        out = [None if v is None else v - t0 for v in out]
    return out


def group_by(
    runs: list[dict[str, Any]], fields: list[str]
) -> list[tuple[dict[str, Any], list[dict[str, Any]]]]:
    """Group runs by the values of fields.

    :param runs: The selected runs with the fields' values.
    :param fields: The grouping fields.
    :return: ``(field values, runs)`` per group."""
    groups: dict[str, tuple[dict[str, Any], list]] = {}
    for r in runs:
        label = {f: r.get(f) for f in fields}
        groups.setdefault(json.dumps(label, sort_keys=True), (label, []))[1].append(r)
    return list(groups.values())


def grouped_curve(
    ctx: Context,
    label: dict[str, Any],
    runs: list[dict[str, Any]],
    y: str,
    window: tuple[int | None, int | None],
    points: int,
    q: m.Series,
) -> dict[str, Any]:
    """Aggregate the curves of a group per bucket: mean, band and run count.

    :param ctx: The query context.
    :param label: The group's field values (or config without the seed).
    :param runs: The group's runs.
    :param y: The metric key.
    :param window: The step window.
    :param points: The point budget of the curve.
    :param q: The query.
    :return: The aggregated curve."""
    series = []
    for r in runs:
        cols = Columns(index=ctx.index, run_id=r["_id"])
        if (col := cols.get(y)) is not None:
            steps, values = col.steps, col.values
            if q.smooth is not None:
                values = ema(values, q.smooth.ema)
            i, j = col.window(*window)
            a, b = finite_range(steps, values, i, j, col.nonfinite)
            if a < b:
                series.append((cols, steps, values, col.nonfinite, steps[a], steps[b - 1]))
                continue
        cols.close()
    out: dict[str, Any] = {
        "by": label,
        "runs": [r["_id"] for r in runs],
        "metric": y,
    }
    if not series:
        return out | {"x": [], "mean": [], "lo": [], "hi": [], "n": []}
    lo = min(s[4] for s in series)
    hi = max(s[5] for s in series)
    width = width_for(lo, hi, points)
    per_bucket: dict[int, list[float]] = defaultdict(list)
    for cols, steps, values, nonfinite, _, _ in series:
        means = bucket_means(steps, values, window=window, width=width, nonfinite=nonfinite)
        for b, v in means.items():
            per_bucket[b].append(v)
        cols.close()
    xs = sorted(per_bucket)
    mean, lo_band, hi_band, n = [], [], [], []
    for b in xs:
        vals = per_bucket[b]
        mu = math.fsum(vals) / len(vals)
        sd = (
            math.sqrt(math.fsum((v - mu) ** 2 for v in vals) / (len(vals) - 1))
            if len(vals) > 1
            else 0.0
        )
        match q.band:
            case "minmax":
                lo_v, hi_v = min(vals), max(vals)
            case "std":
                lo_v, hi_v = mu - sd, mu + sd
            case "stderr":
                se = sd / math.sqrt(len(vals))
                lo_v, hi_v = mu - se, mu + se
            case "none":
                lo_v = hi_v = None
            case _:
                raise QueryError(f"unknown band {q.band!r}")
        mean.append(mu)
        lo_band.append(lo_v)
        hi_band.append(hi_v)
        n.append(len(vals))
    return out | {
        "width": width,
        "x": xs,
        "mean": mean,
        "lo": lo_band,
        "hi": hi_band,
        "n": n,
    }


def data_kind(ctx: Context, q: m.Data) -> dict[str, Any]:
    """Answer logged tables, images and text of a key.

    :param ctx: The query context.
    :param q: The query.
    :return: ``{entries, meta}``."""
    runs, _ = select_runs(ctx, q, [])
    ids = {r["_id"]: r for r in runs}
    db = ctx.index.store.db
    marks = ", ".join("?" * len(ids))
    rows = db.execute(
        f"SELECT run_id, step, record FROM data WHERE key = ? AND run_id IN ({marks}) "
        "ORDER BY run_id, step",
        [q.key, *ids],
    ).fetchall()
    if not rows and ids:
        keys = [r[0] for r in db.execute(
            f"SELECT DISTINCT key FROM data WHERE run_id IN ({marks})", list(ids)
        )]  # fmt: skip
        if keys:
            raise QueryError(
                f"no data key {q.key!r} in {ctx.scope!r}.{closest(q.key, keys)}",
                code="not_found",
            )
    by_run: dict[str, list] = defaultdict(list)
    for run_id, step, record in rows:
        by_run[run_id].append((step, json.loads(record)))
    entries = []
    for run_id, items in by_run.items():
        match q.step:
            case "last":
                last = max(s for s, _ in items)
                items = [(s, r) for s, r in items if s == last]
            case "all":
                pass
            case int():
                items = [(s, r) for s, r in items if s == q.step]
            case [a, b]:
                items = [(s, r) for s, r in items if a <= s <= b]
            case _:
                raise QueryError("data: step is last, all, a step or [first, last]")
        run_dir = ctx.index.logdir / ids[run_id]["_path"]
        entries += [data_entry(run_id, run_dir, record) for _, record in items]
    limit = q.limit if q.limit is not None else ctx.defaults["entries"]
    return {
        "kind": "data",
        "key": q.key,
        "entries": entries[:limit],
        "meta": meta(ctx, matched=len(runs), entries=len(entries), cut=len(entries) > limit),
    }


def data_entry(run_id: str, run_dir: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Shape one logged entry for an answer: tables as columns, files as references.

    :param run_id: The run id.
    :param run_dir: The run directory.
    :param record: The ``_data.jsonl`` record.
    :return: The entry."""
    out = {"run": run_id, "step": record.get("_step"), "kind": record.get("kind")}
    if (caption := record.get("caption")) is not None:
        out["caption"] = caption
    if "columns" in record:
        out["columns"] = record["columns"]
    if "text" in record:
        out["text"] = record["text"]
    if path := record.get("path"):
        out["path"] = path
        out["file"] = str(run_dir / path)
        if record.get("kind") == "table" and path.endswith(".json"):
            try:
                out["columns"] = json.loads((run_dir / path).read_text())["columns"]
            except (OSError, ValueError, KeyError):
                pass
    return out


def timeline_kind(ctx: Context, q: m.Timeline) -> dict[str, Any]:
    """Answer notes and run events in time order.

    :param ctx: The query context.
    :param q: The query.
    :return: ``{entries, meta}``; the most recent ``limit`` entries, oldest first."""
    runs, _ = select_runs(ctx, q, [])
    ids = [r["_id"] for r in runs]
    since = parse_time(q.since) if q.since else None
    types = set(q.types) if q.types else None
    db = ctx.index.store.db
    entries = []
    marks = ", ".join("?" * len(ids))
    for run_id, t, step, kind, message, data in db.execute(
        f"SELECT run_id, t, step, kind, message, data FROM events WHERE run_id IN ({marks})",
        ids,
    ):
        if (types and kind not in types) or (since and (t or 0) < since):
            continue
        extra = json.loads(data or "{}")
        entries.append(
            {
                "t": t,
                "kind": "event",
                "type": kind,
                "run": run_id,
                "step": step,
                "description": message or describe_event(kind, extra),
            }
        )
    cond, params = in_scope("folder", ctx.scope)
    if ctx.run_id is not None:
        cond, params = "run_id = ?", [ctx.run_id]
    for path, folder, run_id, note_id, t, type_, description in db.execute(
        f"SELECT path, folder, run_id, id, t, type, description FROM notes WHERE {cond}",
        params,
    ):
        if (types and type_ not in types) or (since and t < since):
            continue
        entry = {
            "t": t,
            "kind": "note",
            "type": type_,
            "id": note_id,
            "group": folder,
            "run": run_id,
            "description": description,
        }
        if q.full:
            entry["body"] = read_markdown_doc(ctx.index.logdir / path, kind="note").body
        entries.append(entry)
    entries.sort(key=lambda e: e["t"] or 0)
    limit = q.limit if q.limit is not None else ctx.defaults["entries"]
    shown = entries[-limit:] if limit else []
    for e in shown:
        e["t"] = iso(e["t"])
    return {
        "kind": "timeline",
        "entries": shown,
        "meta": meta(ctx, matched=len(entries), cut=len(entries) > len(shown)),
    }


def describe_event(kind: str, data: dict[str, Any]) -> str:
    """Describe a lifecycle event in a few words.

    :param kind: The event kind.
    :param data: Its fields.
    :return: The description."""
    match kind:
        case "failed":
            tb = (data.get("traceback") or "").strip().splitlines()
            return f"failed: {tb[-1]}" if tb else "failed"
        case "killed":
            return f"killed by {data.get('signal') or data.get('reason') or 'a signal'}"
        case "attempt_started":
            step = data.get("resume_step")
            return "started" if step is None else f"resumed from step {step}"
        case "config_conflict":
            return f"config differs on resume: {', '.join(data.get('diff', {}))}"
        case _:
            return kind.replace("_", " ")


def parse_time(text: str) -> float:
    """Parse a date or ISO time as UTC.

    :param text: E.g. ``2026-10-01`` or ``2026-10-01T12:00:00Z``.
    :return: Unix time."""
    try:
        t = datetime.fromisoformat(str(text).replace("Z", "+00:00"))
    except ValueError:
        raise QueryError(f"since: {text!r} is not a date like 2026-10-01") from None
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc)
    return t.timestamp()


def iso(t: float | None) -> str | None:
    """Format a unix time as ISO 8601 UTC.

    :param t: The time.
    :return: The text, or ``None``."""
    if t is None:
        return None
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def groups_kind(ctx: Context, q: m.Groups) -> dict[str, Any]:
    """Answer the group tree with research status, check, verdict and run counts.

    :param ctx: The query context.
    :param q: The query; ``where`` may filter on ``path`` and ``proposal.*``.
    :return: ``{columns, rows, meta}``."""
    from beamtime.record.proposals import Target
    from beamtime.record.status import research_status

    for text in fields_of(q.where):
        if text != "path" and parse_field(text).ns != "proposal":
            raise QueryError(f"groups: filter on path or proposal.* fields, not {text!r}")
    db = ctx.index.store.db
    cond, params = in_scope("path", ctx.scope)
    paths = [r[0] for r in db.execute(f"SELECT path FROM folders WHERE {cond}", params)]
    base = 0 if ctx.scope in (".", "") else ctx.scope.count("/") + 1
    run_paths = {r[0] for r in db.execute("SELECT path FROM runs")}
    statuses = [
        (r[0], derived_status(r[1], r[2], ctx.now))
        for r in db.execute("SELECT folder, status, heartbeat FROM runs")
    ]
    columns = ["path", "proposal", "status", "check", "progress", "verdict", "runs", "direct"]
    columns += ["running", "finished", "failed", "killed", "lost", "view", "notes"]
    rows = []
    for path in sorted(paths):
        depth = 0 if path in (".", "") else path.count("/") + 1
        if path in run_paths or (q.depth != "all" and depth - base > int(q.depth)):
            continue
        research = research_status(Target(index=ctx.index, rel=path, run_id=None))
        values = {"path": path} | {f"proposal.{k}": research[k] for k in PROPOSAL_FIELDS}
        if not matches(q.where, values):
            continue
        below = [
            s
            for folder, s in statuses
            if path == "." or folder == path or folder.startswith(f"{path}/")
        ]
        counts = Counter(below)
        view = newest(ctx.index.folder_path(path) / c.VIEW)
        notes = db.execute("SELECT count(*) FROM notes WHERE folder = ?", (path,)).fetchone()[0]
        check = research["check"]
        if check and research["provisional"]:
            check += " (provisional)"
        rows.append(
            [
                path,
                research["statement"],
                research["status"],
                check,
                research["progress_text"],
                research["verdict"],
                len(below),
                sum(1 for folder, _ in statuses if folder == path),
                counts["running"],
                counts["finished"],
                counts["failed"],
                counts["killed"],
                counts["lost"],
                view.stem if view else None,
                notes,
            ]
        )
    return {
        "kind": "groups",
        "columns": columns,
        "rows": rows,
        "meta": meta(ctx, matched=len(rows)),
    }


def file_kind(ctx: Context, q: m.File) -> dict[str, Any]:
    """Answer a data file stored with a view.

    :param ctx: The query context.
    :param q: The query.
    :return: ``{columns, rows, meta}``."""
    view_dir = (ctx.index.folder_path(ctx.scope) / c.VIEW).resolve()
    path = (view_dir / q.path).resolve()
    if view_dir not in path.parents:
        raise QueryError(f"file {q.path!r} is outside {ctx.scope}/view")
    if not path.is_file():
        raise QueryError(f"no file {q.path!r} in {ctx.scope}/view", code="not_found")
    match path.suffix.lower():
        case ".csv":
            reader = csv.reader(io.StringIO(path.read_text()))
            header, *body = list(reader)
            columns = header
            rows = [[number_or_text(v) for v in row] for row in body]
        case ".json":
            data = json.loads(path.read_text())
            if isinstance(data, dict) and "columns" in data and isinstance(data["columns"], dict):
                data = data["columns"]
            if isinstance(data, dict):
                columns = list(data)
                rows = [list(r) for r in zip(*data.values(), strict=False)]
            else:
                columns = list(dict.fromkeys(k for r in data for k in r))
                rows = [[r.get(k) for k in columns] for r in data]
        case ".parquet":
            try:
                import pyarrow.parquet as pq
            except ImportError:
                raise QueryError(
                    "reading Parquet view files needs PyArrow: pip install pyarrow"
                ) from None
            table = pq.read_table(path).to_pydict()
            columns = list(table)
            rows = [list(r) for r in zip(*table.values(), strict=False)]
        case other:
            raise QueryError(f"file: unsupported format {other!r}; use csv, json or parquet")
    return {
        "kind": "file",
        "group": ctx.scope,
        "path": q.path,
        "columns": columns,
        "rows": rows,
        "meta": meta(ctx, matched=len(rows)),
    }


def number_or_text(value: str) -> Any:
    """Read a CSV cell as a number when it is one.

    :param value: The cell.
    :return: An int, a float or the text."""
    for kind in (int, float):
        try:
            return kind(value)
        except ValueError:
            continue
    return value


def importance_kind(ctx: Context, q: m.Importance) -> dict[str, Any]:
    """Refuse importance queries until v1.1.

    :param ctx: The query context.
    :param q: The query.
    :return: Never returns."""
    raise QueryError("importance comes in v1.1; use a runs query sorted by the target for now")


KIND_FUNCTIONS = {
    "keys": keys_kind,
    "runs": runs_kind,
    "series": series_kind,
    "data": data_kind,
    "timeline": timeline_kind,
    "groups": groups_kind,
    "file": file_kind,
    "importance": importance_kind,
}


def now() -> float:
    """Read the current time, for derived statuses.

    :return: Unix time."""
    return time.time()
