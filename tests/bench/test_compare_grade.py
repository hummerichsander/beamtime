"""Tests of the comparison tasks and grader (``compare/grade.py``); no agent runs."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import formats  # noqa: E402
import grade  # noqa: E402
import truth as truth_module  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 16
IDS = ["20261020-080300-aaaaaaaa", "20261020-081000-bbbbbbbb", "20261020-082000-cccccccc"]

TRUTH: dict[str, dict[str, Any]] = {
    "best-config": {
        "best_lr": 0.0003,
        "runner_up_lr": 0.001,
        "difference": 0.0079,
        "ci": [-0.0002, 0.016],
        "significant": False,
    },
    "failures": {
        "ids": sorted(IDS[:2]),
        "causes": {IDS[0]: "diverged", IDS[1]: "killed"},
    },
    "sweep-summary": {
        "per_arm": {"small": 1.0005, "medium": 0.9267, "large": 0.8404},
        "best_arm": "large",
        "exclude": [IDS[2]],
    },
    "check-prediction": {
        "effect": 0.3985,
        "ci": [0.278, 0.519],
        "threshold": 0.1,
        "verdict": "confirmed",
    },
    "chart": {"points": []},
    "find-runs": {"ids": IDS},
    "fastest": {"lr": 0.003, "step": 466.67},
    "table": {
        "rows": [
            {"id": IDS[0], "lr": 3e-05, "seed": 0, "finished": True, "val_acc": 0.871044},
            {"id": IDS[1], "lr": 0.0003, "seed": 1, "finished": False, "val_acc": 0.5},
            {"id": IDS[2], "lr": 0.003, "seed": 2, "finished": False, "val_acc": None},
        ]
    },
}

CORRECT: dict[str, dict[str, Any]] = {
    "best-config": {
        "best_lr": 3e-4,
        "runner_up_lr": 1e-3,
        "difference": 0.008,
        "significant": False,
    },
    "failures": {
        "runs": [
            {"id": IDS[0], "cause": "loss diverged to NaN"},
            {"id": IDS[1], "cause": "job was killed (SIGTERM)"},
        ]
    },
    "sweep-summary": {
        "per_arm": {"small": 1.0, "medium": 0.927, "large": 0.84},
        "best_arm": "large",
        "exclude": [IDS[2]],
    },
    "check-prediction": {"verdict": "confirmed", "effect": 0.4, "ci": [0.28, 0.52]},
    "chart": {"file": "fig.png"},
    "find-runs": {"runs": IDS},
    "fastest": {"lr": 0.003, "step": 470},
    "table": {"file": "table.csv"},
}

WRONG: dict[str, dict[str, Any]] = {
    "best-config": {
        "best_lr": 1e-3,
        "runner_up_lr": 3e-4,
        "difference": 0.008,
        "significant": False,
    },
    "failures": {
        "runs": [
            {"id": IDS[0], "cause": "loss diverged to NaN"},
            {"id": IDS[1], "cause": "job was killed (SIGTERM)"},
            {"id": IDS[2], "cause": "still running"},
        ]
    },
    "sweep-summary": {
        "per_arm": {"small": 1.0, "medium": 0.927, "large": 0.84},
        "best_arm": "large",
        "exclude": [],
    },
    "check-prediction": {"verdict": "inconclusive", "effect": 0.4, "ci": [0.28, 0.52]},
    "chart": {},
    "find-runs": {"runs": IDS[:2] + ["20261020-099999-dddddddd"]},
    "fastest": {"lr": 0.001, "step": 550},
    "table": {"file": "table.csv"},
}

TABLE = """run_id,lr,seed,finished,val_acc
{a},3e-05,0,yes,0.871044
{b},0.0003,1,no,0.5
{c},0.003,2,no,
"""


def reply(answer: dict[str, Any] | None, *, before: str = "Done.") -> str:
    """Write a reply that ends with a json block.

    :param answer: The block's content, or ``None`` for a reply without a block.
    :param before: The prose before the block.
    :return: The reply text."""
    if answer is None:
        return before
    return f"{before}\n\n```json\n{json.dumps(answer)}\n```\n"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """An agent's folder with a PNG and a correct table in it.

    :param tmp_path: An empty folder.
    :return: The folder."""
    (tmp_path / "fig.png").write_bytes(PNG)
    (tmp_path / "table.csv").write_text(TABLE.format(a=IDS[0], b=IDS[1], c=IDS[2]))
    return tmp_path


@pytest.fixture(scope="module")
def tasks() -> dict[str, grade.Task]:
    """The shipped tasks.

    :return: The tasks by id."""
    return grade.load_tasks()


def test_eight_tasks(tasks: dict[str, grade.Task]) -> None:
    """The plan's eight ids are all there, with limits and all four setups."""
    assert set(tasks) == set(TRUTH)
    assert all(t.time_limit_s >= 300 and t.setups == grade.SETUPS for t in tasks.values())
    assert set(CORRECT) == set(WRONG) == set(tasks)


