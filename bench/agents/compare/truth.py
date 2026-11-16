"""Expected answers of the comparison's tasks, computed from the plain-files export."""

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beamtime.record.stats import mean, welch_interval

SWEEP = "scaling/lr-sweep"
EGNN = "realistic/egnn-bench"
TOKENIZER = "tokenizer/bpe-vs-unigram"

LEVEL = 0.95
FIND_MIN = 0.922
FASTEST_AT = 0.85
PREDICTION_MIN = 0.1


@dataclass(kw_only=True)
class TruthRun:
    """One exported run with the status of its card."""

    group: str
    id: str
    config: dict[str, Any]
    rows: list[dict[str, float]]
    output: str
    finished: bool

    def values(self, key: str) -> list[tuple[int, float]]:
        """Give the logged values of a metric.

        :param key: The metric key.
        :return: ``(step, value)`` in file order, without the rows that did not log the key."""
        return [(int(r["step"]), r[key]) for r in self.rows if key in r]

    def final(self, key: str) -> float | None:
        """Give the last logged value of a metric, not the value of the last row.

        :param key: The metric key.
        :return: The value, or ``None`` when the run never logged the key."""
        values = self.values(key)
        return values[-1][1] if values else None


def load_runs(files_root: Path, logdir: Path) -> list[TruthRun]:
    """Read the plain-files export; ``finished`` comes from the status in ``_run.json``.

    Only finished and not finished are told apart: a run that is running, lost or killed has not
    finished, and no truth value depends on which of the three it is.

    :param files_root: The folder that holds ``runs/``.
    :param logdir: The log dir the export was made from.
    :return: Every run, sorted by group and id."""
    runs = []
    for config_file in sorted((files_root / "runs").glob("*/*/*/config.json")):
        folder = config_file.parent
        group = folder.parent.relative_to(files_root / "runs").as_posix()
        card = json.loads((logdir / group / folder.name / "_run.json").read_text())
        runs.append(
            TruthRun(
                group=group,
                id=folder.name,
                config=json.loads(config_file.read_text()),
                rows=read_rows(folder / "metrics.csv"),
                output=(folder / "output.log").read_text(),
                finished=card["status"] == "finished",
            )
        )
    return runs


def read_rows(path: Path) -> list[dict[str, float]]:
    """Read a metrics CSV; empty cells are left out of their row.

    :param path: The ``metrics.csv`` of a run.
    :return: One dict per row with ``step``, ``time`` and the logged metrics as floats."""
    with path.open(newline="") as f:
        return [{k: float(v) for k, v in row.items() if v != ""} for row in csv.DictReader(f)]


def compute(files_root: Path, logdir: Path) -> dict[str, dict[str, Any]]:
    """Compute the expected values of every task.

    :param files_root: The folder that holds ``runs/`` (the plain-files export).
    :param logdir: The log dir the export was made from.
    :return: The task id mapped to its expected values."""
    runs = load_runs(files_root, logdir)
    return {
        "best-config": best_config(runs),
        "failures": failures(runs),
        "sweep-summary": sweep_summary(runs),
        "check-prediction": check_prediction(runs),
        "chart": chart(runs),
        "find-runs": find_runs(runs),
        "fastest": fastest(runs),
        "table": table(runs),
    }


def in_group(runs: list[TruthRun], group: str) -> list[TruthRun]:
    """Select the runs of one group.

    :param runs: All runs.
    :param group: The group path.
    :return: Its runs."""
    return [r for r in runs if r.group == group]


def finals_by(runs: list[TruthRun], group: str, key: str, metric: str) -> dict[Any, list[float]]:
    """Collect the final value of a metric per config value, over the finished runs of a group.

    :param runs: All runs.
    :param group: The group path.
    :param key: The config key to split by.
    :param metric: The metric key.
    :return: The config value mapped to one final value per finished run."""
    out: dict[Any, list[float]] = defaultdict(list)
    for r in in_group(runs, group):
        if r.finished and (value := r.final(metric)) is not None:
            out[r.config[key]].append(value)
    return dict(out)


def best_config(runs: list[TruthRun]) -> dict[str, Any]:
    """Find the lr with the best final val/acc of the sweep and test its lead over the runner-up.

    :param runs: All runs.
    :return: ``best_lr``, ``runner_up_lr``, ``difference``, ``ci`` (Welch, 95 %), ``significant``
        and the mean per lr."""
    finals = finals_by(runs, SWEEP, "lr", "val/acc")
    means = {lr: mean(v) for lr, v in finals.items()}
    best, runner_up = sorted(means, key=lambda lr: -means[lr])[:2]
    interval = welch_interval(finals[best], finals[runner_up], LEVEL)
    return {
        "best_lr": best,
        "runner_up_lr": runner_up,
        "difference": interval.estimate,
        "ci": [interval.lo, interval.hi],
        "significant": interval.lo > 0 or interval.hi < 0,
        "means": {str(lr): m for lr, m in means.items()},
    }


