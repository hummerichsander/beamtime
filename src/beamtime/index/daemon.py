"""The indexing daemon: the one process per root that keeps the index live."""

import json
import os
import threading
import time
from pathlib import Path

from beamtime.index.cache import SERVE_JSON, SERVE_LOCK, FileLock, cache_dir
from beamtime.index.index import Index

POLL_S = 2.0


class Daemon:
    """Keeps a log dir's index current; ``beamtime serve`` runs one per root."""

    def __init__(
        self, *, logdir: Path, cache: Path | None = None, port: int | None = None
    ):
        """Prepare the daemon; nothing runs before ``start``.

        :param logdir: The log dir.
        :param cache: The cache directory; by default ``cache_dir(logdir)``.
        :param port: The web UI's port, recorded in ``serve.json``."""
        self.logdir = logdir.resolve()
        self.cache = cache or cache_dir(self.logdir)
        self.port = port
        self.lock = FileLock(path=self.cache / SERVE_LOCK)
        self.stopping = threading.Event()
        self.thread = threading.Thread(
            target=self.loop, name="beamtime-index", daemon=True
        )
        self.started = time.time()

    def start(self) -> bool:
        """Take ``serve.lock`` and start indexing.

        :return: ``False`` if another daemon already serves this root."""
        if not self.lock.acquire():
            return False
        self.write_status()
        self.thread.start()
        return True

    def write_status(self) -> None:
        """Write ``serve.json`` with pid, port, version, start time and heartbeat."""
        from importlib.metadata import version

        status = {
            "pid": os.getpid(),
            "port": self.port,
            "version": version("beamtime"),
            "logdir": str(self.logdir),
            "started": self.started,
            "heartbeat": time.time(),
        }
        (self.cache / SERVE_JSON).write_text(json.dumps(status))

    def loop(self) -> None:
        """Index everything once, then poll for changes until stopped."""
        index = Index(logdir=self.logdir, cache=self.cache)
        try:
            while not self.stopping.is_set():
                index.catch_up(".", budget_s=float("inf"), daemon=True)
                self.write_status()
                self.stopping.wait(POLL_S)
        finally:
            index.close()

    def stop(self) -> None:
        """Stop indexing and release ``serve.lock``."""
        self.stopping.set()
        if self.thread.is_alive():
            self.thread.join(30)
        try:
            (self.cache / SERVE_JSON).unlink()
        except OSError:
            pass
        self.lock.release()
