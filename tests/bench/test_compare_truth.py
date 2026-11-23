"""Tests of the expected answers in ``bench/agents/compare/truth.py``; no agent runs."""

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.query import run as query
from beamtime.record.stats import welch_interval

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import formats  # noqa: E402
import grade  # noqa: E402
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
        "logged-tables",
        "run-lifecycle",
    }


def role(made: Made, name: str) -> str:
    """Give the run id of a planted role.

    :param made: The generated seed.
    :param name: The role.
    :return: The run id."""
    return made.roles[name].split("/")[-1]


def test_planted_effects(made: Made) -> None:
    """The planted winners hold on every seed."""
    t = made.truth
    assert t["best-config"]["best_lr"] == 3e-4
    assert t["best-config"]["runner_up_lr"] == 1e-3
    assert t["sweep-summary"]["best_arm"] == "large"
    assert t["fastest"]["lr"] == 1e-3
    assert t["check-prediction"]["seeds"] == [0, 1, 2]


def test_failing_runs_and_their_reruns(made: Made) -> None:
    """The sweep's failures are the three planted ones, told apart by their output; the killed
    and the out-of-memory run were redone, the diverged one was not."""
    diverging, killed, oom = (role(made, n) for n in ("diverging", "killed", "oom"))
    fail = made.truth["failures"]

    assert fail["causes"] == {diverging: "diverged", killed: "killed", oom: "oom"}
    assert fail["ids"] == sorted([diverging, killed, oom])
    assert fail["reruns"] == {
        diverging: None,
        killed: role(made, "killed_rerun"),
        oom: role(made, "oom_rerun"),
    }


def test_significance_pinned(made_seeds: dict[int, Made]) -> None:
    """With both batches the lead of 3e-4 is significant for seeds 7 and 9, not for 8."""
    first = made_seeds[7].truth["best-config"]
    assert first["difference"] == pytest.approx(0.00778, abs=5e-6)
    assert first["ci"] == pytest.approx([0.00185, 0.01372], abs=5e-6)
    assert first["significant"] is True
    assert made_seeds[8].truth["best-config"]["significant"] is False
    last = made_seeds[9].truth["best-config"]
    assert last["difference"] == pytest.approx(0.01096, abs=5e-6)
    assert last["significant"] is True


def naive_best(runs: list[truth.TruthRun], *, groups: tuple[str, ...]) -> tuple[float, float]:
    """Rank the lrs by the mean of every finished run, superseded ones included.

    :param runs: All runs.
    :param groups: The batches to read.
    :return: The best lr and its lead over the runner-up."""
    finals: dict[float, list[float]] = {}
    for r in runs:
        if r.group in groups and r.finished:
            finals.setdefault(r.config["lr"], []).append(r.final_accuracy())
    means = sorted(((sum(v) / len(v), lr) for lr, v in finals.items()), reverse=True)
    return means[0][1], means[0][0] - means[1][0]


def test_superseded_runs_matter(made: Made) -> None:
    """Counting a superseded run, or reading one batch only, gives a different answer."""
    runs = truth.load_runs(made.files, made.logdir)
    best = made.truth["best-config"]

    assert naive_best(runs, groups=(truth.SWEEP,))[0] == 1e-3
    lr, lead = naive_best(runs, groups=truth.SWEEPS)
    assert lr != best["best_lr"] or abs(lead - best["difference"]) > 0.05 * best["difference"]
    assert role(made, "superseded") not in {p["id"] for p in made.truth["chart"]["points"]}


def test_final_is_last_logged_value(made: Made) -> None:
    """The final value is the last non-empty cell, not the cell of the last row."""
    runs = truth.load_runs(made.files, made.logdir)
    last_row_empty = 0
    for r in truth.sweep_runs(runs):
        with (made.files / "runs" / r.group / r.id / "metrics.csv").open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        key = next(k for k in truth.ACCURACY if k in rows[0])
        logged = [row[key] for row in rows if row[key] != ""]
        if rows[-1][key] == "":
            last_row_empty += 1
        assert r.final_accuracy() == (float(logged[-1]) if logged else None)

    assert last_row_empty > 0


