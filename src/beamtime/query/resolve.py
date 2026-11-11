"""Resolving a place to a group or one run: the one resolver behind ``from`` and run arguments."""

import posixpath
from collections.abc import Sequence
from dataclasses import dataclass

from beamtime.format.moves import current
from beamtime.format.place import Place
from beamtime.format.tree import is_reserved, iter_runs
from beamtime.index.index import Index
from beamtime.query.models import QueryError, closest

TOP_GROUPS = 12
MIN_SUFFIX = 4


@dataclass(frozen=True)
class Resolved:
    """A place on this machine: a group relative to the log dir, or one run."""

    path: str
    run_id: str | None


def resolve(
    index: Index,
    target: str | Place,
    *,
    base: str = ".",
    budget_s: float = 0.2,
    sources: Sequence[str] = (),
) -> Resolved:
    """Resolve a place to a group relative to the log dir, or to one run.

    A run is found by its id, else (when no group of that name exists) by a unique id suffix or
    its name.

    :param index: The index.
    :param target: The place: a group, a run, or a ``Place`` on this machine.
    :param base: The group relative paths start from (a view's group; ``.`` for CLI).
    :param budget_s: Seconds to catch up on new runs when a run is not indexed yet.
    :param sources: The configured remote sources, for the message about an unknown one.
    :return: The group or run path relative to the log dir, and the run id if one run was named."""
    place = Place.parse(target) if isinstance(target, str) else target
    if place.source is not None:
        known = ", ".join(f"@{n}" for n in sorted(sources)) or "none configured"
        raise QueryError(
            f"from {place.text!r}: no source @{place.source} (remotes: {known}); "
            "add it under remotes: in the settings"
        )

    if (run_id := place.run_id) is not None:
        if (path := _run_by_id(index, run_id, budget_s)) is None:
            raise QueryError(
                f"no run {run_id!r} below the log dir; `beamtime runs` lists them", code="not_found"
            )
        return Resolved(path, run_id)

    rel = posixpath.normpath(posixpath.join(base, place.path.lstrip("/") or "."))
    if rel == ".." or rel.startswith("../"):
        raise QueryError(f"from {place.text!r} leaves the log dir")
    if rel != "." and any(is_reserved(part) for part in rel.split("/")):
        raise QueryError(
            f"from {place.text!r}: {rel!r} holds authored or machine files, not runs; "
            "name the group above it",
            code="not_found",
        )

    if (
        not index.folder_path(rel).is_dir()
        and index.folder_path(moved := current(index.logdir, rel)).is_dir()
    ):
        # a path from before a group was moved names the group where it is now.
        rel = moved
    if index.folder_path(rel).is_dir():
        return Resolved(rel, None)

    word = place.path.lstrip("/")
    if "/" not in word and (hit := _run_by_suffix_or_name(index, word, budget_s)):
        return Resolved(*hit)

    parent = index.folder_path(posixpath.dirname(rel) or ".")
    options = [p.name for p in parent.iterdir() if p.is_dir()] if parent.is_dir() else []
    top = sorted(
        p.name
        for p in index.logdir.iterdir()
        if p.is_dir() and not p.name.startswith(".") and not is_reserved(p.name)
    )
    more = ", ..." if len(top) > TOP_GROUPS else ""
    raise QueryError(
        f"no group {rel!r} below the log dir."
        + closest(posixpath.basename(rel), options)
        + f" Top-level groups: {', '.join(top[:TOP_GROUPS])}{more}.",
        code="not_found",
    )


def _run_by_id(index: Index, run_id: str, budget_s: float) -> str | None:
    """Find a run by its full id, catching up and walking the tree if the index lacks it.

    :param index: The index.
    :param run_id: The run id.
    :param budget_s: Seconds to catch up for.
    :return: The run directory relative to the log dir, or ``None``."""
    if (path := index.run_path(run_id)) is None:
        index.catch_up(".", budget_s=budget_s)
        path = index.run_path(run_id)
    if path is None:
        path = next((p for p in iter_runs(index.logdir) if p.name == run_id), None)
    return None if path is None else path.relative_to(index.logdir).as_posix()


def _run_by_suffix_or_name(index: Index, word: str, budget_s: float) -> tuple[str, str] | None:
    """Find the one run whose id ends in ``word`` or whose name is ``word``.

    :param index: The index.
    :param word: The id suffix (at least ``MIN_SUFFIX`` characters) or run name.
    :param budget_s: Seconds to catch up for when nothing matches yet.
    :return: The run's path and id, or ``None``.
    :raises QueryError: If several runs match."""
    # a shorter suffix matches by chance, so a mistyped group would name a run; NULL matches none.
    args = (-len(word), word if len(word) >= MIN_SUFFIX else None, word)
    query = "SELECT path, id FROM runs WHERE substr(id, ?) = ? OR name = ?"
    hits = index.store.db.execute(query, args).fetchall()
    if not hits:
        index.catch_up(".", budget_s=budget_s)
        hits = index.store.db.execute(query, args).fetchall()
    if len(hits) > 1:
        raise QueryError(f"{word!r} matches {len(hits)} runs; give the full run id")
    return (hits[0][0], hits[0][1]) if hits else None
