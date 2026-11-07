"""One function per query kind, each returning the canonical JSON answer."""

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.authored import newest, read_markdown_doc
from beamtime.format.run import derived_status, read_preview
from beamtime.format.times import iso, parse_iso
from beamtime.index.columns import TIME_KEY, open_columns
from beamtime.index.store import in_scope
from beamtime.query import models as m
from beamtime.query.aggregate import aggregate, group_by, seed_groups, sort_rows, spread
from beamtime.query.distinguish import distinguishing, flatten
from beamtime.query.fields import PROPOSAL as PROPOSAL_FIELDS
from beamtime.query.fields import parse_field
from beamtime.query.files import file_kind
from beamtime.query.models import QueryError, closest
from beamtime.query.read import (
    bucket_means,
    bucket_means_by_x,
    downsample,
    ema,
    finite_range,
    from_preview,
    is_monotone,
    width_for,
    x_values,
)
from beamtime.query.select import (
    Columns,
    Context,
    check_known,
    meta,
    research,
    scope_condition,
    select_runs,
)
from beamtime.query.where import fields_of, matches

CHART_BUDGET = 30_000


def runs_kind(ctx: Context, q: m.Runs) -> dict[str, Any]:
    """Answer a run table.

    :param ctx: The query context.
    :param q: The query.
    :return: ``{columns, rows, meta}``."""
    select = q.select or default_columns(ctx)
    sort = q.sort or ([] if q.seeds else ["-run.created_at"])
    sorted_by = [s.lstrip("-") for s in sort]
    runs, _ = select_runs(ctx, q, [*select, *sorted_by])
    if q.seeds:
        rows = []
        for _, group in seed_groups(runs, q.seeds):
            row = {"runs": [r["_id"] for r in group]}
            for f in dict.fromkeys([*select, *sorted_by]):
                row[f] = aggregate([r.get(f) for r in group])
            rows.append(row)
        columns = ["runs", *select]
    else:
        rows = [{"run.id": r["_id"]} | r for r in runs]
        columns = ["run.id", *[s for s in select if s != "run.id"]]
    sort_rows(rows, sort)
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
    :return: Metrics, config keys, data keys, tags, code versions and run counts."""
    runs, _ = select_runs(ctx, q, ["run.status", "run.tags", "run.code"], config=True)
    ids = [r["_id"] for r in runs]
    db = ctx.index.store.db
    marks = ", ".join("?" * len(ids))
    metrics = db.execute(
        "SELECT j.key, count(*), max(json_extract(j.value, '$.last_step')), "
        "min(json_extract(j.value, '$.min')) = max(json_extract(j.value, '$.max')) "
        "AND count(json_extract(j.value, '$.min')) = count(*), "
        "max(json_extract(j.value, '$.count')) "
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
    per_run = [flatten(json.loads(r["_config"] or "{}")) for r in runs]
    config: dict[str, list[Any]] = defaultdict(list)
    for cfg in per_run:
        for key, value in cfg.items():
            config[key].append(value)
    distinct = distinguishing(per_run)
    tags = Counter(t for r in runs for t in r["run.tags"])
    codes = Counter(r["run.code"] for r in runs if r["run.code"])
    return {
        "kind": "keys",
        "runs": len(runs),
        "status": dict(Counter(r["run.status"] for r in runs)),
        "metrics": {
            "columns": ["key", "runs", "last_step", "constant", "points"],
            # one value everywhere; a single point in a single run is a result, not a flat line.
            "rows": [
                [k, n, last, bool(same) and (n > 1 or (points or 0) > 1), points]
                for k, n, last, same, points in metrics
            ],
        },
        "config": {
            "columns": ["key", "runs", "values"],
            "rows": [[f"config.{k}", len(v), summarize(v)] for k, v in sorted(config.items())],
            "varying": distinct.varying,
            "aliases": distinct.aliases,
        },
        "data": {
            "columns": ["key", "kind", "runs", "entries"],
            "rows": [list(row) for row in data],
        },
        "tags": dict(tags.most_common()),
        # a fact only when members differ; a single code version isn't worth a line.
        "codes": dict(codes.most_common()) if len(codes) > 1 else {},
        "meta": meta(ctx, matched=len(runs)),
    }


def with_live_keys(
    ctx: Context, runs: list[dict[str, Any]], metrics: list[tuple[str, int, Any, Any, Any]]
) -> list[tuple[str, int, Any, Any, Any]]:
    """Add the metrics running runs logged since their card was last written.

    A run rewrites its card every few minutes, so a new run's keys are in its columns first.

    :param ctx: The query context.
    :param runs: The selected runs.
    :param metrics: ``(key, runs, last_step, one value, points)`` from the cards.
    :return: The rows with the running runs' column keys merged in."""
    out = {key: [n, last, same, points] for key, n, last, same, points in metrics}
    for r in runs:
        if r["run.status"] != "running":
            continue
        carded = {k for (k,) in ctx.index.store.db.execute(
            "SELECT j.key FROM runs, json_each(card, '$.metrics') j WHERE runs.id = ?", (r["_id"],)
        )}  # fmt: skip
        manifest, entries = open_columns(ctx.index.series / r["_id"])
        for key in entries.keys() - carded - {TIME_KEY}:
            # a column just opened has no card entry yet, so its constancy isn't known.
            row = out.setdefault(key, [0, None, False, None])
            steps = [x for x in (row[1], manifest.last_step) if x is not None]
            row[0] += 1
            row[1] = max(steps) if steps else None
            row[3] = max(row[3] or 0, entries[key].length)
    return sorted((k, *row) for k, row in out.items())


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
    if q.by or q.seeds:
        groups = (
            [(cfg, rs) for cfg, rs in seed_groups(runs, q.seeds)]
            if q.seeds and not q.by
            else group_by(runs, by)
        )
        per_curve = point_budget(ctx, q, len(groups) * len(q.y))
        curves = [
            grouped_curve(ctx, label, rs, y, window, per_curve, q)
            for label, rs in groups
            for y in q.y
        ]
    else:
        per_curve = point_budget(ctx, q, len(runs) * len(q.y))
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
            points="all" if q.points == "all" else per_curve,
            downsampled=any(not cv.get("raw", False) for cv in curves),
            from_preview=sum(cv.get("source") == "preview" for cv in curves),
        ),
    }


