import math
from pathlib import Path

from beamtime.format.io import (
    append_lines,
    read_json,
    read_jsonl,
    write_created,
    write_replaced,
)


def test_replace_leaves_no_temp_file(tmp_path: Path) -> None:
    """A replaced file holds the new content and no temp file remains."""
    p = tmp_path / "_run.json"
    write_replaced(p, {"schema": 1, "a": 1})
    write_replaced(p, {"schema": 1, "a": 2}, sync=True)
    assert read_json(p) == {"schema": 1, "a": 2}
    assert [q.name for q in tmp_path.iterdir()] == ["_run.json"]


def test_created_makes_parents(tmp_path: Path) -> None:
    """Created files get their parent folders."""
    p = tmp_path / "_data" / "samples" / "3.png"
    write_created(p, b"png")
    assert p.read_bytes() == b"png"


def test_nonfinite_round_trip(tmp_path: Path) -> None:
    """NaN and Infinity survive a JSON Lines round trip."""
    p = tmp_path / "_metrics.jsonl"
    append_lines(p, [{"_step": 0, "x": math.nan}, {"_step": 1, "x": -math.inf}])
    rows = read_jsonl(p).rows
    assert math.isnan(rows[0]["x"]) and rows[1]["x"] == -math.inf


def test_partial_line_is_left_for_later(tmp_path: Path) -> None:
    """A line without newline is not read until it is complete."""
    p = tmp_path / "_metrics.jsonl"
    p.write_bytes(b'{"_step":0}\n{"_step":1')
    first = read_jsonl(p)
    assert first.rows == [{"_step": 0}] and first.end == 12
    with p.open("ab") as f:
        f.write(b"}\n")
    second = read_jsonl(p, first.end)
    assert second.rows == [{"_step": 1}] and second.end == p.stat().st_size


def test_corrupt_lines_are_counted(tmp_path: Path) -> None:
    """Complete lines that don't parse are skipped and counted."""
    p = tmp_path / "_events.jsonl"
    p.write_bytes(b'{"a":1}\n{"a":\n[1]\n{"a":2}\n')
    chunk = read_jsonl(p)
    assert chunk.rows == [{"a": 1}, {"a": 2}] and chunk.bad == 2


def test_empty_file(tmp_path: Path) -> None:
    """An empty file yields nothing and keeps the offset."""
    p = tmp_path / "_data.jsonl"
    p.write_bytes(b"")
    assert read_jsonl(p).rows == [] and read_jsonl(p).end == 0
