"""``beamtime serve --stdio``: the API over stdin and stdout, which a laptop starts over ssh.

Each line in is a request ``{id, method, params, caller}``; each line out is its answer ``{id,
result}`` or ``{id, error: {message, code}}``, or an event ``{event: "changed", paths}`` for the
scopes the laptop subscribed to. Requests run in a few threads, so several can be in flight. The
process ends when stdin closes, and with it the temporary cache it indexed into."""

import dataclasses
import json
import os
import shutil
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import IO, Any

import msgspec

from beamtime.ops.context import Context, OpError

WORKERS = 4
WATCH_S = 2.0
# which cache this session indexes into, for hello: its path, and why a configured one was refused.
CACHE: dict[str, str | None] = {}
NETWORK_FS = ("nfs", "nfs4", "lustre", "gpfs", "cifs", "smbfs", "smb3", "beegfs", "fuse.sshfs")


class Remote:
    """One stdio session: its context, its answers' writer and the scopes it watches."""

    def __init__(self, *, ctx: Context, out: IO[str]) -> None:
        """Prepare a session.

        :param ctx: The operation context for the remote's log dir.
        :param out: Where answers and events go."""
        self.ctx = ctx
        self.out = out
        self.lock = threading.Lock()
        self.watched: set[str] = set()
        self.stopping = threading.Event()

    def serve(self, lines: IO[str]) -> None:
        """Answer requests until the input ends.

        :param lines: The requests, one JSON object per line."""
        watcher = threading.Thread(target=self.watch, name="beamtime-watch", daemon=True)
        watcher.start()
        with ThreadPoolExecutor(WORKERS, thread_name_prefix="beamtime-stdio") as pool:
            for line in lines:
                if line.strip():
                    pool.submit(self.answer, line)
        self.stopping.set()

    def answer(self, line: str) -> None:
        """Answer one request line.

        :param line: The request."""
        from beamtime.serve.api import dispatch

        try:
            request = json.loads(line)
            rid, method = request["id"], str(request["method"])
            params = request.get("params") or {}
        except (ValueError, KeyError, TypeError):
            error = {"message": f"not a request: {line[:200]!r}", "code": 2}
            self.send({"id": None, "error": error})
            return
        caller = request.get("caller") if request.get("caller") in ("cli", "mcp", "view") else "cli"
        ctx = dataclasses.replace(self.ctx, caller=caller)
        try:
            if method == "subscribe":
                self.watched = {str(p) for p in params.get("paths") or []}
                result: Any = {"kind": "subscribe", "watching": sorted(self.watched)}
            else:
                result = dispatch(ctx, method, params)
            if isinstance(result, bytes):
                import base64

                result = {"kind": "bytes", "data": base64.b64encode(result).decode()}
            self.send({"id": rid, "result": result})
        except OpError as e:
            self.send({"id": rid, "error": {"message": str(e), "code": e.code}})
        except Exception as e:  # noqa: BLE001
            # one broken request must not end the session the laptop relies on.
            self.send({"id": rid, "error": {"message": f"{type(e).__name__}: {e}", "code": 1}})

    def send(self, message: dict[str, Any]) -> None:
        """Write one line of output.

        :param message: An answer or an event."""
        data = msgspec.json.encode(message, enc_hook=str).decode()
        with self.lock:
            self.out.write(data + "\n")
            self.out.flush()

    def watch(self) -> None:
        """Catch up the watched scopes every few seconds and report what changed."""
        from beamtime.index.index import Index

        with Index(logdir=self.ctx.logdir) as index:
            while not self.stopping.wait(WATCH_S):
                changed: set[str] = set()
                for scope in sorted(self.watched):
                    try:
                        changed |= index.catch_up(scope, budget_s=1.0, daemon=True).changed
                    except Exception:  # noqa: BLE001
                        continue
                if changed:
                    self.send({"event": "changed", "paths": sorted(changed)})


def run(*, logdir: str, cache: str | None = None) -> int:
    """Serve the API over stdin and stdout for one log dir.

    :param logdir: The remote log dir.
    :param cache: A persistent cache on a local disk; default a temporary one.
    :return: The exit code."""
    path = Path(expand(logdir)).resolve()
    own, reason = None, None
    if cache is not None and (reason := network_fs(Path(expand(cache)))):
        cache = None
    if cache is None:
        own = tempfile.mkdtemp(prefix="beamtime-remote-")
        cache = own
    os.environ["BEAMTIME_CACHE"] = expand(cache)
    os.environ["BEAMTIME_LOGDIR"] = str(path)
    temporary = "yes" if own else None
    CACHE.update(path=os.environ["BEAMTIME_CACHE"], temporary=temporary, refused=reason)
    if reason:
        print(f"beamtime: the cache is on {reason}; using a temporary one", file=sys.stderr)
    # stdout carries the protocol: everything else an operation prints goes to stderr.
    out, sys.stdout = sys.stdout, sys.stderr
    try:
        ctx = Context.make(root=path.parent, caller="cli")
        ctx = dataclasses.replace(ctx, logdir=path)
        Remote(ctx=ctx, out=out).serve(sys.stdin)
    finally:
        sys.stdout = out
        if own is not None:
            shutil.rmtree(own, ignore_errors=True)
    return 0


def expand(path: str) -> str:
    """Expand a configured path on this machine: ``~``, ``${VAR}`` and ``{user}``.

    :param path: The path as configured, e.g. ``/scratch/{user}/beamtime``.
    :return: The path."""
    import getpass

    return str(Path(os.path.expandvars(path.replace("{user}", getpass.getuser()))).expanduser())


def network_fs(path: Path) -> str | None:
    """Tell whether a folder is on a network or parallel filesystem, where SQLite is unsafe.

    :param path: The folder (it may not exist yet).
    :return: The filesystem type if it is one, else ``None``."""
    try:
        mounts = Path("/proc/mounts").read_text().splitlines()
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
