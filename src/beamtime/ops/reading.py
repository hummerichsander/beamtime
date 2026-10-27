"""The reading operations, shared by the CLI and MCP."""

import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.run import (
    read_card,
    read_config,
    read_events,
    read_output,
    read_run_info,
    run_status,
)
from beamtime.index.cache import daemon_status
from beamtime.index.index import Index
from beamtime.ops import registry as r
from beamtime.ops.budget import MAX_CHARS, cut, offset_of
from beamtime.ops.context import Context, OpError
from beamtime.query import QueryError
from beamtime.query import run as run_query
from beamtime.query.kinds import derived_status, describe_event, iso

RECENT_EVENTS = 10


def ask(ctx: Context, query: dict[str, Any], cursor: str | None = None) -> dict[str, Any]:
    """Answer a query for the context's log dir, with the caller's defaults and budget.

    :param ctx: The operation context.
    :param query: The query in its object form.
    :param cursor: A cursor from an earlier, cut answer.
    :return: The answer."""
    offset = offset_of(cursor)
    if not ctx.logdir.is_dir():
        raise OpError(
            f"no log dir at {ctx.logdir}; runs appear there once a script calls "
            "beamtime.init() (or set BEAMTIME_LOGDIR, or `beamtime init` to set up)",
            code=4,
        )
    try:
        answer = run_query(query, logdir=ctx.logdir, caller=ctx.caller)
    except QueryError as e:
        raise OpError(str(e), code=4 if e.code == "not_found" else 2) from None
    answer["meta"] = {k: v for k, v in answer["meta"].items() if v is not None}
    return cut(answer, offset)


def selection(p: r.Selection) -> dict[str, Any]:
    """Turn the shared selection parameters into query fields.

    :param p: The parameters.
    :return: ``from``, ``where`` and ``depth``."""
    return {"from": p.from_, "where": p.where, "depth": p.depth}


def keys(ctx: Context, p: r.KeysParams) -> dict[str, Any]:
    """List metrics, config keys, data keys and tags.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    return ask(ctx, {"keys": selection(p)})


def folders(ctx: Context, p: r.FoldersParams) -> dict[str, Any]:
    """Show the folder tree with proposals and run counts.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    return ask(ctx, {"folders": selection(p)}, p.cursor)


def runs(ctx: Context, p: r.RunsParams) -> dict[str, Any]:
    """Answer a run table.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {
        "select": p.select,
        "sort": p.sort,
        "limit": p.limit,
        "seeds": p.seeds,
    }
    return ask(ctx, {"runs": q}, p.cursor)


def series(ctx: Context, p: r.SeriesParams) -> dict[str, Any]:
    """Answer curves.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {
        "y": p.y,
        "x": p.x,
        "steps": p.steps,
        "points": p.points,
        "group": p.group,
        "seeds": p.seeds,
        "band": p.band,
        "smooth": {"ema": p.smooth} if p.smooth is not None else None,
    }
    return ask(ctx, {"series": q}, p.cursor)


def data(ctx: Context, p: r.DataParams) -> dict[str, Any]:
    """Answer logged tables, images and text.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {"key": p.key, "step": p.step, "limit": p.limit}
    return ask(ctx, {"data": q}, p.cursor)


def file(ctx: Context, p: r.FileParams) -> dict[str, Any]:
    """Answer a data file stored with a view.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    return ask(ctx, {"file": {"view": p.view, "path": p.path}})


def timeline(ctx: Context, p: r.TimelineParams) -> dict[str, Any]:
    """Answer notes and run events in time order.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {
        "types": p.types,
        "since": p.since,
        "limit": p.limit,
        "full": p.full,
    }
    return ask(ctx, {"timeline": q}, p.cursor)


def query(ctx: Context, p: r.QueryParams) -> dict[str, Any]:
    """Answer any query in its object form.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    return ask(ctx, p.query, p.cursor)


def find_run(ctx: Context, run_id: str) -> tuple[Index, Path]:
    """Find a run by id (or a unique id suffix) after catching up.

    :param ctx: The operation context.
    :param run_id: The run id.
    :return: The open index and the run directory."""
    index = Index(logdir=ctx.logdir)
    if (path := index.run_path(run_id)) is None:
        index.catch_up(".", budget_s=0.2)
        path = index.run_path(run_id)
    if path is None:
        hits = index.store.db.execute(
            "SELECT path FROM runs WHERE id LIKE ? OR name = ?", (f"%{run_id}", run_id)
        ).fetchall()
        if len(hits) == 1:
            path = ctx.logdir / hits[0][0]
        elif len(hits) > 1:
            index.close()
            raise OpError(f"{run_id!r} matches {len(hits)} runs; give the full run id", code=2)
    if path is None:
        index.close()
        raise OpError(f"no run {run_id!r} below {ctx.logdir}; `beamtime runs` lists them", code=4)
    return index, path


