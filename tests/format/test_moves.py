from pathlib import Path

from beamtime.format import moves


def test_unscoped_move_applies_everywhere(tmp_path: Path) -> None:
    """A move without ``within`` maps typed paths and paths named anywhere."""
    moves.record(tmp_path, "a", "b")
    assert moves.read(tmp_path) == [moves.Move("a", "b", None)]
    assert moves.current(tmp_path, "a/x") == "b/x"
    assert moves.current(tmp_path, "a/x", "other") == "b/x"
    assert moves.earlier(tmp_path, "b", "other") == ["a"]


def test_within_maps_only_files_below_it(tmp_path: Path) -> None:
    """A scoped move maps ``scaling`` for a file inside ``imported/x`` and for none outside."""
    moves.record(tmp_path, "scaling", "imported/x/scaling", within="imported/x")
    assert moves.read(tmp_path)[0].within == "imported/x"
    assert moves.current(tmp_path, "scaling", "imported/x/deep") == "imported/x/scaling"
    assert moves.current(tmp_path, "scaling", "scaling") == "scaling"
    assert moves.current(tmp_path, "scaling", "imported/y") == "scaling"
    assert moves.earlier(tmp_path, "imported/x/scaling", "imported/x/deep") == ["scaling"]
    assert moves.earlier(tmp_path, "imported/x/scaling", "elsewhere") == []


def test_within_is_inclusive(tmp_path: Path) -> None:
    """A file in the ``within`` group itself counts as below it."""
    moves.record(tmp_path, "scaling", "imported/x/scaling", within="imported/x")
    assert moves.current(tmp_path, "scaling", "imported/x") == "imported/x/scaling"


def test_typed_path_is_native(tmp_path: Path) -> None:
    """User input has no ``named_in``, so a scoped move never applies to it."""
    moves.record(tmp_path, "scaling", "imported/x/scaling", within="imported/x")
    assert moves.current(tmp_path, "scaling") == "scaling"
    assert moves.earlier(tmp_path, "imported/x/scaling") == []


def test_unreadable_lines_are_skipped(tmp_path: Path) -> None:
    """Damaged lines don't stop the readable ones."""
    moves.record(tmp_path, "a", "b")
    with (tmp_path / "_moves.jsonl").open("a") as f:
        f.write('not json\n{"from": "c"}\n{"from": "c", "to": "d", "within": 3}\n')
    assert moves.read(tmp_path) == [moves.Move("a", "b", None)]
