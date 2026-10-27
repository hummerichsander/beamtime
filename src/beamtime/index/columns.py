"""Raw column files of a run's metrics: int64 steps and float64 values per key.

Writers append to the files, then publish the new lengths by replacing
``_manifest.json``; readers map only the published length, so they never see a
partial write. A truncation (a resumed attempt) writes a new generation of the
files instead of shrinking files that readers may have mapped."""

import json
import mmap
import os
from array import array
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

from beamtime.format.io import write_replaced

MANIFEST = "_manifest.json"
TIME_KEY = "_t"


@dataclass(kw_only=True)
class Entry:
    """The published state of one key's columns."""

    file: str
    length: int = 0
    nonfinite: bool = False


@dataclass(kw_only=True)
class Manifest:
    """What a run's column files hold and where ingest continues."""

    source_offset: int = 0
    last_step: int | None = None
    attempts: list[list[int]] = field(default_factory=list)
    entries: dict[str, Entry] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> "Manifest":
        """Read a manifest, or start an empty one.

        :param path: The ``_manifest.json`` file.
        :return: The manifest."""
        try:
            d = json.loads(path.read_text())
        except (OSError, ValueError):
            return cls()
        return cls(
            source_offset=d.get("source_offset", 0),
            last_step=d.get("last_step"),
            attempts=d.get("attempts", []),
            entries={k: Entry(**e) for k, e in d.get("entries", {}).items()},
        )

    def dump(self) -> dict[str, Any]:
        """Serialize the manifest.

        :return: The JSON-ready content."""
        return {
            "schema": 1,
            "source_offset": self.source_offset,
            "last_step": self.last_step,
            "attempts": self.attempts,
            "entries": {
                k: {"file": e.file, "length": e.length, "nonfinite": e.nonfinite}
                for k, e in self.entries.items()
            },
        }


def file_stem(key: str, generation: int = 0) -> str:
    """Name a key's column files safely on every filesystem.

    :param key: The metric key, e.g. ``train/loss``.
    :param generation: Bumped whenever the columns are rewritten.
    :return: E.g. ``train%2Floss.0``."""
    return f"{quote(key, safe='')}.{generation}"


class ColumnWriter:
    """Appends to a run's column files; one writer at a time, under the indexer lock."""

    def __init__(self, *, dir: Path) -> None:
        """Open a run's columns, cutting off anything written after the last publish.

        :param dir: The run's directory in the cache, created if missing."""
        self.dir = dir
        dir.mkdir(parents=True, exist_ok=True)
        self.manifest = Manifest.load(dir / MANIFEST)
        self.steps: dict[str, array] = {}
        self.values: dict[str, array] = {}
        self.nonfinite: set[str] = set()
        self.retired: list[str] = []
        for e in self.manifest.entries.values():
            for ext in ("steps", "values"):
                path = dir / f"{e.file}.{ext}"
                if path.exists() and path.stat().st_size > e.length * 8:
                    os.truncate(path, e.length * 8)

    def append(self, key: str, step: int, value: float) -> None:
        """Buffer one point.

        :param key: The metric key.
        :param step: The step.
        :param value: The value."""
        if key not in self.steps:
            self.steps[key], self.values[key] = array("q"), array("d")
        self.steps[key].append(step)
        self.values[key].append(value)
        if value != value or value in (float("inf"), float("-inf")):
            self.nonfinite.add(key)

    def truncate_from(self, step: int) -> None:
        """Drop every point at or after a step, published and buffered alike.

        :param step: The resume step of a new attempt."""
        for key in list(self.steps):
            i = bisect_left(self.steps[key], step)
            del self.steps[key][i:], self.values[key][i:]
        for key, e in list(self.manifest.entries.items()):
            col = Column.open(self.dir, e)
            keep = bisect_left(col.steps, step)
            if keep == e.length:
                col.close()
                continue
            generation = int(e.file.rsplit(".", 1)[1]) + 1
            new = Entry(file=file_stem(key, generation), length=keep, nonfinite=e.nonfinite)
            for ext, view in (("steps", col.steps), ("values", col.values)):
                (self.dir / f"{new.file}.{ext}").write_bytes(view[:keep].tobytes())
            col.close()
            self.manifest.entries[key] = new
            self.retired.append(e.file)

    def commit(self, source_offset: int) -> None:
        """Append the buffered points and publish the new lengths.

        :param source_offset: Where ingest continues in ``_metrics.jsonl``."""
        for key, steps in self.steps.items():
            if not steps:
                continue
            e = self.manifest.entries.setdefault(key, Entry(file=file_stem(key)))
            for ext, buf in (("steps", steps), ("values", self.values[key])):
                with (self.dir / f"{e.file}.{ext}").open("ab") as f:
                    f.write(buf.tobytes())
            e.length += len(steps)
            e.nonfinite = e.nonfinite or key in self.nonfinite
            last = steps[-1]
            if key != TIME_KEY and (
                self.manifest.last_step is None or last > self.manifest.last_step
            ):
                self.manifest.last_step = last
        self.manifest.source_offset = source_offset
        write_replaced(self.dir / MANIFEST, self.manifest.dump())
        for stem in self.retired:
            for ext in ("steps", "values"):
                try:
                    (self.dir / f"{stem}.{ext}").unlink()
                except OSError:
                    pass
        self.retired = []
        self.steps, self.values, self.nonfinite = {}, {}, set()


class Column:
    """A read-only view of one key's published points."""

    def __init__(self, *, steps: memoryview, values: memoryview, maps: list, nonfinite: bool):
        """Wrap mapped columns; use ``Column.open``.

        :param steps: The int64 steps.
        :param values: The float64 values.
        :param maps: The underlying maps, closed by ``close``.
        :param nonfinite: Whether any value is NaN or infinite."""
        self.steps = steps
        self.values = values
        self.maps = maps
        self.nonfinite = nonfinite

    @classmethod
    def open(cls, dir: Path, entry: Entry) -> "Column":
        """Map a key's published points.

        :param dir: The run's directory in the cache.
        :param entry: The key's manifest entry.
        :return: The column."""
        views, maps = [], []
        for ext, fmt in (("steps", "q"), ("values", "d")):
            if entry.length == 0:
                views.append(memoryview(array(fmt)))
                continue
            with (dir / f"{entry.file}.{ext}").open("rb") as f:
                m = mmap.mmap(f.fileno(), entry.length * 8, access=mmap.ACCESS_READ)
            maps.append(m)
            views.append(memoryview(m).cast(fmt))
        return cls(steps=views[0], values=views[1], maps=maps, nonfinite=entry.nonfinite)

    def window(self, lo: int | None, hi: int | None) -> tuple[int, int]:
        """Find the index range of steps in ``[lo, hi]``.

        :param lo: The first step, or ``None`` for the start.
        :param hi: The last step (inclusive), or ``None`` for the end.
        :return: Start and end index."""
        i = 0 if lo is None else bisect_left(self.steps, lo)
        j = len(self.steps) if hi is None else bisect_right(self.steps, hi)
        return i, j

    def close(self) -> None:
        """Release the maps; slices held elsewhere keep them alive until collected."""
        try:
            for v in (self.steps, self.values):
                v.release()
            for m in self.maps:
                m.close()
        except BufferError:
            return
        self.maps = []


def open_columns(dir: Path) -> tuple[Manifest, dict[str, Entry]]:
    """Read a run's manifest for querying.

    :param dir: The run's directory in the cache.
    :return: The manifest and its entries by key."""
    manifest = Manifest.load(dir / MANIFEST)
    return manifest, manifest.entries
