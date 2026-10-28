"""The index facade: discovery, catch-up within a time budget, and freshness."""

import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from beamtime.format import constants as c
from beamtime.format.tree import is_reserved
from beamtime.index.cache import INDEX_LOCK, FileLock, cache_dir, daemon_status
from beamtime.index.ingest import Ingester, mtime, read_notes
from beamtime.index.store import Store

# mtimes can be a second coarse; folders changed around a walk are listed again.
MTIME_SLACK_S = 2.0
AUTHORED = (c.PROPOSAL, c.MEMORY, c.VIEW)


@dataclass(kw_only=True)
class Freshness:
    """How current an answer is."""

    daemon: bool = False
    busy: bool = False
    behind: int = 0
    behind_s: float | None = None
    damaged: list[str] = field(default_factory=list)
    changed: set[str] = field(default_factory=set)

    def text(self) -> str:
        """Describe the freshness in one line for CLI and MCP answers.

        :return: E.g. ``catch-up only (daemon not running); 3 runs are up to
            4 min behind``."""
        if self.daemon:
            out = "live (daemon running)"
        else:
            out = "catch-up only (daemon not running)"
        if self.busy:
            out += "; another process is indexing"
        if self.behind:
            age = (
                "not yet indexed"
                if self.behind_s is None
                else f"up to {format_age(self.behind_s)} behind"
            )
            out += f"; {self.behind} run{'s' * (self.behind != 1)} {age}"
        if self.damaged:
            out += f"; {len(self.damaged)} unreadable run(s) skipped"
        return out

    def dump(self) -> dict:
        """Serialize for answers' meta.

        :return: The JSON-ready freshness."""
        return {
            "text": self.text(),
            "daemon": self.daemon,
            "behind": self.behind,
            "behind_s": self.behind_s,
            "damaged": self.damaged,
        }


def format_age(seconds: float) -> str:
    """Format a duration compactly.

    :param seconds: The duration.
    :return: E.g. ``40 s``, ``4 min``, ``2 h``."""
    if seconds < 90:
        return f"{seconds:.0f} s"
    if seconds < 5400:
        return f"{seconds / 60:.0f} min"
    return f"{seconds / 3600:.0f} h"


