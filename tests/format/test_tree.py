from pathlib import Path

from beamtime.format.constants import key_to_path, output_names
from beamtime.format.tree import is_reserved, is_run, iter_runs


def test_reserved_names() -> None:
    """Authored folders, underscore and dot names are never groups."""
    for name in ("proposal", "notes", "view", "memory", "blocks", "_trash", ".git"):
        assert is_reserved(name)
    assert not is_reserved("artifacts") and is_reserved("artifacts", in_run=True)
    assert not is_reserved("lr-sweep")


def test_iter_runs_skips_reserved(golden: Path) -> None:
    """Runs are found below groups, never in the trash or hidden folders."""
    runs = [p.name for p in iter_runs(golden)]
    assert runs == [
        "20261024-101532-k3m9xq2a",
        "20261024-111500-r3s4m5d6",
        "20261024-121500-f4a1ed00",
        "20261025-100000-h4shc0de",
    ]


def test_iter_runs_on_a_run(golden: Path) -> None:
    """A run is its own only run."""
    run = next(iter_runs(golden))
    assert is_run(run) and list(iter_runs(run)) == [run]
    assert list(iter_runs(golden / "missing")) == []


def test_paths() -> None:
    """Keys map to paths and ranks to output files."""
    assert key_to_path("grads/layer3") == "grads__layer3"
    assert output_names(0)[0] == "_output.log"
    assert output_names(3) == (
        "_output.rank3.log",
        "_output.rank3.tail.log",
        "_output.rank3.tail.prev.log",
    )
