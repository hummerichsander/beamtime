"""Write the results of scored batches.

``python bench/agents/report.py bench/agents/runs/<stamp>`` writes RESULTS.md into the batch's
folder: one row per run, and the means per kind and model.
``python bench/agents/report.py --base <stamp> --new <stamp>`` prints per-task deltas between two
batches (reps of 3 or more on haiku and sonnet make a delta mean something).
"""

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
COLUMNS = "task kind model correct rounds errors tokens turns violations seconds".split()
NUMBERS = ("correct", "rounds", "tool_errors", "tokens", "turns", "violations")


def runs_of(stamp: Path) -> list[dict[str, Any]]:
    """Read the scored runs of a batch.

    :param stamp: The batch's folder.
    :return: One flat row per run: its record and score."""
    rows = []
    for folder in sorted(stamp.iterdir()):
        if (folder / "score.json").is_file():
            record = json.loads((folder / "record.json").read_text())
            score = json.loads((folder / "score.json").read_text())
            rows.append(
                {
                    "task": record["task"],
                    "kind": record.get("kind", "view"),
                    "model": record["model"],
                    "correct": bool(score.get("correct")),
                    "rounds": score.get("rounds"),
                    "tool_errors": score.get("tool_errors", 0),
                    "tokens": score.get("tokens"),
                    "turns": score.get("turns"),
                    "violations": sum((score.get("violations") or {}).values()),
                    "seconds": record.get("seconds"),
                }
            )
    return rows


def report(stamp: Path) -> Path:
    """Write the batch's RESULTS.md.

    :param stamp: The batch's folder.
    :return: The file."""
    rows = runs_of(stamp)
    lines = [
        f"# Agent tasks: {stamp.name}",
        "",
        table_row(COLUMNS),
        table_row(["---"] * len(COLUMNS)),
    ]
    for r in rows:
        cells = [r[k] if k != "errors" else r["tool_errors"] for k in COLUMNS]
        lines.append(table_row([str(c) for c in cells]))
    head = ["kind", "model", "runs", "correct", "rounds", "tool errors", "tokens", "violations"]
    lines += ["", "## Per kind and model", "", table_row(head), table_row(["---"] * len(head))]
    for kind, model in sorted({(r["kind"], r["model"]) for r in rows}):
        mine = [r for r in rows if (r["kind"], r["model"]) == (kind, model)]
        cells = [
            kind,
            model,
            len(mine),
            f"{sum(r['correct'] for r in mine)}/{len(mine)}",
            mean(mine, "rounds"),
            mean(mine, "tool_errors"),
            mean(mine, "tokens"),
            mean(mine, "violations"),
        ]
        lines.append(table_row([str(c) for c in cells]))
    file = stamp / "RESULTS.md"
    file.write_text("\n".join(lines) + "\n")
    return file


def compare(base: Path, new: Path) -> str:
    """Compare two batches task by task and model by model.

    :param base: The batch before a change.
    :param new: The batch after it.
    :return: A Markdown table of the means and the delta; ``n`` is the reps, base/new."""
    before, after = runs_of(base), runs_of(new)
    head = ["task", "model", "n", *(f"{k} (base → new)" for k in NUMBERS)]
    lines = [table_row(head), table_row(["---"] * len(head))]
    for task, model in sorted(
        {(r["task"], r["model"]) for r in before} & {(r["task"], r["model"]) for r in after}
    ):
        a = [r for r in before if (r["task"], r["model"]) == (task, model)]
        b = [r for r in after if (r["task"], r["model"]) == (task, model)]
        cells = [task, model, f"{len(a)}/{len(b)}" + ("" if min(len(a), len(b)) >= 3 else " (< 3)")]
        for key in NUMBERS:
            x, y = value(a, key), value(b, key)
            cells.append("–" if x is None or y is None else f"{x:.2f} → {y:.2f} ({y - x:+.2f})")
        lines.append(table_row(cells))
    return "\n".join(lines)


def value(rows: list[dict[str, Any]], key: str) -> float | None:
    """Average a number over runs, ignoring runs without it.

    :param rows: The runs.
    :param key: The number's key.
    :return: The mean, or ``None`` if no run has it."""
    values = [float(r[key]) for r in rows if r.get(key) is not None]
    return statistics.fmean(values) if values else None


def mean(rows: list[dict[str, Any]], key: str) -> str:
    """Show a mean of a number.

    :param rows: The runs.
    :param key: The number's key.
    :return: E.g. ``3.5``, or ``–``."""
    v = value(rows, key)
    return "–" if v is None else f"{v:.1f}"


def table_row(cells: list[Any]) -> str:
    """Write one Markdown table row.

    :param cells: The cells.
    :return: The row."""
    return "| " + " | ".join(str(c) for c in cells) + " |"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("batch", nargs="?", type=Path, help="a batch to write RESULTS.md for")
    parser.add_argument("--base", help="the stamp of the batch before a change")
    parser.add_argument("--new", help="the stamp of the batch after it")
    args = parser.parse_args()
    if args.base and args.new:
        print(compare(HERE / "runs" / args.base, HERE / "runs" / args.new))
    elif args.batch:
        print(report(args.batch))
    else:
        parser.error("give a batch, or --base and --new")
