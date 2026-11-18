"""``ps``: the Beamtime processes of this user on this machine.

Agents never run these; they hand the user the command."""

import json
import os
import re
import signal
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Literal

from beamtime.index.cache import (
    SERVE_JSON,
    SERVE_LOCK,
    FileLock,
    cache_value,
    resolve_cache,
    runtime_base,
)
from beamtime.index.procs import listed
from beamtime.ops import registry as r
from beamtime.ops.context import Context, OpError
from beamtime.settings import expand_path

KINDS = ("serve", "index", "remote", "mcp", "ssh")
TOKEN_FILE = "serve.token"
SSH_CHECK_S = 3
SHUTDOWN_S = 3


def ps(ctx: Context, p: r.NoParams) -> dict[str, Any]:
    """List every Beamtime process of this user on this machine, and remove the dead ones' files.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer: rows by kind, the stale rows that were removed and notes."""
    live, stale = scan(ctx)
    now = time.time()
    rows = [row(ctx, record, now) for record in live] + ssh_rows()
    groups = {kind: [x for x in rows if x["kind"] == kind] for kind in KINDS}
    return {
        "kind": "ps",
        "groups": groups,
        "stale": [row(ctx, record, now, alive=False) for record in stale],
        "lines": [] if rows or stale else ["no Beamtime process runs"],
        "meta": {},
    }


def stop(ctx: Context, p: r.StopParams) -> dict[str, Any]:
    """Stop serves: this directory's, the one a root, log dir or pid names, or all.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was stopped, with a line each."""
    if p.all and p.target:
        raise OpError("pass a root, log dir or pid, or --all, not both", code=2)
    rows = serves(ctx)
    if p.all:
        chosen, name = rows, "any serve"
    elif p.target:
        chosen, name = named(ctx, rows, p.target), p.target
    else:
        here = ctx.logdir.resolve()
        chosen = [x for x in rows if x.get("logdir") and Path(x["logdir"]).resolve() == here]
        name = str(ctx.root)
    if not chosen:
        return {"kind": "stop", "stopped": [], "lines": [f"no serve runs for {name}"]}
    lines, stuck = [], []
    for x in chosen:
        where = x.get("root") or x.get("logdir")
        match stop_serve(x):
            case "running":
                stuck.append(
                    f"still stopping {where} (pid {x['pid']}); `kill -9 {x['pid']}` ends it now"
                )
            case how:
                via = "through the token" if how == "token" else "with SIGTERM"
                lines.append(f"stopped {where} (pid {x['pid']}) {via}")
    if stuck:
        raise OpError("\n".join(lines + stuck))
    return {"kind": "stop", "stopped": [x["pid"] for x in chosen], "lines": lines}


def named(ctx: Context, rows: list[dict[str, Any]], target: str) -> list[dict[str, Any]]:
    """Pick the serves a target names.

    :param ctx: The operation context.
    :param rows: The running serves.
    :param target: A pid as ``ps`` prints it, or a path matching a serve's root or log dir.
    :return: The serves; none when no serve has that root or log dir.
    :raises OpError: With code 2 when the pid belongs to a process that is listed, never stopped,
        and code 4 when no Beamtime process has it."""
    if not target.isdigit():
        path = Path(target).expanduser().resolve()
        paths = ("root", "logdir")
        return [x for x in rows if any(x.get(k) and Path(x[k]).resolve() == path for k in paths)]
    pid = int(target)
    if found := [x for x in rows if x["pid"] == pid]:
        return found
    live, _ = scan(ctx)
    now = time.time()
    others = [row(ctx, record, now) for record in live] + ssh_rows()
    for x in others:
        if x["pid"] == pid:
            owner = x.get("client") or x.get("host") or x["kind"]
            raise OpError(
                f"listed, not stopped: pid {pid} is a {x['kind']} process that belongs to {owner}",
                code=2,
            )
    raise OpError(f"no Beamtime process has pid {pid}; `beamtime ps` lists them", code=4)


