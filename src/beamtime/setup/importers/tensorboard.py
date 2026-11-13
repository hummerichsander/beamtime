"""TensorBoard event files: TFRecord framing and the ``Event`` protobuf decoded in pure Python."""

import os
import struct
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml

from beamtime.setup.importers import Found, Imported, files, label
from beamtime.setup.importers.mlflow import metric_rows

EVENT_PREFIX = "events.out.tfevents."
DT_FLOAT, DT_DOUBLE = 1, 2
# Summary.Value fields that hold a non-scalar summary of the old style.
OLD_STYLE = {3: "histograms", 4: "images", 5: "histograms", 6: "audio"}


def detect(path: Path) -> Found | None:
    """Count the folders with event files at or below a path.

    :param path: A file or a folder.
    :return: The runs found, or ``None``."""
    n = len(run_folders(path))
    return Found(kind="tensorboard", path=path, n=n, label=label("tensorboard", n)) if n else None


def runs(path: Path) -> Iterator[Imported]:
    """Read every folder of event files at or below a path as one run.

    :param path: A file or a folder.
    :return: The runs, in folder order; the group is the folder's path below ``path``."""
    root = path if path.is_dir() else path.parent
    for folder in run_folders(path):
        yield read_folder(folder, root)


def run_folders(path: Path) -> list[Path]:
    """List the folders that hold event files, in name order.

    :param path: A file or a folder.
    :return: The folders."""
    return sorted({f.parent for f in files(path) if f.name.startswith(EVENT_PREFIX)})


def read_folder(folder: Path, root: Path) -> Imported:
    """Read the event files of one folder, merged by step, and the ``hparams.yaml`` beside them.

    :param folder: The run's folder, e.g. Lightning's ``version_0``.
    :param root: The path the search started at.
    :return: The run, with the kinds of non-scalar summaries it left out in ``skipped``."""
    points: list[tuple[str, float, int, float]] = []
    skipped: dict[str, set[str]] = defaultdict(set)
    times: list[float] = []
    for f in sorted(folder.glob(f"{EVENT_PREFIX}*")):
        for record in tfrecords(f):
            try:
                read_event(record, points, skipped, times)
            except (ValueError, struct.error):
                continue
    mtime = max((f.stat().st_mtime for f in folder.glob(f"{EVENT_PREFIX}*")), default=0.0)
    created = min(times, default=mtime)
    rel = folder.relative_to(root).as_posix()
    return Imported(
        name=folder.name,
        group="" if rel == "." else rel,
        created_at=created,
        ended_at=max(times, default=mtime),
        config=read_hparams(folder / "hparams.yaml"),
        rows=metric_rows(points, created),
        source_id=rel,
        skipped={kind: len(tags) for kind, tags in sorted(skipped.items())},
    )


def read_hparams(path: Path) -> dict[str, Any]:
    """Read Lightning's ``hparams.yaml``.

    :param path: The file.
    :return: Its mapping; empty when the file is missing, unreadable or not a mapping."""
    try:
        config = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return {str(k): v for k, v in config.items()} if isinstance(config, dict) else {}


def tfrecords(path: Path) -> Iterator[bytes]:
    """Read the records of an event file; a truncated last record ends the stream quietly.

    :param path: The event file.
    :return: The records' payloads; the checksums are not checked."""
    with path.open("rb") as f:
        total = os.fstat(f.fileno()).st_size
        while len(head := f.read(12)) == 12:
            (size,) = struct.unpack("<Q", head[:8])
            if size > total:
                return
            data = f.read(size)
            if len(data) < size or len(f.read(4)) < 4:
                return
            yield data


