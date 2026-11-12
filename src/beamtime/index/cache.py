"""The index cache directory and the file locks that coordinate its writers."""

import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from beamtime.settings import expand_path

if TYPE_CHECKING:
    from beamtime.settings import Settings

INDEX_LOCK = "index.lock"
SERVE_LOCK = "serve.lock"
SERVE_JSON = "serve.json"
MOUNTS = Path("/proc/mounts")
NETWORK_FS = ("nfs", "nfs4", "lustre", "gpfs", "cifs", "smbfs", "smb3", "beegfs", "fuse.sshfs")


def runtime_dir(logdir: Path) -> Path:
    """Locate where a memory cache publishes ``serve.lock``, ``serve.json`` and the token.

    :param logdir: The log dir.
    :return: ``<tmp>/beamtime-<uid>/<hash of the log dir>``, created with mode 0700."""
    import getpass
    import tempfile

    uid = os.getuid() if hasattr(os, "getuid") else getpass.getuser()
    base = Path(tempfile.gettempdir()) / f"beamtime-{uid}"
    base.mkdir(mode=0o700, exist_ok=True)
    base.chmod(0o700)
    path = base / log_hash(logdir)
    path.mkdir(mode=0o700, exist_ok=True)
    return path


def log_hash(logdir: Path) -> str:
    """Name a log dir in the cache.

    :param logdir: The log dir.
    :return: The first 16 hex digits of the hash of its resolved path."""
    return hashlib.sha256(str(logdir.resolve()).encode()).hexdigest()[:16]


def network_fs(path: Path) -> str | None:
    """Tell whether a folder is on a network or parallel filesystem, where SQLite is unsafe.

    :param path: The folder (it may not exist yet).
    :return: The filesystem type if it is one, else ``None``."""
    try:
        mounts = MOUNTS.read_text().splitlines()
    except OSError:
        return None
    target = str(path.resolve())
    best, kind = "", None
    for line in mounts:
        parts = line.split()
        if len(parts) < 3:
            continue
        mount = parts[1]
        below = target == mount or target.startswith(mount.rstrip("/") + "/")
        if below and len(mount) > len(best):
            best, kind = mount, parts[2]
    return kind if kind in NETWORK_FS else None


@dataclass(frozen=True)
class Cache:
    """Where the index of a log dir lives on this machine, and why."""

    path: Path
    kind: Literal["disk", "memory"]
    refused: str | None
    source: str


def resolve_cache(logdir: Path, settings: "Settings | None" = None) -> Cache:
    """Resolve the cache of a log dir, the one way every consumer does.

    The first match wins: a ``--cache`` flag, ``BEAMTIME_CACHE``, the ``cache`` setting, the user
    cache dir. A folder on a network filesystem is refused and becomes ``memory``.

    :param logdir: The log dir.
    :param settings: The effective settings; without them only the environment counts.
    :return: For ``disk``, ``<cache>/<hash of the log dir>``; for ``memory``, ``runtime_dir``
        (where ``serve`` publishes itself), while each index uses its own temporary folder."""
    configured = settings.get("cache") if settings is not None else None
    level = settings.levels.get("cache") if settings is not None else None
    if configured and level == "flag":
        value, source = configured, "--cache"
    elif env := os.environ.get("BEAMTIME_CACHE"):
        value, source = env, "BEAMTIME_CACHE"
    elif configured:
        value, source = configured, f"{level} settings"
    else:
        xdg = os.environ.get("XDG_CACHE_HOME")
        value, source = (
            str((Path(xdg).expanduser() if xdg else Path.home() / ".cache") / "beamtime"),
            "default",
        )
    if value == "memory":
        return Cache(runtime_dir(logdir), "memory", None, source)
    root = Path(expand_path(value))
    if refused := network_fs(root):
        return Cache(runtime_dir(logdir), "memory", refused, source)
    return Cache(root / log_hash(logdir), "disk", None, source)


def cache_dir(logdir: Path, settings: "Settings | None" = None) -> Path:
    """Find the cache directory of a log dir: outside the repository, never on a network
    filesystem.

    :param logdir: The log dir.
    :param settings: The effective settings.
    :return: The path of ``resolve_cache``."""
    return resolve_cache(logdir, settings).path


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
