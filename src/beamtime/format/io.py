"""The write protocol (replaced, appended, created) and the matching readers."""

import json
import os
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def json_line(obj: Any) -> bytes:
    """Encode one JSON Lines record, NaN and Infinity as Python's JSON literals.

    :param obj: The record.
    :return: The encoded line including its newline."""
    return (json.dumps(obj, separators=(",", ":")) + "\n").encode()


def _replace(src: Path, dst: Path) -> None:
    """Rename ``src`` over ``dst``, retrying briefly while a reader blocks it.

    :param src: The temporary file.
    :param dst: The final path."""
    for delay in (0.01, 0.05, 0.1, 0.25, 0.5):
        try:
            os.replace(src, dst)
            return
        except PermissionError:
            # Windows refuses to replace a file another process has open.
            time.sleep(delay)
    os.replace(src, dst)


def write_bytes_replaced(path: Path, data: bytes, *, sync: bool = False) -> None:
    """Replace a whole file atomically: write ``._<name>.tmp``, then rename it.

    :param path: The file to replace.
    :param data: The new content.
    :param sync: Whether to fsync before renaming, as at the end of a run."""
    tmp = path.with_name(f"._{path.name}.tmp")
    with tmp.open("wb") as f:
        f.write(data)
        if sync:
            f.flush()
            os.fsync(f.fileno())
    _replace(tmp, path)


def write_replaced(path: Path, obj: Any, *, sync: bool = False) -> None:
    """Replace a JSON file atomically.

    :param path: The file to replace.
    :param obj: The JSON value.
    :param sync: Whether to fsync before renaming."""
    write_bytes_replaced(path, (json.dumps(obj, indent=1) + "\n").encode(), sync=sync)


def write_created(path: Path, data: bytes) -> None:
    """Create a new file under a temporary name, then rename it into place.

    :param path: The file's unique final path; its parent is created if needed.
    :param data: The content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    write_bytes_replaced(path, data)


def append_lines(path: Path, objs: Iterable[Any]) -> None:
    """Append records to a JSON Lines file, one ``write`` per line.

    :param path: The file.
    :param objs: The records."""
    with path.open("ab") as f:
        for obj in objs:
            f.write(json_line(obj))


def read_json(path: Path) -> Any:
    """Read a JSON file.

    :param path: The file.
    :return: The parsed value."""
    return json.loads(path.read_bytes())


@dataclass(kw_only=True, frozen=True)
class Chunk:
    """Records read from a JSON Lines file, and where to continue."""

    rows: list[dict[str, Any]] = field(default_factory=list)
    end: int = 0
    bad: int = 0


def read_jsonl(path: Path, offset: int = 0) -> Chunk:
    """Read complete records from a JSON Lines file, starting at a byte offset.

    A trailing line without newline is still being written and is left for the next
    read; complete lines that don't parse (a writer killed mid-line) are counted.

    :param path: The file.
    :param offset: The byte offset to start from, a previous ``Chunk.end``.
    :return: The records, the offset after the last complete line, and the bad count."""
    with path.open("rb") as f:
        f.seek(offset)
        data = f.read()
    if (cut := data.rfind(b"\n")) < 0:
        return Chunk(end=offset)
    rows, bad = [], 0
    for line in data[:cut].split(b"\n"):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            bad += 1
    return Chunk(rows=rows, end=offset + cut + 1, bad=bad)
