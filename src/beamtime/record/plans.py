"""Plans: which runs complete an experiment, and how far along it is."""

import itertools
import json
from typing import Any

from beamtime.query.where import compare
from beamtime.record.proposals import Proposal, RecordError, Target, current, load

DROPPED = ("failed", "killed", "lost")


def progress(
    target: Target, version: str, proposal: Proposal, members: list[dict[str, Any]]
) -> dict[str, Any]:
    """Measure a version's progress against its plan.

    :param target: The group or run.
    :param version: The version id.
    :param proposal: The version.
    :param members: Its runs, from ``Target.members``.
    :return: ``form``, ``done``, ``total``, ``complete``, ``fraction``, ``text``,
        the ``running`` count and the ``dropped`` runs (failed, killed, lost)."""
    finished = [r for r in members if r["status"] == "finished"]
    out: dict[str, Any] = {
        "running": sum(r["status"] == "running" for r in members),
        "dropped": [r["id"] for r in members if r["status"] in DROPPED],
    }
    match proposal.plan:
        case _ if target.run_id is not None:
            done, total = len(finished), 1
            complete = done == 1
            noun = "run finished"
            out["form"] = "run"
        case None:
            complete = completed_by_decision(target)
            done, total, noun = len(finished), None, None
            out["form"] = "none"
        case "children":
            done, total = children(target)
            complete = total > 0 and done == total
            noun = "subgroups complete"
            out["form"] = "children"
        case {"runs": int(n)}:
            done, total = min(len(finished), n), n
            complete = done == total
            noun = "runs"
            out["form"] = "runs"
        case {"grid": dict(grid)}:
            done, total = grid_points(target, version, grid)
            complete = done == total
            noun = "grid points"
            out["form"] = "grid"
        case _:
            raise RecordError(f"unknown plan {proposal.plan!r}")
    if total is not None:
        text = f"{done} of {total} {noun}"
    else:
        text = f"{done} finished run{'s' * (done != 1)}, no plan"
        text += "; a decision note completes it" if complete else ""
    if out["dropped"]:
        text += f"; {len(out['dropped'])} failed, killed or lost not counted"
    return out | {
        "done": done,
        "total": total,
        "complete": complete,
        "fraction": round(done / total, 3) if total else (1.0 if complete else None),
        "text": text,
    }


def grid_points(target: Target, version: str, grid: dict[str, list[Any]]) -> tuple[int, int]:
    """Count the grid points that have a finished run.

    :param target: The group or run.
    :param version: The version id.
    :param grid: Field to its planned values.
    :return: Points done and points planned."""
    fields = list(grid)
    runs = [
        r
        for r in target.select(version, {}, [*fields, "run.status"])
        if r["run.status"] == "finished"
    ]
    points = list(itertools.product(*grid.values()))
    done = sum(
        any(all(compare("eq", r[f], v) for f, v in zip(fields, point, strict=True)) for r in runs)
        for point in points
    )
    return done, len(points)


def children(target: Target) -> tuple[int, int]:
    """Count the subgroups with a proposal whose plans are complete.

    :param target: The group.
    :return: Complete subgroups and subgroups with a proposal."""
    row = target.index.store.folder(target.rel)
    names = json.loads(row["children"]) if row and row["children"] else []
    done = total = 0
    for name in names:
        rel = name if target.rel in (".", "") else f"{target.rel}/{name}"
        child = Target(index=target.index, rel=rel, run_id=None)
        if (version := current(child.dir)) is None:
            continue
        total += 1
        try:
            proposal = load(child.dir, version)
        except RecordError:
            continue
        done += progress(child, version, proposal, child.members(version))["complete"]
    return done, total


def completed_by_decision(target: Target) -> bool:
    """Tell whether a decision note declares a group's experiment complete.

    :param target: The group.
    :return: Whether any decision lists it in ``completes``."""
    keys = target.keys
    row = target.index.store.db.execute(
        "SELECT 1 FROM notes, json_each(notes.meta, '$.completes') j "
        f"WHERE notes.type = 'decision' AND j.value IN ({', '.join('?' * len(keys))}) LIMIT 1",
        keys,
    ).fetchone()
    return row is not None
