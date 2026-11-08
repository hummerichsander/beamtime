"""Selecting runs: the query context, ``from`` resolved to a scope, and the runs in it that match.

The research record builds on this module (its checks select runs with ``select_runs``); the
``proposal.*`` fields in turn need the record's status, so ``research`` imports it at call time."""

import posixpath
from dataclasses import dataclass
from typing import Any, Literal

from beamtime.format.ids import is_run_id
from beamtime.format.moves import current
from beamtime.format.run import derived_status
from beamtime.format.tree import is_reserved
from beamtime.index.columns import Column, open_columns
from beamtime.index.index import Index
from beamtime.index.store import in_scope
from beamtime.query import models as m
from beamtime.query.fields import Field, decode_cell, parse_field, sql
from beamtime.query.models import QueryError, closest
from beamtime.query.read import window_stat
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

    @property
    def defaults(self) -> dict[str, int]:
        """The caller's default limits."""
        return DEFAULTS[self.caller]


TOP_GROUPS = 12


def resolve_from(index: Index, base: str, target: str) -> tuple[str, str | None]:
    """Resolve ``from`` to a group relative to the log dir, or to one run.

    :param index: The index.
    :param base: The group relative paths start from (a view's group; ``.`` for CLI).
    :param target: The ``from`` value: a group, a run id, or ``@remote/...``.
    :return: The group relative to the log dir, and the run id if one run was named."""
    if target.startswith("@"):
        raise QueryError(
            f"from {target!r}: no remote source of that name is connected; configure it under "
            "remotes: in the settings, and run `beamtime serve` or name it in the call"
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
    if (
        not index.folder_path(rel).is_dir()
        and index.folder_path(moved := current(index.logdir, rel)).is_dir()
    ):
        # a path from before a group was moved names the group where it is now.
        rel = moved
    if not index.folder_path(rel).is_dir():
        parent = index.folder_path(posixpath.dirname(rel) or ".")
        options = [p.name for p in parent.iterdir() if p.is_dir()] if parent.is_dir() else []
        top = sorted(
            p.name
            for p in index.logdir.iterdir()
            if p.is_dir() and not p.name.startswith(".") and not is_reserved(p.name)
        )
        more = ", ..." if len(top) > TOP_GROUPS else ""
        raise QueryError(
            f"no group {rel!r} below the log dir."
            + closest(posixpath.basename(rel), options)
            + f" Top-level groups: {', '.join(top[:TOP_GROUPS])}{more}.",
            code="not_found",
        )
    return rel, None


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
            status = research(ctx, row[1], row[0])
            values |= {f.text: status[f.key] for f in proposal}
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
    return {"source": "local", "from": ctx.scope} | kwargs