def test_accuracy_has_two_names(made: Made) -> None:
    """The first batch logs val/acc every 50 steps, the second val/accuracy every 100."""
    runs = truth.load_runs(made.files, made.logdir)
    for r in truth.sweep_runs(runs):
        first = r.group == truth.SWEEP
        assert (r.final("val/acc") is not None) is first
        assert (r.final("val/accuracy") is not None) is not first
        steps = [s for s, _ in r.accuracy()]
        assert steps[1] - steps[0] == (50 if first else 100)


def test_matches_beamtime_query(seed7: Made) -> None:
    """Every sweep run's final accuracy and every egnn checkpoint equal Beamtime's own reading."""
    rows = query(
        {
            "runs": {
                "from": "scaling",
                "select": ["run.id", "metric.val/acc.last", "metric.val/accuracy.last"],
                "limit": 100,
            }
        },
        logdir=seed7.logdir,
        now=NOW.timestamp(),
    )["rows"]
    by_id = {row[0]: row[1] if row[1] is not None else row[2] for row in rows}
    sweep = truth.sweep_runs(truth.load_runs(seed7.files, seed7.logdir))

    assert len(sweep) == 29
    for r in sweep:
        assert by_id[r.id] == pytest.approx(r.final_accuracy(), rel=1e-12)

    curves = query(
        {
            "series": {
                "from": truth.EGNN,
                "y": ["validation/loss", "validation/w1_energy"],
                "points": "all",
            }
        },
        logdir=seed7.logdir,
        now=NOW.timestamp(),
    )["curves"]
    nan_run = role(seed7, "nan_loss")
    for r in truth.in_group(truth.load_runs(seed7.files, seed7.logdir), truth.EGNN):
        loss = next(c for c in curves if c["run"] == r.id and c["metric"] == "validation/loss")
        w1 = next(c for c in curves if c["run"] == r.id and c["metric"] == "validation/w1_energy")
        assert loss["x"] == [s for s, _ in r.values("validation/loss")]
        assert (None in loss["y"]) is (r.id == nan_run)
        pairs = [(y, x) for x, y in zip(loss["x"], loss["y"], strict=True) if y is not None]
        step = min(pairs)[1]
        if r.finished:
            expected = truth.checkpoint(r, monitor="validation/loss", metric="validation/w1_energy")
            assert dict(zip(w1["x"], w1["y"], strict=True))[step] == expected


def test_unfinished_runs_are_not_told_apart(made: Made) -> None:
    """Running, lost, killed and failed runs all count as not finished; no truth value names a
    status."""
    runs = truth.load_runs(made.files, made.logdir)
    by_id = {r.id: r for r in runs}

    for name in (
        "lost",
        "running",
        "killed",
        "diverging",
        "oom",
        "unpaired_killed",
        "realistic_killed",
    ):
        assert by_id[role(made, name)].finished is False
    assert by_id[role(made, "resumed")].finished is True
    rows = made.truth["table"]["rows"]
    assert {type(row["finished"]) for row in rows} == {bool}
    assert all("status" not in row for row in rows)


def test_table_and_chart(made: Made) -> None:
    """The table has one row per run of both batches; the chart one point per lr and seed."""
    rows = made.truth["table"]["rows"]
    points = made.truth["chart"]["points"]
    superseded = {row["id"] for row in rows if row["superseded"]}

    assert len(rows) == 29
    assert superseded == {role(made, n) for n in ("superseded", "killed", "oom")}
    assert len(points) == 25
    assert [p["id"] for p in points] == [
        row["id"]
        for row in sorted(rows, key=lambda x: (x["lr"], x["id"]))
        if row["finished"] and not row["superseded"]
    ]


def test_find_runs_counts_every_status(made: Made) -> None:
    """The threshold applies to the last validation accuracy, under either name, of any run."""
    ids = set(made.truth["find-runs"]["ids"])
    runs = truth.load_runs(made.files, made.logdir)
    finals = {r.id: r.final_accuracy() for r in runs}

    assert ids == {i for i, v in finals.items() if v is not None and v >= truth.FIND_MIN}
    assert role(made, "superseded") in ids
    assert {r.group for r in runs if r.id in ids} >= set(truth.SWEEPS)


def test_find_runs_threshold_survives_rounding(made: Made) -> None:
    """No run's last accuracy lies within 5e-4 of the threshold, so three digits decide alike."""
    finals = [r.final_accuracy() for r in truth.load_runs(made.files, made.logdir)]

    assert min(abs(v - truth.FIND_MIN) for v in finals if v is not None and v == v) > 5e-4