def test_prompts(tasks: dict[str, grade.Task]) -> None:
    """Every prompt ends with the answer line and none names a product or a file layout."""
    banned = re.compile(
        r"beamtime|tensorboard|csv|metrics|events|hparams|config\.|output\.log|runs/|\.log", re.I
    )
    for task in tasks.values():
        assert task.prompt.endswith(f"End your reply with a fenced json block: {task.answer}")
        assert not banned.search(task.prompt), task.id
    assert "full precision" in tasks["table"].prompt


@pytest.mark.parametrize("task_id", sorted(CORRECT))
def test_correct_answer(tasks: dict[str, grade.Task], project: Path, task_id: str) -> None:
    """A hand-written correct answer scores 1."""
    result = grade.grade(tasks[task_id], reply(CORRECT[task_id]), TRUTH[task_id], project)
    assert result.score == 1.0 and result.correct, result.checks


@pytest.mark.parametrize("task_id", sorted(WRONG))
def test_typical_wrong_answer(tasks: dict[str, grade.Task], project: Path, task_id: str) -> None:
    """A typical wrong answer scores below 1."""
    if task_id == "table":
        (project / "table.csv").write_text(
            TABLE.format(a=IDS[0], b=IDS[1], c=IDS[2]).replace("0.0003,1,no", "0.0003,1,yes")
        )
    result = grade.grade(tasks[task_id], reply(WRONG[task_id]), TRUTH[task_id], project)
    assert result.score < 1.0 and not result.correct, result.checks


def test_counting_the_killed_run(tasks: dict[str, grade.Task], project: Path) -> None:
    """Listing only the diverged run, or a wrong cause, fails the matching check only."""
    answer = {"runs": [{"id": IDS[0], "cause": "failed"}, {"id": IDS[1], "cause": "cancelled"}]}
    result = grade.grade(tasks["failures"], reply(answer), TRUTH["failures"], project)
    assert result.checks == {"ids": 1.0, "causes": 0.0}


def test_no_block_scores_zero(tasks: dict[str, grade.Task], project: Path) -> None:
    """A reply without a json block, or with a broken one, scores 0 on every check."""
    for text in ("The best is 3e-4.", '```json\n{"best_lr": \n```'):
        result = grade.grade(tasks["best-config"], text, TRUTH["best-config"], project)
        assert result.score == 0.0 and set(result.checks.values()) == {0.0}


def test_last_block(tasks: dict[str, grade.Task], project: Path) -> None:
    """Of several json blocks the last one counts."""
    text = reply(WRONG["best-config"]) + "\nOn second thought:\n" + reply(CORRECT["best-config"])
    assert grade.grade(tasks["best-config"], text, TRUTH["best-config"], project).correct
    swapped = reply(CORRECT["best-config"]) + reply(WRONG["best-config"])
    assert not grade.grade(tasks["best-config"], swapped, TRUTH["best-config"], project).correct


def test_answer_json_ignores_other_fences() -> None:
    """Code fences of other languages are not answers."""
    text = "```python\nprint({'a': 1})\n```\n```json\n{\"a\": 1}\n```\n```python\nx = {}\n```"
    assert grade.answer_json(text) == {"a": 1}
    assert grade.answer_json("```json\n[1, 2]\n```") is None


@pytest.mark.parametrize("info", ["python3", "c++", "py title=x", "shell-session"])
def test_answer_json_after_other_info_strings(info: str) -> None:
    """A fence whose info string is not a plain word does not swallow the answer after it."""
    text = f'```{info}\nx = 1\n```\n\nDone.\n\n```JSON\n{{"a": 1}}\n```\n'
    assert grade.answer_json(text) == {"a": 1}


def test_unknown_check_kind(tmp_path: Path) -> None:
    """A task file with a misspelt check kind fails on load instead of scoring 0."""
    (tmp_path / "x.yaml").write_text(
        "prompt: p\nanswer: '{}'\ntime_limit_s: 1\nchecks:\n  a: {kind: equals, truth: a}\n"
    )
    with pytest.raises(ValueError, match="equals"):
        grade.load_tasks(tmp_path)


