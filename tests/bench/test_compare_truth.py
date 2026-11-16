"""Tests of the expected answers in ``bench/agents/compare/truth.py``; no agent runs."""

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from beamtime.query import run as query

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import formats  # noqa: E402
import truth  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
SEEDS = (7, 8, 9)


class Made:
    """One seed's log dir, its plain-files export and the expected values."""

    def __init__(self, root: Path, seed: int) -> None:
        """Generate, export and compute.

        :param root: An empty folder.
        :param seed: The data seed."""
        self.roles = data.make_logdir(root, seed=seed, now=NOW).roles
        self.logdir = root / "beamtime"
        formats.export_files(self.logdir, root)
        self.files = root
        self.truth = truth.compute(root, self.logdir)


@pytest.fixture(scope="module", params=SEEDS)
def made(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Made:
    """A log dir per seed with its export and truth.

    :param request: The pytest request holding the seed.
    :param tmp_path_factory: Makes the folder.
    :return: The generated seed."""
    return Made(tmp_path_factory.mktemp(f"seed{request.param}"), request.param)


@pytest.fixture(scope="module")
def seed7(made_seeds: dict[int, Made]) -> Made:
    """The seed 7 case.

    :param made_seeds: All seeds.
    :return: Seed 7."""
    return made_seeds[7]


@pytest.fixture(scope="module")
def made_seeds(tmp_path_factory: pytest.TempPathFactory) -> dict[int, Made]:
    """All three seeds at once.

    :param tmp_path_factory: Makes the folders.
    :return: The seeds mapped to their case."""
    return {s: Made(tmp_path_factory.mktemp(f"all{s}"), s) for s in SEEDS}


def test_every_task_has_truth(made: Made) -> None:
    """Every task id of the plan has an entry."""
    assert set(made.truth) == {
        "best-config",
        "failures",
        "sweep-summary",
        "check-prediction",
        "chart",
        "find-runs",
        "fastest",
        "table",
    }


def test_planted_effects(made: Made) -> None:
    """The planted winners hold on every seed."""
    t = made.truth
    assert t["best-config"]["best_lr"] == 3e-4
    assert t["best-config"]["runner_up_lr"] == 1e-3
    assert t["sweep-summary"]["best_arm"] == "large"
    assert t["check-prediction"]["verdict"] == "confirmed"
    assert t["fastest"]["lr"] == 3e-3


def test_failing_runs_are_the_diverging_and_killed_roles(made: Made) -> None:
    """The sweep's failures are the two planted ones, told apart by their output."""
    diverging = made.roles["diverging"].split("/")[-1]
    killed = made.roles["killed"].split("/")[-1]

    assert made.truth["failures"]["causes"] == {diverging: "diverged", killed: "killed"}
    assert made.truth["failures"]["ids"] == sorted([diverging, killed])


def test_significance_pinned(made_seeds: dict[int, Made]) -> None:
    """Seeds 7 and 8 leave the lead of 3e-4 open, seed 9 settles it (Finding 3)."""
    first = made_seeds[7].truth["best-config"]
    assert first["difference"] == pytest.approx(0.0079, abs=5e-5)
    assert first["ci"] == pytest.approx([-0.0002, 0.0160], abs=5e-5)
    assert made_seeds[8].truth["best-config"]["significant"] is False
    last = made_seeds[9].truth["best-config"]
    assert last["difference"] == pytest.approx(0.0066, abs=5e-5)
    assert last["ci"] == pytest.approx([0.0011, 0.0122], abs=5e-5)
    assert last["significant"] is True
    assert first["significant"] is False


def test_completed_only(made: Made) -> None:
    """3e-4 stays best because its killed run is left out; counting it flips the winner."""
    runs = truth.load_runs(made.files, made.logdir)
    with_killed: dict[Any, list[float]] = {}
    for r in truth.in_group(runs, truth.SWEEP):
        if (v := r.final("val/acc")) is not None and r.id != made.roles["diverging"].split("/")[-1]:
            with_killed.setdefault(r.config["lr"], []).append(v)
    means = {lr: sum(v) / len(v) for lr, v in with_killed.items()}

    assert made.truth["best-config"]["best_lr"] == 3e-4
    assert max(means, key=means.__getitem__) == 1e-3
    assert made.roles["realistic_killed"].split("/")[-1] in made.truth["sweep-summary"]["exclude"]


def test_final_is_last_logged_value(made: Made) -> None:
    """The final value is the last non-empty cell, not the cell of the last row."""
    runs = truth.load_runs(made.files, made.logdir)
    sweep = truth.in_group(runs, truth.SWEEP)
    last_row_empty = 0
    for r in sweep:
        with (made.files / "runs" / r.group / r.id / "metrics.csv").open() as f:
            rows = list(csv.DictReader(f))
        logged = [row["val/acc"] for row in rows if row["val/acc"] != ""]
        if rows[-1]["val/acc"] == "":
            last_row_empty += 1
        assert r.final("val/acc") == (float(logged[-1]) if logged else None)

    assert last_row_empty > 0


def test_matches_beamtime_query(seed7: Made) -> None:
    """Per-lr means over finished runs equal what Beamtime's own query path reports."""
    answer = query(
        {
            "runs": {
                "from": truth.SWEEP,
                "select": ["config.lr", "metric.val/acc.last", "run.status"],
                "limit": 100,
            }
        },
        logdir=seed7.logdir,
        now=NOW.timestamp(),
    )
    finals: dict[float, list[float]] = {}
    for _, lr, last, status in answer["rows"]:
        if status == "finished":
            finals.setdefault(lr, []).append(last)

    assert len(answer["rows"]) == 17
    means = seed7.truth["best-config"]["means"]
    assert set(means) == {str(lr) for lr in finals}
    for lr, values in finals.items():
        assert means[str(lr)] == pytest.approx(sum(values) / len(values), rel=1e-9)


def test_unfinished_runs_are_not_told_apart(made: Made) -> None:
    """Running, lost and killed runs all count as not finished; no truth value names a status."""
    runs = truth.load_runs(made.files, made.logdir)
    by_id = {r.id: r for r in runs}

    for role in ("lost", "running", "killed", "diverging", "realistic_killed"):
        assert by_id[made.roles[role].split("/")[-1]].finished is False
    assert by_id[made.roles["resumed"].split("/")[-1]].finished is True
    rows = made.truth["table"]["rows"]
    assert {type(row["finished"]) for row in rows} == {bool}
    assert all("status" not in row for row in rows)


def test_table_and_chart(made: Made) -> None:
    """The table has one row per sweep run; the chart one point per finished run."""
    rows = made.truth["table"]["rows"]
    points = made.truth["chart"]["points"]

    assert len(rows) == 17
    assert len(points) == sum(row["finished"] for row in rows) == 15
    assert [p["id"] for p in points] == [
        row["id"] for row in sorted(rows, key=lambda x: (x["lr"], x["id"])) if row["finished"]
    ]


def test_find_runs_counts_every_status(made: Made) -> None:
    """The threshold applies to the last val/acc of any run in the project."""
    ids = set(made.truth["find-runs"]["ids"])
    finals = {r.id: r.final("val/acc") for r in truth.load_runs(made.files, made.logdir)}

    assert ids == {i for i, v in finals.items() if v is not None and v >= 0.925}
    assert ids