def test_checkpoint_is_not_the_final_value(made: Made) -> None:
    """The overfitting arm's checkpoint differs from its final value by far more than the
    tolerance, and a NaN-blind argmin picks another step for one run."""
    summary = made.truth["sweep-summary"]
    large, final = summary["per_arm"]["large"], summary["per_arm_final"]["large"]

    assert abs(large - final) > 0.02 * large
    nan_run = next(
        r for r in truth.load_runs(made.files, made.logdir) if r.id == role(made, "nan_loss")
    )
    values = nan_run.values("validation/loss")
    blind = min(range(len(values)), key=lambda i: (values[i][1] == values[i][1], values[i][1]))
    w1 = dict(nan_run.values("validation/w1_energy"))
    assert w1[values[blind][0]] != truth.checkpoint(
        nan_run, monitor="validation/loss", metric="validation/w1_energy"
    )


def test_prediction_paired_by_seed(made_seeds: dict[int, Made]) -> None:
    """The paired interval decides: confirmed for 7 and 9, inconclusive for 8, and Welch over
    every finished run gives bounds the check tells apart."""
    verdicts = {s: m.truth["check-prediction"]["verdict"] for s, m in made_seeds.items()}
    assert verdicts == {7: "confirmed", 8: "inconclusive", 9: "confirmed"}
    for made in made_seeds.values():
        finals: dict[str, list[float]] = {"bpe": [], "unigram": []}
        for r in truth.in_group(truth.load_runs(made.files, made.logdir), truth.TOKENIZER):
            if r.finished:
                finals[r.config["tokenizer"]].append(r.final("val/ppl"))
        welch = welch_interval(finals["bpe"], finals["unigram"], truth.LEVEL)
        paired = made.truth["check-prediction"]["ci"]
        assert max(abs(welch.lo - paired[0]), abs(welch.hi - paired[1])) > 0.005


def test_fastest_needs_every_run(made: Made) -> None:
    """3e-3 never qualifies at 0.9, and counting the superseded run moves 1e-3's step."""
    fast = made.truth["fastest"]
    runs = truth.load_runs(made.files, made.logdir)
    early = next(r for r in runs if r.id == role(made, "superseded"))
    hit = next(s for s, v in early.accuracy() if v >= truth.FASTEST_AT)

    assert "0.003" not in fast["steps"]
    assert fast["step"] == pytest.approx(840, abs=40)
    assert abs((fast["step"] * 5 + hit) / 6 - fast["step"]) > 0.01 * fast["step"]


def test_logged_tables(made: Made) -> None:
    """The runs that logged the table are the first batch's runs that have one, not the failed and killed ones; the three
    lowest classes are the ones with the lowest mean of what the run files hold."""
    found = made.truth["logged-tables"]
    tables = []
    for card in sorted(made.logdir.glob("scaling/lr-sweep/*/_data.jsonl")):
        records = [json.loads(line) for line in card.read_text(encoding="utf-8").splitlines()]
        tables.append(next(r for r in records if r["key"] == "val/per_class")["columns"])
    means = {
        name: sum(t["acc"][t["class"].index(name)] for t in tables) / len(tables)
        for name in tables[0]["class"]
    }
    lowest = sorted(means, key=means.__getitem__)[:3]

    assert found["runs"] == len(tables)
    assert len(tables) < len(list(made.logdir.glob("scaling/lr-sweep/*/_run.json")))
    assert [c["class"] for c in found["classes"]] == lowest
    assert [c["mean_acc"] for c in found["classes"]] == pytest.approx([means[n] for n in lowest])
    assert means[lowest[-1]] < sorted(means.values())[3]


