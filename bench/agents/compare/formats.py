"""Exports of a log dir for the comparison's baselines: plain files and TensorBoard event files."""

import csv
import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beamtime.format.run import read_config, read_effective_metrics, read_output, read_run_info
from beamtime.format.tree import iter_runs


@dataclass(kw_only=True)
class ExportRun:
    """One run as the exporters see it."""

    group: str
    id: str
    config: dict[str, Any]
    rows: list[dict[str, Any]]
    output: str
    status: str


def export_runs(logdir: Path) -> Iterator[ExportRun]:
    """Read every run of a log dir; the one reader of the plain-files and TensorBoard exports.

    :param logdir: The log dir.
    :return: The runs in sorted order; ``id`` is the folder name, the same in every setup."""
    for run in iter_runs(logdir):
        yield ExportRun(
            group=run.parent.relative_to(logdir).as_posix(),
            id=run.name,
            config=read_config(run),
            rows=read_effective_metrics(run),
            output=read_output(run),
            status=read_run_info(run).status,
        )


def export_files(logdir: Path, dest: Path) -> int:
    """Write ``dest/runs/<group>/<run id>/{config.json, metrics.csv, output.log}`` per run.

    :param logdir: The log dir.
    :param dest: The folder that will hold ``runs/``.
    :return: The number of runs written."""
    n = 0
    for run in export_runs(logdir):
        folder = dest / "runs" / run.group / run.id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "config.json").write_text(json.dumps(run.config, indent=1) + "\n")
        (folder / "output.log").write_text(run.output)
        write_metrics_csv(folder / "metrics.csv", run.rows)
        n += 1
    return n


def write_metrics_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write metric records as a CSV with ``step``, ``time`` and the sorted metric keys.

    A metric a record did not log is an empty cell; ``nan`` and ``inf`` are written as Python does.

    :param path: The CSV file.
    :param rows: The records; ``_step`` and ``_t`` are the reserved keys, the rest are metrics."""
    keys = sorted({k for row in rows for k in row if not k.startswith("_")})
    with path.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["step", "time", *keys])
        for row in rows:
            writer.writerow([row["_step"], row["_t"], *(row.get(k, "") for k in keys)])
