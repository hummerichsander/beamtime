"""W&B offline runs: ``files/`` as files, the history through the ``wandb`` package's reader."""

import json
from collections import defaultdict
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from beamtime.setup.importers import Found, Imported, files, label

NO_HISTORY = "history needs the wandb package"
EXIT_KEYS = ("exit_code", "exitcode")
HOST_KEYS = {"hostname": "host", "os": "os", "python": "python"}
Reader = Callable[[Path], Iterator[dict[str, Any]]]


def detect(path: Path) -> Found | None:
    """Count the offline runs at or below a path.

    :param path: A file or a folder.
    :return: The runs found, with a note when their history cannot be read, or ``None``."""
    if not (n := len(run_folders(path))):
        return None
    note = NO_HISTORY if reader() is None else ""
    return Found(kind="wandb", path=path, n=n, label=label("wandb", n), note=note)


def runs(path: Path) -> Iterator[Imported]:
    """Read every offline run at or below a path.

    :param path: A file or a folder.
    :return: The runs, in folder order."""
    read = reader()
    for folder in run_folders(path):
        yield read_folder(folder, read)


def run_folders(path: Path) -> list[Path]:
    """Find the ``offline-run-*`` folders that hold a ``.wandb`` file.

    :param path: A file or a folder.
    :return: The folders, in name order."""
    found = {
        f.parent
        for f in files(path)
        if f.suffix == ".wandb" and f.parent.name.startswith("offline-run-")
    }
    return sorted(found)


def reader() -> Reader | None:
    """Find the ``wandb`` package's datastore reader, which versions 0.12 to 0.28 ship.

    :return: A function that reads a ``.wandb`` file's history records, or ``None``."""
    try:
        from wandb.proto import wandb_internal_pb2
        from wandb.sdk.internal.datastore import DataStore
    except ImportError:
        return None

    def read(path: Path) -> Iterator[dict[str, Any]]:
        store = DataStore()
        store.open_for_scan(str(path))
        try:
            while data := store.scan_data():
                record = wandb_internal_pb2.Record()
                record.ParseFromString(data)
                if record.WhichOneof("record_type") == "history":
                    yield {
                        (item.key or ".".join(item.nested_key)): json.loads(item.value_json)
                        for item in record.history.item
                    }
        except Exception:
            # a run cut off mid-write ends its history where the file does.
            return

    return read


def read_folder(folder: Path, read: Reader | None) -> Imported:
    """Read one offline run.

    :param folder: The ``offline-run-*`` folder.
    :param read: The history reader, or ``None`` without one.
    :return: The run, with the summary as its one step when there is no history."""
    meta = read_json(folder / "files" / "wandb-metadata.json")
    summary = read_json(folder / "files" / "wandb-summary.json")
    run_id = folder.name.rsplit("-", 1)[-1]
    created = start_time(meta, summary, folder)
    ended = summary.get("_timestamp") or (
        created + runtime if isinstance(runtime := run_time(summary), int | float) else None
    )
    skipped: dict[str, set[str]] = defaultdict(set)
    rows = []
    if read is not None:
        for wb in sorted(folder.glob("*.wandb")):
            for values in read(wb):
                rows.append(history_row(values, len(rows), created, skipped))
    if not rows:
        row = history_row(summary, 0, ended or created, skipped)
        rows = [row | {"_step": 0}] if len(row) > 2 else []
    return Imported(
        name=run_id,
        created_at=created,
        ended_at=ended,
        status=status_of(meta, summary),
        config=read_config(folder / "files" / "config.yaml"),
        rows=rows,
        host={k: meta[w] for k, w in HOST_KEYS.items() if w in meta} or None,
        git=meta.get("git") or None,
        command=command_of(meta),
        source_id=run_id,
        skipped={kind: len(keys) for kind, keys in sorted(skipped.items())},
    )


def history_row(
    values: dict[str, Any], index: int, fallback_time: float, skipped: dict[str, set[str]]
) -> dict[str, Any]:
    """Turn one history record into a metric record.

    :param values: The record's keys and values.
    :param index: The step for a record that has none.
    :param fallback_time: The time for a record that has none.
    :param skipped: Receives the keys of media by their ``_type``.
    :return: ``_step``, ``_t`` and the numeric values; keys that begin with ``_`` are left out."""
    step, wall = values.get("_step"), values.get("_timestamp")
    row = {
        "_step": step if isinstance(step, int) else index,
        "_t": wall if isinstance(wall, int | float) else fallback_time,
    }
    for key, value in values.items():
        if key.startswith("_"):
            continue
        if isinstance(value, int | float) and not isinstance(value, bool):
            row[key] = value
        elif isinstance(value, dict) and "_type" in value:
            skipped[str(value["_type"])].add(key)
    return row


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file of the run.

    :param path: The file.
    :return: Its mapping, empty when the file is missing or unreadable."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def read_config(path: Path) -> dict[str, Any]:
    """Read ``config.yaml``, where each setting is ``{desc, value}``.

    :param path: The file.
    :return: The settings by name without W&B's own ``_wandb`` and ``wandb_version``."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {
        k: v["value"] if isinstance(v, dict) and "value" in v else v
        for k, v in raw.items()
        if k not in ("_wandb", "wandb_version")
    }


def start_time(meta: dict[str, Any], summary: dict[str, Any], folder: Path) -> float:
    """Find when the run started, from the metadata, the summary or the folder.

    :param meta: ``wandb-metadata.json``.
    :param summary: ``wandb-summary.json``.
    :param folder: The run's folder.
    :return: Unix seconds."""
    try:
        return datetime.fromisoformat(meta["startedAt"]).timestamp()
    except (KeyError, TypeError, ValueError):
        pass
    runtime, wall = run_time(summary), summary.get("_timestamp")
    if isinstance(runtime, int | float) and isinstance(wall, int | float):
        return wall - runtime
    return folder.stat().st_mtime


def run_time(summary: dict[str, Any]) -> Any:
    """Read the runtime in seconds from ``wandb-summary.json``.

    :param summary: The summary.
    :return: ``_runtime``, else ``_wandb.runtime``, else ``None``."""
    inner = summary.get("_wandb")
    return summary.get("_runtime", inner.get("runtime") if isinstance(inner, dict) else None)


def status_of(meta: dict[str, Any], summary: dict[str, Any]) -> str:
    """Tell how the run ended from an exit code in the summary or the metadata.

    :param meta: ``wandb-metadata.json``.
    :param summary: ``wandb-summary.json``.
    :return: ``failed`` for a non-zero code, ``finished`` otherwise."""
    for source in (summary, meta):
        for key in EXIT_KEYS:
            if isinstance(code := source.get(key), int) and not isinstance(code, bool):
                return "finished" if code == 0 else "failed"
    return "finished"


def command_of(meta: dict[str, Any]) -> list[str] | None:
    """Rebuild the command line from the metadata.

    :param meta: ``wandb-metadata.json``.
    :return: The executable, the program and the arguments that are there, or ``None``."""
    parts = [meta.get("executable"), meta.get("program"), *(meta.get("args") or [])]
    return [str(p) for p in parts if p] or None
