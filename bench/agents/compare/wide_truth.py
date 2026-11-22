"""Expected answers of the tasks on the ``wide`` data set, computed from the plain-files export."""

import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from truth import TruthRun, load_runs

SWEEPS = "sweeps/"
STABILITY = "long/stability"
SCHEDULES = "long/schedules"
STUDY = "study/optimizer"
COMPARED = ("sweeps/s04", "sweeps/s11")

LEADERS = 5
DIVERGENCE_FACTOR = 10
LEVEL = 0.95
# the check keeps six significant digits; the truth rounds alike, so the two compare exactly.
DIGITS = 6


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
        "check-all": check_all(runs, files_root),
        "stale-verdicts": stale_verdicts(runs, files_root),
        "cross-group": cross_group(runs),
        "record-history": record_history(runs, files_root),
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


def t_density(t: float, df: float) -> float:
    """Give the density of Student's t distribution.

    :param t: The point.
    :param df: The degrees of freedom, possibly fractional.
    :return: The density."""
    norm = math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi)
    return norm * (1 + t * t / df) ** (-(df + 1) / 2)


def t_quantile(p: float, df: float) -> float:
    """Invert the distribution function of Student's t for ``0.5 < p < 1``: bisection on the
    integral of the density (Simpson's rule), so no statistics library is needed.

    :param p: The probability.
    :param df: The degrees of freedom, possibly fractional.
    :return: The quantile."""

    def cdf(t: float, panels: int = 2000) -> float:
        h = t / panels
        inner = math.fsum((4 if i % 2 else 2) * t_density(i * h, df) for i in range(1, panels))
        return 0.5 + h / 3 * (t_density(0, df) + inner + t_density(t, df))

    lo, hi = 0.0, 100.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) < p else (lo, mid)
    return (lo + hi) / 2


def mean(xs: list[float]) -> float:
    """Average exactly.

    :param xs: The values.
    :return: The mean."""
    return math.fsum(xs) / len(xs)


def variance(xs: list[float]) -> float:
    """Give the sample variance.

    :param xs: At least two values.
    :return: The sum of squares over ``n - 1``."""
    m = mean(xs)
    return math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def mean_interval(xs: list[float]) -> tuple[float, float, float]:
    """Give the mean of the values and its t-interval at 95 %.

    :param xs: At least two values.
    :return: The mean, the lower and the upper end."""
    m, n = mean(xs), len(xs)
    half = t_quantile((1 + LEVEL) / 2, n - 1) * math.sqrt(variance(xs) / n)
    return m, m - half, m + half


def welch_interval(a: list[float], b: list[float]) -> tuple[float, float, float]:
    """Give the difference of two means and its Welch t-interval at 95 %.

    :param a: At least two values.
    :param b: At least two values.
    :return: The difference ``mean(a) - mean(b)``, the lower and the upper end."""
    va, vb = variance(a) / len(a), variance(b) / len(b)
    df = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))
    half = t_quantile((1 + LEVEL) / 2, df) * math.sqrt(va + vb)
    d = mean(a) - mean(b)
    return d, d - half, d + half


def decide(op: str, lo: float, hi: float, threshold: float) -> str:
    """Judge an interval against the claim ``estimate op threshold``.

    :param op: ``<``, ``<=``, ``>`` or ``>=``.
    :param lo: The lower end.
    :param hi: The upper end.
    :param threshold: What the estimate is compared with.
    :return: ``confirmed`` when the whole interval satisfies the claim, ``refuted`` when the whole
        interval violates it, else ``inconclusive``."""
    if op.startswith(">"):
        # x > t is -x < -t
        lo, hi, threshold, op = -hi, -lo, -threshold, op.replace(">", "<")
    strict = op == "<"
    if hi < threshold if strict else hi <= threshold:
        return "confirmed"
    if lo >= threshold if strict else lo > threshold:
        return "refuted"
    return "inconclusive"


def significant(x: float) -> float:
    """Round to the digits the check keeps.

    :param x: The number.
    :return: The rounded number."""
    return float(f"{x:.{DIGITS}g}")


def finals(runs: list[TruthRun], where: dict[str, Any], metric: str) -> list[tuple[dict, float]]:
    """Give the config and final value of the finished study runs that match a condition.

    :param runs: All runs.
    :param where: ``config.<key>`` mapped to its value.
    :param metric: The metric; runs that never logged it are left out.
    :return: ``(config, last logged value)`` per run."""
    return [
        (r.config, r.final(metric))
        for r in runs
        if r.group == STUDY
        and r.finished
        and r.final(metric) is not None
        and all(r.config.get(k.removeprefix("config.")) == v for k, v in where.items())
    ]


def check_each(pr: dict[str, Any], runs: list[TruthRun]) -> dict[str, Any]:
    """Test a prediction of the ``each`` kind: every point, the mean over the seeds of the runs that
    agree on all other config keys, satisfies the claim against the value.

    :param pr: The prediction from the proposal.
    :param runs: All runs.
    :return: ``verdict``, ``effect`` (the worst point's mean minus the value), ``ci`` and
        ``points``."""
    seed = pr["seeds"].removeprefix("config.")
    by_point: dict[tuple, list[float]] = defaultdict(list)
    for config, value in finals(runs, pr.get("where", {}), pr["reduce"]["metric"]):
        by_point[tuple(sorted((k, v) for k, v in config.items() if k != seed))].append(value)
    op, margin, base = pr["op"], pr.get("margin", 0), pr["value"]
    threshold = base + (margin if op.startswith(">") else -margin)
    points = [mean_interval(v) for v in by_point.values()]
    verdicts = {decide(op, lo, hi, threshold) for _, lo, hi in points}
    worst = (
        min(points, key=lambda p: p[1]) if op.startswith(">") else max(points, key=lambda p: p[2])
    )
    return {
        "verdict": "refuted"
        if "refuted" in verdicts
        else verdicts.pop()
        if len(verdicts) == 1
        else "inconclusive",
        "effect": significant(worst[0] - base),
        "ci": [significant(worst[1] - base), significant(worst[2] - base)],
        "points": len(points),
    }


