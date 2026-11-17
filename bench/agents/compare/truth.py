"""Expected answers of the comparison's tasks, computed from the plain-files export."""

import csv
import json
import math
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beamtime.record.stats import mean, paired_interval, welch_interval

SWEEP = "scaling/lr-sweep"
SWEEPS = (SWEEP, "scaling/lr-sweep-2")
ACCURACY = ("val/acc", "val/accuracy")
EGNN = "realistic/egnn-bench"
TOKENIZER = "tokenizer/bpe-vs-unigram"

LEVEL = 0.95
FIND_MIN = 0.922
FASTEST_AT = 0.9
PREDICTION_MIN = 0.2


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

    def accuracy(self) -> list[tuple[int, float]]:
        """Give the validation accuracy, under whichever of its two names the run logged it.

        :return: ``(step, value)`` in file order; empty when the run logged neither."""
        return next((v for key in ACCURACY if (v := self.values(key))), [])

    def final_accuracy(self) -> float | None:
        """Give the last logged validation accuracy.

        :return: The value, or ``None`` when the run never logged one."""
        values = self.accuracy()
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


def sweep_runs(runs: list[TruthRun]) -> list[TruthRun]:
    """Select the runs of both batches of the lr sweep.

    :param runs: All runs.
    :return: Their runs, oldest first; a run id starts with its start time."""
    return sorted((r for r in runs if r.group in SWEEPS), key=lambda r: r.id)


def latest(runs: list[TruthRun]) -> dict[tuple[float, int], TruthRun]:
    """Give the most recent run of every lr and seed of the sweep, whatever its status.

    :param runs: All runs.
    :return: ``(lr, seed)`` mapped to the run that counts for it."""
    return {(r.config["lr"], r.config["seed"]): r for r in sweep_runs(runs)}


def counted(runs: list[TruthRun]) -> list[TruthRun]:
    """Give the sweep runs that count: the most recent of each lr and seed, if it finished.

    :param runs: All runs.
    :return: The runs."""
    return [r for r in latest(runs).values() if r.finished]


def best_config(runs: list[TruthRun]) -> dict[str, Any]:
    """Find the lr with the best final validation accuracy of the sweep and test its lead.

    :param runs: All runs.
    :return: ``best_lr``, ``runner_up_lr``, ``difference``, ``ci`` (Welch, 95 %), ``significant``
        and the mean per lr."""
    finals: dict[float, list[float]] = defaultdict(list)
    for r in counted(runs):
        finals[r.config["lr"]].append(r.final_accuracy())
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
    :return: ``diverged`` (non-finite loss), ``oom`` (out of GPU memory), ``killed`` (cancelled
        job) or ``unknown``."""
    tail = run.output.strip().splitlines()[-1] if run.output.strip() else ""
    if "FloatingPointError" in tail:
        return "diverged"
    if "OutOfMemoryError" in tail:
        return "oom"
    if "CANCELLED" in tail or "SIGTERM" in tail:
        return "killed"
    return "unknown"


def failures(runs: list[TruthRun]) -> dict[str, Any]:
    """List the sweep runs that did not finish, why they stopped and which later run redid them.

    :param runs: All runs.
    :return: ``ids``, ``causes`` (id mapped to the cause) and ``reruns`` (id mapped to the most
        recent run of the same lr and seed when that one is newer and finished, else ``None``)."""
    failed = [r for r in sweep_runs(runs) if not r.finished]
    newest = latest(runs)
    reruns = {}
    for r in failed:
        later = newest[(r.config["lr"], r.config["seed"])]
        reruns[r.id] = later.id if later.id > r.id and later.finished else None
    return {
        "ids": sorted(r.id for r in failed),
        "causes": {r.id: failure_cause(r) for r in failed},
        "reruns": reruns,
    }


def checkpoint(run: TruthRun, *, monitor: str, metric: str) -> float:
    """Read a metric at the evaluation a trainer keeps: the lowest finite value of a monitor.

    :param run: A run.
    :param monitor: The metric whose lowest value picks the step, e.g. ``validation/loss``.
    :param metric: The metric to read at that step.
    :return: The metric's value at that step."""
    step, _ = min(((s, v) for s, v in run.values(monitor) if math.isfinite(v)), key=lambda x: x[1])
    return dict(run.values(metric))[step]


