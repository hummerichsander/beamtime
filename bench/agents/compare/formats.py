"""Exports of a log dir for the comparison's baselines: plain files and TensorBoard event files."""

import csv
import json
import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from data import RECORD

from beamtime.format.run import read_config, read_effective_metrics, read_output, read_run_info
from beamtime.format.tree import is_run, iter_runs


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

    The research record goes to ``dest/record/`` (``export_record``).

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
    export_record(logdir, dest)
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


def export_tensorboard(logdir: Path, dest: Path) -> int:
    """Write ``dest/tb/<group>/<run id>/{events, hparams.yaml, output.log}`` per run.

    The event file holds one scalar event per logged value (step and wall time as logged) and one
    hparams event with the flattened config; ``hparams.yaml`` keeps the config nested. The research
    record goes to ``dest/record/`` (``export_record``).

    :param logdir: The log dir.
    :param dest: The folder that will hold ``tb/``.
    :return: The number of runs written."""
    from tensorboard.compat.proto.event_pb2 import Event
    from tensorboard.compat.proto.summary_pb2 import Summary
    from tensorboard.plugins.hparams.summary_v2 import hparams_pb
    from tensorboard.summary.writer.event_file_writer import EventFileWriter

    n = 0
    for run in export_runs(logdir):
        folder = dest / "tb" / run.group / run.id
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "hparams.yaml").write_text(yaml.safe_dump(run.config, sort_keys=False))
        (folder / "output.log").write_text(run.output)

        start = run.rows[0]["_t"] if run.rows else 0.0
        writer = EventFileWriter(str(folder))
        writer.add_event(
            Event(
                wall_time=start,
                summary=hparams_pb(hparam_values(run.config), start_time_secs=start),
            )
        )
        for row in run.rows:
            for key, value in row.items():
                if key.startswith("_"):
                    continue
                summary = Summary(value=[Summary.Value(tag=key, simple_value=value)])
                writer.add_event(Event(wall_time=row["_t"], step=row["_step"], summary=summary))
        writer.close()
        n += 1
    export_record(logdir, dest)
    return n


def export_record(logdir: Path, dest: Path, folder: Path | None = None) -> int:
    """Copy the research record to ``dest/record/<group>/{proposal,notes,memory}``, byte for byte.

    The project memory goes to ``dest/record/memory``; a run's own folders are not record.

    :param logdir: The log dir.
    :param dest: The folder that will hold ``record/``.
    :param folder: The folder to walk; defaults to the log dir.
    :return: The number of folders copied."""
    n = 0
    for child in sorted((folder or logdir).iterdir()):
        if not child.is_dir() or is_run(child):
            continue
        if child.name in RECORD:
            shutil.copytree(child, dest / "record" / child.relative_to(logdir))
            n += 1
        else:
            n += export_record(logdir, dest, child)
    return n


def hparam_values(config: dict[str, Any]) -> dict[str, bool | int | float | str]:
    """Flatten a nested config for the hparams plugin, which takes only scalars.

    Keys of nested dicts are joined with ``.``; lists and ``None`` become their JSON text.

    :param config: The config as logged.
    :return: Flat keys with ``bool``, ``int``, ``float`` or ``str`` values."""
    flat: dict[str, bool | int | float | str] = {}
    for key, value in config.items():
        if isinstance(value, dict):
            flat.update({f"{key}.{k}": v for k, v in hparam_values(value).items()})
        elif isinstance(value, bool | int | float | str):
            flat[key] = value
        else:
            flat[key] = json.dumps(value)
    return flat
