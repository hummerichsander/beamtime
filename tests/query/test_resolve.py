import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.format import moves
from beamtime.format.place import Place
from beamtime.index.index import Index
from beamtime.query import QueryError
from beamtime.query.resolve import Resolved, resolve
from beamtime.synth import generate


@pytest.fixture(scope="module")
def logdir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A synthetic log dir with a group that was moved.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The log dir."""
    out = tmp_path_factory.mktemp("resolve") / "beamtime"
    generate(out, seed=0, now=datetime.now(timezone.utc))
    (out / "scaling" / "moved").mkdir()
    moves.record(out, "scaling/old", "scaling/moved")
    return out


@pytest.fixture(scope="module")
def index(logdir: Path, tmp_path_factory: pytest.TempPathFactory) -> Index:
    """A caught-up index of the log dir.

    :param logdir: The log dir.
    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The index."""
    index = Index(logdir=logdir, cache=tmp_path_factory.mktemp("cache"))
    index.catch_up(".", budget_s=float("inf"))
    return index


@pytest.fixture(scope="module")
def run_id(logdir: Path) -> str:
    """A run's id.

    :param logdir: The log dir.
    :return: The id of the generator's baseline role."""
    return next(iter(json.loads((logdir / "_synth.json").read_text())["roles"].values()))


def name_run(index: Index, run_id: str, name: str) -> None:
    """Give an indexed run a name.

    :param index: The index.
    :param run_id: The run.
    :param name: The name."""
    index.store.db.execute("UPDATE runs SET name = ? WHERE id = ?", (name, run_id))


def test_group_and_root(index: Index) -> None:
    """A group resolves relative to the base; ``.`` is the log dir."""
    assert resolve(index, "scaling") == Resolved("scaling", None)
    assert resolve(index, ".") == Resolved(".", None)
    assert resolve(index, Place.parse("scaling/")) == Resolved("scaling", None)
    assert resolve(index, "..", base="scaling") == Resolved(".", None)


def test_run_by_id_and_path(index: Index, run_id: str) -> None:
    """A full run id resolves anywhere, also behind a group path."""
    path = index.run_path(run_id).relative_to(index.logdir).as_posix()
    assert resolve(index, run_id) == Resolved(path, run_id)
    assert resolve(index, f"somewhere/{run_id}") == Resolved(path, run_id)


def test_run_by_suffix(index: Index, run_id: str) -> None:
    """A unique id suffix names the run."""
    path = index.run_path(run_id).relative_to(index.logdir).as_posix()
    assert resolve(index, run_id[-8:]) == Resolved(path, run_id)


def test_short_suffix_is_a_group(index: Index, run_id: str) -> None:
    """A suffix under four characters is not a run, so a mistyped group never names one."""
    with pytest.raises(QueryError, match=f"no group '{run_id[-3:]}' below the log dir") as e:
        resolve(index, run_id[-3:])
    assert e.value.code == "not_found"


def test_run_by_name_and_ambiguous(index: Index, run_id: str) -> None:
    """A unique name names the run; a shared one is refused as invalid (code 2)."""
    others = [r[0] for r in index.store.db.execute("SELECT id FROM runs LIMIT 3")]
    name_run(index, run_id, "the-one")
    assert resolve(index, "the-one").run_id == run_id
    for other in others:
        name_run(index, other, "twin")
    with pytest.raises(QueryError, match="matches 3 runs; give the full run id") as e:
        resolve(index, "twin")
    assert e.value.code == "invalid"


def test_unknown_run(index: Index) -> None:
    """A full id that exists nowhere is not found."""
    with pytest.raises(QueryError, match="no run '20000101-000000-aaaaaaaa'") as e:
        resolve(index, "20000101-000000-aaaaaaaa")
    assert e.value.code == "not_found"


def test_group_wins_over_suffix(index: Index, logdir: Path, run_id: str) -> None:
    """A group of the same name as a run's id suffix is the group."""
    (logdir / run_id[-6:]).mkdir()
    try:
        assert resolve(index, run_id[-6:]) == Resolved(run_id[-6:], None)
    finally:
        (logdir / run_id[-6:]).rmdir()


def test_moved_group_is_followed(index: Index) -> None:
    """A path from before a move names the group where it is now."""
    assert resolve(index, "scaling/old") == Resolved("scaling/moved", None)


def test_unknown_group_lists_siblings_and_top_level(index: Index) -> None:
    """An unknown group suggests its siblings and lists the top-level groups."""
    with pytest.raises(QueryError) as e:
        resolve(index, "scalng")
    assert e.value.code == "not_found"
    assert "no group 'scalng' below the log dir. Did you mean 'scaling'?" in str(e.value)
    assert "Top-level groups: " in str(e.value) and "scaling" in str(e.value)


@pytest.mark.parametrize("target", ["scaling/notes", "view", "scaling/_hidden/x"])
def test_reserved_paths_are_refused(index: Index, target: str) -> None:
    """A path through authored or machine files is not a group."""
    with pytest.raises(QueryError, match="holds authored or machine files") as e:
        resolve(index, target)
    assert e.value.code == "not_found"


@pytest.mark.parametrize("target", ["../..", "scaling/../.."])
def test_escaping_paths_are_refused(index: Index, target: str) -> None:
    """A path leaving the log dir is invalid."""
    with pytest.raises(QueryError, match="leaves the log dir") as e:
        resolve(index, target)
    assert e.value.code == "invalid"


def test_unknown_source_lists_the_known_ones(index: Index) -> None:
    """A source nobody configured is refused with the configured ones named; ``@local`` is here."""
    with pytest.raises(QueryError, match=r"no source @nope \(remotes: @a, @b\)") as e:
        resolve(index, "@nope/scaling", sources=["b", "a"])
    assert e.value.code == "invalid"
    with pytest.raises(QueryError, match=r"\(remotes: none configured\)"):
        resolve(index, "@nope")
    assert resolve(index, "@local/scaling") == Resolved("scaling", None)
