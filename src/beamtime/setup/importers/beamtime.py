"""Beamtime log dirs: copied with their record under ``imported/<name>/``, without conversion."""

import os
import shutil
import socket
import time
from dataclasses import dataclass
from pathlib import Path

from beamtime.format import constants as c
from beamtime.format import moves
from beamtime.format.io import read_json, write_replaced
from beamtime.format.times import iso
from beamtime.format.tree import is_reserved, is_run, iter_runs
from beamtime.ops.copy import TEMP_PREFIX, sync_tree
from beamtime.setup.importers.write import IMPORTED


@dataclass(kw_only=True, frozen=True)
class Copied:
    """What a copy did: runs copied and runs skipped because their id is in the log dir."""

    runs: int
    skipped: int


class Copier:
    """Copy one Beamtime log dir into ``imported/<name>/`` of another."""

    def __init__(self, *, logdir: Path, source: Path, name: str) -> None:
        """Set up a copy.

        :param logdir: The destination log dir.
        :param source: The log dir to copy, or a folder of its groups and runs.
        :param name: The folder below ``imported/`` that takes the tree."""
        self.logdir = logdir
        self.source = source.resolve()
        self.prefix = f"{IMPORTED}/{name}"
        self.dest = logdir / self.prefix
        self.known = {run.name for run in iter_runs(logdir)}
        self.copied = 0
        self.skipped = 0

    def copy(self) -> Copied:
        """Copy the tree, then record the moves that keep its paths meaningful.

        :return: The runs copied and skipped."""
        if is_run(self.source):
            self.copy_run(self.source, self.dest / self.source.name)
        else:
            self.copy_folder(self.source, self.dest)
            self.record_moves()
        return Copied(runs=self.copied, skipped=self.skipped)

    def copy_folder(self, src: Path, dst: Path) -> None:
        """Copy a group below ``src`` into ``dst``: its runs, authored folders and groups.

        :param src: A folder of the source.
        :param dst: Its place in the destination."""
        for entry in sorted(src.iterdir()):
            if entry.is_dir() and entry.resolve() == self.logdir.resolve():
                continue
            if entry.is_dir() and is_run(entry):
                self.copy_run(entry, dst / entry.name)
            elif entry.is_dir() and entry.name in c.AUTHORED:
                self.copy_new_files(entry, dst / entry.name)
            elif entry.is_dir() and not is_reserved(entry.name):
                self.copy_folder(entry, dst / entry.name)

    def copy_new_files(self, src: Path, dst: Path) -> None:
        """Copy the files of an authored folder that the destination lacks.

        Authored files are immutable versions, so a file that exists is the same file.

        :param src: An authored folder of the source.
        :param dst: Its place in the destination."""
        for folder, _, names in os.walk(src):
            target = dst / Path(folder).relative_to(src)
            for name in names:
                if not (target / name).exists():
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(Path(folder) / name, target / name)

    def copy_run(self, src: Path, dst: Path) -> None:
        """Copy a run unless its id is in the log dir, and rewrite its ``_run.json``.

        :param src: The run in the source.
        :param dst: Its place in the destination."""
        if src.name in self.known:
            self.skipped += 1
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        temp = dst.parent / f"{TEMP_PREFIX}{src.name}"
        shutil.copytree(src, temp)
        info = read_json(temp / c.RUN)
        for key in ("proposals", "proposal_hashes"):
            info[key] = {
                (k if k == "." else f"{self.prefix}/{k}"): v
                for k, v in (info.get(key) or {}).items()
            }
        info["imported_from"] = {
            "kind": "beamtime",
            "path": str(src),
            "id": info["id"],
            "host": socket.gethostname(),
            "at": iso(time.time()),
        }
        stat = (src / c.RUN).stat()
        write_replaced(temp / c.RUN, info, sync=True)
        # the heartbeat is the file's mtime; a fresh one would turn a lost run into a running one.
        os.utime(temp / c.RUN, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        sync_tree(temp)
        os.replace(temp, dst)
        self.known.add(src.name)
        self.copied += 1

    def record_moves(self) -> None:
        """Record one scoped move per top-level group, then the source's own moves.

        The source's moves name paths before and after its own ``mv``; their old first folders get
        a move too, so a path named before the source's move reaches the copy."""
        source_moves = moves.read(self.source)
        top = [
            d.name
            for d in sorted(self.source.iterdir())
            if d.is_dir() and not is_reserved(d.name) and not is_run(d)
        ]
        top += [m.old.split("/")[0] for m in source_moves if m.old.split("/")[0] not in top]
        known = {(m.old, m.new) for m in moves.read(self.logdir)}
        for group in top:
            self.record(group, f"{self.prefix}/{group}", self.prefix, known)
        for m in source_moves:
            within = f"{self.prefix}/{m.within}" if m.within else self.prefix
            self.record(f"{self.prefix}/{m.old}", f"{self.prefix}/{m.new}", within, known)

    def record(self, old: str, new: str, within: str, known: set[tuple[str, str]]) -> None:
        """Append a scoped move unless an earlier import recorded it.

        :param old: The path before.
        :param new: The path after.
        :param within: The scope.
        :param known: The ``(old, new)`` pairs recorded already; extended."""
        if (old, new) not in known:
            moves.record(self.logdir, old, new, within)
            known.add((old, new))


def copy_logdir(logdir: Path, source: Path, name: str) -> Copied:
    """Copy a Beamtime log dir under ``imported/<name>/`` with its proposals, notes, memory, views
    and blocks; run ids stay, and ``_run.json`` gains ``imported_from``.

    :param logdir: The destination log dir.
    :param source: The log dir to copy.
    :param name: The folder below ``imported/`` that takes the tree.
    :return: The runs copied and the runs skipped as known."""
    return Copier(logdir=logdir, source=source, name=name).copy()
