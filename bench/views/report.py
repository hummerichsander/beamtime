"""Write the results of a scored batch: python bench/views/report.py bench/views/runs/<stamp>.

Writes RESULTS.md into the batch's folder: one row per run, and the means per model."""

import json
import statistics
import sys
from pathlib import Path
from typing import Any


def report(stamp: Path) -> Path:
    """Write the batch's RESULTS.md.

    :param stamp: The batch's folder.
    :return: The file."""
    rows = []
    for folder in sorted(stamp.iterdir()):
        if (folder / "score.json").is_file():
            record = json.loads((folder / "record.json").read_text())
            rows.append(row(record, json.loads((folder / "score.json").read_text())))
    lines = [
        f"# View tasks: {stamp.name}",
        "",
        table_row(COLUMNS),
        table_row(["---"] * len(COLUMNS)),
    ]
    lines += [table_row([str(r[k]) for k in COLUMNS]) for r in rows]
    per_model = ["model", "runs", "saved", "valid", "finding true", "checklist", "robust"]
    lines += ["", "## Per model", "", table_row(per_model), table_row(["---"] * len(per_model))]
    for model in sorted({r["model"] for r in rows}):
        mine = [r for r in rows if r["model"] == model]
        lines.append(
            f"| {model} | {len(mine)} | {share(mine, 'saved')} | {share(mine, 'valid')} | "
            f"{share(mine, 'finding')} | {mean([r['_checklist'] for r in mine])} | "
            f"{share(mine, 'robust')} |"
        )
    file = stamp / "RESULTS.md"
    file.write_text("\n".join(lines) + "\n")
    return file


COLUMNS = (
    "task model saved valid rounds metrics runs finding checklist robust turns seconds".split()
)


def table_row(cells: list[str] | tuple[str, ...]) -> str:
    """Write one Markdown table row.

    :param cells: The cells.
    :return: The row."""
    return "| " + " | ".join(cells) + " |"


def row(record: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    """Flatten one run's record and score into a table row.

    :param record: The run's record.
    :param score: Its score.
    :return: The row; ``_checklist`` holds the share of items met."""
    items = score.get("checklist", {}).get("items", [])
    met = sum(i["yes"] for i in items) / len(items) if items else 0.0
    robust = score.get("robust") or {}
    return {
        "task": record["task"],
        "model": record["model"],
        "saved": score.get("saved", False),
        "valid": score.get("valid", False),
        "rounds": score.get("rounds"),
        "metrics": ratio(score.get("metrics")),
        "runs": ratio(score.get("runs")),
        "finding": (score.get("finding") or {}).get("true", False),
        "checklist": f"{sum(i['yes'] for i in items)}/{len(items)}" if items else "–",
        "robust": all(v is not False for v in robust.values()) if robust else False,
        "turns": record.get("turns"),
        "seconds": record.get("seconds"),
        "_checklist": met,
    }


def ratio(covered: dict[str, bool] | None) -> str:
    """Show how many required items a view covers.

    :param covered: Covered, per item.
    :return: E.g. ``2/2``, or ``–`` without requirements."""
    return f"{sum(covered.values())}/{len(covered)}" if covered else "–"


def share(rows: list[dict[str, Any]], key: str) -> str:
    """Show the share of rows where a key is true.

    :param rows: The rows.
    :param key: The key.
    :return: E.g. ``8/10``."""
    return f"{sum(bool(r[key]) for r in rows)}/{len(rows)}"


def mean(values: list[float]) -> str:
    """Show a mean as a percentage.

    :param values: Shares between 0 and 1.
    :return: E.g. ``82 %``."""
    return f"{statistics.fmean(values) * 100:.0f} %" if values else "–"


if __name__ == "__main__":
    print(report(Path(sys.argv[1])))
