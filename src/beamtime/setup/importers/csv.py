"""CSV files: one run per file, a step column and one metric per numeric column."""

import csv
import math
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from beamtime.setup.importers import Found, Imported, files, label

STEP_COLUMNS = ("step", "epoch", "iteration")


def detect(path: Path) -> Found | None:
    """Count the CSV files at or below a path.

    :param path: A file or a folder.
    :return: The CSV files found, or ``None``."""
    if not (n := sum(1 for _ in csv_files(path))):
        return None
    return Found(kind="csv", path=path, n=n, label=label("csv", n))


def runs(path: Path) -> Iterator[Imported]:
    """Read every CSV file at or below a path as one run.

    :param path: A file or a folder.
    :return: The runs, in file name order."""
    for f in csv_files(path):
        yield read_csv(f)


def csv_files(path: Path) -> Iterator[Path]:
    """List the CSV files at or below a path in name order.

    :param path: A file or a folder.
    :return: The files."""
    return iter(sorted(f for f in files(path) if f.suffix.lower() == ".csv"))


def read_csv(path: Path) -> Imported:
    """Read one CSV file: numeric cells become metrics, anything else is skipped.

    :param path: The file.
    :return: The run, started and ended when the file was last written."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        table = list(csv.DictReader(f))
    header = {name.strip().lower(): name for name in (table[0] if table else {}) if name}
    step = next((header[s] for s in STEP_COLUMNS if s in header), None)
    rows = []
    for i, line in enumerate(table):
        row: dict[str, Any] = {}
        for name, cell in line.items():
            if (
                name
                and name != step
                and not name.startswith("_")
                and (v := number(cell)) is not None
            ):
                row[name] = v
        if step is None:
            rows.append({"_step": i} | row)
        elif (s := number(line[step])) is not None and math.isfinite(s):
            rows.append({"_step": int(s)} | row)
    mtime = path.stat().st_mtime
    return Imported(name=path.stem, created_at=mtime, ended_at=mtime, config={}, rows=rows)


def number(cell: str | None) -> float | None:
    """Read a cell as a number.

    :param cell: The cell's text; ``None`` for a missing cell.
    :return: The value, or ``None`` for text and empty cells."""
    try:
        return float(cell) if cell is not None and cell.strip() else None
    except ValueError:
        return None
