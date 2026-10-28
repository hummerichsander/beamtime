"""The research status of a group or run, derived from its proposal, runs and notes."""

from typing import Any

from beamtime.record.check import evaluate, newest_verdict
from beamtime.record.proposals import RecordError, Target, current, load


def research_status(target: Target) -> dict[str, Any]:
    """Derive a group's (or run's) research status from its current proposal.

    :param target: The group or run.
    :return: ``status`` (open, proposed, running, evaluable, concluded), ``version``,
        ``statement``, ``check``, ``provisional``, ``progress`` (0 to 1),
        ``progress_text`` and ``verdict`` (the overall verdict on the current version)."""
    out: dict[str, Any] = {
        "status": "open",
        "version": None,
        "statement": None,
        "check": None,
        "provisional": None,
        "progress": None,
        "progress_text": None,
        "verdict": None,
    }
    if (version := current(target.dir)) is None:
        return out
    try:
        proposal = load(target.dir, version)
    except RecordError as e:
        return out | {
            "status": "proposed",
            "version": version,
            "check": "invalid",
            "problem": str(e),
        }
    if target.run_id is not None and proposal.blank:
        return out
    out |= {"version": version, "statement": proposal.statement}
    check = evaluate(target, version, proposal)
    plan = check.get("progress") or {}
    out |= {
        "check": check["result"],
        "provisional": check.get("provisional"),
        "progress": plan.get("fraction"),
        "progress_text": plan.get("text"),
    }
    if (verdict := newest_verdict(target, version)) is not None:
        return out | {"status": "concluded", "verdict": verdict.get("overall")}
    if not target.members(version):
        return out | {"status": "proposed"}
    return out | {"status": "evaluable" if plan.get("complete") else "running"}
