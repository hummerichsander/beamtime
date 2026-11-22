"""Tests of the expected answers in ``bench/agents/compare/wide_truth.py``; no agent runs."""

import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from itertools import accumulate
from pathlib import Path
from typing import Any

import pytest

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import formats  # noqa: E402
import grade  # noqa: E402
import truth  # noqa: E402
import wide  # noqa: E402
import wide_truth  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
SEEDS = (7, 8, 9)
TASKS = (
    "drivers",
    "leaderboard",
    "divergence",
    "best-checkpoint",
    "check-all",
    "stale-verdicts",
    "cross-group",
    "record-history",
)
STUDY = wide.STUDY_GROUP
NOW_VERDICT = {"pass": "confirmed", "fail": "refuted", "inconclusive": "inconclusive"}


class Made:
    """One seed's wide log dir, its plain-files export and the expected values."""

    def __init__(self, root: Path, seed: int) -> None:
        """Generate, export and compute.

        :param root: An empty folder.
        :param seed: The data seed."""
        self.root = root
        self.roles = data.DATASETS["wide"](root, seed=seed, now=NOW).roles
        self.logdir = root / "beamtime"
        formats.export_files(self.logdir, root)
        self.truth = truth.TRUTHS["wide"](root, self.logdir)
        self.runs = truth.load_runs(root, self.logdir)

    def check(self) -> list[dict[str, Any]]:
        """Run ``beamtime check`` on the study group.

        :return: The predictions of its canonical answer."""
        out = subprocess.run(
            [sys.executable, "-m", "beamtime.cli", "--root", str(self.root), "--json"]
            + ["check", STUDY],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(out.stdout)["predictions"]

    def role(self, name: str) -> list[str]:
        """Give the run ids of a planted role.

        :param name: The role.
        :return: The ids in the manifest's order."""
        return self.roles[name].split(",")


@pytest.fixture(scope="module", params=SEEDS)
def made(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Made:
    """A wide log dir per seed with its export and truth.

    :param request: The pytest request holding the seed.
    :param tmp_path_factory: Makes the folder.
    :return: The generated seed."""
    return Made(tmp_path_factory.mktemp(f"wide{request.param}"), request.param)


def run_of(rows: list[tuple[int, dict[str, float]]], **config: Any) -> truth.TruthRun:
    """Make a finished run from ``(step, metrics)`` pairs.

    :param rows: The records.
    :param config: The run's config.
    :return: The run."""
    return truth.TruthRun(
        group="sweeps/s01",
        id="r",
        config=config,
        rows=[{"step": s, **m} for s, m in rows],
        output="",
        finished=True,
    )


def reply(answer: dict[str, Any]) -> str:
    """Write a reply that ends with a json block.

    :param answer: The block's content.
    :return: The reply text."""
    return f"Done.\n\n```json\n{json.dumps(answer)}\n```\n"


def score(task_id: str, answer: dict[str, Any], expected: dict[str, Any], tmp: Path) -> float:
    """Grade an answer with a shipped task.

    :param task_id: The task.
    :param answer: The answer's json.
    :param expected: The task's truth.
    :param tmp: A folder for the grader.
    :return: The score."""
    return grade.grade(grade.load_tasks()[task_id], reply(answer), expected, tmp).score


def test_truth_registered_and_complete(made: Made) -> None:
    """The wide data set has a truth function with the four tasks, all with shipped task files."""
    assert truth.TRUTHS["wide"] is truth.compute_wide
    assert set(made.truth) == set(TASKS)
    tasks = grade.load_tasks()
    assert all(tasks[t].data == "wide" and tasks[t].time_limit_s == 600 for t in TASKS)


def test_drivers(made: Made) -> None:
    """The driver is weight decay with best value 1e-3, far ahead of the next key."""
    t = made.truth["drivers"]
    eta = sorted(t["eta"].values(), reverse=True)

    assert (t["key"], t["best_value"]) == ("weight_decay", 1e-3)
    assert eta[0] > 2 * eta[1]
    assert set(t["eta"]) == {"lr", "batch_size", "weight_decay", "dropout", "model"}
    assert wide.BASE_LOSS < t["mean_at_best"] < wide.BASE_LOSS + 0.1


def test_config_values_exact() -> None:
    """A weight decay of 0 and one of 1e-4 are two values, not one."""
    runs = [
        run_of([(0, {"val/loss": 0.9})], weight_decay=0),
        run_of([(0, {"val/loss": 0.5})], weight_decay=1e-4),
        run_of([(0, {"val/loss": 0.7})], weight_decay=1e-3),
    ]

    t = wide_truth.drivers(runs)

    assert (t["key"], t["best_value"], t["mean_at_best"]) == ("weight_decay", 1e-4, 0.5)


def test_leaderboard(made: Made) -> None:
    """The leaderboard is the five planted leaders in order and no trap."""
    board = made.truth["leaderboard"]["runs"]
    finals = [x["val_loss"] for x in board]

    assert [x["id"] for x in board] == made.role("leaders")
    assert not {x["id"] for x in board} & set(made.role("traps"))
    assert all(x["group"].startswith("sweeps/s") for x in board)
    assert finals == sorted(finals)
    assert all(b - a >= wide.LEADER_GAP - 1e-6 for a, b in zip(finals, finals[1:]))


def test_divergence(made: Made) -> None:
    """The divergence set is the three planted runs, by step; the spike run is absent."""
    found = made.truth["divergence"]["runs"]
    steps = [x["step"] for x in found]
    onset = (20_000, 80_000 + wide.DIVERGE_NAN_AFTER)

    assert [x["id"] for x in found] == made.role("diverged")
    assert made.role("spike")[0] not in {x["id"] for x in found}
    assert steps == sorted(set(steps))
    assert all(onset[0] <= s <= onset[1] for s in steps)


def test_divergence_step_is_the_first_crossing(made: Made) -> None:
    """At each step the loss is above 10 times its running minimum and at no earlier step."""
    for x in made.truth["divergence"]["runs"]:
        run = next(r for r in made.runs if r.id == x["id"])
        losses = [v for _, v in run.values("train/loss")]
        low = list(accumulate(losses, lambda a, b: min(a, b) if math.isfinite(b) else a))
        crossed = [
            i
            for i in range(1, len(losses))
            if not math.isfinite(losses[i]) or losses[i] > 10 * low[i - 1]
        ]
        assert crossed[0] == x["step"]


def test_running_min() -> None:
    """The bar is 10 times the lowest finite loss before the step, not the loss before it."""
    losses = [1.0, 0.1, 0.9, 0.99, 1.01, 5.0]
    run = run_of([(s, {"train/loss": v}) for s, v in enumerate(losses)])

    assert wide_truth.diverged_at(run) == 4
    assert (
        wide_truth.diverged_at(run_of([(s, {"train/loss": v}) for s, v in enumerate([1, 9.9])]))
        is None
    )


def test_nan_ignored() -> None:
    """A NaN validation loss never wins a minimum; a NaN training loss is a divergence."""
    values = [(0, 0.9), (500, math.nan), (1000, 0.4), (1500, math.inf), (2000, 0.6)]
    run = run_of([(s, {"val/loss": v, "train/loss": v / 2}) for s, v in values])

    assert wide_truth.lowest_finite(run.values("val/loss")) == (1000, 0.4)
    assert wide_truth.diverged_at(run) == 500


def test_best_checkpoint(made: Made) -> None:
    """Eight runs, one distinct minimum each on the evaluation grid, clear of the next lowest."""
    found = made.truth["best-checkpoint"]["runs"]
    steps = [x["step"] for x in found]

    assert len(found) == 8
    assert len(set(steps)) == 8
    assert all(
        s % wide.LONG_VAL_EVERY == 0 and wide.MINIMA_RANGE[0] <= s < wide.MINIMA_RANGE[1]
        for s in steps
    )
    for x in found:
        run = next(r for r in made.runs if r.id == x["id"])
        vals = sorted(v for _, v in run.values("val/loss"))
        assert vals[1] - vals[0] > 0.001
        assert x["train_loss"] == dict(run.values("train/loss"))[x["step"]]
        assert dict(run.values("val/loss"))[x["step"]] == vals[0]


def test_perfect_answers_score_one(made: Made, tmp_path: Path) -> None:
    """A hand-written perfect answer scores 1.0, with run ids in other forms and numbers as text."""
    t = made.truth
    leaders = made.role("leaders")
    values = [x["val_loss"] for x in t["leaderboard"]["runs"]]
    answers = {
        "drivers": {
            "key": "weight_decay",
            "best_value": "0.001",
            "mean_at_best": t["drivers"]["mean_at_best"],
        },
        "leaderboard": {
            "runs": [
                {"id": f"sweeps/s01/{i}", "group": "sweeps/s01", "val_loss": v}
                for i, v in zip(leaders, values, strict=True)
            ]
        },
        "divergence": {
            "runs": [
                {"id": i, "step": x["step"]}
                for i, x in zip(made.role("diverged"), t["divergence"]["runs"], strict=True)
            ]
        },
        "best-checkpoint": {"runs": [dict(x) for x in t["best-checkpoint"]["runs"]]},
        "check-all": {"predictions": [dict(x) for x in t["check-all"]["predictions"]]},
        "stale-verdicts": {"changed": [dict(x) for x in t["stale-verdicts"]["changed"]]},
        "cross-group": {
            "groups": [dict(x) for x in t["cross-group"]["groups"]],
            "better": t["cross-group"]["better"],
        },
        "record-history": {
            "added": [f"{wide.STUDY_GROUP}/{i}" for i in t["record-history"]["added"]],
            "change": [dict(x) for x in t["record-history"]["change"]],
        },
    }

    for task_id in TASKS:
        assert score(task_id, answers[task_id], t[task_id], tmp_path) == 1.0


def test_trap_answers_score_below_one(made: Made, tmp_path: Path) -> None:
    """The typical wrong answers fail: a trap on the leaderboard, a spike as divergence, a lr driver,
    the last evaluation as the best checkpoint."""
    t = made.truth
    board = [dict(x) for x in t["leaderboard"]["runs"]]
    board[-1]["id"] = made.role("traps")[0]
    spiked = [dict(x) for x in t["divergence"]["runs"]] + [
        {"id": made.role("spike")[0], "step": 40_000}
    ]
    last = [
        {"id": x["id"], "step": wide.LONG_STEPS - 1, "train_loss": x["train_loss"]}
        for x in t["best-checkpoint"]["runs"]
    ]
    answers = {
        "drivers": {"key": "lr", "best_value": 3e-4, "mean_at_best": t["drivers"]["mean_at_best"]},
        "leaderboard": {"runs": board},
        "divergence": {"runs": spiked},
        "best-checkpoint": {"runs": last},
        "check-all": {
            "predictions": [
                dict(x, verdict="confirmed") for x in t["check-all"]["predictions"]
            ]
        },
        "stale-verdicts": {"changed": t["stale-verdicts"]["changed"][:1]},
        "cross-group": {
            "groups": [dict(x, mean=x["mean"] + 0.01) for x in t["cross-group"]["groups"]],
            "better": wide_truth.COMPARED[0]
            if t["cross-group"]["better"] != wide_truth.COMPARED[0]
            else wide_truth.COMPARED[1],
        },
        "record-history": {
            "added": t["record-history"]["added"][:-1],
            "change": [dict(x, change=0.0) for x in t["record-history"]["change"]],
        },
    }

    for task_id in TASKS:
        assert score(task_id, answers[task_id], t[task_id], tmp_path) < 1.0


def test_t_quantile() -> None:
    """The quantiles equal the textbook values for 2, 10 and 1 degrees of freedom."""
    for df, expected in ((1, 12.706205), (2, 4.302653), (10, 2.228139)):
        assert wide_truth.t_quantile(0.975, df) == pytest.approx(expected, abs=1e-6)


def test_matches_beamtime_check(made: Made) -> None:
    """Verdict, effect, interval and points equal those of ``beamtime check`` (ends abs 1e-9)."""
    checked = {p["name"]: p for p in made.check()}
    found = made.truth["check-all"]["predictions"]

    assert [p["name"] for p in found] == list(checked)
    for p in found:
        c = checked[p["name"]]
        assert p["verdict"] == NOW_VERDICT[c["result"]]
        assert p["effect"] == pytest.approx(c["effect"], abs=1e-9)
        assert p["ci"] == pytest.approx(c["ci"], abs=1e-9)
        assert p["points"] == c["points"]


def test_points_convention(made: Made) -> None:
    """A compare over six seeds has 12 points, an each over its one point has 1; three seeds halve
    the compare to 6, and the early truth equals what the verdict note recorded."""
    found = {p["name"]: p for p in made.truth["check-all"]["predictions"]}
    early = [r for r in made.runs if r.group != STUDY or r.config["seed"] < 3]
    first = {
        p["name"]: p for p in wide_truth.check_all(early, made.root)["predictions"]
    }

    assert [found[n]["points"] for n in wide.EARLY_CHECK] == [1, 12, 12, 1]
    for name, recorded in wide.EARLY_CHECK.items():
        assert NOW_VERDICT[recorded["result"]] == first[name]["verdict"]
        assert first[name]["effect"] == pytest.approx(recorded["effect"], abs=1e-9)
        assert first[name]["ci"] == pytest.approx(recorded["ci"], abs=1e-9)
        assert first[name]["points"] == recorded["points"]


def test_less_than_verdicts() -> None:
    """For ``<`` an interval below the threshold confirms and one above refutes; ``>`` mirrors it."""
    decide = wide_truth.decide

    assert decide("<", -0.2, -0.1, 0.0) == "confirmed"
    assert decide("<", 0.1, 0.2, 0.0) == "refuted"
    assert decide("<", -0.1, 0.1, 0.0) == "inconclusive"
    assert decide("<", 0.0, 0.2, 0.0) == "refuted"
    assert decide("<=", -0.2, 0.0, 0.0) == "confirmed"
    assert decide(">", 0.1, 0.2, 0.0) == "confirmed"
    assert decide(">", -0.2, -0.1, 0.0) == "refuted"
    assert decide(">", -0.1, 0.1, 0.0) == "inconclusive"
    assert decide(">=", 0.0, 0.2, 0.0) == "confirmed"


def test_planted_flips(made: Made) -> None:
    """Exactly two verdicts changed since the note: Lion's lead became clear, the SGD bound unclear."""
    assert made.truth["stale-verdicts"]["changed"] == [
        {"name": "lion-beats-adamw", "old": "inconclusive", "new": "confirmed"},
        {"name": "sgd-under", "old": "confirmed", "new": "inconclusive"},
    ]


def test_old_from_note(made: Made, tmp_path: Path) -> None:
    """The old verdict is the newest verdict note's, not the memory's; a newer note replaces it."""
    record = tmp_path / "record"
    shutil.copytree(made.root / "record", record)
    memory = next((record / "memory").glob("*.md"))
    memory.write_text(memory.read_text(encoding="utf-8").replace("inconclusive", "refuted"), encoding="utf-8")

    assert wide_truth.stale_verdicts(made.runs, tmp_path) == made.truth["stale-verdicts"]

    folder = record / STUDY / "notes"
    older = next(folder.glob("*.md"))
    (folder / "99999999-000000-zzzz.md").write_text(
        older.read_text(encoding="utf-8").replace("sgd-under: confirmed", "sgd-under: inconclusive")
    , encoding="utf-8")
    changed = wide_truth.stale_verdicts(made.runs, tmp_path)["changed"]

    assert [x["name"] for x in changed] == ["lion-beats-adamw"]


def test_independent_of_beamtime() -> None:
    """The wide truth reads the export only: no beamtime import beyond what ``truth`` already uses."""
    source = (COMPARE / "wide_truth.py").read_text(encoding="utf-8")

    assert "beamtime" not in source
    assert wide_truth.compute.__module__ == "wide_truth"


def test_cross_group(made: Made) -> None:
    """The two groups' counts are their finished runs read from the run cards, and the better
    group has the lower mean."""
    found = made.truth["cross-group"]
    for g in found["groups"]:
        cards = [
            json.loads(f.read_text(encoding="utf-8"))
            for f in (made.logdir / g["group"]).glob("*/_run.json")
        ]
        assert len(cards) == wide.SWEEP_RUNS
        assert g["runs"] == sum(c["status"] == "finished" for c in cards)
    means = [g["mean"] for g in found["groups"]]

    assert [g["group"] for g in found["groups"]] == list(wide_truth.COMPARED)
    assert found["difference"] == pytest.approx(means[0] - means[1], abs=1e-12)
    assert found["better"] == wide_truth.COMPARED[0 if means[0] < means[1] else 1]


def test_cross_group_leaves_ended_runs_out() -> None:
    """A killed run with a low loss does not count; the mean is of the finished runs by hand."""
    first, second = wide_truth.COMPARED
    runs = [
        run_of([(0, {"val/loss": 0.5})], g=1),
        run_of([(0, {"val/loss": 0.7})], g=2),
        run_of([(0, {"val/loss": 0.2})], g=3),
        run_of([(0, {"val/loss": 0.4})], g=4),
    ]
    for r, group in zip(runs, (first, first, first, second), strict=True):
        r.group = group
    runs[2].finished = False

    t = wide_truth.cross_group(runs)

    assert t["groups"] == [
        {"group": first, "runs": 2, "mean": pytest.approx(0.6)},
        {"group": second, "runs": 1, "mean": 0.4},
    ]
    assert t["difference"] == pytest.approx(0.2)
    assert t["better"] == second


def test_record_history_planted(made: Made) -> None:
    """The nine runs of seeds 3 to 5 came after the note; the shift per optimizer is half the
    difference of the planted means, since all runs weigh the two halves equally."""
    t = made.truth["record-history"]
    expected = {o: (late - early) / 2 for o, (early, late) in wide.STUDY_MEANS.items()}

    assert len(t["added"]) == 9
    assert t["added"] == sorted(
        r.id for r in made.runs if r.group == STUDY and r.config["seed"] >= 3
    )
    assert {x["optimizer"] for x in t["change"]} == set(wide.OPTIMIZERS)
    for x in t["change"]:
        assert x["change"] == pytest.approx(expected[x["optimizer"]], abs=1e-9)


def test_record_history_by_hand(tmp_path: Path) -> None:
    """The note's time splits the runs: ids starting before it are then, the rest are added; only
    a verdict note counts and the newest one wins."""
    notes = tmp_path / "record" / STUDY / "notes"
    notes.mkdir(parents=True)
    for stem, kind in (("20261021-120000-aaaa", "verdict"), ("20261021-130000-bbbb", "theory")):
        (notes / f"{stem}.md").write_text(f"---\ntype: {kind}\n---\nbody\n", encoding="utf-8")
    ids = ("20261021-110000-r1", "20261021-115959-r2", "20261021-120000-r3", "20261021-140000-r4")
    runs = [
        run_of([(0, {"val/loss": v})], optimizer="sgd")
        for v in (1.0, 0.5, 0.25, 0.125)
    ]
    for r, i in zip(runs, ids, strict=True):
        r.id, r.group = i, STUDY

    t = wide_truth.record_history(runs, tmp_path)

    assert t["added"] == list(ids[2:])
    assert t["change"] == [
        {"optimizer": "sgd", "change": pytest.approx((1.0 + 0.5 + 0.25 + 0.125) / 4 - 0.75)}
    ]