def test_logged_tables_by_hand(tmp_path: Path) -> None:
    """Two runs with known tables: the mean per class, lowest first, over the runs that logged it;
    a run without the file and a run with another table do not count, and the last table of a run
    is the one that counts."""
    group = truth.SWEEP

    def write(run_id: str, *entries: tuple[str, list[str], list[float]]) -> truth.TruthRun:
        folder = tmp_path / group / run_id
        folder.mkdir(parents=True)
        lines = [
            {"_step": i, "key": key, "kind": "table", "columns": {"class": cls, "acc": acc}}
            for i, (key, cls, acc) in enumerate(entries)
        ]
        (folder / "_data.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8"
        )
        return truth.TruthRun(
            group=group, id=run_id, config={}, rows=[], output="", finished=True
        )

    classes = ["a", "b", "c", "d"]
    runs = [
        write("r1", ("val/per_class", classes, [0.9, 0.5, 0.7, 0.8])),
        write(
            "r2",
            ("val/per_class", classes, [0.0, 0.0, 0.0, 0.0]),
            ("other", classes, [0.1, 0.1, 0.1, 0.1]),
            ("val/per_class", classes, [0.7, 0.3, 0.9, 0.6]),
        ),
        truth.TruthRun(group=group, id="r3", config={}, rows=[], output="", finished=False),
    ]
    (tmp_path / group / "r3").mkdir()

    found = truth.logged_tables(runs, tmp_path)

    assert found["runs"] == 2
    assert [c["class"] for c in found["classes"]] == ["b", "d", "a"]
    assert [c["mean_acc"] for c in found["classes"]] == pytest.approx([0.4, 0.7, 0.8])


def test_run_lifecycle(made: Made) -> None:
    """The one interrupted run is the planted resumed run: interrupted at step 1200 of 2000,
    continued from 1000 by a job that started two minutes less a second later."""
    runs = made.truth["run-lifecycle"]["runs"]

    assert runs == [
        {
            "id": role(made, "resumed"),
            "interrupted_at": 1200,
            "resumed_from": 1000,
            "wait_s": pytest.approx(119.0),
        }
    ]


def test_run_lifecycle_by_hand(tmp_path: Path) -> None:
    """A run with a requeue and a restart is listed with its steps and the gap between the events;
    a run that only started once is not."""
    group = truth.LONG_CONTEXT
    events = {
        "a": [
            {"_t": 100.0, "kind": "created"},
            {"_t": 150.5, "_step": 30, "kind": "requeue_requested", "signal": "SIGUSR1"},
            {"_t": 210.0, "kind": "attempt_started", "resume_step": 20},
        ],
        "b": [{"_t": 100.0, "kind": "created"}, {"_t": 100.0, "kind": "attempt_started"}],
    }
    runs = []
    for run_id, records in events.items():
        folder = tmp_path / group / run_id
        folder.mkdir(parents=True)
        (folder / "_events.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in records), encoding="utf-8"
        )
        runs.append(truth.TruthRun(group=group, id=run_id, config={}, rows=[], output="", finished=True))

    assert truth.run_lifecycle(runs, tmp_path)["runs"] == [
        {"id": "a", "interrupted_at": 30, "resumed_from": 20, "wait_s": 59.5}
    ]


def test_new_tasks_grade_against_truth(made: Made, tmp_path: Path) -> None:
    """A hand-written perfect answer scores 1.0 and the typical wrong ones score below it."""
    tasks = grade.load_tasks()
    t = made.truth

    def score(task: str, answer: dict) -> float:
        reply = f"Done.\n\n```json\n{json.dumps(answer)}\n```\n"
        return grade.grade(tasks[task], reply, t[task], tmp_path).score

    classes = [dict(c) for c in t["logged-tables"]["classes"]]
    lifecycle = [dict(r) for r in t["run-lifecycle"]["runs"]]
    stopped = [dict(r, interrupted_at=r["interrupted_at"] + 1) for r in lifecycle]

    assert score("logged-tables", {"runs": t["logged-tables"]["runs"], "classes": classes}) == 1.0
    assert score("logged-tables", {"runs": 24, "classes": classes[::-1][:2]}) < 1.0
    assert score("run-lifecycle", {"runs": lifecycle}) == 1.0
    assert score("run-lifecycle", {"runs": stopped}) < 1.0
    assert score("run-lifecycle", {"runs": []}) < 1.0


NEW_TASKS = ("cross-group", "record-history", "logged-tables", "run-lifecycle")
OPERATIONS = ("compare", "check", "importance", "timeline", "diagnose", "digest", "series", "query")


def test_new_tasks_name_no_operation() -> None:
    """The four newer tasks ask a question and give the answer shape; none names an operation."""
    tasks = grade.load_tasks()

    for task_id in NEW_TASKS:
        task = tasks[task_id]
        assert not [o for o in OPERATIONS if re.search(rf"\b{o}\b", task.prompt.lower())]
        assert "mcp" in task.setups
