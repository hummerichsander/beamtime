"""Helpers every authored write shares: the target group, the author, the new version file and
the answer."""

import posixpath
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.authored import newest
from beamtime.format.ids import is_run_id, new_version_id
from beamtime.format.io import write_created
from beamtime.format.tree import is_reserved, is_run
from beamtime.index.index import Index
from beamtime.ops.context import Context, OpError
from beamtime.query.models import QueryError
from beamtime.query.select import resolve_from
from beamtime.record.proposals import RecordError, Target


@contextmanager
def target_of(ctx: Context, group: str, *, create: bool = False) -> Iterator[Target]:
    """Open the index, catch up, and resolve a group or run.

    :param ctx: The operation context.
    :param group: A group below the log dir, or a run id.
    :param create: Whether a missing group is created, for writes before the first run.
    :return: The target, while the index is open."""
    if create:
        make_group(ctx, group)
    if not ctx.logdir.is_dir():
        raise OpError(f"no log dir at {ctx.logdir}; `beamtime init` sets one up", code=4)
    with Index(logdir=ctx.logdir) as index:
        index.catch_up(".", 0.2)
        try:
            rel, run_id = resolve_from(index, ".", group)
        except QueryError as e:
            raise OpError(str(e), code=4 if e.code == "not_found" else 2) from None
        try:
            yield Target(index=index, rel=rel, run_id=run_id, now=ctx.now)
        except RecordError as e:
            raise OpError(str(e), code=3) from None


def make_group(ctx: Context, group: str) -> None:
    """Create a missing group below the log dir, refusing reserved names and runs.

    :param ctx: The operation context.
    :param group: The group relative to the log dir, or a run id."""
    rel = posixpath.normpath(group.strip("/") or ".")
    if is_run_id(rel.rsplit("/", 1)[-1]) or rel == ".":
        return
    if rel.startswith(".."):
        raise OpError(f"{group!r} leaves the log dir", code=2)
    path = ctx.logdir / rel
    if path.is_dir():
        return
    if any(is_reserved(part) for part in rel.split("/")):
        raise OpError(f"{group!r}: names starting with _ or . and {sorted(c.AUTHORED)} are "
                      "reserved; choose another group name", code=2)  # fmt: skip
    if any(is_run(parent) for parent in path.parents):
        raise OpError(f"{group!r} is inside a run; give the run id instead", code=2)
    path.mkdir(parents=True)


def author_of(ctx: Context, author: str | None) -> tuple[str, str]:
    """Name who writes a file and the account it is written for.

    :param ctx: The operation context.
    :param author: The given author, if any.
    :return: ``(author, user)``."""
    from beamtime.sdk.env import user

    account = user()
    return author or (account if ctx.caller in ("cli", "view") else "agent"), account


def save(folder: Path, suffix: str, text: str) -> Path:
    """Write a new version of an authored file.

    :param folder: The authored folder, e.g. ``<group>/notes``.
    :param suffix: ``.md`` or ``.yaml``.
    :param text: The content.
    :return: The new file."""
    # the newest version counts, so a save must sort after it, also within the same second.
    latest = (newest(folder) or Path("")).stem
    path = folder / f"{new_version_id()}{suffix}"
    while path.exists() or path.stem <= latest:
        time.sleep(0.01)
        path = folder / f"{new_version_id()}{suffix}"
    write_created(path, text.encode())
    return path


def written(ctx: Context, kind: str, path: Path, lines: list[str]) -> dict[str, Any]:
    """Build the answer of a write.

    :param ctx: The operation context.
    :param kind: The operation.
    :param path: The new file.
    :param lines: What else to say.
    :return: The answer."""
    rel = path.relative_to(ctx.logdir).as_posix()
    return {
        "kind": kind,
        "lines": [f"wrote {rel}", *lines],
        "path": rel,
        "version": path.stem,
        "meta": {},
    }