def failure_cause(run: TruthRun) -> str:
    """Read why a run stopped from the end of its output.

    :param run: A run that did not finish.
    :return: ``diverged`` (non-finite loss), ``killed`` (cancelled job) or ``unknown``."""
    tail = run.output.strip().splitlines()[-1] if run.output.strip() else ""
    if "FloatingPointError" in tail:
        return "diverged"
    if "CANCELLED" in tail or "SIGTERM" in tail:
        return "killed"
    return "unknown"


def failures(runs: list[TruthRun]) -> dict[str, Any]:
    """List the runs of the sweep that did not finish and why they stopped.

    :param runs: All runs.
    :return: ``ids`` and ``causes`` (id mapped to the cause)."""
    failed = [r for r in in_group(runs, SWEEP) if not r.finished]
    return {"ids": sorted(r.id for r in failed), "causes": {r.id: failure_cause(r) for r in failed}}


def sweep_summary(runs: list[TruthRun]) -> dict[str, Any]:
    """Average the final validation W1 energy per arm over the finished runs.

    :param runs: All runs.
    :return: ``per_arm``, ``best_arm`` (lowest) and ``exclude`` (the runs that did not finish)."""
    per_arm = {
        arm: mean(v) for arm, v in finals_by(runs, EGNN, "arm", "validation/w1_energy").items()
    }
    return {
        "per_arm": per_arm,
        "best_arm": min(per_arm, key=per_arm.__getitem__),
        "exclude": sorted(r.id for r in in_group(runs, EGNN) if not r.finished),
    }


def check_prediction(runs: list[TruthRun]) -> dict[str, Any]:
    """Test whether unigram lowers the final val/ppl against BPE by more than 0.1.

    :param runs: All runs.
    :return: ``effect`` (BPE minus unigram), ``ci`` (Welch, 95 %), ``threshold`` and ``verdict``
        (``confirmed``, ``refuted`` or ``inconclusive``)."""
    finals = finals_by(runs, TOKENIZER, "tokenizer", "val/ppl")
    interval = welch_interval(finals["bpe"], finals["unigram"], LEVEL)
    verdict = (
        "confirmed"
        if interval.lo > PREDICTION_MIN
        else "refuted"
        if interval.hi <= PREDICTION_MIN
        else "inconclusive"
    )
    return {
        "effect": interval.estimate,
        "ci": [interval.lo, interval.hi],
        "threshold": PREDICTION_MIN,
        "verdict": verdict,
    }


def chart(runs: list[TruthRun]) -> dict[str, Any]:
    """Give the points of the figure: the final val/acc of every finished run of the sweep.

    :param runs: All runs.
    :return: ``points`` as ``{id, lr, val_acc}`` sorted by lr and id."""
    points = [
        {"id": r.id, "lr": r.config["lr"], "val_acc": r.final("val/acc")}
        for r in in_group(runs, SWEEP)
        if r.finished
    ]
    return {"points": sorted(points, key=lambda p: (p["lr"], p["id"]))}


def find_runs(runs: list[TruthRun]) -> dict[str, Any]:
    """Find every run of the project whose last logged val/acc is at least 0.922.

    :param runs: All runs.
    :return: ``ids``, sorted; the status of a run does not matter."""
    finals = {r.id: r.final("val/acc") for r in runs}
    return {"ids": sorted(i for i, v in finals.items() if v is not None and v >= FIND_MIN)}


def fastest(runs: list[TruthRun]) -> dict[str, Any]:
    """Find the lr whose finished runs first reach val/acc 0.85 at the lowest mean step.

    An lr counts only when every finished run of it reaches the threshold.

    :param runs: All runs.
    :return: ``lr``, ``step`` (mean over its runs) and the mean step per lr."""
    first: dict[float, list[int | None]] = defaultdict(list)
    for r in in_group(runs, SWEEP):
        if r.finished:
            hits = [step for step, v in r.values("val/acc") if v >= FASTEST_AT]
            first[r.config["lr"]].append(hits[0] if hits else None)
    steps = {lr: mean(s) for lr, s in first.items() if None not in s}
    best = min(steps, key=steps.__getitem__)
    return {"lr": best, "step": steps[best], "steps": {str(lr): s for lr, s in steps.items()}}


def table(runs: list[TruthRun]) -> dict[str, Any]:
    """Give the rows of the sweep's table: id, lr, seed, whether it finished, final val/acc.

    :param runs: All runs.
    :return: ``rows``, sorted by id; ``val_acc`` is ``None`` for a run that never logged it."""
    rows = [
        {
            "id": r.id,
            "lr": r.config["lr"],
            "seed": r.config["seed"],
            "finished": r.finished,
            "val_acc": r.final("val/acc"),
        }
        for r in in_group(runs, SWEEP)
    ]
    return {"rows": sorted(rows, key=lambda row: row["id"])}
