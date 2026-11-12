"""``beamtime serve --stdio``: the API over stdin and stdout, which a laptop starts over ssh.

Each line in is a request ``{id, method, params, caller}``; each line out is its answer ``{id,
result}`` or ``{id, error: {message, code}}``, or an event ``{event: "changed", changed}`` for the
scopes the laptop subscribed to, where ``changed`` maps each path to the kinds that changed
(``metrics``, ``status``, ``authored``). Requests run in a few threads, so several can be in
flight. The process ends when stdin closes, and with it the temporary cache it indexed into."""

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

from beamtime.index.cache import resolve_cache
from beamtime.ops.context import Context, OpError
from beamtime.settings import expand_path

WORKERS = 4
WATCH_S = 2.0
# which cache this session indexes into, for hello: its path, and why a configured one was refused.
CACHE: dict[str, str | None] = {}


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
        ctx = dataclasses.replace(
            self.ctx, caller=caller, whole=request.get("whole") is True, wire=True
        )
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
        """Catch up the watched scopes every few seconds and report what changed, and how."""
        from beamtime.index.index import Index

        with Index(logdir=self.ctx.logdir, settings=self.ctx.settings) as index:
            while not self.stopping.wait(WATCH_S):
                changed: dict[str, set[str]] = {}
                for scope in sorted(self.watched):
                    try:
                        fresh = index.catch_up(scope, budget_s=1.0, daemon=True).changed
                    except Exception:  # noqa: BLE001
                        continue
                    for path, kinds in fresh.items():
                        changed.setdefault(path, set()).update(kinds)
                if changed:
                    payload = {path: sorted(kinds) for path, kinds in changed.items()}
                    self.send({"event": "changed", "changed": payload})


def run(*, logdir: str, cache: str | None = None) -> int:
    """Serve the API over stdin and stdout for one log dir.

    :param logdir: The remote log dir.
    :param cache: A persistent cache on a local disk; default the remote's own ``cache`` setting,
        else a temporary one.
    :return: The exit code."""
    path = Path(expand_path(logdir)).resolve()
    os.environ["BEAMTIME_LOGDIR"] = str(path)
    ctx = Context.make(root=path.parent, caller="cli")
    settings = ctx.settings
    if cache is not None:
        settings.values["cache"], settings.levels["cache"] = cache, "flag"
    # the remote's own BEAMTIME_CACHE doesn't count: only --cache or the setting persist a cache.
    resolved = resolve_cache(path, settings) if settings.get("cache") else None
    refused = resolved.refused if resolved else None
    own = None
    if resolved is None or resolved.kind == "memory":
        # one temporary cache for the whole session, so requests share their index.
        own = tempfile.mkdtemp(prefix="beamtime-remote-")
        settings.values["cache"], settings.levels["cache"] = own, "flag"
        resolved = resolve_cache(path, settings)
    CACHE.update(path=str(resolved.path), temporary="yes" if own else None, refused=refused)
    if refused:
        print(f"beamtime: the cache is on {refused}; using a temporary one", file=sys.stderr)
    # stdout carries the protocol: everything else an operation prints goes to stderr.
    out, sys.stdout = sys.stdout, sys.stderr
    try:
        ctx = dataclasses.replace(ctx, logdir=path)
        Remote(ctx=ctx, out=out).serve(sys.stdin)
    finally:
        sys.stdout = out
        if own is not None:
            shutil.rmtree(own, ignore_errors=True)
    return 0
