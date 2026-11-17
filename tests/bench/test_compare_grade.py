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
sys.path.insert(0, str(COMPARE.parent))

import data  # noqa: E402
import formats  # noqa: E402
import grade  # noqa: E402
import score  # noqa: E402
import truth as truth_module  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 16
IDS = [
    "20261020-080300-aaaaaaaa",
    "20261020-081000-bbbbbbbb",
    "20261020-082000-cccccccc",
    "20261021-090000-dddddddd",
]

TRUTH: dict[str, dict[str, Any]] = {
    "best-config": {
        "best_lr": 0.0003,
        "runner_up_lr": 0.001,
        "difference": 0.0078,
        "ci": [0.0019, 0.0137],
        "significant": True,
    },
    "failures": {
        "ids": sorted([IDS[0], IDS[1], IDS[3]]),
        "causes": {IDS[0]: "diverged", IDS[1]: "killed", IDS[3]: "oom"},
        "reruns": {IDS[0]: None, IDS[1]: IDS[2], IDS[3]: "20261021-091000-eeeeeeee"},
    },
    "sweep-summary": {
        "per_arm": {"small": 1.0164, "medium": 0.9267, "large": 0.9118},
        "best_arm": "large",
        "exclude": [IDS[2]],
        "per_arm_final": {"small": 1.0005, "medium": 0.9267, "large": 0.8404},
    },
    "check-prediction": {
        "effect": 0.3985,
        "ci": [0.2734, 0.5236],
        "seeds": [0, 1, 2],
        "threshold": 0.2,
        "verdict": "confirmed",
    },
    "chart": {"points": []},
    "find-runs": {"ids": IDS[:3]},
    "fastest": {"lr": 0.001, "step": 840.0},
    "table": {
        "rows": [
            {
                "id": IDS[0],
                "lr": 3e-05,
                "seed": 0,
                "finished": True,
                "superseded": False,
                "val_acc": 0.871044,
            },
            {
                "id": IDS[1],
                "lr": 0.0003,
                "seed": 1,
                "finished": False,
                "superseded": True,
                "val_acc": 0.5,
            },
            {
                "id": IDS[2],
                "lr": 0.003,
                "seed": 2,
                "finished": False,
                "superseded": False,
                "val_acc": None,
            },
        ]
    },
}

CORRECT: dict[str, dict[str, Any]] = {
    "best-config": {
        "best_lr": 3e-4,
        "runner_up_lr": 1e-3,
        "difference": 0.0079,
        "significant": True,
    },
    "failures": {
        "runs": [
            {"id": IDS[0], "cause": "loss diverged to NaN", "rerun": None},
            {"id": IDS[1], "cause": "job was killed (SIGTERM)", "rerun": IDS[2]},
            {"id": IDS[3], "cause": "CUDA out of memory", "rerun": "20261021-091000-eeeeeeee"},
        ]
    },
    "sweep-summary": {
        "per_arm": {"small": 1.0165, "medium": 0.92672, "large": 0.9119},
        "best_arm": "large",
        "exclude": [IDS[2]],
    },
    "check-prediction": {"verdict": "confirmed", "effect": 0.399, "ci": [0.274, 0.523]},
    "chart": {"file": "fig.png"},
    "find-runs": {"runs": IDS[:3]},
    "fastest": {"lr": 0.001, "step": 842},
    "table": {"file": "table.csv"},
}

WRONG: dict[str, dict[str, Any]] = {
    "best-config": {
        "best_lr": 1e-3,
        "runner_up_lr": 3e-4,
        "difference": 0.0015,
        "significant": False,
    },
    "failures": {
        "runs": [
            {"id": IDS[0], "cause": "loss diverged to NaN", "rerun": None},
            {"id": IDS[1], "cause": "job was killed (SIGTERM)", "rerun": None},
        ]
    },
    "sweep-summary": {
        "per_arm": {"small": 1.0005, "medium": 0.9267, "large": 0.8404},
        "best_arm": "large",
        "exclude": [IDS[2]],
    },
    "check-prediction": {"verdict": "confirmed", "effect": 0.4024, "ci": [0.2934, 0.5115]},
    "chart": {},
    "find-runs": {"runs": IDS[:2] + ["20261020-099999-dddddddd"]},
    "fastest": {"lr": 0.003, "step": 480},
    "table": {"file": "table.csv"},
}

TABLE = """run_id,lr,seed,finished,superseded,val_acc
{a},3e-05,0,yes,no,0.871044
{b},0.0003,1,no,yes,0.5
{c},0.003,2,no,no,
"""