def check_compare(pr: dict[str, Any], runs: list[TruthRun]) -> dict[str, Any]:
    """Test a prediction of the ``compare`` kind: the runs of ``a`` against those of ``b``, with a
    Welch interval of the difference of their means.

    :param pr: The prediction from the proposal.
    :param runs: All runs.
    :return: ``verdict``, ``effect`` (mean of ``a`` minus mean of ``b``), ``ci`` and ``points``
        (the runs on both sides)."""
    metric = pr["reduce"]["metric"]
    a, b = ([v for _, v in finals(runs, pr[side], metric)] for side in ("a", "b"))
    effect, lo, hi = welch_interval(a, b)
    op, margin = pr["op"], pr.get("margin", 0)
    return {
        "verdict": decide(op, lo, hi, margin if op.startswith(">") else -margin),
        "effect": significant(effect),
        "ci": [significant(lo), significant(hi)],
        "points": len(a) + len(b),
    }


def front_matter(file: Path) -> dict[str, Any]:
    """Read the YAML head of a record file.

    :param file: A Markdown note, or a YAML proposal.
    :return: The fields."""
    text = file.read_text()
    return yaml.safe_load(text.split("---\n")[1] if text.startswith("---\n") else text)


def check_all(runs: list[TruthRun], files_root: Path) -> dict[str, Any]:
    """Test every prediction of the study's newest proposal against all its finished runs.

    :param runs: All runs.
    :param files_root: The folder that holds ``record/``.
    :return: ``predictions`` as ``{name, verdict, effect, ci, points}`` in the proposal's order."""
    folder = files_root / "record" / STUDY / "proposal"
    proposal = front_matter(max(folder.glob("*.yaml")))
    tests = {"each": check_each, "compare": check_compare}
    return {
        "predictions": [
            {"name": pr["name"], **tests[pr.get("test", "each")](pr, runs)}
            for pr in proposal["predictions"]
        ]
    }


def stale_verdicts(runs: list[TruthRun], files_root: Path) -> dict[str, Any]:
    """Find the predictions whose verdict in the study's newest verdict note no longer holds.

    :param runs: All runs.
    :param files_root: The folder that holds ``record/``.
    :return: ``changed`` as ``{name, old, new}``: the note's verdict and the one with all runs."""
    notes = [
        front_matter(f) | {"file": f.name}
        for f in (files_root / "record" / STUDY / "notes").glob("*.md")
    ]
    note = max((n for n in notes if n["type"] == "verdict"), key=lambda n: n["file"])
    now = {p["name"]: p["verdict"] for p in check_all(runs, files_root)["predictions"]}
    return {
        "changed": [
            {"name": name, "old": old, "new": now[name]}
            for name, old in note["verdicts"].items()
            if now[name] != old
        ]
    }


def cross_group(runs: list[TruthRun]) -> dict[str, Any]:
    """Compare two sweep groups by the mean final validation loss of their finished runs.

    :param runs: All runs.
    :return: ``groups`` as ``{group, runs, mean}``, in the order of ``COMPARED``, ``difference``
        (first minus second) and ``better`` (the group with the lower mean)."""
    groups = []
    for group in COMPARED:
        finals = [
            r.final("val/loss")
            for r in runs
            if r.group == group and r.finished and r.final("val/loss") is not None
        ]
        groups.append({"group": group, "runs": len(finals), "mean": mean(finals)})
    first, second = groups
    return {
        "groups": groups,
        "difference": first["mean"] - second["mean"],
        "better": min(groups, key=lambda g: g["mean"])["group"],
    }


def record_history(runs: list[TruthRun], files_root: Path) -> dict[str, Any]:
    """Find what changed in the study after its newest verdict note: the runs added since and the
    shift of each optimizer's mean final validation loss.

    A run belongs to the time before the note when it started before the note was written; both
    start with their time in the id, so the first fifteen characters tell.

    :param runs: All runs.
    :param files_root: The folder that holds ``record/``.
    :return: ``added`` (run ids, sorted) and ``change`` as ``{optimizer, change}``: the mean over
        all finished runs now minus the mean over those that started before the note."""
    folder = files_root / "record" / STUDY / "notes"
    written = max(f.stem for f in folder.glob("*.md") if front_matter(f)["type"] == "verdict")[:15]
    study = [r for r in runs if r.group == STUDY]
    finals: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    for r in study:
        if r.finished and (value := r.final("val/loss")) is not None:
            then, now = finals[r.config["optimizer"]]
            now.append(value)
            if r.id[:15] < written:
                then.append(value)
    return {
        "added": sorted(r.id for r in study if r.id[:15] >= written),
        "change": [
            {"optimizer": optimizer, "change": mean(now) - mean(then)}
            for optimizer, (then, now) in sorted(finals.items())
        ],
    }
