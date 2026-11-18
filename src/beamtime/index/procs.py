"""The registry of a user's long-running Beamtime processes, in ``<runtime base>/procs/``."""

import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Literal

from beamtime.index.cache import FileLock, runtime_base

SCHEMA = 1
YOUNG = 60.0


def procs_dir() -> Path:
    """Locate the registry folder without creating it.

    :return: ``<runtime base>/procs``."""
    return runtime_base() / "procs"


class Registration:
    """One process's lock file and JSON record, held for its whole life."""

    def __init__(self, *, kind: str, fields: dict[str, Any]) -> None:
        """Prepare a registration; nothing is written before ``open``.

        :param kind: The process kind.
        :param fields: The record's fields besides ``schema`` and ``kind``."""
        self.kind = kind
        self.fields = dict(fields)
        self.record: Path | None = None
        self.lock: FileLock | None = None

    def open(self) -> "Registration":
        """Take the lock, then write the record.

        :return: This registration."""
        folder = procs_dir()
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        while True:
            stem = f"{self.kind}-{os.getpid()}-{secrets.token_hex(3)}"
            if not (folder / f"{stem}.lock").exists():
                break
        self.lock = FileLock(path=folder / f"{stem}.lock")
        if not self.lock.acquire():
            raise OSError(f"cannot lock {self.lock.path}")
        self.record = folder / f"{stem}.json"
        self.write()
        return self

    def update(self, **fields: Any) -> None:
        """Change fields of the record.

        :param fields: The new values."""
        self.fields.update(fields)
        self.write()

    def write(self) -> None:
        """Write the record atomically, mode 0600."""
        assert self.record is not None
        tmp = self.record.with_suffix(".tmp")
        data = {"schema": SCHEMA, "kind": self.kind, **self.fields}
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp, self.record)

    def close(self) -> None:
        """Remove the record, then release and remove the lock."""
        if self.record is None or self.lock is None:
            return
        self.record.unlink(missing_ok=True)
        self.lock.release()
        try:
            self.lock.path.unlink()
        except OSError:
            pass
        self.record = None

    def __enter__(self) -> "Registration":
        """Register if not yet open.

        :return: This registration."""
        if self.record is None:
            self.open()
        return self

    def __exit__(self, *exc: Any) -> None:
        """Unregister.

        :param exc: The exception information, ignored."""
        self.close()


def register(kind: Literal["serve", "index", "remote", "mcp"], **fields: Any) -> Registration:
    """Register this process.

    :param kind: The process kind.
    :param fields: The record's fields: ``root``, ``logdir``, ``cache``, ``cache_kind``, ``port``,
        ``sources`` and ``client``; missing ones are ``None``.
    :return: The open registration; ``close()`` it when the process ends."""
    from importlib.metadata import version

    defaults = {"root": None, "logdir": None, "cache": None, "cache_kind": None, "client": None}
    defaults |= {"port": None, "sources": []} if kind == "serve" else {}
    record = {
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "version": version("beamtime"),
        "started": time.time(),
        **defaults,
        **fields,
    }
    return Registration(kind=kind, fields=record).open()


def listed() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Read the registry and remove the records of processes that died.

    :return: The live records and the stale ones (their files are removed), each sorted by kind,
        then start."""
    folder = procs_dir()
    live, stale = [], []
    if not folder.is_dir():
        return live, stale
    for path in sorted(folder.glob("*.json")):
        lock = FileLock(path=path.with_suffix(".lock"))
        if not lock.path.exists():
            continue
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(record, dict):
            continue
        if not lock.acquire():
            live.append(record)
            continue
        stale.append(record)
        remove(path, lock)
    for path in folder.glob("*.lock"):
        if path.with_suffix(".json").exists() or time.time() - mtime(path) < YOUNG:
            continue
        if (lock := FileLock(path=path)).acquire():
            remove(path.with_suffix(".json"), lock)
    return sorted(live, key=order), sorted(stale, key=order)


def order(record: dict[str, Any]) -> tuple[str, float]:
    """Sort key of a record.

    :param record: The record.
    :return: Its kind and start."""
    return str(record.get("kind", "")), float(record.get("started", 0))


def remove(record: Path, lock: FileLock) -> None:
    """Delete a dead process's files while holding its lock.

    :param record: The JSON record.
    :param lock: The held lock; released here."""
    try:
        record.unlink(missing_ok=True)
    except OSError:
        pass
    lock.release()
    try:
        lock.path.unlink()
    except OSError:
        pass


def mtime(path: Path) -> float:
    """Read a file's modification time.

    :param path: The file.
    :return: Its mtime, or now when it is gone."""
    try:
        return path.stat().st_mtime
    except OSError:
        return time.time()
