"""MLflow: the file store (``mlruns/``) and the SQLite store (``mlflow.db``)."""

import json
import math
import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

from beamtime.setup.importers import Found, Imported, files, label

STATUS = {
    "RUNNING": "running",
    "SCHEDULED": "running",
    "FINISHED": "finished",
    "FAILED": "failed",
    "KILLED": "killed",
}
# the file store writes the RunStatus enum as a number.
STATUS_NUMBERS = dict(enumerate(STATUS, start=1))
LIVE_RUNS = (
    "FROM runs r JOIN experiments e ON e.experiment_id = r.experiment_id "
    "WHERE r.lifecycle_stage != 'deleted' AND e.lifecycle_stage != 'deleted'"
)
GIT_COMMIT = "mlflow.source.git.commit"
RUN_NAME = "mlflow.runName"


def detect(path: Path) -> Found | None:
    """Count the MLflow runs at or below a path without reading their metrics.

    :param path: A file or a folder.
    :return: The runs found, or ``None``."""
    n = sum(1 for _ in live_folders(path))
    for f in files(path):
        if f.name == "mlflow.db":
            con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
            try:
                n += con.execute(f"SELECT count(*) {LIVE_RUNS}").fetchone()[0]
            except sqlite3.Error:
                pass
            finally:
                con.close()
    return Found(kind="mlflow", path=path, n=n, label=label("mlflow", n)) if n else None


def runs(path: Path) -> Iterator[Imported]:
    """Read every run of the stores at or below a path; deleted runs are skipped.

    :param path: A file or a folder.
    :return: The runs, the SQLite stores first, each in name order."""
    for f in sorted(files(path)):
        if f.name == "mlflow.db":
            yield from read_db(f)
    for folder, meta, experiment in live_folders(path):
        yield read_run_folder(folder, meta, experiment)


def live_folders(path: Path) -> Iterator[tuple[Path, dict[str, Any], dict[str, Any]]]:
    """Find the runs of the file stores below a path that are not deleted.

    :param path: A file or a folder.
    :return: Each run's folder, its ``meta.yaml`` and its experiment's, in folder order."""
    for f in sorted(files(path)):
        if f.name != "meta.yaml" or not is_run_folder(f.parent) or in_trash(f, path):
            continue
        meta, experiment = read_yaml(f), read_yaml(f.parent.parent / "meta.yaml")
        if "deleted" not in (meta.get("lifecycle_stage"), experiment.get("lifecycle_stage")):
            yield f.parent, meta, experiment


def is_run_folder(folder: Path) -> bool:
    """Tell a run's folder from an experiment's by the folders beside its ``meta.yaml``.

    :param folder: The folder.
    :return: Whether it has ``params`` or ``metrics``."""
    return (folder / "params").is_dir() or (folder / "metrics").is_dir()


def in_trash(f: Path, root: Path) -> bool:
    """Tell whether a file lies in a folder MLflow keeps deleted experiments in (``.trash``).

    :param f: The file.
    :param root: The path the search started at.
    :return: Whether a folder between them starts with a dot."""
    return root.is_dir() and any(p.startswith(".") for p in f.relative_to(root).parts[:-1])


def read_run_folder(folder: Path, meta: dict[str, Any], experiment: dict[str, Any]) -> Imported:
    """Read one run of the file store.

    :param folder: The run's folder, ``mlruns/<experiment>/<run>``.
    :param meta: The run's ``meta.yaml``.
    :param experiment: The experiment's ``meta.yaml``.
    :return: The run."""
    records = []
    for key, f in keyed_files(folder / "metrics"):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                ts, value, step = line.split()[:3]
                records.append((key, float(value), int(step), float(ts) / 1000))
    status = meta.get("status")
    return make_run(
        run_id=str(meta.get("run_uuid") or meta.get("run_id") or folder.name),
        name=meta.get("run_name"),
        experiment=str(experiment.get("name") or folder.parent.name),
        status=STATUS_NUMBERS.get(status) if isinstance(status, int) else str(status),
        start=meta.get("start_time"),
        end=meta.get("end_time"),
        params={
            k: f.read_text(encoding="utf-8").strip() for k, f in keyed_files(folder / "params")
        },
        tags={k: f.read_text(encoding="utf-8").strip() for k, f in keyed_files(folder / "tags")},
        records=records,
        fallback_time=(folder / "meta.yaml").stat().st_mtime,
    )


