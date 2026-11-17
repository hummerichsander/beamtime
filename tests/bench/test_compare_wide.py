"""Tests of the wide log dir in ``bench/agents/compare/wide.py``; no agent runs."""

import json
import math
import statistics
import sys
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from typing import Any

import pytest

from beamtime.format.tree import iter_runs
from beamtime.synth.generate import Manifest

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import wide  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
SEEDS = (7, 8, 9)
LAST = wide.SCALE.steps - 1


@cache
def rows(run: Path) -> list[dict[str, Any]]:
    """Read a run's metric records.

    :param run: The run folder.
    :return: One dict per line of ``_metrics.jsonl``."""
    return [json.loads(line) for line in (run / "_metrics.jsonl").read_text().splitlines()]


def status(run: Path) -> str:
    """Read a run's status.

    :param run: The run folder.
    :return: The status of its card."""
    return json.loads((run / "_run.json").read_text())["status"]


def values(run: Path, key: str) -> list[tuple[int, float]]:
    """Give the logged values of a metric.

    :param run: The run folder.
    :param key: The metric key.
    :return: ``(step, value)`` for every record that holds the key."""
    return [(r["_step"], r[key]) for r in rows(run) if key in r]


def last_val(run: Path) -> float:
    """Give the last logged validation loss.

    :param run: The run folder.
    :return: The value."""
    return values(run, "val/loss")[-1][1]


def group_runs(logdir: Path, group: str) -> list[Path]:
    """List the runs of a group.

    :param logdir: The log dir.
    :param group: The group path.
    :return: The run folders, sorted."""
    return sorted(iter_runs(logdir / group))


def ratio_to_running_min(run: Path) -> list[tuple[int, float]]:
    """Divide each finite train loss by the smallest one before it, itself included.

    :param run: The run folder.
    :return: ``(step, ratio)``; a NaN or infinite loss gives infinity."""
    out, low = [], math.inf
    for step, value in values(run, "train/loss"):
        if math.isfinite(value):
            low = min(low, value)
            out.append((step, value / low))
        else:
            out.append((step, math.inf))
    return out


def divergence_step(run: Path) -> int | None:
    """Find the first step whose train loss is 10 times its running minimum, or not finite.

    :param run: The run folder.
    :return: The step, or ``None`` when there is none."""
    return next((s for s, r in ratio_to_running_min(run) if r > 10), None)


