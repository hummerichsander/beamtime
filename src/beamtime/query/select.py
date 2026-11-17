"""Selecting runs: the query context, ``from`` resolved to a scope, and the runs in it that match.

The research record builds on this module (its checks select runs with ``select_runs``); the
``proposal.*`` fields in turn need the record's status, so ``research`` imports it at call time."""

import math
from dataclasses import dataclass, field
from typing import Any, Literal

from beamtime.format.run import derived_status
from beamtime.index.columns import Column, open_columns
from beamtime.index.index import Index
from beamtime.index.store import in_scope
from beamtime.query import models as m
from beamtime.query.fields import SERIES_STATS, Field, decode_cell, parse_field, sql
from beamtime.query.models import QueryError, closest
from beamtime.query.read import nonfinite_step, rise_step, value_at, window_stat
from beamtime.query.resolve import resolve
from beamtime.query.where import fields_of, matches, number

Caller = Literal["cli", "mcp", "view"]
DEFAULTS: dict[str, dict[str, int]] = {
    "cli": {"rows": 50, "points": 100, "entries": 30},
    "mcp": {"rows": 50, "points": 100, "entries": 30},
    "view": {"rows": 1000, "points": 1000, "entries": 200},
}


@dataclass(kw_only=True)
class Context:
    """What a query runs against."""

    index: Index
    caller: Caller
    scope: str
    run_id: str | None
    now: float
    ingested: set[str] = field(default_factory=set)

    @property
    def defaults(self) -> dict[str, int]:
        """The caller's default limits."""
        return DEFAULTS[self.caller]


def resolve_from(index: Index, base: str, target: str) -> tuple[str, str | None]:
    """Resolve ``from`` to a group relative to the log dir, or to one run.

    :param index: The index.
    :param base: The group relative paths start from (a view's group; ``.`` for CLI).
    :param target: The ``from`` value: a group, a run id, id suffix or name, or ``@remote/...``.
    :return: The group relative to the log dir, and the run id if one run was named."""
    r = resolve(index, target, base=base)
    return r.path, r.run_id


class Columns:
    """Lazily opened column files of one run."""

    def __init__(self, *, index: Index, run_id: str, ingested: set[str] | None = None) -> None:
        """Prepare access to a run's columns, ingesting its streams first when they are stale.

        :param index: The index.
        :param run_id: The run id.
        :param ingested: Collects the id of a run this call had to ingest."""
        if index.ensure_streams(run_id) and ingested is not None:
            ingested.add(run_id)
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
    # the steps a window refers to are fetched like fields but not part of the answer.
    steps = [r for f in fields if (r := f.ref) is not None and r not in fields]
    check_known(ctx, [*fields, *steps])
    exprs = [(f, e) for f in [*fields, *steps] if (e := sql(f)) is not None]
    whole = "config" if config else "NULL"
    cols = ", ".join(["id", "path", "status", "heartbeat", whole, *[e for _, e in exprs]])
    cond, params = scope_condition(ctx, sel.depth)
    if restrict is not None:
        cond, params = f"{cond} AND {restrict[0]}", [*params, *restrict[1]]
    pre, pre_params = prefilter(sel.where, dict(exprs))
    rows = ctx.index.store.db.execute(
        f"SELECT {cols} FROM runs WHERE {cond}{pre}", [*params, *pre_params]
    ).fetchall()
    windowed = [
        f for f in fields if f.window is not None or f.ref is not None or f.stat in SERIES_STATS
    ]
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
            status = research(ctx, row[1], row[0])
            values |= {f.text: status[f.key] for f in proposal}
        if windowed:
            cols_ = Columns(index=ctx.index, run_id=row[0], ingested=ctx.ingested)
            for f in windowed:
                values[f.text] = series_field(f, cols_, values)
            cols_.close()
        for r in steps:
            values.pop(r.text, None)
        if matches(sel.where, values):
            out.append(values)
    return out, fields


def series_field(f: Field, cols: Columns, values: dict[str, Any]) -> Any:
    """Compute a field that reads a metric's column: a window, a step or a value at a step.

    :param f: The field.
    :param cols: The run's columns.
    :param values: The run's SQL-backed field values, which hold the card's steps.
    :return: The value, or ``None`` without a column."""
    if (col := cols.get(f.key)) is None:
        return None
    if f.ref is not None:
        if f.ref.stat in SERIES_STATS:
            step = series_field(f.ref, cols, values)
        else:
            step = values[f.ref.text]
        value = None if step is None else value_at(col.steps, col.values, step)
        # answers carry no NaN or infinity (not JSON), so a non-finite value reads as empty.
        return value if value is not None and math.isfinite(value) else None
    match f.stat:
        case "nonfinite_step":
            return nonfinite_step(col.steps, col.values) if col.nonfinite else None
        case "rise_step":
            return rise_step(col.steps, col.values, f.arg)
        case _:
            return window_stat(col.steps, col.values, f.window, f.stat, nonfinite=col.nonfinite)


def research(ctx: Context, rel: str, run_id: str | None) -> dict[str, Any]:
    """Derive the research status of a group, or of a run from its own proposal.

    :param ctx: The query context.
    :param rel: The group or run path relative to the log dir.
    :param run_id: The run id, or ``None`` for a group.
    :return: ``status``, ``check``, ``progress``, ``verdict`` and the texts shown with them."""
    # the record imports this module, so it is imported here, at call time.
    from beamtime.record.proposals import Target
    from beamtime.record.status import research_status

    return research_status(Target(index=ctx.index, rel=rel, run_id=run_id, now=ctx.now))


def meta(ctx: Context, **kwargs: Any) -> dict[str, Any]:
    """Start an answer's meta.

    :param ctx: The query context.
    :param kwargs: Kind-specific entries.
    :return: The meta dict; freshness is added by ``run``."""
    return {"source": ".", "from": ctx.scope} | kwargs
