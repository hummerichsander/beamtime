"""The index cache directory and the file locks that coordinate its writers."""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

INDEX_LOCK = "index.lock"
SERVE_LOCK = "serve.lock"
SERVE_JSON = "serve.json"


def cache_dir(logdir: Path) -> Path:
    """Find the cache directory of a log dir: outside the repository, and on a cluster
    filesystem only if the user points it there.

    :param logdir: The log dir.
    :return: ``<cache>/beamtime/<hash of the log dir>``."""
    if base := os.environ.get("BEAMTIME_CACHE"):
        root = Path(base).expanduser()
    else:
        xdg = os.environ.get("XDG_CACHE_HOME")
        root = (Path(xdg).expanduser() if xdg else Path.home() / ".cache") / "beamtime"
    digest = hashlib.sha256(str(logdir.resolve()).encode()).hexdigest()[:16]
    return root / digest


class FileLock:
    """An exclusive lock on a file, released when its process ends."""

    def __init__(self, *, path: Path) -> None:
        """Prepare a lock; nothing is locked before ``acquire``.

        :param path: The lock file, created if missing."""
        self.path = path
        self.fd: int | None = None

    def acquire(self, timeout: float = 0.0) -> bool:
        """Try to take the lock, waiting up to ``timeout`` seconds.

        :param timeout: How long to keep trying; 0 tries once.
        :return: Whether the lock is held now."""
        if self.fd is not None:
            return True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        deadline = time.monotonic() + timeout
        while True:
            if self.try_lock(fd):
                self.fd = fd
                return True
            if time.monotonic() >= deadline:
                os.close(fd)
                return False
            time.sleep(0.01)

    @staticmethod
    def try_lock(fd: int) -> bool:
        """Take an exclusive lock without waiting.

        :param fd: The open lock file.
        :return: Whether it was taken."""
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True

    def release(self) -> None:
        """Release the lock if held."""
        if self.fd is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt

                os.lseek(self.fd, 0, os.SEEK_SET)
                msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.fd, fcntl.LOCK_UN)
        finally:
            os.close(self.fd)
            self.fd = None

    def held_elsewhere(self) -> bool:
        """Tell whether another process holds the lock, without keeping it.

        :return: Whether the lock is taken by someone else."""
        if self.fd is not None:
            return False
        if not self.acquire():
            return True
        self.release()
        return False

    def __enter__(self) -> "FileLock":
        """Take the lock, waiting as long as needed.

        :return: The lock."""
        self.acquire(timeout=float("inf"))
        return self

    def __exit__(self, *exc: Any) -> None:
        """Release the lock.

        :param exc: The exception information, ignored."""
        self.release()


def daemon_status(cache: Path) -> dict[str, Any] | None:
    """Describe the running daemon of a cache, if any.

    :param cache: The cache directory.
    :return: ``serve.json`` while ``serve.lock`` is held, else ``None``."""
    if not FileLock(path=cache / SERVE_LOCK).held_elsewhere():
        return None
    try:
        return json.loads((cache / SERVE_JSON).read_text())
    except (OSError, ValueError):
        return {}
