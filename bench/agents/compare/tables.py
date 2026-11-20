"""Write the comparison benchmark's report from a batch.

``uv run python bench/agents/compare/tables.py bench/agents/runs/compare-<stamp> [...]
[--out bench/agents/results]`` takes one batch per model and writes each into ``<out>/<alias>/``
(``sonnet``, ``haiku``): ``results.md`` (the facts, a table per task and setup, a table per setup;
cost first, then the score) and the figures ``tokens-vs-score`` and ``time-per-task`` as ``.pdf``
and ``.svg``. Given several batches it also writes ``<out>/models.md``, the per-setup table of
every model side by side. Ungraded sessions (``crashed``, ``not started``, ``usage limit``,
``judge failed``, not graded yet) are left out of every mean and counted; a session that leaked is
listed and left out of the figures only. Figures are refused when a setup lacks a task.
"""

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import figures

OUT = Path(__file__).resolve().parents[1] / "results"
COLUMNS = ["n", "tokens", "uncached", "cost", "seconds", "turns", "tool calls", "score", "correct"]


class Batch:
    """A batch's sessions: record and grade merged, graded ones apart from the rest."""

    def __init__(self, *, folder: Path) -> None:
        """Read ``batch.json``, every ``record.json`` and its ``grade.json``.

        :param folder: The batch's folder."""
        self.meta: dict[str, Any] = json.loads((folder / "batch.json").read_text())
        self.graded: list[dict[str, Any]] = []
        self.ungraded: Counter[str] = Counter()
        for path in sorted(folder.glob("*/record.json")):
            record = json.loads(path.read_text())
            record["name"] = path.parent.name
            grade = path.parent / "grade.json"
            if "ungraded" in record:
                self.ungraded[record["ungraded"]] += 1
            elif not grade.exists():
                self.ungraded["not graded yet"] += 1
            else:
                self.graded.append(record | json.loads(grade.read_text()))

    @property
    def name(self) -> str:
        """The folder of the batch's report: the model alias it ran with, else the model id."""
        return self.meta.get("alias") or self.meta["model"]

    @property
    def setups(self) -> list[str]:
        """The setups, in the order the batch ran them."""
        return self.meta["setups"]

    @property
    def tasks(self) -> list[str]:
        """The tasks of the batch."""
        return self.meta["tasks"]

    @property
    def leaked(self) -> list[dict[str, Any]]:
        """The graded sessions that leaked."""
        return [r for r in self.graded if r.get("leak")]

    @property
    def other_model(self) -> list[dict[str, Any]]:
        """The graded sessions that used another model than the pinned one."""
        return [r for r in self.graded if r.get("other_model")]

    @property
    def plotted(self) -> list[dict[str, Any]]:
        """The sessions of the figures: graded and without a leak, as flat rows."""
        return [
            {
                "setup": r["setup"],
                "task": r["task"],
                "seed": r["seed"],
                "tokens": r["tokens"]["total"],
                "seconds": r["seconds"],
                "score": r["score"],
            }
            for r in self.graded
            if not r.get("leak")
        ]


def uncached(record: dict[str, Any]) -> int:
    """Count the tokens a session did not read from the cache.

    :param record: The session's record.
    :return: Input, cache-write and output tokens."""
    t = record["tokens"]
    return t["input"] + t["cache_write"] + t["output"]


def spread(values: list[float], fmt: str) -> str:
    """Write the median and the range of values.

    :param values: The values; ``None`` entries are skipped.
    :param fmt: The format spec of one number.
    :return: ``median (min-max)``, or a dash without values."""
    values = [v for v in values if v is not None]
    if not values:
        return "-"
    return f"{statistics.median(values):{fmt}} ({min(values):{fmt}}-{max(values):{fmt}})"


def cells(rows: list[dict[str, Any]]) -> list[str]:
    """Summarize the sessions of one table row.

    :param rows: The graded sessions of the row.
    :return: One cell per entry of ``COLUMNS``."""
    return [
        str(len(rows)),
        spread([r["tokens"]["total"] for r in rows], ",.0f"),
        spread([uncached(r) for r in rows], ",.0f"),
        spread([r["cost_usd"] for r in rows], ".2f"),
        spread([r["seconds"] for r in rows], ".0f"),
        spread([r["turns"] for r in rows], ".0f"),
        spread([sum((r.get("tools") or {}).values()) for r in rows], ".0f"),
        f"{statistics.fmean(r['score'] for r in rows):.2f}",
        f"{sum(bool(r['correct']) for r in rows)}/{len(rows)}",
    ]