@pytest.mark.parametrize("lr", [0.0003, "0.0003", "3e-4", "3.0e-4", "3E-4", 3e-4])
def test_lr_forms(tasks: dict[str, grade.Task], project: Path, lr: Any) -> None:
    """A learning rate written in any form equals the truth as a float."""
    answer = {**CORRECT["best-config"], "best_lr": lr}
    assert grade.grade(tasks["best-config"], reply(answer), TRUTH["best-config"], project).correct


@pytest.mark.parametrize(
    "form", ["{id}", "scaling/lr-sweep/{id}", "@host/scaling/lr-sweep/{id}/", "`{id}`"]
)
def test_id_forms(tasks: dict[str, grade.Task], project: Path, form: str) -> None:
    """A run id with a group prefix or decoration matches the trailing id."""
    answer = {"runs": [form.format(id=i) for i in IDS]}
    assert grade.grade(tasks["find-runs"], reply(answer), TRUTH["find-runs"], project).correct


def test_find_runs_f1(tasks: dict[str, grade.Task], project: Path) -> None:
    """The score of ``find-runs`` is the F1 of the two sets."""
    answer = {"runs": IDS[:2]}
    result = grade.grade(tasks["find-runs"], reply(answer), TRUTH["find-runs"], project)
    assert result.score == pytest.approx(0.8)


def test_cause_words(tasks: dict[str, grade.Task], project: Path) -> None:
    """``failed`` alone is no cause; a divergence word or a kill word is."""
    check = tasks["failures"].checks["causes"]
    expected = TRUTH["failures"]["causes"]

    def passes(first: str, second: str) -> float:
        answer = {"runs": [{"id": IDS[0], "cause": first}, {"id": IDS[1], "cause": second}]}
        return grade.run_check("causes", check, answer, TRUTH["failures"], project)

    assert expected == {IDS[0]: "diverged", IDS[1]: "killed"}
    assert passes("failed", "failed") == 0.0
    assert passes("failed: non-finite loss", "stopped by SIGTERM") == 1.0
    assert passes("FloatingPointError", "JOB CANCELLED") == 1.0
    assert passes("loss became inf", "killed") == 1.0
    assert passes("killed", "diverged") == 0.0
    assert passes("information", "failed") == 0.0


def test_difference_tolerance(tasks: dict[str, grade.Task], project: Path) -> None:
    """The difference passes within 20 % and fails beyond."""
    for value, ok in ((0.0079 * 1.15, True), (0.0079 * 1.3, False), (0.0079 * 0.7, False)):
        answer = {**CORRECT["best-config"], "difference": value}
        result = grade.grade(tasks["best-config"], reply(answer), TRUTH["best-config"], project)
        assert (result.checks["difference"] == 1.0) is ok


def test_ci_contains_effect(tasks: dict[str, grade.Task], project: Path) -> None:
    """The interval must contain the true effect, in either order."""
    for ci, ok in (
        ([0.28, 0.52], True),
        ([0.52, 0.28], True),
        ([0.45, 0.6], False),
        ([0.4], False),
    ):
        answer = {**CORRECT["check-prediction"], "ci": ci}
        result = grade.grade(
            tasks["check-prediction"], reply(answer), TRUTH["check-prediction"], project
        )
        assert (result.checks["ci"] == 1.0) is ok, ci


def test_per_arm_needs_every_arm(tasks: dict[str, grade.Task], project: Path) -> None:
    """A missing arm, or one off by more than 1 %, fails ``per_arm``."""
    base = CORRECT["sweep-summary"]
    for per_arm, ok in (
        (base["per_arm"], True),
        ({"small": 1.0, "medium": 0.927}, False),
        ({**base["per_arm"], "large": 0.9}, False),
    ):
        result = grade.grade(
            tasks["sweep-summary"],
            reply({**base, "per_arm": per_arm}),
            TRUTH["sweep-summary"],
            project,
        )
        assert (result.checks["per_arm"] == 1.0) is ok