def read_yaml(path: Path) -> dict[str, Any]:
    """Read a ``meta.yaml``.

    :param path: The file.
    :return: Its mapping, empty when the file is missing."""
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def keyed_files(folder: Path) -> Iterator[tuple[str, Path]]:
    """List the files below a folder with their keys; the key ``val/loss`` is a nested file.

    :param folder: ``params``, ``tags`` or ``metrics``.
    :return: Pairs of key and file, in key order."""
    if folder.is_dir():
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                yield f.relative_to(folder).as_posix(), f


def read_db(path: Path) -> Iterator[Imported]:
    """Read every run of an SQLite store; deleted runs and experiments are skipped.

    :param path: The ``mlflow.db`` file.
    :return: The runs, in start order."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        table = con.execute(
            f"SELECT r.run_uuid, r.name, e.name, r.status, r.start_time, r.end_time {LIVE_RUNS} "
            "ORDER BY r.start_time, r.run_uuid"
        ).fetchall()
        for run_id, name, experiment, status, start, end in table:
            where = (run_id,)
            records = [
                (key, math.nan if is_nan else value, step, ts / 1000)
                for key, value, step, ts, is_nan in con.execute(
                    "SELECT key, value, step, timestamp, is_nan FROM metrics "
                    "WHERE run_uuid = ? ORDER BY step, timestamp",
                    where,
                )
            ]
            yield make_run(
                run_id=run_id,
                name=name,
                experiment=experiment,
                status=status,
                start=start,
                end=end,
                params=dict(con.execute("SELECT key, value FROM params WHERE run_uuid = ?", where)),
                tags=dict(con.execute("SELECT key, value FROM tags WHERE run_uuid = ?", where)),
                records=records,
                fallback_time=path.stat().st_mtime,
            )
    finally:
        con.close()


def make_run(
    *,
    run_id: str,
    name: str | None,
    experiment: str,
    status: str | None,
    start: float | None,
    end: float | None,
    params: dict[str, str],
    tags: dict[str, str],
    records: list[tuple[str, float, int, float]],
    fallback_time: float,
) -> Imported:
    """Turn what either store holds into an imported run.

    :param run_id: MLflow's run id.
    :param name: The run name; the ``mlflow.runName`` tag or the id's start otherwise.
    :param experiment: The experiment's name, the run's group.
    :param status: MLflow's status name.
    :param start: Start time in milliseconds.
    :param end: End time in milliseconds.
    :param params: The parameters as text.
    :param tags: The tags.
    :param records: Metric points as key, value, step and time in seconds, in logging order.
    :param fallback_time: Start time in seconds for a run that has none.
    :return: The run."""
    created = start / 1000 if start else fallback_time
    return Imported(
        name=name or tags.get(RUN_NAME) or run_id[:8],
        group=experiment,
        created_at=created,
        ended_at=end / 1000 if end else None,
        status=STATUS.get(str(status).upper(), "finished"),
        config={k: coerce(v) for k, v in params.items()},
        rows=metric_rows(records, created),
        git={"commit": tags[GIT_COMMIT]} if GIT_COMMIT in tags else None,
        source_id=run_id,
    )


def metric_rows(
    records: list[tuple[str, float, int, float]], created: float
) -> list[dict[str, Any]]:
    """Merge metric points into one record per step.

    A key logged twice at a step starts another record, so no point is lost.

    :param records: Points as key, value, step and time in seconds, in logging order.
    :param created: The time for points that have none.
    :return: The records in step order."""
    by_step: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for key, value, step, ts in records:
        rows = by_step[step]
        if (row := next((r for r in rows if key not in r), None)) is None:
            row = {"_step": step, "_t": ts or created}
            rows.append(row)
        row[key] = value
    return [row for step in sorted(by_step) for row in by_step[step]]


def coerce(value: str) -> Any:
    """Read a parameter's text as a number or a boolean where it is one.

    MLflow stores every parameter as text.

    :param value: The text.
    :return: The number, the boolean or the text itself."""
    try:
        parsed = json.loads(value)
    except ValueError:
        return {"True": True, "False": False}.get(value, value)
    if isinstance(parsed, bool) or (isinstance(parsed, int | float) and math.isfinite(parsed)):
        return parsed
    return value
