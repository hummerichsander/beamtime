"""The comparison benchmark's two figures, from the graded sessions of a batch.

``tokens_vs_score`` is single column: total tokens against mean score, one point per setup.
``time_per_task`` is double column: wall seconds per task, one point per setup. Both are written as
``.pdf`` and ``.svg`` with the scienceplots theme as it is; ``tables.py`` calls them.
"""

import shutil
import statistics
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import scienceplots  # noqa: E402, F401

MARKERS = ["o", "s", "^", "D"]


def style() -> list[str]:
    """Pick the scienceplots style: without LaTeX on the machine, its text rendering is dropped.

    :return: The style names for ``plt.style.use``."""
    base = ["science", "nature"]
    return base if shutil.which("latex") else [*base, "no-latex"]


def check_complete(rows: list[dict[str, Any]], *, setups: list[str], tasks: list[str]) -> None:
    """Refuse figures where a setup lacks a task.

    :param rows: The sessions that enter the figures.
    :param setups: The batch's setups.
    :param tasks: The batch's tasks.
    :raises ValueError: Naming every missing (setup, task) pair."""
    have = {(r["setup"], r["task"]) for r in rows}
    missing = [f"{s}/{t}" for s in setups for t in tasks if (s, t) not in have]
    if missing:
        raise ValueError(f"no graded session without a leak for: {', '.join(missing)}")


def geometric_mean(values: list[float]) -> float:
    """Give the geometric mean of the positive values.

    :param values: The values.
    :return: Their geometric mean, 0 when none is positive."""
    positive = [v for v in values if v > 0]
    return statistics.geometric_mean(positive) if positive else 0.0


def save(fig: Any, out: Path, name: str) -> list[Path]:
    """Write a figure as ``.pdf`` and ``.svg``.

    :param fig: The matplotlib figure.
    :param out: The folder.
    :param name: The file name without suffix.
    :return: The two files."""
    paths = [out / f"{name}.pdf", out / f"{name}.svg"]
    for path in paths:
        fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return paths


def tokens_vs_score(rows: list[dict[str, Any]], *, setups: list[str], out: Path) -> list[Path]:
    """Plot total tokens per session against the mean score, one point per setup.

    Each seed gives one value per setup (geometric mean of the tokens and mean score over its
    tasks); the point is the mean over seeds and the bars span the seeds' minimum and maximum.

    :param rows: The graded sessions without a leak: ``setup``, ``seed``, ``tokens``, ``score``.
    :param setups: The setups, in plotting order.
    :param out: The folder.
    :return: The ``.pdf`` and ``.svg`` files."""
    with plt.style.context(style()):
        fig, ax = plt.subplots(figsize=(3.3, 2.5))
        for marker, setup in zip(MARKERS, setups, strict=False):
            mine = [r for r in rows if r["setup"] == setup]
            seeds = sorted({r["seed"] for r in mine})
            x = [geometric_mean([r["tokens"] for r in mine if r["seed"] == s]) for s in seeds]
            y = [statistics.fmean(r["score"] for r in mine if r["seed"] == s) for s in seeds]
            px, py = geometric_mean(x), statistics.fmean(y)
            ax.errorbar(
                px,
                py,
                xerr=[[px - min(x)], [max(x) - px]],
                yerr=[[py - min(y)], [max(y) - py]],
                fmt=marker,
                label=setup,
            )
        ax.set_xscale("log")
        ax.set_xlabel("Tokens per session")
        ax.set_ylabel("Mean score")
        ax.legend()
        return save(fig, out, "tokens-vs-score")


def time_per_task(
    rows: list[dict[str, Any]], *, setups: list[str], tasks: list[str], out: Path
) -> list[Path]:
    """Plot wall seconds per task, one point per setup: the median over seeds, bars min to max.

    :param rows: The graded sessions without a leak, with ``setup``, ``task``, ``seconds``.
    :param setups: The setups, in plotting order.
    :param tasks: The tasks, in plotting order.
    :param out: The folder.
    :return: The ``.pdf`` and ``.svg`` files."""
    with plt.style.context(style()):
        fig, ax = plt.subplots(figsize=(6.9, 2.5))
        step = 0.15
        for i, (marker, setup) in enumerate(zip(MARKERS, setups, strict=False)):
            xs, mid, low, high = [], [], [], []
            for j, task in enumerate(tasks):
                seconds = [r["seconds"] for r in rows if r["setup"] == setup and r["task"] == task]
                xs.append(j + (i - (len(setups) - 1) / 2) * step)
                mid.append(statistics.median(seconds))
                low.append(statistics.median(seconds) - min(seconds))
                high.append(max(seconds) - statistics.median(seconds))
            ax.errorbar(xs, mid, yerr=[low, high], fmt=marker, label=setup)
        ax.set_yscale("log")
        ax.set_xticks(range(len(tasks)), tasks)
        ax.set_ylabel("Seconds per session")
        ax.legend()
        return save(fig, out, "time-per-task")