def read_event(
    record: bytes,
    points: list[tuple[str, float, int, float]],
    skipped: dict[str, set[str]],
    times: list[float],
) -> None:
    """Decode one ``Event`` and add its scalars to ``points``.

    :param record: The event's bytes.
    :param points: Receives scalars as tag, value, step and wall time.
    :param skipped: Receives the tags of non-scalar summaries by kind.
    :param times: Receives the event's wall time."""
    wall, step, summary = 0.0, 0, b""
    for number, _, value in fields(record):
        match number:
            case 1:
                (wall,) = struct.unpack("<d", value)
            case 2:
                step = value - (1 << 64) if value >= 1 << 63 else value
            case 5:
                summary = value
    if wall:
        times.append(wall)
    for number, _, value in fields(summary):
        if number == 1:
            read_value(value, step, wall, points, skipped)


def read_value(
    buf: bytes,
    step: int,
    wall: float,
    points: list[tuple[str, float, int, float]],
    skipped: dict[str, set[str]],
) -> None:
    """Decode one ``Summary.Value``: a scalar becomes a point, anything else is counted.

    :param buf: The value's bytes.
    :param step: The event's step.
    :param wall: The event's wall time.
    :param points: Receives scalars.
    :param skipped: Receives the tags of other summaries by kind."""
    tag, scalar, kind = "", None, "tensors"
    for number, _, value in fields(buf):
        match number:
            case 1:
                tag = value.decode("utf-8", errors="replace")
            case 2:
                (scalar,) = struct.unpack("<f", value)
            case 8:
                scalar = scalar_tensor(value)
            case 9:
                kind = plugin_name(value) or kind
            case n if n in OLD_STYLE:
                kind = OLD_STYLE[n]
    if scalar is not None:
        points.append((tag, scalar, step, wall))
    else:
        skipped[kind].add(tag)


def plugin_name(metadata: bytes) -> str | None:
    """Read the plugin name of a ``SummaryMetadata`` (``images``, ``histograms``, ``text``, ...).

    :param metadata: The message's bytes.
    :return: The name, or ``None``."""
    for number, _, data in fields(metadata):
        if number == 1:
            for n, _, name in fields(data):
                if n == 1:
                    return name.decode("utf-8", errors="replace")
    return None


def scalar_tensor(buf: bytes) -> float | None:
    """Read a ``TensorProto`` that holds one float32 or float64.

    :param buf: The message's bytes.
    :return: The value, or ``None`` for any other tensor."""
    dtype, ndim, content, values = 0, 0, b"", b""
    for number, _, value in fields(buf):
        match number:
            case 1:
                dtype = value
            case 2:
                ndim = sum(1 for n, _, _ in fields(value) if n == 2)
            case 4:
                content = value
            case 5 | 6:
                values = value
    if dtype not in (DT_FLOAT, DT_DOUBLE) or ndim:
        return None
    width, code = (4, "<f") if dtype == DT_FLOAT else (8, "<d")
    # a zero is omitted from a proto3 message, so an empty tensor is 0.0.
    raw = (content or values)[:width]
    return struct.unpack(code, raw)[0] if len(raw) == width else 0.0


def fields(buf: bytes) -> Iterator[tuple[int, int, Any]]:
    """Walk the fields of a protobuf message.

    :param buf: The message's bytes.
    :return: Field number, wire type and value: an ``int`` for a varint, ``bytes`` otherwise.
    :raises ValueError: On a truncated or unknown field."""
    i, n = 0, len(buf)
    while i < n:
        key, i = varint(buf, i)
        number, wire = key >> 3, key & 7
        match wire:
            case 0:
                value, i = varint(buf, i)
            case 1:
                value, i = buf[i : i + 8], i + 8
            case 2:
                size, i = varint(buf, i)
                value, i = buf[i : i + size], i + size
            case 5:
                value, i = buf[i : i + 4], i + 4
            case _:
                raise ValueError(f"unknown wire type {wire}")
        if i > n:
            raise ValueError("truncated field")
        yield number, wire, value


def varint(buf: bytes, i: int) -> tuple[int, int]:
    """Read a base-128 varint.

    :param buf: The bytes.
    :param i: The offset of its first byte.
    :return: The value and the offset after it.
    :raises ValueError: When the buffer ends inside the varint."""
    value = shift = 0
    while i < len(buf):
        byte = buf[i]
        i += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, i
        shift += 7
    raise ValueError("truncated varint")