def table(head: list[str], body: list[list[str]]) -> list[str]:
    """Write a Markdown table.

    :param head: The column names.
    :param body: The rows.
    :return: The lines."""
    rows = [head, ["---"] * len(head), *body]
    return [f"| {' | '.join(row)} |" for row in rows]


def results(batch: Batch) -> str:
    """Write the report fragment of a batch.

    :param batch: The batch.
    :return: The Markdown of ``results.md``."""
    meta = batch.meta
    by_task = [
        [t, s, *cells(rows)]
        for t in batch.tasks
        for s in batch.setups
        if (rows := [r for r in batch.graded if r["task"] == t and r["setup"] == s])
    ]
    by_setup = [
        [s, *cells(rows)]
        for s in batch.setups
        if (rows := [r for r in batch.graded if r["setup"] == s])
    ]
    lines = [
        f"Model `{meta['model']}`, Claude Code {meta['claude_version']}, {meta['started'][:10]}, "
        f"data seeds {', '.join(map(str, meta['seeds']))}, {meta['reps']} rep per "
        "task, setup and seed.",
        "",
        f"{len(batch.graded)} graded sessions of "
        f"{len(batch.graded) + sum(batch.ungraded.values())}.",
    ]
    if batch.ungraded:
        left = ", ".join(f"{n} {why}" for why, n in sorted(batch.ungraded.items()))
        lines += ["", f"Left out of every mean, ungraded: {left}."]
    if batch.leaked:
        names = ", ".join(r["name"] for r in batch.leaked)
        lines += ["", f"Leaked (in the tables, left out of the figures): {names}."]
    if batch.other_model:
        names = ", ".join(r["name"] for r in batch.other_model)
        lines += ["", f"Another model than `{meta['model']}` took part in: {names}."]
    lines += [
        "",
        "Tokens, cost, seconds, turns and tool calls are the median of the sessions with the "
        "minimum and maximum in brackets. Uncached tokens are input, cache-write and output "
        "tokens; cache reads are only in the total. Score is the mean over sessions in [0, 1]; "
        "correct counts sessions with every check right.",
        "",
        "### Per task",
        "",
        *table(["task", "setup", *COLUMNS], by_task),
        "",
        "### Per setup, over all tasks",
        "",
        *table(["setup", *COLUMNS], by_setup),
        "",
    ]
    return "\n".join(lines)


def models(batches: list[Batch]) -> str:
    """Write the per-setup table of several batches, one row per setup and model.

    :param batches: The batches, one per model.
    :return: The Markdown of ``models.md``."""
    body = [
        [s, b.meta["model"], *cells(rows)]
        for s in batches[0].setups
        for b in batches
        if (rows := [r for r in b.graded if r["setup"] == s])
    ]
    lines = [
        "Per setup over all tasks, one row per model; the measures as in each model's "
        "`results.md`.",
        "",
        *table(["setup", "model", *COLUMNS], body),
        "",
    ]
    return "\n".join(lines)


def write_report(batch: Batch, out: Path) -> list[Path]:
    """Write ``results.md`` and the figures; refuse when a setup lacks a task in the figures.

    :param batch: The batch.
    :param out: The folder.
    :return: The files written.
    :raises ValueError: When a setup has no plottable session for a task."""
    rows = batch.plotted
    figures.check_complete(rows, setups=batch.setups, tasks=batch.tasks)
    out.mkdir(parents=True, exist_ok=True)
    md = out / "results.md"
    md.write_text(results(batch))
    return [
        md,
        *figures.tokens_vs_score(rows, setups=batch.setups, out=out),
        *figures.time_per_task(rows, setups=batch.setups, tasks=batch.tasks, out=out),
    ]


def main() -> None:
    """Write the report of the batch named on the command line."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "batch", type=Path, nargs="+", help="batch folders, bench/agents/runs/compare-<stamp>"
    )
    parser.add_argument("--out", type=Path, default=OUT, help="where the reports go")
    args = parser.parse_args()
    batches = [Batch(folder=f) for f in args.batch]
    if len({b.name for b in batches}) < len(batches):
        raise SystemExit("one batch per model: two batches have the same model")
    files = []
    for b in batches:
        try:
            files += write_report(b, args.out / b.name)
        except ValueError as e:
            raise SystemExit(f"figures of {b.name} refused: {e}") from None
    if len(batches) > 1:
        files.append(args.out / "models.md")
        files[-1].write_text(models(batches))
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
