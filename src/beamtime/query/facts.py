"""Run facts: what the group tools need to know about runs, read from the index alone."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from beamtime.index.index import Index
from beamtime.query import models as m
from beamtime.query.distinguish import flatten
from beamtime.query.select import Context, select_runs

FIELDS = [
    "run.name",
    "run.status",
    "run.code",
    "run.path",
    "run.group",
    "run.error",
    "run.steps",
    "run.attempts",
    "run.last_logged",
]

BARE_TYPE = re.compile(r"[A-Za-z_][\w.]*:?")
QUOTED = re.compile(r"(?<!\w)(?:'[^'\n]*'|\"[^\"\n]*\")")
PATH = re.compile(r"(?<![\w.])(?:[A-Za-z]:\\|~/|\.{1,2}/|/)[^\s'\",;:)]+")
NUMBER = re.compile(r"0x[0-9a-f]+|\d+(\.\d+)?")


@dataclass(frozen=True)
class RunFacts:
    """What the index knows about one run; ``config`` and ``metrics`` only when asked for."""

    id: str
    name: str | None
    status: str
    code: str | None
    group: str
    path: str
    dir: Path
    error: str | None
    steps: int | None
    attempts: int
    last_logged: float | None
    config: dict[str, Any] | None
    metrics: dict[str, dict[str, Any]] | None


def run_facts(
    index: Index,
    *,
    scope: str,
    run_id: str | None,
    now: float,
    where: dict[str, Any] | None = None,
    depth: Literal["all"] | int = "all",
    config: bool = False,
    metrics: bool = False,
    hidden: bool = False,
) -> list[RunFacts]:
    """List the runs of a scope that meet a condition, with their facts, without reading run files.

    Catches the index up once. Status is judged at ``now``.

    :param index: The open index.
    :param scope: The group relative to the log dir, or the run's path (see ``resolve``).
    :param run_id: The run id if one run was named, else ``None``.
    :param now: The time run status is judged at.
    :param where: A condition the runs must meet.
    :param depth: How many group levels below the scope to look into.
    :param config: Whether to include each run's flattened config.
    :param metrics: Whether to include each run's card statistics by metric.
    :param hidden: Whether to include hidden runs.
    :return: One ``RunFacts`` per run.
    :raises QueryError: As the query language does, e.g. for an unknown field in ``where``."""
    index.catch_up(scope)
    ctx = Context(index=index, caller="cli", scope=scope, run_id=run_id, now=now)
    sel = m.Selection(from_=scope, depth=depth, where=where or {}, hidden=hidden)
    rows, _ = select_runs(ctx, sel, FIELDS, config=config)
    return [
        RunFacts(
            id=row["_id"],
            name=row["run.name"],
            status=row["run.status"],
            code=row["run.code"],
            group=row["run.group"],
            path=row["run.path"],
            dir=index.logdir / row["run.path"],
            error=row["run.error"],
            steps=row["run.steps"],
            attempts=row["run.attempts"],
            last_logged=row["run.last_logged"],
            config=flatten(json.loads(row["_config"] or "{}")) if config else None,
            metrics=card_metrics(index, row["_id"]) if metrics else None,
        )
        for row in rows
    ]


def card_metrics(index: Index, run_id: str) -> dict[str, dict[str, Any]]:
    """Read a run's metric statistics from its indexed card.

    :param index: The index.
    :param run_id: The run id.
    :return: Metric key to its statistics; empty without a card."""
    row = index.store.db.execute(
        "SELECT json_extract(card, '$.metrics') FROM runs WHERE id = ?", (run_id,)
    ).fetchone()
    return json.loads(row[0]) if row and row[0] else {}


def failure_key(error: str | None, traceback: list[str] | None) -> str:
    """Name how a run failed: the signature of its recorded error, else of its traceback.

    :param error: The error the run's card recorded, if any.
    :param traceback: The last traceback in the run's output up to its exception line, if any.
    :return: The signature; empty without either."""
    if error:
        return failure_signature(error)
    return failure_signature("\n".join(traceback)) if traceback else ""


def failure_signature(text: str | None) -> str:
    """Reduce an error to what runs of one failure share: its normalized last line.

    A last line that is a bare exception type carries the line before it, so different failures
    re-raised without a message stay apart.

    :param text: An error message or traceback, or ``None``.
    :return: The signature; empty without an error."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return ""
    last = lines[-1]
    if BARE_TYPE.fullmatch(last) and len(lines) > 1:
        last = f"{last.rstrip(':')} (after: {lines[-2]})"
    last = QUOTED.sub("<str>", last)
    last = PATH.sub("<path>", last)
    return NUMBER.sub("#", last)[:120]