class Index:
    """The index of one log dir: a cache that can always be rebuilt from the files."""

    def __init__(self, *, logdir: Path, cache: Path | None = None) -> None:
        """Open (or create) the index of a log dir.

        :param logdir: The log dir.
        :param cache: The cache directory; by default ``cache_dir(logdir)``."""
        self.logdir = logdir.resolve()
        self.cache = cache or cache_dir(self.logdir)
        self.store = Store(path=self.cache / "index.sqlite")
        self.series = self.cache / "series"
        if self.store.rebuilt:
            shutil.rmtree(self.series, ignore_errors=True)
        self.lock = FileLock(path=self.cache / INDEX_LOCK)
        self.ingester = Ingester(store=self.store, logdir=self.logdir, series=self.series)
        self.authored: dict[str, tuple[float | None, ...]] = {}

    def folder_path(self, rel: str) -> Path:
        """Turn a folder relative to the log dir into a path.

        :param rel: The folder, ``.`` for the log dir.
        :return: The absolute path."""
        return self.logdir if rel in (".", "") else self.logdir / rel

    def walk(self, scope: str = ".", changed: set[str] | None = None) -> list[tuple[str, float]]:
        """Find the runs at or below a folder, reusing listings of unchanged folders.

        One ``stat`` of ``_run.json`` per run both identifies it and gives its
        heartbeat, so a walk over many finished runs stays cheap.

        :param scope: The folder relative to the log dir.
        :param changed: If given, collects folders whose notes, proposals, memory or
            views changed since the last walk of this index.
        :return: Each run's path relative to the log dir and its ``_run.json`` mtime."""
        now = time.time()
        root = str(self.logdir)
        found: list[tuple[str, float]] = []
        stack = [scope]
        while stack:
            rel = stack.pop()
            d = root if rel in (".", "") else os.path.join(root, rel)
            try:
                found.append((rel, os.stat(os.path.join(d, c.RUN)).st_mtime))
                continue
            except OSError:
                pass
            try:
                st = os.stat(d)
            except OSError:
                continue
            row = self.store.folder(rel)
            fresh = (
                row is not None
                and row["mtime"] == st.st_mtime
                and st.st_mtime < row["walked"] - MTIME_SLACK_S
            )
            if fresh:
                children = json.loads(row["children"])
            else:
                children = sorted(
                    e.name
                    for e in os.scandir(d)
                    if e.is_dir(follow_symlinks=True) and not is_reserved(e.name)
                )
                self.store.set_folder(rel, mtime=st.st_mtime, walked=now, children=children)
            notes = mtime(os.path.join(d, c.NOTES))
            if row is None or row["notes_mtime"] != notes:
                with self.store.transaction():
                    folder = Path(d) / c.NOTES
                    entries = read_notes(folder, self.logdir) if notes else []
                    self.store.replace_notes(rel, None, entries)
                    self.store.set_folder(rel, notes_mtime=notes)
                if changed is not None and row is not None:
                    changed.add(rel)
            if changed is not None:
                authored = tuple(mtime(os.path.join(d, name)) for name in AUTHORED)
                if self.authored.setdefault(rel, authored) != authored:
                    self.authored[rel] = authored
                    changed.add(rel)
            stack.extend(name if rel in (".", "") else f"{rel}/{name}" for name in children)
        return found

    def forget(self, run_id: str) -> None:
        """Drop a vanished run from the index.

        :param run_id: The run id."""
        with self.store.transaction():
            self.store.delete_run(run_id)
        shutil.rmtree(self.series / run_id, ignore_errors=True)

    def catch_up(
        self, scope: str = ".", budget_s: float = 0.2, *, daemon: bool = False
    ) -> Freshness:
        """Bring a folder's runs up to date, spending at most a time budget on streams.

        Small files (``_run.json``, config, card, notes) are always indexed, so run
        tables are complete; metric, event and data streams only while the budget lasts.

        :param scope: The folder relative to the log dir.
        :param budget_s: Seconds to spend on streams.
        :param daemon: Whether the caller is the daemon itself; only the daemon's
            ``Freshness.changed`` also lists folders with new authored files.
        :return: The freshness of the index for that folder."""
        if not daemon and daemon_status(self.cache) is not None:
            return Freshness(daemon=True)
        if not self.lock.acquire(timeout=budget_s):
            return Freshness(busy=True)
        try:
            deadline = time.monotonic() + budget_s
            freshness = Freshness(daemon=daemon)
            todo = []
            rows = {r["id"]: r for r in self.store.runs_in(scope)}
            if (one := self.store.run(scope.rsplit("/", 1)[-1])) is not None:
                rows[one["id"]] = one
            changed = freshness.changed if daemon else None
            found = self.walk(scope, changed)
            ids = {rel.rsplit("/", 1)[-1] for rel, _ in found}
            for run_id, row in rows.items():
                if run_id not in ids and not (self.logdir / row["path"]).is_dir():
                    self.forget(run_id)
                    freshness.changed.add(row["path"])
            for rel, run_mtime in found:
                run_id = rel.rsplit("/", 1)[-1]
                try:
                    meta, streams = self.ingester.stale(rel, run_mtime, rows.get(run_id))
                    if meta:
                        self.ingester.ingest_meta(self.logdir / rel)
                        freshness.changed.add(rel)
                except (OSError, ValueError) as e:
                    freshness.damaged.append(f"{run_id}: {e}")
                    continue
                if streams:
                    todo.append(self.logdir / rel)
            now = time.time()
            lags: list[float | None] = []
            for run_dir in todo:
                if time.monotonic() > deadline:
                    indexed = self.store.run(run_dir.name)["indexed_at"]
                    lags.append(None if indexed is None else now - indexed)
                    continue
                try:
                    self.ingester.ingest_streams(run_dir)
                    freshness.changed.add(run_dir.relative_to(self.logdir).as_posix())
                except (OSError, ValueError) as e:
                    freshness.damaged.append(f"{run_dir.name}: {e}")
            freshness.behind = len(lags)
            if lags and None not in lags:
                freshness.behind_s = max(lags)
            return freshness
        finally:
            self.lock.release()

    def reindex(self) -> Freshness:
        """Rebuild the index from the files.

        :return: The freshness after the rebuild."""
        with self.lock:
            self.store.rebuild()
            shutil.rmtree(self.series, ignore_errors=True)
        return self.catch_up(".", budget_s=float("inf"))

    def run_path(self, run_id: str) -> Path | None:
        """Find an indexed run's directory.

        :param run_id: The run id.
        :return: The directory, or ``None`` if the run isn't indexed."""
        row = self.store.run(run_id)
        return self.logdir / row["path"] if row else None

    def close(self) -> None:
        """Close the database connection."""
        self.store.db.close()
