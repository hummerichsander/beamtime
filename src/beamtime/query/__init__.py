"""The query language shared by CLI, MCP and views (layer 3)."""

import time
from pathlib import Path
from typing import Any

from beamtime.index.index import Index
from beamtime.query.kinds import KIND_FUNCTIONS
from beamtime.query.models import QueryError, parse
from beamtime.query.select import Caller, Context, resolve_from

__all__ = ["QueryError", "run"]


def run(
    query: Any,
    *,
    logdir: Path,
    caller: Caller = "cli",
    base: str = ".",
    budget_s: float = 0.2,
    index: Index | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    """Answer a query in its object form.

    :param query: E.g. ``{"runs": {"from": "scaling", "limit": 5}}``.
    :param logdir: The log dir.
    :param caller: ``cli``, ``mcp`` or ``view``; sets default limits.
    :param base: The group relative ``from`` paths start at (a view's group).
    :param budget_s: Seconds to spend catching up on new data first.
    :param index: An open index to reuse; by default one is opened and closed.
    :param now: The time run status is judged at; default now (a snapshot passes its own).
    :return: The canonical answer with ``meta``, including freshness."""
    kind, q = parse(query)
    own = index is None
    index = index or Index(logdir=logdir)
    try:
        target = q.view if kind == "file" else q.from_
        scope, run_id = resolve_from(index, base, target)
        freshness = index.catch_up(scope, budget_s)
        now = now or time.time()
        ctx = Context(index=index, caller=caller, scope=scope, run_id=run_id, now=now)
        answer = KIND_FUNCTIONS[kind](ctx, q)
        answer["meta"]["freshness"] = freshness.dump()
        return answer
    finally:
        if own:
            index.close()
