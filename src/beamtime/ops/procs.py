"""``ps``: the Beamtime processes of this user on this machine.

Agents never run these; they hand the user the command."""

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

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
from beamtime.ops.context import Context
from beamtime.settings import expand_path

KINDS = ("serve", "index", "remote", "mcp", "ssh")
TOKEN_FILE = "serve.token"
SSH_CHECK_S = 3


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

    :return: One row per marked host of ``~/.ssh/config`` whose login is open."""
    from beamtime.setup.remotes import SSH_MARK

    try:
        lines = (Path.home() / ".ssh" / "config").read_text().splitlines()
    except OSError:
        return []
    hosts = [line[len(SSH_MARK) :].strip() for line in lines if line.startswith(SSH_MARK)]
    out = []
    for host in dict.fromkeys(h for h in hosts if h):
        try:
            done = subprocess.run(
                ["ssh", "-O", "check", host],
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=SSH_CHECK_S,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if done.returncode:
            continue
        found = re.search(r"pid=(\d+)", done.stderr + done.stdout)
        out.append(
            {
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
        )
    return out
