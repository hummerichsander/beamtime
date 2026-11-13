"""Group moves: ``_moves.jsonl`` in the log dir lists every group moved with ``beamtime mv``.

Files written before a move keep naming the old path (runs record proposal membership by group
path, notes name groups they complete or cite), and they are never rewritten. Readers map paths
through the moves instead: ``earlier`` lists a group's former paths, ``current`` follows an old path
to where it is now. A move with ``within`` applies only to paths named by files at or below that
group; paths typed by a user are never named in a file."""

import json
import time
from pathlib import Path
from typing import NamedTuple

from beamtime.format import constants as c
from beamtime.format.io import append_lines


class Move(NamedTuple):
    """One move: the old path, the new path and the group its scope is limited to, if any."""

    old: str
    new: str
    within: str | None = None


def record(logdir: Path, old: str, new: str, within: str | None = None) -> None:
    """Append a move.

    :param logdir: The log dir.
    :param old: The group's path before the move.
    :param new: Its path after.
    :param within: Limit the move to paths named by files at or below this group."""
    entry = {"schema": 1, "from": old, "to": new, "t": time.time()}
    if within is not None:
        entry["within"] = within
    append_lines(logdir / c.MOVES, [entry])


def read(logdir: Path) -> list[Move]:
    """Read the moves, oldest first.

    :param logdir: The log dir.
    :return: The moves, each scope followed to where its group is now; lines that can't be read
        are skipped."""
    path = logdir / c.MOVES
    if not path.is_file():
        return []
    out: list[Move] = []
    for line in path.read_text().splitlines():
        try:
            entry = json.loads(line)
            within = entry.get("within")
            out.append(
                Move(
                    entry["from"].strip("/"),
                    entry["to"].strip("/"),
                    None if within is None else within.strip("/"),
                )
            )
        except (ValueError, KeyError, AttributeError, TypeError):
            continue
    return [m._replace(within=moved_scope(m.within, out[i + 1 :])) for i, m in enumerate(out)]


def moved_scope(within: str | None, later: list[Move]) -> str | None:
    """Follow a move's scope through the moves after it.

    :param within: The scope as recorded, or ``None``.
    :param later: The moves recorded after it, oldest first.
    :return: The scope's path today; scoped moves rename no folder, so only unscoped ones count."""
    if within is None:
        return None
    for m in later:
        if m.within is None and (moved := under(within, m.old, m.new)) is not None:
            within = moved
    return within


def earlier(logdir: Path, rel: str, named_in: str | None = None) -> list[str]:
    """List the paths a group had before its moves (or its parents' moves), newest first.

    :param logdir: The log dir.
    :param rel: The group's current path.
    :param named_in: The group path of the file that names the path; ``None`` for user input.
    :return: Former paths, without ``rel`` itself."""
    out: list[str] = []
    for old, new, within in reversed(read(logdir)):
        if not applies(within, named_in):
            continue
        if (moved := under(rel, new, old)) is not None and moved not in out and moved != rel:
            out.append(moved)
            rel = moved
    return out


def current(logdir: Path, rel: str, named_in: str | None = None) -> str:
    """Follow a path through the moves since, to where that group is now.

    :param logdir: The log dir.
    :param rel: A path, possibly from before a move.
    :param named_in: The group path of the file that names the path; ``None`` for user input.
    :return: The path today (``rel`` if it never moved)."""
    for old, new, within in read(logdir):
        if not applies(within, named_in):
            continue
        if (moved := under(rel, old, new)) is not None:
            rel = moved
    return rel


def applies(within: str | None, named_in: str | None) -> bool:
    """Tell whether a move maps a path named in a file.

    :param within: The move's scope, or ``None`` for everywhere.
    :param named_in: The group path of the file that names the path; ``None`` for user input.
    :return: ``True`` if the move has no scope or ``named_in`` is at or below it."""
    return within is None or (named_in is not None and under(named_in, within, "") is not None)


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
