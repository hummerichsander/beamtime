"""Notes and memory files written as they are: one observation note on the log dir per file."""

from dataclasses import dataclass, field
from pathlib import Path

from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.setup.importers import files

SNIFF = 8192


@dataclass(kw_only=True)
class NotesImported:
    """The notes written and the binary files skipped."""

    notes: list[str] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


def import_notes(ctx: Context, paths: list[Path]) -> NotesImported:
    """Write each text file at or below the paths as an ``observation`` note on the log dir.

    Notes go through the ``note add`` operation, so author and user are the local account.

    :param ctx: The operation context.
    :param paths: Files and folders.
    :return: The paths of the notes and the binary files skipped, in file order."""
    done = NotesImported()
    for path in paths:
        for f in sorted(files(path)):
            if (text := read_text(f)) is None:
                done.skipped.append(f)
                continue
            params = {
                "group": ".",
                "type": "observation",
                "description": describe(f, text),
                "body": text,
            }
            done.notes.append(call("note add", params, ctx)["path"])
    return done


def read_text(path: Path) -> str | None:
    """Read a file as text.

    :param path: The file.
    :return: The text, or ``None`` for a binary file."""
    data = path.read_bytes()
    if b"\0" in data[:SNIFF]:
        return None
    try:
        return data.decode()
    except UnicodeDecodeError:
        return None


def describe(path: Path, text: str) -> str:
    """Take the first heading of a Markdown file, or else the file name.

    :param path: The file.
    :param text: Its text.
    :return: The note's one-line description."""
    for line in text.splitlines():
        if line.startswith("#") and (heading := line.lstrip("#").strip()):
            return heading
    return path.name
