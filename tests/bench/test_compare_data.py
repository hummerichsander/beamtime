"""Tests of the benchmark's log dirs in ``bench/agents/compare/data.py``; no agent runs."""

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.format.tree import iter_runs
from beamtime.query import run as query

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
SEEDS = (7, 8, 9)


@pytest.fixture(scope="module", params=SEEDS)
def made(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, int]:
    """A stripped log dir per seed.

    :param request: The pytest request holding the seed.
    :param tmp_path_factory: Makes the folder.
    :return: The log dir and its seed."""
    dest = tmp_path_factory.mktemp(f"seed{request.param}")
    data.make_logdir(dest, seed=request.param, now=NOW)
    return dest / "beamtime", request.param


def test_shape(made: tuple[Path, int]) -> None:
    """Every seed has 61 runs in six groups, no manifest, no record folders, no proposals."""
    logdir, _ = made
    runs = list(iter_runs(logdir))

    assert len(runs) == 61
    assert len({r.parent.relative_to(logdir) for r in runs}) == 6
    assert not (logdir / "_synth.json").exists()
    for name in data.RECORD:
        assert not list(logdir.rglob(name))
    for r in runs:
        assert '"proposals": {}' in (r / "_run.json").read_text(encoding="utf-8")
        assert '"proposal_hashes": {}' in (r / "_run.json").read_text(encoding="utf-8")


def test_no_answers_left(made: tuple[Path, int]) -> None:
    """No file of the tree holds the text of a planted conclusion."""
    logdir, _ = made
    for path in logdir.rglob("*"):
        if path.is_file():
            text = path.read_text(errors="replace", encoding="utf-8")
            for needle in ("3e-4 gives", "verdict", "unigram beats"):
                assert needle not in text, f"{needle!r} in {path}"


def test_manifest_stays_in_memory(tmp_path: Path) -> None:
    """The returned manifest names the roles, and nothing of it is on disk."""
    manifest = data.make_logdir(tmp_path, seed=7, now=NOW)

    assert manifest.roles
    assert [p.name for p in tmp_path.iterdir()] == ["beamtime"]


def test_heartbeats_survive(tmp_path: Path) -> None:
    """The lost run keeps its old heartbeat, so it still reads as lost."""
    manifest = data.make_logdir(tmp_path, seed=7, now=NOW)
    logdir = tmp_path / "beamtime"
    lost = next(r for r in iter_runs(logdir) if r.name == manifest.roles["lost"].split("/")[-1])
    age = NOW.timestamp() - (lost / "_run.json").stat().st_mtime

    assert age >= 3600.0
    answer = query(
        {"runs": {"from": ".", "where": {"run.status": "lost"}, "select": ["run.id"]}},
        logdir=logdir,
        now=NOW.timestamp(),
    )

    assert [row[0] for row in answer["rows"]] == [lost.name]


def test_index_reads_stripped_logdir(made: tuple[Path, int]) -> None:
    """The index and the query path read the stripped log dir without errors."""
    logdir, _ = made
    answer = query({"runs": {"from": ".", "select": ["run.id"], "limit": 100}}, logdir=logdir)

    assert len(answer["rows"]) == 61


def test_deterministic_metrics(tmp_path: Path) -> None:
    """Two calls with the same seed give byte-identical metrics."""
    for name in ("a", "b"):
        data.make_logdir(tmp_path / name, seed=7, now=NOW)
    a, b = (tmp_path / n / "beamtime" for n in "ab")

    files = sorted(p.relative_to(a) for p in a.rglob("_metrics.jsonl"))
    assert len(files) == 61
    for rel in files:
        assert (a / rel).read_bytes() == (b / rel).read_bytes()
