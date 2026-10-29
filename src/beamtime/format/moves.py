"""Group moves: ``_moves.jsonl`` in the log dir lists every group moved with ``beamtime mv``.

Files written before a move keep naming the old path (runs record proposal membership by group
path, notes name groups they complete or cite), and they are never rewritten. Readers map paths
through the moves instead: ``earlier`` lists a group's former paths, ``current`` follows an old path
to where it is now."""

import json
import time
from pathlib import Path

from beamtime.format import constants as c
from beamtime.format.io import append_lines


def record(logdir: Path, old: str, new: str) -> None:
    """Append a move.

    :param logdir: The log dir.
    :param old: The group's path before the move.
    :param new: Its path after."""
    append_lines(logdir / c.MOVES, [{"schema": 1, "from": old, "to": new, "t": time.time()}])


def read(logdir: Path) -> list[tuple[str, str]]:
    """Read the moves, oldest first.

    :param logdir: The log dir.
    :return: ``(old, new)`` pairs; lines that can't be read are skipped."""
    path = logdir / c.MOVES
    if not path.is_file():
        return []
    out = []
    for line in path.read_text().splitlines():
        try:
            entry = json.loads(line)
            out.append((entry["from"].strip("/"), entry["to"].strip("/")))
        except (ValueError, KeyError, AttributeError):
            continue
    return out


def earlier(logdir: Path, rel: str) -> list[str]:
    """List the paths a group had before its moves (or its parents' moves), newest first.

    :param logdir: The log dir.
    :param rel: The group's current path.
    :return: Former paths, without ``rel`` itself."""
    out: list[str] = []
    for old, new in reversed(read(logdir)):
        if (moved := under(rel, new, old)) is not None and moved not in out and moved != rel:
            out.append(moved)
            rel = moved
    return out


def current(logdir: Path, rel: str) -> str:
    """Follow a path through the moves since, to where that group is now.

    :param logdir: The log dir.
    :param rel: A path, possibly from before a move.
    :return: The path today (``rel`` if it never moved)."""
    for old, new in read(logdir):
        if (moved := under(rel, old, new)) is not None:
            rel = moved
    return rel


def under(rel: str, prefix: str, replacement: str) -> str | None:
    """Replace a leading group path.

    :param rel: A path.
    :param prefix: The group path to replace.
    :param replacement: What it becomes.
    :return: The new path, or ``None`` if ``rel`` is not at or below ``prefix``."""
    if rel == prefix:
        return replacement
    if rel.startswith(f"{prefix}/"):
        return f"{replacement}{rel[len(prefix) :]}"
    return None