def reply(answer: dict[str, Any] | None, *, before: str = "Done.") -> str:
    """Write a reply that ends with a json block.

    :param answer: The block's content, or ``None`` for a reply without a block.
    :param before: The prose before the block.
    :return: The reply text."""
    if answer is None:
        return before
    return f"{before}\n\n```json\n{json.dumps(answer)}\n```\n"


@pytest.fixture(autouse=True)
def judge(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Stub the judge model: it answers yes to all seven chart items and records every call.

    :param monkeypatch: Replaces ``score.ask``.
    :return: One dict per call with the prompt, the model, the tools and the folder's files."""
    calls: list[dict[str, Any]] = []

    def ask(prompt: str, folder: Path, *, tools: str, model: str = score.JUDGE) -> dict[str, Any]:
        calls.append(
            {
                "prompt": prompt,
                "model": model,
                "tools": tools,
                "files": sorted(p.name for p in folder.iterdir()),
            }
        )
        return {"items": [{"item": i, "yes": True, "why": f"ok {i}"} for i in range(1, 8)]}

    monkeypatch.setattr(score, "ask", ask)
    return calls


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
            TABLE.format(a=IDS[0], b=IDS[1], c=IDS[2]).replace("0.0003,1,no,yes", "0.0003,1,no,no")
        )
    result = grade.grade(tasks[task_id], reply(WRONG[task_id]), TRUTH[task_id], project)
    assert result.score < 1.0 and not result.correct, result.checks


def test_failure_checks_apart(tasks: dict[str, grade.Task], project: Path) -> None:
    """A vague cause, or a rerun left out, fails the matching check only."""
    answer = {"runs": [dict(r) for r in CORRECT["failures"]["runs"]]}
    answer["runs"][0]["cause"] = "failed"
    result = grade.grade(tasks["failures"], reply(answer), TRUTH["failures"], project)
    assert result.checks == {"ids": 1.0, "causes": 0.0, "reruns": 1.0}
    answer = {"runs": [dict(r) for r in CORRECT["failures"]["runs"]]}
    answer["runs"][1]["rerun"] = None
    result = grade.grade(tasks["failures"], reply(answer), TRUTH["failures"], project)
    assert result.checks == {"ids": 1.0, "causes": 1.0, "reruns": 0.0}


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
    answer = {"runs": [form.format(id=i) for i in IDS[:3]]}
    assert grade.grade(tasks["find-runs"], reply(answer), TRUTH["find-runs"], project).correct


def test_find_runs_f1(tasks: dict[str, grade.Task], project: Path) -> None:
    """The score of ``find-runs`` is the F1 of the two sets."""
    answer = {"runs": IDS[:2]}
    result = grade.grade(tasks["find-runs"], reply(answer), TRUTH["find-runs"], project)
    assert result.score == pytest.approx(0.8)


def test_cause_words(tasks: dict[str, grade.Task], project: Path) -> None:
    """``failed`` alone is no cause; a divergence, kill or memory word is."""
    check = tasks["failures"].checks["causes"]
    expected = TRUTH["failures"]["causes"]

    def passes(first: str, second: str, third: str = "OOM") -> float:
        answer = {
            "runs": [
                {"id": IDS[0], "cause": first},
                {"id": IDS[1], "cause": second},
                {"id": IDS[3], "cause": third},
            ]
        }
        return grade.run_check("causes", check, answer, TRUTH["failures"], project)

    assert expected == {IDS[0]: "diverged", IDS[1]: "killed", IDS[3]: "oom"}
    assert passes("failed", "failed") == 0.0
    assert passes("failed: non-finite loss", "stopped by SIGTERM") == 1.0
    assert passes("FloatingPointError", "JOB CANCELLED", "ran out of GPU memory") == 1.0
    assert passes("loss became inf", "killed", "torch.OutOfMemoryError") == 1.0
    assert passes("loss became inf", "killed", "crashed") == 0.0
    assert passes("killed", "diverged") == 0.0
    assert passes("information", "failed") == 0.0


def test_rerun_forms(tasks: dict[str, grade.Task], project: Path) -> None:
    """No rerun may be written as null, an empty string or none; a rerun id in any id form."""
    check = tasks["failures"].checks["reruns"]
    runs = CORRECT["failures"]["runs"]
    for none in (None, "", "null", "None"):
        for later, ok in (
            (f"scaling/lr-sweep-2/{IDS[2]}", True),
            (IDS[3], False),
            (None, False),
        ):
            answer = {"runs": [{**runs[0], "rerun": none}, {**runs[1], "rerun": later}, runs[2]]}
            assert grade.run_check("reruns", check, answer, TRUTH["failures"], project) == ok
    answer = {"runs": [{**runs[0], "rerun": IDS[2]}, *runs[1:]]}
    assert grade.run_check("reruns", check, answer, TRUTH["failures"], project) == 0.0
    assert grade.run_check("reruns", check, {"runs": runs[:2]}, TRUTH["failures"], project) == 0.0