def sweep_summary(runs: list[TruthRun]) -> dict[str, Any]:
    """Average the validation W1 energy at each run's best-validation-loss checkpoint per arm.

    :param runs: All runs.
    :return: ``per_arm``, ``best_arm`` (lowest), ``exclude`` (the runs that did not finish) and
        ``per_arm_final`` (the means of the last values, the typical wrong answer)."""
    at_checkpoint: dict[str, list[float]] = defaultdict(list)
    last: dict[str, list[float]] = defaultdict(list)
    for r in in_group(runs, EGNN):
        if r.finished:
            at_checkpoint[r.config["arm"]].append(
                checkpoint(r, monitor="validation/loss", metric="validation/w1_energy")
            )
            last[r.config["arm"]].append(r.final("validation/w1_energy"))
    per_arm = {arm: mean(v) for arm, v in at_checkpoint.items()}
    return {
        "per_arm": per_arm,
        "best_arm": min(per_arm, key=per_arm.__getitem__),
        "exclude": sorted(r.id for r in in_group(runs, EGNN) if not r.finished),
        "per_arm_final": {arm: mean(v) for arm, v in last.items()},
    }


def check_prediction(runs: list[TruthRun]) -> dict[str, Any]:
    """Test whether unigram lowers the final val/ppl against BPE by more than 0.2, seed by seed.

    :param runs: All runs.
    :return: ``effect`` (mean of BPE minus unigram over the seeds with a finished run of each),
        ``ci`` (paired t-interval, 95 %), ``seeds``, ``threshold`` and ``verdict`` (``confirmed``,
        ``refuted`` or ``inconclusive``)."""
    finals = {
        (r.config["tokenizer"], r.config["seed"]): r.final("val/ppl")
        for r in in_group(runs, TOKENIZER)
        if r.finished
    }
    seeds = sorted(s for t, s in finals if t == "bpe" and ("unigram", s) in finals)
    interval = paired_interval(
        [finals["bpe", s] for s in seeds], [finals["unigram", s] for s in seeds], LEVEL
    )
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
        "seeds": seeds,
        "threshold": PREDICTION_MIN,
        "verdict": verdict,
    }


def chart(runs: list[TruthRun]) -> dict[str, Any]:
    """Give the points of the figure: the final validation accuracy of every counted sweep run.

    :param runs: All runs.
    :return: ``points`` as ``{id, lr, val_acc}`` sorted by lr and id, and the ``means`` per lr."""
    points = [
        {"id": r.id, "lr": r.config["lr"], "val_acc": r.final_accuracy()} for r in counted(runs)
    ]
    return {
        "points": sorted(points, key=lambda p: (p["lr"], p["id"])),
        "means": best_config(runs)["means"],
    }


def find_runs(runs: list[TruthRun]) -> dict[str, Any]:
    """Find every run of the project whose last validation accuracy is at least 0.922.

    :param runs: All runs.
    :return: ``ids``, sorted; the status of a run does not matter."""
    finals = {r.id: r.final_accuracy() for r in runs}
    return {"ids": sorted(i for i, v in finals.items() if v is not None and v >= FIND_MIN)}


def fastest(runs: list[TruthRun]) -> dict[str, Any]:
    """Find the lr whose counted runs first reach a validation accuracy of 0.9 at the lowest
    mean step.

    An lr qualifies only when every one of its counted runs reaches the threshold.

    :param runs: All runs.
    :return: ``lr``, ``step`` (mean over its runs) and the mean step per qualifying lr."""
    first: dict[float, list[int | None]] = defaultdict(list)
    for r in counted(runs):
        hits = [step for step, v in r.accuracy() if v >= FASTEST_AT]
        first[r.config["lr"]].append(hits[0] if hits else None)
    steps = {lr: mean(s) for lr, s in first.items() if None not in s}
    best = min(steps, key=steps.__getitem__)
    return {"lr": best, "step": steps[best], "steps": {str(lr): s for lr, s in steps.items()}}


def table(runs: list[TruthRun]) -> dict[str, Any]:
    """Give the rows of the sweep's table: id, lr, seed, finished, superseded, final accuracy.

    :param runs: All runs.
    :return: ``rows``, sorted by id; ``val_acc`` is ``None`` for a run that never logged it, and
        ``superseded`` tells whether a later run of the same lr and seed exists."""
    newest = latest(runs)
    rows = [
        {
            "id": r.id,
            "lr": r.config["lr"],
            "seed": r.config["seed"],
            "finished": r.finished,
            "superseded": newest[(r.config["lr"], r.config["seed"])].id != r.id,
            "val_acc": r.final_accuracy(),
        }
        for r in sweep_runs(runs)
    ]
    return {"rows": sorted(rows, key=lambda row: row["id"])}


TRUTHS: dict[str, Callable[[Path, Path], dict[str, dict[str, Any]]]] = {"s": compute}
