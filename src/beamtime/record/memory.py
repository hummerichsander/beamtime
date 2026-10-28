"""Memory: the compressed summary of a folder's record, and how stale it is."""

from datetime import datetime, timezone
from typing import Any

from beamtime.format import constants as c
from beamtime.format.authored import newest, read_markdown_doc
from beamtime.format.schema import SchemaError
from beamtime.index.store import in_scope
from beamtime.record.proposals import Target

# about 1.5k tokens at roughly four characters per token.
BUDGET_CHARS = 6000


def to_time(value: Any) -> float | None:
    """Read ``covers_until``, which YAML may already have parsed into a datetime.

    :param value: The field's value.
    :return: Unix time, or ``None`` if missing or unreadable."""
    if isinstance(value, datetime):
        t = value
    elif isinstance(value, str):
        try:
            t = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return (t if t.tzinfo else t.replace(tzinfo=timezone.utc)).timestamp()


def iso(t: float) -> str:
    """Format a unix time like ``2026-10-25T14:00:00Z``.

    :param t: The time.
    :return: The text."""
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def chain(target: Target) -> list[dict[str, Any]]:
    """Read the memory of a folder and of every folder above it, root first.

    :param target: The folder or run.
    :return: Per folder with a memory: its version, fields, body and staleness."""
    parts = [] if target.rel in (".", "") else target.rel.split("/")
    out = []
    for i in range(len(parts) + 1):
        rel = "/".join(parts[:i]) or "."
        if (path := newest(target.index.folder_path(rel) / c.MEMORY)) is None:
            continue
        try:
            doc = read_markdown_doc(path, kind="memory")
        except (SchemaError, ValueError, OSError) as e:
            out.append({"folder": rel, "version": path.stem, "problem": str(e)})
            continue
        covers = to_time(doc.meta.get("covers_until"))
        out.append(
            {
                "folder": rel,
                "version": doc.id,
                "covers_until": iso(covers) if covers is not None else None,
                "author": doc.meta.get("author"),
                "notes_since": notes_since(target, rel, covers),
                "chars": len(doc.body),
                "body": doc.body,
            }
        )
    return out


def notes_since(target: Target, rel: str, since: float | None) -> int:
    """Count the notes at or below a folder that are newer than a time.

    :param target: Any target, for its index.
    :param rel: The folder.
    :param since: The time; ``None`` counts every note.
    :return: The count."""
    cond, params = in_scope("folder", rel)
    return target.index.store.db.execute(
        f"SELECT count(*) FROM notes WHERE {cond} AND t > ?", [*params, since or 0]
    ).fetchone()[0]


def newest_note_time(target: Target) -> float | None:
    """Find the time of the newest note at or below a folder.

    :param target: The folder.
    :return: Unix time, or ``None`` without notes."""
    cond, params = in_scope("folder", target.rel)
    return target.index.store.db.execute(
        f"SELECT max(t) FROM notes WHERE {cond}", params
    ).fetchone()[0]
