"""Read-only snapshots of remote groups: ``beamtime pull`` copies a group through the ``files``
method into the cache, and the snapshot answers for its remote while the remote can't.

A group comes with the ``view/``, ``blocks/`` and ``memory/`` folders of its ancestors, so its view,
library blocks and memory keep working; large data stays behind. Copies are incremental: a file
that grew is read from where the copy ends, others are copied again when their size or time
changed."""

import base64
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.ops.context import Context, OpError

SNAPSHOT = "_snapshot.json"
DATA_LIMIT = 16 << 20
SKIPPED = ("artifacts", "checkpoints")
APPENDED = (".jsonl", ".log")


def snapshots_dir(ctx: Context) -> Path:
    """Locate the snapshots of this project's remotes.

    :param ctx: The operation context.
    :return: ``<cache>/pulled``."""
    from beamtime.index.cache import cache_dir

    return cache_dir(ctx.logdir) / "pulled"


def snapshot_of(ctx: Context, name: str) -> tuple[Path, dict[str, Any]] | None:
    """Find a remote's snapshot.

    :param ctx: The operation context.
    :param name: The remote, without ``@``.
    :return: Its log dir copy and record, or ``None`` without one."""
    folder = snapshots_dir(ctx) / name
    try:
        return folder, json.loads((folder / SNAPSHOT).read_text())
    except (OSError, ValueError):
        return None


def wanted(path: str, size: int) -> bool:
    """Tell whether a remote file belongs in a snapshot.

    :param path: Its path relative to the remote log dir.
    :param size: Its size in bytes.
    :return: Whether to copy it."""
    parts = path.split("/")
    if any(p in SKIPPED for p in parts):
        return False
    return not (c.DATA_DIR in parts and size > DATA_LIMIT)


def pull(ctx: Context, name: str, group: str) -> dict[str, Any]:
    """Copy a remote group (and what its pages need from above) into the snapshot.

    :param ctx: The operation context.
    :param name: The remote.
    :param group: The group, relative to the remote's log dir.
    :return: What was copied."""
    from beamtime.remote.sources import client_for

    client = client_for(ctx, name)
    folder = snapshots_dir(ctx) / name
    parts = [] if group in (".", "") else group.strip("/").split("/")
    ancestors = ["/".join(parts[:i]) or "." for i in range(len(parts))]
    listings = [group, *(f"{a}/{sub}" for a in ancestors for sub in (c.VIEW, c.BLOCKS, c.MEMORY))]
    entries = [e for rel in listings for e in client.request("files", {"list": rel})["entries"]]
    if parts and not any(e["path"].startswith(f"{group}/") for e in entries):
        raise OpError(f"@{name} has no group {group!r}", code=4)
    copied = grown = same = moved = 0
    for e in entries:
        if not wanted(e["path"], e["size"]):
            continue
        dest = folder / e["path"]
        have = dest.stat() if dest.is_file() else None
        if have is not None and have.st_size == e["size"] and have.st_mtime >= e["mtime"]:
            same += 1
            continue
        appended = have is not None and e["path"].endswith(APPENDED) and have.st_size < e["size"]
        start = have.st_size if appended and have is not None else 0
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("ab" if appended else "wb") as f:
            offset = start
            while True:
                part = client.request("files", {"read": e["path"], "offset": offset})
                data = base64.b64decode(part["data"])
                f.write(data)
                offset += len(data)
                if part["eof"] or not data:
                    break
        moved += offset - start
        # the copy keeps the remote's times: heartbeats stay what they were there.
        os.utime(dest, (e["mtime"], e["mtime"]))
        grown += appended
        copied += not appended
    record = snapshot_of(ctx, name)
    groups = sorted({*(record[1].get("groups", []) if record else []), group})
    info = {
        "schema": 1,
        "source": name,
        "groups": groups,
        "at": time.time(),
        "host": client.spec.host or name,
        "path": client.spec.path,
    }
    (folder / SNAPSHOT).write_text(json.dumps(info) + "\n")
    lines = [
        f"@{name}:{group} → {folder}",
        f"{copied} copied, {grown} grown, {same} unchanged ({moved / 1e6:.1f} MB)",
        f"while @{name} is unreachable, @{name}/... answers from this snapshot (read-only)",
    ]
    return {
        "kind": "pull",
        "source": f"@{name}",
        "group": group,
        "folder": str(folder),
        "copied": copied,
        "grown": grown,
        "unchanged": same,
        "lines": lines,
        "meta": {},
    }


def drop(ctx: Context, name: str, group: str) -> dict[str, Any]:
    """Remove a group from a remote's snapshot, and the snapshot once it holds none.

    :param ctx: The operation context.
    :param name: The remote.
    :param group: The group.
    :return: What was removed."""
    if (found := snapshot_of(ctx, name)) is None:
        raise OpError(f"no snapshot of @{name}", code=4)
    folder, record = found
    groups = [g for g in record.get("groups", []) if g != group]
    if not groups or group in (".", ""):
        shutil.rmtree(folder)
        return {"kind": "pull", "lines": [f"removed the snapshot of @{name}"], "meta": {}}
    shutil.rmtree(folder / group, ignore_errors=True)
    (folder / SNAPSHOT).write_text(json.dumps(record | {"groups": groups}) + "\n")
    return {"kind": "pull", "lines": [f"removed @{name}:{group} from the snapshot"], "meta": {}}


def pull_op(ctx: Context, p: Any) -> dict[str, Any]:
    """Pull a remote group, or drop it from the snapshot (the ``pull`` operation).

    :param ctx: The operation context.
    :param p: The parameters: ``target`` as ``remote:group`` or ``@remote/group``, and ``drop``.
    :return: What happened."""
    name, group = split_target(p.target)
    return drop(ctx, name, group) if p.drop else pull(ctx, name, group)


def split_target(target: str) -> tuple[str, str]:
    """Read a pull target.

    :param target: ``cluster:scaling/lr-sweep``, ``@cluster/scaling`` or ``cluster``.
    :return: The remote and the group.
    :raises OpError: Without a remote name."""
    if target.startswith("@"):
        name, _, group = target[1:].partition("/")
    else:
        name, _, group = target.partition(":")
    if not name:
        raise OpError(f"pull {target!r}: name the remote, e.g. cluster:scaling/lr-sweep", code=2)
    return name, group.strip("/") or "."