@pytest.fixture(scope="module", params=SEEDS)
def made(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> tuple[Path, Manifest, int]:
    """A wide log dir per seed.

    :param request: The pytest request holding the seed.
    :param tmp_path_factory: Makes the folder.
    :return: The log dir, its manifest and its seed."""
    dest = tmp_path_factory.mktemp(f"seed{request.param}")
    manifest = data.DATASETS["wide"](dest, seed=request.param, now=NOW)
    return dest / "beamtime", manifest, request.param


@pytest.fixture
def sweep_runs(made: tuple[Path, Manifest, int]) -> list[Path]:
    """The 300 sweep runs.

    :param made: The log dir.
    :return: The run folders of ``sweeps/s01`` to ``s20``."""
    logdir, _, _ = made
    return [r for g in range(1, 21) for r in group_runs(logdir, f"sweeps/s{g:02d}")]


def finished_finals(runs: list[Path]) -> list[tuple[float, Path]]:
    """Rank the finished runs by their last validation loss.

    :param runs: Sweep runs.
    :return: ``(final, run)`` ascending."""
    return sorted((last_val(r), r) for r in runs if status(r) == "finished")


def test_shape(made: tuple[Path, Manifest, int], sweep_runs: list[Path]) -> None:
    """300 runs in 20 groups of 15, 8 in each long group, nothing else, no manifest file."""
    logdir, manifest, _ = made

    assert len(sweep_runs) == 300
    for g in range(1, 21):
        assert len(group_runs(logdir, f"sweeps/s{g:02d}")) == 15
    assert len(group_runs(logdir, "long/stability")) == 8
    assert len(group_runs(logdir, "long/schedules")) == 8
    assert len(list(iter_runs(logdir))) == 316 == manifest.runs
    assert not (logdir / "_synth.json").exists()


def test_sweep_logging(sweep_runs: list[Path]) -> None:
    """Sweep runs log train/loss every 10 steps and val/loss every 50 steps and at the last step."""
    for run in sweep_runs[::7]:
        assert {k for r in rows(run) for k in r} == {"_step", "_t", "train/loss", "val/loss"}
        assert all(s % 10 == 0 for s, _ in values(run, "train/loss"))
        assert all(s % 50 == 0 or s == LAST for s, _ in values(run, "val/loss"))


def test_sweep_endings(sweep_runs: list[Path]) -> None:
    """24 runs fail with an error line between 30 % and 90 % of the steps, 6 are killed."""
    failed = [r for r in sweep_runs if status(r) == "failed"]
    killed = [r for r in sweep_runs if status(r) == "killed"]

    assert (len(failed), len(killed)) == (wide.FAILED, wide.KILLED)
    for run in failed + killed:
        assert 0.3 * 1000 - 50 <= rows(run)[-1]["_step"] <= 0.9 * 1000
    for run in failed:
        assert any(e in (run / "_output.log").read_text() for e in wide.ERRORS)


def test_sweep_recipe(sweep_runs: list[Path]) -> None:
    """The finished runs' final val/loss is the recipe plus noise of sd 0.02."""
    residuals = [
        last_val(r) - wide.expected_loss(json.loads((r / "_config.json").read_text()))
        for r in sweep_runs
        if status(r) == "finished"
    ]

    assert 0.012 < statistics.pstdev(residuals) < 0.03
    assert abs(statistics.fmean(residuals)) < 0.01
    assert max(abs(x) for x in residuals) < 0.1


def test_leaderboard_gap(sweep_runs: list[Path]) -> None:
    """The five best finished runs are 0.002 apart from each other and from the sixth."""
    finals = [f for f, _ in finished_finals(sweep_runs)]

    assert all(b - a >= wide.LEADER_GAP - 1e-6 for a, b in zip(finals[:6], finals[1:6]))
    assert finals[5] - finals[4] >= 1e-3


def test_leaders_in_manifest(made: tuple[Path, Manifest, int], sweep_runs: list[Path]) -> None:
    """The manifest names the five best finished runs in order."""
    _, manifest, _ = made

    ranked = [r.name for _, r in finished_finals(sweep_runs)[:5]]
    assert manifest.roles["leaders"].split(",") == ranked


def test_traps(made: tuple[Path, Manifest, int], sweep_runs: list[Path]) -> None:
    """Exactly three failed or killed runs last logged a val/loss below the fifth best finished."""
    _, manifest, _ = made
    fifth = finished_finals(sweep_runs)[4][0]

    below = sorted(r.name for r in sweep_runs if status(r) != "finished" and last_val(r) < fifth)
    assert below == sorted(manifest.roles["traps"].split(","))
    assert len(below) == 3


def test_stability_endings(made: tuple[Path, Manifest, int]) -> None:
    """Three runs fail at distinct divergence steps; five finish."""
    logdir, manifest, _ = made
    runs = group_runs(logdir, "long/stability")
    failed = [r for r in runs if status(r) == "failed"]

    assert len(failed) == wide.DIVERGENCES
    assert sum(status(r) == "finished" for r in runs) == 5
    steps = [divergence_step(r) for r in failed]
    assert None not in steps and len(set(steps)) == 3
    assert all(20_000 <= s <= 82_000 for s in steps)
    assert manifest.roles["diverged"].split(",") == [r.name for _, r in sorted(zip(steps, failed))]
    for run in failed:
        train = [v for _, v in values(run, "train/loss")]
        assert math.isnan(train[-300]) and math.isinf(train[-1]) and not math.isnan(train[-1])
        assert all(math.isfinite(v) for v in train[:-300])


def test_long_logging(made: tuple[Path, Manifest, int]) -> None:
    """Finished long runs log train/loss at every step and val/loss every 500 steps and at the end."""
    logdir, _, _ = made
    for group in ("long/stability", "long/schedules"):
        for run in group_runs(logdir, group):
            assert {k for r in rows(run) for k in r} == {"_step", "_t", "train/loss", "val/loss"}
            if status(run) == "finished":
                assert len(values(run, "train/loss")) == wide.LONG_STEPS
                vals = [s for s, _ in values(run, "val/loss")]
                assert vals == [*range(0, wide.LONG_STEPS, 500), wide.LONG_STEPS - 1]


def test_spike_stays_below_bar(made: tuple[Path, Manifest, int]) -> None:
    """One run spikes to about six times its running minimum for 200 steps and never to ten; the
    other finished runs stay close to it."""
    logdir, manifest, _ = made
    spike = logdir / "long/stability" / manifest.roles["spike"]

    peak = max(r for _, r in ratio_to_running_min(spike))
    assert 5.0 < peak < 8.0
    above = [s for s, r in ratio_to_running_min(spike) if r > 2]
    assert 100 <= len(above) <= 200 and above[-1] - above[0] < 200
    for run in group_runs(logdir, "long/stability"):
        if status(run) == "finished" and run != spike:
            assert max(r for _, r in ratio_to_running_min(run)) < 1.5


def test_checkpoint_unique(made: tuple[Path, Manifest, int]) -> None:
    """Each schedules run has one evaluation step of lowest val/loss, a different one per run."""
    logdir, _, _ = made
    best = []
    for run in group_runs(logdir, "long/schedules"):
        ranked = sorted((v, s) for s, v in values(run, "val/loss"))
        assert ranked[1][0] - ranked[0][0] >= 1e-3
        assert 30_000 <= ranked[0][1] < 70_000
        best.append(ranked[0][1])

    assert len(set(best)) == 8


def test_overfit(made: tuple[Path, Manifest, int]) -> None:
    """The validation loss of a schedules run ends higher than its minimum while training goes on."""
    logdir, _, _ = made
    for run in group_runs(logdir, "long/schedules"):
        assert last_val(run) > min(v for _, v in values(run, "val/loss")) + 0.05
        train = [v for _, v in values(run, "train/loss")]
        assert statistics.fmean(train[-1000:]) < statistics.fmean(train[:1000])


def test_deterministic(made: tuple[Path, Manifest, int], tmp_path: Path) -> None:
    """Equal seeds give byte-identical metric files."""
    logdir, _, seed = made
    wide.make_wide_logdir(tmp_path, seed=seed, now=NOW)

    first = sorted(logdir.rglob("_metrics.jsonl"))
    second = sorted((tmp_path / "beamtime").rglob("_metrics.jsonl"))
    assert [p.relative_to(logdir) for p in first] == [
        p.relative_to(tmp_path / "beamtime") for p in second
    ]
    assert all(a.read_bytes() == b.read_bytes() for a, b in zip(first, second, strict=True))