def point_budget(ctx: Context, q: m.Series, curves: int) -> int:
    """Share the chart's point budget between its curves.

    :param ctx: The query context.
    :param q: The query.
    :param curves: How many curves the answer has.
    :return: Points per curve; every point for ``points: all``."""
    if q.points == "all":
        return sys.maxsize
    return max(2, min(q.points or ctx.defaults["points"], CHART_BUDGET // max(1, curves)))


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
    head = {"run": run["_id"], "name": run.get("run.name"), "metric": y, "monotone": True}
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
        xs = x_values(cols, q.x, curve["x"] if curve["raw"] else curve["first"])
        known = [i for i, x in enumerate(xs) if x is not None]
        curve["x"] = xs
        for key, v in curve.items():
            if isinstance(v, list) and len(v) == len(xs):
                curve[key] = [v[i] for i in known]
        curve["monotone"] = is_monotone(curve["x"])
    return head | {"source": "columns"} | curve


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
    if q.x != "_step":
        return grouped_curve_by_x(ctx, label, runs, y, window, points, q)
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
    return out | {"width": width, "x": xs} | band_stats([per_bucket[b] for b in xs], q.band)


def grouped_curve_by_x(
    ctx: Context,
    label: dict[str, Any],
    runs: list[dict[str, Any]],
    y: str,
    window: tuple[int | None, int | None],
    points: int,
    q: m.Series,
) -> dict[str, Any]:
    """Aggregate the curves of a group per bucket of another x axis.

    :param ctx: The query context.
    :param label: The group's field values (or config without the seed).
    :param runs: The group's runs.
    :param y: The metric key.
    :param window: The step window.
    :param points: The point budget of the curve.
    :param q: The query.
    :return: The aggregated curve; ``x`` is the bucket centre."""
    series = []
    for r in runs:
        cols = Columns(index=ctx.index, run_id=r["_id"])
        known = []
        if (col := cols.get(y)) is not None:
            values = ema(col.values, q.smooth.ema) if q.smooth is not None else col.values
            i, j = col.window(*window)
            a, b = finite_range(col.steps, values, i, j, col.nonfinite)
            xs = x_values(cols, q.x, col.steps[a:b])
            known = [
                (x, v)
                for x, v in zip(xs, values[a:b], strict=True)
                if x is not None and math.isfinite(v)
            ]
        cols.close()
        if known:
            known_x, known_v = zip(*known, strict=True)
            if not is_monotone(known_x):
                raise QueryError(
                    f"series: aggregating needs a monotone x, and {q.x!r} is not "
                    f"in run {r['_id']}; show each run instead"
                )
            series.append((known_x, known_v))
    out: dict[str, Any] = {
        "by": label,
        "runs": [r["_id"] for r in runs],
        "metric": y,
    }
    if not series:
        return out | {"x": [], "mean": [], "lo": [], "hi": [], "n": []}
    lo = min(xs[0] for xs, _ in series)
    hi = max(xs[-1] for xs, _ in series)
    width = (hi - lo) / points
    per_bucket: dict[int, list[float]] = defaultdict(list)
    for xs, vs in series:
        for b, v in bucket_means_by_x(xs, vs, lo=lo, width=width, last=points - 1).items():
            per_bucket[b].append(v)
    buckets = sorted(per_bucket)
    centres = [lo + (b + 0.5) * width for b in buckets]
    return (
        out | {"width": width, "x": centres} | band_stats([per_bucket[b] for b in buckets], q.band)
    )


def band_stats(per_bucket: list[list[float]], band: str) -> dict[str, list[Any]]:
    """Summarize the runs' bucket means of a grouped curve.

    :param per_bucket: The per-run means of every bucket, in x order.
    :param band: ``minmax``, ``std``, ``stderr`` or ``none``.
    :return: ``{mean, lo, hi, n}`` per bucket."""
    mean, lo, hi, n = [], [], [], []
    for vals in per_bucket:
        mu, sd = spread(vals)
        match band:
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
                raise QueryError(f"unknown band {band!r}")
        mean.append(mu)
        lo.append(lo_v)
        hi.append(hi_v)
        n.append(len(vals))
    return {"mean": mean, "lo": lo, "hi": hi, "n": n}


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
        # a note removed since the index last looked is gone from the timeline too.
        if not (ctx.index.logdir / path).is_file():
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
        e["t"] = None if e["t"] is None else iso(e["t"])
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
            if (reason := data.get("reason")) is not None:
                return f"killed · {reason.replace('_', ' ')}"
            return f"killed by {data.get('signal') or 'a signal'}"
        case "attempt_started":
            step = data.get("resume_step")
            return "started" if step is None else f"resumed from step {step}"
        case "config_conflict":
            return f"config differs on resume: {', '.join(data.get('diff', {}))}"
        case _:
            return kind.replace("_", " ")


def parse_time(text: str) -> float:
    """Parse ``since``: a date or ISO time, UTC unless it names a zone.

    :param text: E.g. ``2026-10-01`` or ``2026-10-01T12:00:00Z``.
    :return: Unix time."""
    try:
        return parse_iso(text)
    except ValueError:
        raise QueryError(f"since: {text!r} is not a date like 2026-10-01") from None


def groups_kind(ctx: Context, q: m.Groups) -> dict[str, Any]:
    """Answer the group tree with research status, check, verdict and run counts.

    :param ctx: The query context.
    :param q: The query; ``where`` may filter on ``path`` and ``proposal.*``.
    :return: ``{columns, rows, meta}``."""
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
        status = research(ctx, path, None)
        values = {"path": path} | {f"proposal.{k}": status[k] for k in PROPOSAL_FIELDS}
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
        check = status["check"]
        if check and status["provisional"]:
            check += " (provisional)"
        rows.append(
            [
                path,
                status["statement"],
                status["status"],
                check,
                status["progress_text"],
                status["verdict"],
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
