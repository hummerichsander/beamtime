"""Importers: read another tool's runs and hand them to the one run writer."""

import os
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Kind = Literal["tensorboard", "wandb", "mlflow", "csv", "beamtime"]

SOURCES: dict[Kind, str] = {
    "beamtime": "Beamtime",
    "mlflow": "MLflow",
    "wandb": "W&B offline",
    "tensorboard": "TensorBoard",
    "csv": "CSV",
}
PRUNED = frozenset({".git", ".venv", "node_modules", "__pycache__"})


@dataclass(kw_only=True, frozen=True)
class Found:
    """What a path holds: the kind of source, how many runs, and a line for the review."""

    kind: Kind
    path: Path
    n: int
    label: str
    note: str = ""


@dataclass(kw_only=True)
class Imported:
    """One run read from a source, before it is written as a run folder."""

    name: str
    created_at: float
    ended_at: float | None = None
    status: Literal["running", "finished", "failed", "killed"] = "finished"
    config: dict[str, Any]
    rows: Iterable[dict[str, Any]]
    host: dict[str, Any] | None = None
    git: dict[str, Any] | None = None
    command: list[str] | None = None
    source_id: str | None = None
    group: str = ""
    skipped: dict[str, int] = field(default_factory=dict)


def detect(path: Path) -> Found | None:
    """Tell what a path holds, from file names only.

    :param path: A file or a folder.
    :return: The first source found, or ``None``."""
    from beamtime.setup.importers import csv, wandb

    counts = count_names(path)
    for kind in SOURCES:
        if n := counts[kind]:
            if kind == "wandb":
                return wandb.detect(path)
            return Found(kind=kind, path=path, n=n, label=label(kind, n))
    return csv.detect(path)


def label(kind: Kind, n: int) -> str:
    """Word the review's line for a source.

    :param kind: The kind of source.
    :param n: The number of runs.
    :return: E.g. ``14 TensorBoard runs``."""
    return f"{n} {SOURCES[kind]} {'run' if n == 1 else 'runs'}"


def count_names(path: Path) -> Counter[str]:
    """Count the runs of every source but CSV by the names of the files below a path.

    :param path: A file or a folder.
    :return: The count per kind."""
    counts: Counter[str] = Counter()
    tensorboard: set[Path] = set()
    for f in files(path):
        match f.suffix.lower(), f.name:
            case _, "_run.json":
                counts["beamtime"] += 1
            case _, "mlflow.db":
                counts["mlflow"] += 1
            case _, "meta.yaml" if (f.parent / "params").is_dir() or (
                f.parent / "metrics"
            ).is_dir():
                counts["mlflow"] += 1
            case ".wandb", _ if f.parent.name.startswith("offline-run-"):
                counts["wandb"] += 1
            case _, name if name.startswith("events.out.tfevents."):
                tensorboard.add(f.parent)
    counts["tensorboard"] = len(tensorboard)
    return counts


def files(path: Path) -> Iterator[Path]:
    """List the files at or below a path, skipping environments and checkouts' internals.

    :param path: A file or a folder.
    :return: The files."""
    if path.is_file():
        yield path
        return
    for folder, dirs, names in os.walk(path):
        dirs[:] = [d for d in dirs if d not in PRUNED]
        for name in names:
            yield Path(folder) / name