def test_difference_tolerance(tasks: dict[str, grade.Task], project: Path) -> None:
    """The difference passes within 5 % and fails beyond."""
    for value, ok in ((0.0078 * 1.04, True), (0.0078 * 1.07, False), (0.0078 * 0.9, False)):
        answer = {**CORRECT["best-config"], "difference": value}
        result = grade.grade(tasks["best-config"], reply(answer), TRUTH["best-config"], project)
        assert (result.checks["difference"] == 1.0) is ok


def test_ci_bounds(tasks: dict[str, grade.Task], project: Path) -> None:
    """Both bounds of the interval must lie within 0.005 of the true ones, in either order."""
    for ci, ok in (
        ([0.274, 0.523], True),
        ([0.523, 0.274], True),
        ([0.2934, 0.5115], False),
        ([0.28, 0.52], False),
        ([0.3985], False),
    ):
        answer = {**CORRECT["check-prediction"], "ci": ci}
        result = grade.grade(
            tasks["check-prediction"], reply(answer), TRUTH["check-prediction"], project
        )
        assert (result.checks["ci"] == 1.0) is ok, ci


def test_per_arm_needs_every_arm(tasks: dict[str, grade.Task], project: Path) -> None:
    """A missing arm, or one off by more than 0.2 %, fails ``per_arm``."""
    base = CORRECT["sweep-summary"]
    for per_arm, ok in (
        (base["per_arm"], True),
        ({"small": 1.0, "medium": 0.927}, False),
        ({**base["per_arm"], "large": 0.9118 * 1.003}, False),
        (TRUTH["sweep-summary"]["per_arm_final"], False),
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


def test_chart_judge_items(
    tasks: dict[str, grade.Task], project: Path, judge: list[dict[str, Any]]
) -> None:
    """The seven items count as checks next to the file; the pinned model judges the image."""
    chart = tasks["chart"]
    assert len(chart.judge) == 7
    result = grade.grade(chart, reply({"file": "fig.png"}), TRUTH["chart"], project, model="pinned")
    assert list(result.checks) == ["file", *(f"judge{i}" for i in range(1, 8))]
    assert result.correct and result.notes["judge2"] == "ok 2"
    assert [c["model"] for c in judge] == ["pinned"] and judge[0]["tools"] == "Read"
    for i, item in enumerate(chart.judge, 1):
        assert f"{i}. {item}" in judge[0]["prompt"]


def test_chart_judge_marks(
    tasks: dict[str, grade.Task], project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A no scores 0 on its own item; marks as text and item numbers as text count."""
    marks = [{"item": 1, "yes": True}, {"item": "2", "yes": "no"}, {"item": 3, "yes": "Yes"}]
    marks += [{"item": i, "yes": i % 2 == 0, "why": f"w{i}"} for i in range(4, 8)]
    chart, text = tasks["chart"], reply({"file": "fig.png"})
    monkeypatch.setattr(score, "ask", lambda *a, **k: {"items": marks})
    result = grade.grade(chart, text, TRUTH["chart"], project)
    judged = [result.checks[f"judge{i}"] for i in range(1, 8)]
    assert result.checks["file"] == 1.0 and judged == [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0]
    assert result.notes == {f"judge{i}": f"w{i}" for i in range(4, 8)}


def test_chart_judge_retry(
    tasks: dict[str, grade.Task], project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A judge answer lacking a usable mark is asked again; failing twice raises, never scores 0."""
    full = {"items": [{"item": i, "yes": True} for i in range(1, 8)]}
    partial = {"items": full["items"][:3] + [{"item": 4, "yes": "maybe"}]}
    chart, text = tasks["chart"], reply({"file": "fig.png"})
    for answers, ok in (
        ([{"error": "no JSON object"}, full], True),
        ([partial, full], True),
        ([partial, {"error": "no JSON object"}], False),
    ):
        calls = iter(answers)

        def ask(*args: Any, calls: Any = calls, **kwargs: Any) -> dict[str, Any]:
            return next(calls)

        monkeypatch.setattr(score, "ask", ask)
        if ok:
            assert grade.grade(chart, text, TRUTH["chart"], project).correct
        else:
            with pytest.raises(grade.JudgeFailed, match="marks for"):
                grade.grade(chart, text, TRUTH["chart"], project)


@pytest.mark.parametrize(
    "text",
    [
        '{"items": [{"item": 1, "yes": true}]}',
        'Looking at {chart.png}:\n```json\n{"items": [{"item": 1, "yes": true}]}\n```\nDone {ok}.',
    ],
)
def test_judge_json_after_prose(text: str) -> None:
    """The judge's object is found also after prose with braces and before trailing text.

    :param text: The judge's answer."""
    assert score.first_object(text) == {"items": [{"item": 1, "yes": True}]}


def test_not_png(tasks: dict[str, grade.Task], project: Path, judge: list[dict[str, Any]]) -> None:
    """A PDF or SVG instead of a PNG scores the file 0 and is not judged."""
    for name, content in (("fig.pdf", b"%PDF-1.4"), ("fig.svg", b"<svg/>")):
        (project / name).write_bytes(content)
        result = grade.grade(tasks["chart"], reply({"file": name}), TRUTH["chart"], project)
        assert result.checks["file"] == 0.0 and result.score == 0.0, name
    assert judge == []


def test_no_block_not_judged(
    tasks: dict[str, grade.Task], project: Path, judge: list[dict[str, Any]]
) -> None:
    """A reply without a json block scores 0 everywhere and costs no judge call."""
    result = grade.grade(tasks["chart"], "Here it is.", TRUTH["chart"], project)
    assert result.score == 0.0 and len(result.checks) == 8 and judge == []


def test_judge_sees_only_image(
    tasks: dict[str, grade.Task], project: Path, judge: list[dict[str, Any]]
) -> None:
    """The judge's folder holds one image; the project's other files and path stay out of reach."""
    grade.grade(tasks["chart"], reply({"file": "fig.png"}), TRUTH["chart"], project)
    assert judge[0]["files"] == ["chart.png"]
    assert str(project) not in judge[0]["prompt"] and "table.csv" not in judge[0]["prompt"]


def test_judge_usage_limit(
    tasks: dict[str, grade.Task], project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A usage-limit answer raises, so the session stays ungraded instead of scoring 0."""

    def ask(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise score.JudgeStalled("You've hit your limit")

    monkeypatch.setattr(score, "ask", ask)
    with pytest.raises(score.JudgeStalled):
        grade.grade(tasks["chart"], reply({"file": "fig.png"}), TRUTH["chart"], project)


def test_table_checks(tasks: dict[str, grade.Task], project: Path) -> None:
    """The table is graded on its rows, values, finished and superseded flags apart."""
    table, truth = tasks["table"], TRUTH["table"]
    path = project / "table.csv"
    good = TABLE.format(a=IDS[0], b=IDS[1], c=IDS[2])

    def checks(text: str) -> dict[str, float]:
        path.write_text(text)
        return grade.grade(table, reply({"file": "table.csv"}), truth, project).checks

    assert set(checks(good).values()) == {1.0}
    assert checks(good.replace(f"{IDS[2]},0.003,2,no,no,\n", ""))["rows"] == 0.0
    assert checks(good.replace("0.871044", "0.8710"))["values"] == 0.0
    assert checks(good.replace("0.871044", "0.8710441"))["values"] == 1.0
    assert checks(good.replace(",no,yes,0.5", ",yes,yes,0.5")) == {
        "file": 1.0,
        "rows": 1.0,
        "values": 1.0,
        "finished": 0.0,
        "superseded": 1.0,
    }
    assert checks(good.replace(",no,yes,0.5", ",no,no,0.5")) == {
        "file": 1.0,
        "rows": 1.0,
        "values": 1.0,
        "finished": 1.0,
        "superseded": 0.0,
    }
    assert checks(good.replace(",0,yes,", ",0,finished,").replace(",1,no,", ",1,killed,")) == {
        k: 1.0 for k in table.checks
    }
    assert checks(good.replace("0.003,2,no,no,", "0.003,2,no,no,nan"))["values"] == 1.0
    assert checks(good.replace("0.003,2,no,no,", "0.003,2,no,no,0.9"))["values"] == 0.0
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
        "failures": {
            "runs": [
                {"id": i, "cause": c, "rerun": fail["reruns"][i]} for i, c in fail["causes"].items()
            ]
        },
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
        {
            **r,
            "cause": {"diverged": "diverged", "killed": "killed", "oom": "out of memory"}[
                r["cause"]
            ],
        }
        for r in answers["failures"]["runs"]
    ]
    for task in tasks.values():
        assert all(
            spec["truth"] in truth[task.id] for spec in task.checks.values() if "truth" in spec
        )
    for task_id, answer in answers.items():
        assert grade.grade(tasks[task_id], reply(answer), truth[task_id], project).correct, task_id
    rows = truth["table"]["rows"]
    lines = ["run_id,lr,seed,finished,superseded,val_acc"] + [
        f"{r['id']},{r['lr']!r},{r['seed']},{'yes' if r['finished'] else 'no'},"
        f"{'yes' if r['superseded'] else 'no'},"
        f"{'' if r['val_acc'] is None else repr(r['val_acc'])}"
        for r in rows
    ]
    (project / "table.csv").write_text("\n".join(lines) + "\n")
    for task_id in ("table", "chart"):
        assert grade.grade(tasks[task_id], reply(CORRECT[task_id]), truth[task_id], project).correct


def rows(*pairs: tuple[str, Any]) -> list[dict[str, Any]]:
    """Objects with an id and a step.

    :param pairs: The ids and steps.
    :return: One object per pair."""
    return [{"id": i, "step": v} for i, v in pairs]


def test_keyed_scores_per_key() -> None:
    """Right keys over the larger of the given and expected counts; ids reduce to their last part."""
    expected = rows(("a", 10), ("b", 20), ("c", 30), ("d", 40))
    assert (
        grade.keyed(
            rows(("g/a", 10), ("b", 20), ("c", 30), ("d", 40)), expected, key="id", field="step"
        )
        == 1
    )
    assert grade.keyed(rows(("a", 10), ("b", 21)), expected, key="id", field="step") == 0.25
    extra = rows(("a", 10), ("b", 20), ("c", 30), ("d", 40), ("e", 1), ("f", 2))
    assert grade.keyed(extra, expected, key="id", field="step") == pytest.approx(4 / 6)
    assert (
        grade.keyed({"a": {"step": 10}, "b": {"step": 20}}, expected, key="id", field="step") == 0.5
    )
    assert grade.keyed(expected, {x["id"]: x for x in expected}, key="id", field="step") == 1


def test_keyed_tolerance() -> None:
    """Without a tolerance the field is equal, with ``abs`` or ``rel`` it is close."""
    expected = [{"id": "a", "v": 100.0}, {"id": "b", "v": 0.001}]
    given = [{"id": "a", "v": 101.0}, {"id": "b", "v": 0.001}]
    assert grade.keyed(given, expected, key="id", field="v") == 0.5
    assert grade.keyed(given, expected, key="id", field="v", rel=0.02) == 1
    assert grade.keyed(given, expected, key="id", field="v", abs=0.5) == 0.5
    assert grade.keyed(given, expected, key="id", field="v", abs=0) == 0.5


def test_keyed_empty() -> None:
    """Both empty is right; one empty is wrong."""
    assert grade.keyed([], [], key="id", field="step") == 1
    assert grade.keyed([], rows(("a", 1)), key="id", field="step") == 0
    assert grade.keyed(rows(("a", 1)), [], key="id", field="step") == 0


def test_keyed_duplicates() -> None:
    """A key given twice counts once; a key without the field is wrong, not an error."""
    expected = rows(("a", 10), ("b", 20))
    assert grade.keyed(rows(("a", 10), ("a", 10), ("b", 20)), expected, key="id", field="step") == 1
    assert grade.keyed(rows(("a", 10), ("a", 10)), expected, key="id", field="step") == 0.5
    assert grade.keyed([{"id": "a"}, *rows(("b", 20))], expected, key="id", field="step") == 0.5


def test_keyed_check_in_a_task(tmp_path: Path) -> None:
    """A task file with a keyed check scores through ``grade``; a malformed answer scores 0."""
    (tmp_path / "x.yaml").write_text(
        "prompt: p\nanswer: '{}'\ntime_limit_s: 1\ndata: wide\nchecks:\n"
        "  runs: {kind: keyed, truth: runs, key: id, field: step, abs: 0}\n"
    )
    task = grade.load_tasks(tmp_path)["x"]
    truth = {"runs": rows(("a", 10), ("b", 20))}

    assert task.data == "wide"
    assert (
        grade.grade(task, reply({"runs": rows(("g/a", 10), ("b", 20))}), truth, tmp_path).score == 1
    )
    assert grade.grade(task, reply({"runs": "a, b"}), truth, tmp_path).score == 0
    assert grade.grade(task, reply({"runs": [1, 2]}), truth, tmp_path).score == 0