def test_chart_file(
    tasks: dict[str, grade.Task], project: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """The chart must exist inside the project and be a PNG."""
    chart, truth = tasks["chart"], TRUTH["chart"]
    (project / "fake.png").write_bytes(b"not a png")
    outside = tmp_path_factory.mktemp("outside") / "fig.png"
    outside.write_bytes(PNG)
    for name, ok in (
        ("fig.png", True),
        (str(project / "fig.png"), True),
        ("fake.png", False),
        ("missing.png", False),
        (str(outside), False),
        ("../" + outside.name, False),
    ):
        assert grade.grade(chart, reply({"file": name}), truth, project).correct is ok, name


def test_table_checks(tasks: dict[str, grade.Task], project: Path) -> None:
    """The table is graded on its rows, values and finished flags apart."""
    table, truth = tasks["table"], TRUTH["table"]
    path = project / "table.csv"
    good = TABLE.format(a=IDS[0], b=IDS[1], c=IDS[2])

    def checks(text: str) -> dict[str, float]:
        path.write_text(text)
        return grade.grade(table, reply({"file": "table.csv"}), truth, project).checks

    assert set(checks(good).values()) == {1.0}
    assert checks(good.replace(f"{IDS[2]},0.003,2,no,\n", ""))["rows"] == 0.0
    assert checks(good.replace("0.871044", "0.8710"))["values"] == 0.0
    assert checks(good.replace("0.871044", "0.8710441"))["values"] == 1.0
    assert checks(good.replace(",no,0.5", ",yes,0.5")) == {
        "file": 1.0,
        "rows": 1.0,
        "values": 1.0,
        "finished": 0.0,
    }
    assert (
        checks(good.replace(",yes,", ",finished,").replace(",no,", ",killed,"))["finished"] == 1.0
    )
    assert checks(good.replace("0.003,2,no,", "0.003,2,no,nan"))["values"] == 1.0
    assert checks(good.replace("0.003,2,no,", "0.003,2,no,0.9"))["values"] == 0.0
    assert checks(good.replace(IDS[0], f"scaling/lr-sweep/{IDS[0]}")) == {
        k: 1.0 for k in table.checks
    }
    assert set(checks(good.replace("val_acc", "accuracy")).values()) == {0.0}


@pytest.fixture(scope="module")
def seed7(tmp_path_factory: pytest.TempPathFactory) -> tuple[dict[str, Any], dict[str, Any]]:
    """The truth of seed 7 and a correct answer for every task built from it.

    :param tmp_path_factory: Makes the folder.
    :return: The truth and the answers."""
    root = tmp_path_factory.mktemp("seed7")
    data.make_logdir(root, seed=7, now=NOW)
    formats.export_files(root / "beamtime", root)
    truth = truth_module.compute(root, root / "beamtime")
    best, fail = truth["best-config"], truth["failures"]
    answers = {
        "best-config": {
            k: best[k] for k in ("best_lr", "runner_up_lr", "difference", "significant")
        },
        "failures": {"runs": [{"id": i, "cause": c} for i, c in fail["causes"].items()]},
        "sweep-summary": {k: truth["sweep-summary"][k] for k in ("per_arm", "best_arm", "exclude")},
        "check-prediction": {k: truth["check-prediction"][k] for k in ("verdict", "effect", "ci")},
        "find-runs": {"runs": truth["find-runs"]["ids"]},
        "fastest": {k: truth["fastest"][k] for k in ("lr", "step")},
    }
    return truth, answers


def test_shipped_truth_shapes(
    tasks: dict[str, grade.Task], seed7: tuple[dict, dict], project: Path
) -> None:
    """Every check's truth key exists in the real truth, and answers copied from it score 1."""
    truth, answers = seed7
    answers["failures"]["runs"] = [
        {"id": r["id"], "cause": {"diverged": "diverged", "killed": "killed"}[r["cause"]]}
        for r in answers["failures"]["runs"]
    ]
    for task in tasks.values():
        assert all(
            spec["truth"] in truth[task.id] for spec in task.checks.values() if "truth" in spec
        )
    for task_id, answer in answers.items():
        assert grade.grade(tasks[task_id], reply(answer), truth[task_id], project).correct, task_id
    rows = truth["table"]["rows"]
    lines = ["run_id,lr,seed,finished,val_acc"] + [
        f"{r['id']},{r['lr']!r},{r['seed']},{'yes' if r['finished'] else 'no'},"
        f"{'' if r['val_acc'] is None else repr(r['val_acc'])}"
        for r in rows
    ]
    (project / "table.csv").write_text("\n".join(lines) + "\n")
    for task_id in ("table", "chart"):
        assert grade.grade(tasks[task_id], reply(CORRECT[task_id]), truth[task_id], project).correct
