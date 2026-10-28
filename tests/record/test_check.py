from pathlib import Path

import pytest

from beamtime.format.authored import newest
from beamtime.index.index import Index
from beamtime.record.check import evaluate
from beamtime.record.proposals import Target, current, parse
from beamtime.synth import Manifest, generate

SWEEP = "scaling/lr-sweep"
BEST = {"config.lr": 3e-4}
ACC = {"metric": "val/acc", "stat": "last"}


@pytest.fixture(scope="module")
def target(synth: tuple[Path, Manifest], tmp_path_factory: pytest.TempPathFactory):
    """The lr sweep of the shared synthetic log dir, with its own index.

    :param synth: The log dir and manifest.
    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The sweep as a check target."""
    index = Index(logdir=synth[0], cache=tmp_path_factory.mktemp("cache"))
    index.catch_up(".", budget_s=float("inf"))
    yield Target(index=index, rel=SWEEP, run_id=None)
    index.close()


def check(target: Target, *predictions: dict, **fields) -> dict:
    """Check predictions against the runs of the sweep's proposal version.

    :param target: The sweep.
    :param predictions: The predictions.
    :param fields: Further proposal fields, e.g. plan or significance.
    :return: The check."""
    proposal = parse({"statement": "test", "predictions": list(predictions), **fields}, source="t")
    return evaluate(target, current(target.dir), proposal)


def test_planted_effects_pass(target: Target) -> None:
    """The generator's own proposal passes, final once the grid is complete."""
    result = evaluate(target, current(target.dir))
    assert result["result"] == "pass" and not result["provisional"]
    assert result["progress"]["text"].startswith("15 of 15 grid points")
    assert len(result["progress"]["dropped"]) == 2
    converges, mid = result["predictions"]
    assert converges["ci"][0] > 0 and converges["points"] == 1
    assert mid["n"] == {"a": 3, "b": 3} and mid["effect"] > 0.01


def test_each_outcomes(target: Target) -> None:
    """each passes, fails, stays inconclusive, or is insufficient, as the interval says."""
    base = {"where": BEST, "reduce": ACC, "seeds": "config.seed", "op": ">"}
    results = check(
        target,
        base | {"name": "pass", "value": 0.9},
        base | {"name": "fail", "value": 0.99},
        base | {"name": "unclear", "value": 0.928},
        base | {"name": "few", "value": 0.9, "where": BEST | {"config.seed": 0}},
    )["predictions"]
    assert [p["result"] for p in results] == ["pass", "fail", "inconclusive", "insufficient"]
    assert "add seeds" in results[3]["detail"]
    assert results[2]["ci"][0] < 0 < results[2]["ci"][1]


def test_each_over_points(target: Target) -> None:
    """Every point must pass; the worst point is reported; without seeds no interval."""
    seeded = {"reduce": ACC, "seeds": "config.seed", "op": ">", "value": 0.9}
    result = check(target, {"name": "all", **seeded})["predictions"][0]
    assert result["points"] == 5 and result["result"] == "fail"
    assert len(result["by_point"]) == 5 and "config.lr" in result["by_point"][0]["point"]
    direct = check(target, {"name": "d", "where": BEST, "reduce": ACC, "op": ">", "value": 0.9})
    entry = direct["predictions"][0]
    assert entry["result"] == "pass" and entry["ci"] is None and "directly" in entry["detail"]
    none = check(target, {"name": "n", **seeded, "where": BEST | {"config.seed": 0}},
                 significance="none")  # fmt: skip
    assert none["predictions"][0]["result"] == "pass" and none["level"] is None


def test_ref_and_compare(target: Target) -> None:
    """ref compares with another run; compare uses Welch or, with pair_by, pairs."""
    high = next(
        r["_id"] for r in target.select(current(target.dir), {"config.lr": 3e-3}, ["config.lr"])
    )
    pair = {"reduce": ACC, "test": "compare", "a": BEST, "b": {"config.lr": 3e-3}, "op": ">"}
    results = check(
        target,
        {"name": "ref", "where": BEST, "reduce": ACC, "seeds": "config.seed", "op": ">",
         "ref": {"run": high}},
        pair | {"name": "paired", "pair_by": ["config.seed"]},
        pair | {"name": "margin", "margin": 0.2},
        pair | {"name": "nobody", "b": {"config.lr": 42}},
    )["predictions"]  # fmt: skip
    assert [p["result"] for p in results] == ["pass", "pass", "fail", "pending"]
    assert results[1]["n"] == {"pairs": 3} and results[1]["points"] == 3


def test_pending_and_manual(target: Target) -> None:
    """Missing metrics and manual predictions are pending; one pending blocks a pass."""
    result = check(
        target,
        {"name": "ok", "where": BEST, "reduce": ACC, "op": ">", "value": 0.5},
        {"name": "later", "reduce": {"metric": "val/f1"}, "op": ">", "value": 0.5},
        {"name": "looks", "kind": "manual", "description": "Samples look sharp."},
    )
    assert [p["result"] for p in result["predictions"]] == ["pass", "pending", "pending"]
    assert result["result"] == "pending"
    assert "val/acc" in result["predictions"][1]["detail"]


def test_plans_and_provisional(target: Target) -> None:
    """Checks stay provisional until the plan is complete."""
    pred = {"name": "p", "where": BEST, "reduce": ACC, "op": ">", "value": 0.5}
    grid = {"grid": {"config.lr": [3e-4, 1e-2], "config.seed": [0, 1, 2]}}
    result = check(target, pred, plan=grid)
    assert result["provisional"] and result["progress"]["text"].startswith("3 of 6 grid points")
    assert check(target, pred, plan={"runs": 20})["progress"]["done"] == 15
    assert check(target, pred, plan={"runs": 10})["provisional"] is False
    assert check(target, pred)["provisional"] is True


def test_edited_frozen_file_is_invalid(tmp_path: Path) -> None:
    """An edit of a version runs recorded shows as a hash mismatch, not as a result."""
    generate(tmp_path / "beamtime", seed=0)
    index = Index(logdir=tmp_path / "beamtime", cache=tmp_path / "cache")
    index.catch_up(".", budget_s=float("inf"))
    target = Target(index=index, rel=SWEEP, run_id=None)
    path = newest(target.dir / "proposal")
    path.write_text(path.read_text().replace("value: 0.9", "value: 0.5"))
    result = evaluate(target, path.stem)
    index.close()
    assert result["result"] == "invalid" and "edited after runs recorded it" in result["problem"]