def card(ctx: Context, p: r.CardParams) -> dict[str, Any]:
    """Show one run's card with its identity, config, statistics and recent events.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    index, run_dir = find_run(ctx, p.run)
    try:
        freshness = index.catch_up(run_dir.relative_to(ctx.logdir).as_posix(), 0.2)
    finally:
        index.close()
    info = read_run_info(run_dir)
    status = run_status(info, heartbeat=(run_dir / c.RUN).stat().st_mtime, now=time.time())
    run_card = read_card(run_dir) if (run_dir / c.CARD).exists() else None
    events = read_events(run_dir)
    return {
        "kind": "card",
        "run": {
            "id": info.id,
            "name": info.name,
            "path": run_dir.relative_to(ctx.logdir).as_posix(),
            "status": status,
            "created_at": info.created_at,
            "ended_at": info.ended_at,
            "exit": info.exit,
            "tags": info.tags,
            "attempts": len(info.attempts),
            "host": info.host.get("hostname"),
            "scheduler": info.scheduler,
            "git": info.git,
            "proposals": info.proposals,
            "duration_s": run_card.duration_s if run_card else None,
            "steps": run_card.steps if run_card else None,
            "error": run_card.error if run_card else None,
            "warnings": run_card.warnings if run_card else 0,
        },
        "config": read_config(run_dir) if (run_dir / c.CONFIG).exists() else {},
        "metrics": {
            k: {f: v for f, v in m.__dict__.items() if v is not None}
            for k, m in (run_card.metrics if run_card else {}).items()
        },
        "values": run_card.values if run_card else {},
        "events": [
            {
                "t": iso(e.t),
                "type": e.kind,
                "step": e.step,
                "description": e.message or describe_event(e.kind, e.data),
            }
            for e in events[-RECENT_EVENTS:]
        ],
        "meta": {"source": "local", "freshness": freshness.dump()},
    }


def output(ctx: Context, p: r.OutputParams) -> dict[str, Any]:
    """Show a run's captured output, as the terminal showed it.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer: ``lines`` and how many there were in total."""
    index, run_dir = find_run(ctx, p.run)
    index.close()
    lines = [collapse(line) for line in read_output(run_dir, rank=p.rank).splitlines()]
    total = len(lines)
    if p.grep:
        try:
            pattern = re.compile(p.grep)
        except re.error as e:
            raise OpError(f"grep: {p.grep!r} is not a regular expression: {e}", code=2) from None
        lines = [f"{i + 1}: {line}" for i, line in enumerate(lines) if pattern.search(line)]
    shown = lines[-p.tail :] if p.tail else lines
    meta: dict[str, Any] = {
        "total_lines": total,
        "matched": len(lines),
        "shown": len(shown),
    }
    size = sum(len(line) + 1 for line in shown)
    while shown and size > MAX_CHARS:
        size -= len(shown.pop(0)) + 1
    if len(shown) < len(lines):
        meta["cut"] = True
        meta["hint"] = "earlier lines left out; use tail or grep to see them"
    return {
        "kind": "output",
        "run": run_dir.name,
        "rank": p.rank,
        "lines": shown,
        "meta": meta,
    }


def collapse(line: str) -> str:
    """Show a line as a terminal would after carriage returns (progress bars).

    :param line: A captured line.
    :return: The text after the last carriage return."""
    return line.rstrip("\r").rsplit("\r", 1)[-1]


def status(ctx: Context, p: r.NoParams) -> dict[str, Any]:
    """Report the daemon, the index and the log dir.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    index = Index(logdir=ctx.logdir)
    try:
        freshness = index.catch_up(".", 0.2) if ctx.logdir.is_dir() else None
        now = time.time()
        counts = Counter(
            derived_status(status, heartbeat, now)
            for status, heartbeat in index.store.db.execute("SELECT status, heartbeat FROM runs")
        )
        cache = index.cache
    finally:
        index.close()
    daemon = daemon_status(cache)
    return {
        "kind": "status",
        "root": str(ctx.root),
        "root_from": ctx.root_reason,
        "logdir": str(ctx.logdir),
        "logdir_exists": ctx.logdir.is_dir(),
        "cache": str(cache),
        "runs": dict(counts),
        "daemon": daemon,
        "web_ui": f"http://localhost:{daemon['port']}" if daemon and daemon.get("port") else None,
        "remotes": sorted(ctx.settings.get("remotes") or {}),
        "meta": {"freshness": freshness.dump() if freshness else None},
    }