def stop_serve(x: dict[str, Any], wait_s: float = 10.0) -> Literal["token", "sigterm", "running"]:
    """Stop one serve through its token, else with SIGTERM, and wait for its lock.

    :param x: The serve's row.
    :param wait_s: How long to wait for the lock after each attempt.
    :return: How it stopped, or ``running`` when it still holds its lock; SIGKILL is never sent."""
    lock = FileLock(path=Path(x["cache"]) / SERVE_LOCK)
    if x.get("port") and shutdown_request(x):
        if wait_free(lock, wait_s):
            return "token"
    if x.get("pid"):
        try:
            os.kill(x["pid"], signal.SIGTERM)
        except ProcessLookupError:
            pass
        if wait_free(lock, wait_s):
            return "sigterm"
    return "running"


def shutdown_request(x: dict[str, Any]) -> bool:
    """Ask a serve to stop with ``POST /api/shutdown``.

    :param x: The serve's row.
    :return: Whether the serve accepted."""
    try:
        token = (Path(x["cache"]) / TOKEN_FILE).read_text().strip()
        request = urllib.request.Request(
            f"http://127.0.0.1:{x['port']}/api/shutdown",
            data=b"{}",
            headers={"authorization": f"Bearer {token}", "content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=SHUTDOWN_S):
            return True
    except (OSError, ValueError):
        return False


def wait_free(lock: FileLock, wait_s: float) -> bool:
    """Wait until nobody holds a lock.

    :param lock: The lock.
    :param wait_s: The longest wait in seconds.
    :return: Whether it is free."""
    deadline = time.monotonic() + wait_s
    while lock.held_elsewhere():
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)
    return True


def serves(ctx: Context) -> list[dict[str, Any]]:
    """List the running serves: web UIs and index daemons, also those of an older Beamtime.

    :param ctx: The operation context.
    :return: One row per live ``serve`` or ``index`` process, as ``ps`` shows it."""
    live, _ = scan(ctx)
    now = time.time()
    return [row(ctx, record, now) for record in live if record["kind"] in ("serve", "index")]


def scan(ctx: Context) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Read the registry and the ``serve.json`` files, and remove what belongs to dead processes.

    :param ctx: The operation context.
    :return: The live records, with a record for each serve that has none, and the stale ones."""
    live, stale = listed()
    seen = {
        cache_key(record) for record in live + stale if record.get("kind") in ("serve", "index")
    }
    for path in serve_files(ctx):
        key = str(path.parent.resolve())
        if FileLock(path=path.parent / SERVE_LOCK).held_elsewhere():
            if key not in seen:
                live.append(legacy_record(path))
            continue
        if key not in seen:
            stale.append(legacy_record(path))
        path.unlink(missing_ok=True)
    return sorted(live, key=order), sorted(stale, key=order)


def serve_files(ctx: Context) -> list[Path]:
    """Find the ``serve.json`` files of the disk cache root and the runtime base.

    :param ctx: The operation context.
    :return: The files, one level below each folder."""
    folders = [runtime_base()]
    if (value := cache_value(ctx.settings)[0]) != "memory":
        folders.append(Path(expand_path(value)))
    found: dict[Path, Path] = {}
    for folder in folders:
        for path in folder.glob(f"*/{SERVE_JSON}"):
            found[path.resolve()] = path
    return sorted(found.values())


def legacy_record(path: Path) -> dict[str, Any]:
    """Make the record of a serve from its ``serve.json``, for one that did not register.

    :param path: The ``serve.json``.
    :return: A record with ``schema`` 0."""
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        data = {}
    cache = path.parent
    return {
        "schema": 0,
        "kind": "serve" if data.get("port") else "index",
        "pid": data.get("pid"),
        "ppid": None,
        "version": data.get("version"),
        "started": data.get("started"),
        "root": None,
        "logdir": data.get("logdir"),
        "cache": str(cache),
        "cache_kind": "memory" if cache.parent == runtime_base() else "disk",
        "port": data.get("port"),
        "sources": [],
        "client": None,
    }


def cache_key(record: dict[str, Any]) -> str:
    """Name the cache folder of a record, to tell a serve from its own ``serve.json``.

    :param record: The record.
    :return: The resolved cache path."""
    return str(Path(record["cache"]).resolve()) if record.get("cache") else ""


def order(record: dict[str, Any]) -> tuple[str, float]:
    """Sort key of a record.

    :param record: The record.
    :return: Its kind and start."""
    return str(record.get("kind", "")), float(record.get("started") or 0)


def row(ctx: Context, record: dict[str, Any], now: float, *, alive: bool = True) -> dict[str, Any]:
    """Add what ``ps`` shows to a record.

    :param ctx: The operation context.
    :param record: The record.
    :param now: The current time.
    :param alive: Whether the process runs; a dead one has no URL and is used by nobody.
    :return: The record with ``url``, ``uptime_s`` and ``used_here``."""
    started = record.get("started")
    return record | {
        "url": url(record) if alive else None,
        "uptime_s": now - started if alive and started else None,
        "used_here": used_here(ctx, record) if alive else "-",
    }


def url(record: dict[str, Any]) -> str | None:
    """Write the URL of a serve with the token, as ``serve`` prints it.

    :param record: The record.
    :return: The URL, or ``None`` for a process without a port."""
    if not (port := record.get("port")):
        return None
    try:
        token = (Path(record["cache"]) / TOKEN_FILE).read_text().strip()
    except (OSError, KeyError, TypeError):
        token = ""
    return f"http://localhost:{port}/f/local" + (f"?token={token}" if token else "")


def used_here(ctx: Context, record: dict[str, Any]) -> str:
    """Say whether this directory's CLI and MCP calls use a serve.

    :param ctx: The operation context.
    :param record: The record.
    :return: The words of the design's table; ``-`` for other kinds and other log dirs."""
    if record["kind"] not in ("serve", "index") or not record.get("logdir"):
        return "-"
    if Path(record["logdir"]).resolve() != ctx.logdir.resolve():
        return "-"
    mine = resolve_cache(ctx.logdir, ctx.settings)
    if Path(record["cache"]).resolve() != mine.path.resolve():
        where = "memory" if mine.kind == "memory" else str(mine.path)
        return f"no: this shell's cache is {where} ({mine.source})"
    memory = record["cache_kind"] == "memory"
    match record["kind"], memory:
        case "index", True:
            return "no: memory, no UI"
        case "index", False:
            return "live index"
        case _, True:
            return "all reads"
        case _:
            return "live index, remote calls"


def ssh_rows() -> list[dict[str, Any]]:
    """List the logins kept open for the hosts that ``beamtime setup`` configured.

    :return: One row per marked host of ``~/.ssh/config`` whose login is open, in file order."""
    from beamtime.setup.remotes import SSH_MARK

    try:
        lines = (Path.home() / ".ssh" / "config").read_text().splitlines()
    except OSError:
        return []
    hosts = [line[len(SSH_MARK) :].strip() for line in lines if line.startswith(SSH_MARK)]
    hosts = list(dict.fromkeys(h for h in hosts if h))
    if not hosts:
        return []
    with ThreadPoolExecutor(max_workers=len(hosts)) as pool:
        rows = pool.map(ssh_row, hosts)
    return [row for row in rows if row is not None]


def ssh_row(host: str) -> dict[str, Any] | None:
    """Check one host's login with ``ssh -O check``.

    :param host: A host that ``beamtime setup`` configured.
    :return: The row of the open login, or None when there is none or ``ssh`` fails or hangs."""
    try:
        done = subprocess.run(
            ["ssh", "-O", "check", host],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=SSH_CHECK_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if done.returncode:
        return None
    found = re.search(r"pid=(\d+)", done.stderr + done.stdout)
    return {
        "kind": "ssh",
        "pid": int(found[1]) if found else None,
        "host": host,
        "started": None,
        "root": None,
        "logdir": None,
        "cache": None,
        "cache_kind": None,
        "url": None,
        "uptime_s": None,
        "used_here": "-",
        "end": f"ssh -O exit {host}",
    }
