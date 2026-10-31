"""Folders below the log dir: groups, runs and reserved names."""

import shutil
from collections.abc import Iterator
from pathlib import Path

from beamtime.format import constants as c


def is_reserved(name: str, *, in_run: bool = False) -> bool:
    """Tell whether a folder name never counts as a group.

    :param name: The folder name.
    :param in_run: Whether the folder is inside a run.
    :return: Whether the name is reserved."""
    return (
        name.startswith("_")
        or name.startswith(".")
        or name in c.AUTHORED
        or (in_run and name in c.RUN_ONLY)
    )


def is_run(path: Path) -> bool:
    """Tell whether a folder is a run.

    :param path: The folder.
    :return: Whether it holds a ``_run.json``."""
    return (path / c.RUN).is_file()


def iter_runs(folder: Path) -> Iterator[Path]:
    """Find the runs in and below a folder, without descending into runs.

    :param folder: A group, a run or the log dir.
    :return: The run directories, in sorted order per folder."""
    if is_run(folder):
        yield folder
        return
    if not folder.is_dir():
        return
    for child in sorted(folder.iterdir()):
        if child.is_dir() and not is_reserved(child.name):
            yield from iter_runs(child)


def to_trash(logdir: Path, rel: Path, stamp: str) -> Path:
    """Move a file or folder into the log dir's trash, keeping its path below a time stamp.

    :param logdir: The log dir.
    :param rel: What to move, relative to the log dir.
    :param stamp: The trash folder, e.g. ``20261024-101532``; one per removal.
    :return: Where it went, relative to the log dir."""
    dest = Path(c.TRASH) / stamp / rel
    (logdir / dest).parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(logdir / rel), str(logdir / dest))
    return dest
