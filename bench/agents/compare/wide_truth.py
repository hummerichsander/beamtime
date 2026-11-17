"""Expected answers of the tasks on the ``wide`` data set, computed from the plain-files export."""

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from truth import TruthRun, load_runs

SWEEPS = "sweeps/"
STABILITY = "long/stability"
SCHEDULES = "long/schedules"

LEADERS = 5
DIVERGENCE_FACTOR = 10


def compute(files_root: Path, logdir: Path) -> dict[str, dict[str, Any]]:
    """Compute the expected values of the tasks on the ``wide`` data set.

    :param files_root: The folder that holds ``runs/`` (the plain-files export).
    :param logdir: The log dir the export was made from.
    :return: The task id mapped to its expected values."""
    runs = load_runs(files_root, logdir)
    return {
        "drivers": drivers(runs),
        "leaderboard": leaderboard(runs),
        "divergence": divergence(runs),
        "best-checkpoint": best_checkpoint(runs),
    }


def finished_sweeps(runs: list[TruthRun]) -> list[TruthRun]:
    """Select the finished runs of the sweeps that logged a validation loss.

    :param runs: All runs.
    :return: Their runs."""
    return [
        r
        for r in runs
        if r.group.startswith(SWEEPS) and r.finished and r.final("val/loss") is not None
    ]


def drivers(runs: list[TruthRun]) -> dict[str, Any]:
    """Find the config key that explains most of the final validation loss of the finished sweep runs.

    Per key except ``seed``, the share of the total sum of squares that lies between the runs of
    different values (eta squared).

    :param runs: All runs.
    :return: ``key``, ``best_value`` (the value with the lowest mean final loss), ``mean_at_best``
        and ``eta`` per key."""
    sweep = finished_sweeps(runs)
    finals = [r.final("val/loss") for r in sweep]
    grand = math.fsum(finals) / len(finals)
    total = math.fsum((v - grand) ** 2 for v in finals)
    eta, by_value = {}, {}
    for key in sorted(set().union(*(r.config for r in sweep)) - {"seed"}):
        groups: dict[Any, list[float]] = defaultdict(list)
        for r, v in zip(sweep, finals, strict=True):
            groups[r.config[key]].append(v)
        means = {value: math.fsum(v) / len(v) for value, v in groups.items()}
        eta[key] = math.fsum(len(groups[x]) * (m - grand) ** 2 for x, m in means.items()) / total
        by_value[key] = means
    key = max(eta, key=eta.__getitem__)
    best = min(by_value[key], key=by_value[key].__getitem__)
    return {"key": key, "best_value": best, "mean_at_best": by_value[key][best], "eta": eta}


def leaderboard(runs: list[TruthRun]) -> dict[str, Any]:
    """List the five finished sweep runs with the lowest final validation loss.

    :param runs: All runs.
    :return: ``runs`` as ``{id, group, val_loss}``, best first."""
    ranked = sorted(finished_sweeps(runs), key=lambda r: r.final("val/loss"))[:LEADERS]
    return {
        "runs": [{"id": r.id, "group": r.group, "val_loss": r.final("val/loss")} for r in ranked]
    }


def diverged_at(run: TruthRun) -> int | None:
    """Find the first step at which the training loss is NaN or infinite or more than 10 times the
    lowest finite training loss logged before that step.

    :param run: A run.
    :return: The step, or ``None`` when the run never diverges."""
    lowest = math.inf
    for step, value in run.values("train/loss"):
        if not math.isfinite(value) or value > DIVERGENCE_FACTOR * lowest:
            return step
        lowest = min(lowest, value)
    return None


def divergence(runs: list[TruthRun]) -> dict[str, Any]:
    """List the runs of ``long/stability`` that diverge and the step they do at.

    :param runs: All runs.
    :return: ``runs`` as ``{id, step}``, by step."""
    found = [(r.id, diverged_at(r)) for r in runs if r.group == STABILITY]
    hits = sorted(((i, s) for i, s in found if s is not None), key=lambda x: x[1])
    return {"runs": [{"id": i, "step": s} for i, s in hits]}


def lowest_finite(values: list[tuple[int, float]]) -> tuple[int, float]:
    """Find the first step of the lowest finite value.

    :param values: ``(step, value)`` in file order.
    :return: The step and value; NaN and infinite values never win."""
    return min(((s, v) for s, v in values if math.isfinite(v)), key=lambda x: x[1])


def best_checkpoint(runs: list[TruthRun]) -> dict[str, Any]:
    """Find per run of ``long/schedules`` the step of the lowest validation loss and the training
    loss at that step.

    :param runs: All runs.
    :return: ``runs`` as ``{id, step, train_loss}``, sorted by id."""
    rows = []
    for r in sorted((r for r in runs if r.group == SCHEDULES), key=lambda r: r.id):
        step, _ = lowest_finite(r.values("val/loss"))
        rows.append({"id": r.id, "step": step, "train_loss": dict(r.values("train/loss"))[step]})
    return {"runs": rows}
