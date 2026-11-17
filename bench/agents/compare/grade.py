"""The comparison's tasks and their grader: an agent's last json block against the truth."""

import csv
import json
import math
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

TASKS = Path(__file__).resolve().parent / "tasks"
AGENTS = Path(__file__).resolve().parents[1]
SETUPS = ["mcp", "cli", "files", "tensorboard"]
PNG = b"\x89PNG\r\n\x1a\n"
COLUMNS = ("run_id", "lr", "seed", "finished", "superseded", "val_acc")
YES = {"yes", "y", "true", "1", "finished", "completed", "complete", "done", "superseded"}
NONE = {"", "null", "none", "no", "-"}
KINDS = {
    "equal",
    "close",
    "set",
    "f1",
    "contains",
    "interval",
    "cause",
    "rerun",
    "file",
    "table_ids",
    "table_values",
    "table_flag",
    "keyed",
}
# a judge's ``yes`` given as text; a bool is used as it is, anything else is no usable mark.
MARKS = {"yes": True, "true": True, "no": False, "false": False}


class JudgeFailed(Exception):
    """The judge gave no usable mark for some checklist item, also when asked a second time."""


@dataclass(kw_only=True)
class Task:
    """One researcher task: the prompt, the answer shape, the checks and the limits."""

    id: str
    prompt: str
    answer: str
    checks: dict[str, dict[str, Any]]
    time_limit_s: int
    data: str = "s"
    setups: list[str] = field(default_factory=lambda: list(SETUPS))
    judge: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, file: Path) -> "Task":
        """Read a task from ``tasks/<id>.yaml``; the prompt ends with the answer line.

        :param file: The task file; its stem is the task id.
        :return: The task.
        :raises ValueError: When a check has an unknown kind; grading would score it 0 silently."""
        data = yaml.safe_load(file.read_text())
        if unknown := {c["kind"] for c in data["checks"].values()} - KINDS:
            raise ValueError(f"{file.name}: unknown check kinds {sorted(unknown)}")
        answer = data["answer"].strip()
        data["prompt"] = (
            f"{data['prompt'].strip()}\n\nEnd your reply with a fenced json block: {answer}"
        )
        return cls(id=file.stem, **data)


@dataclass(kw_only=True)
class Grade:
    """The result of grading one answer; ``checks`` maps each check to its score in [0, 1]."""

    score: float
    correct: bool
    checks: dict[str, float]
    notes: dict[str, str] = field(default_factory=dict)


def load_tasks(directory: Path = TASKS) -> dict[str, Task]:
    """Read every task of a folder.

    :param directory: The folder with the task files.
    :return: The tasks by id, in file order."""
    return {t.id: t for t in (Task.load(f) for f in sorted(directory.glob("*.yaml")))}


def answer_json(text: str) -> dict[str, Any] | None:
    """Parse the last fenced json block of a reply.

    :param text: The agent's reply.
    :return: The block as a dict, or ``None`` when there is none or the last one is malformed."""
    fences = re.findall(r"```([^`\n]*)\n(.*?)```", text, re.DOTALL)
    blocks = [
        body
        for info, body in fences
        if (info.split() or [""])[0].lower() in ("", "json") and body.lstrip().startswith("{")
    ]
    if not blocks:
        return None
    try:
        answer = json.loads(blocks[-1])
    except ValueError:
        return None
    return answer if isinstance(answer, dict) else None


def grade(
    task: Task,
    answer_text: str,
    truth: dict[str, Any],
    project: Path,
    *,
    model: str | None = None,
) -> Grade:
    """Grade a reply: the score is the share of checks passed, a missing block fails all of them.

    A task with ``judge`` items adds one check per item (``judge1``, ...), asked of a model that
    sees only the PNG the answer names under ``file``; they score 0 when the ``file`` check fails.

    :param task: The task.
    :param answer_text: The agent's last message.
    :param truth: The expected values of this task (``truth.compute(...)[task.id]``).
    :param project: The folder the agent worked in; files it names must lie inside.
    :param model: The pinned judge model id; the harness default when ``None``.
    :return: The grade.
    :raises score.JudgeStalled: When the judge hits its usage limit; the session stays ungraded.
    :raises JudgeFailed: When the judge gives no usable mark for an item; it stays ungraded."""
    answer = answer_json(answer_text)
    checks = {
        name: 0.0 if answer is None else run_check(name, spec, answer, truth, project)
        for name, spec in task.checks.items()
    }
    notes: dict[str, str] = {}
    if task.judge:
        image = project_png(project, answer) if checks.get("file") else None
        marks = judge_chart(image, task.judge, model=model) if image else {}
        for i in range(1, len(task.judge) + 1):
            checks[f"judge{i}"] = float(marks.get(i, {}).get("yes", False))
            if why := marks.get(i, {}).get("why"):
                notes[f"judge{i}"] = why
    score = sum(checks.values()) / len(checks)
    return Grade(score=score, correct=score == 1, checks=checks, notes=notes)


def project_png(project: Path, answer: dict[str, Any] | None) -> Path | None:
    """Find the PNG an answer names.

    :param project: The agent's folder.
    :param answer: The parsed answer.
    :return: The path, or ``None`` when it names no file inside the project."""
    try:
        return project_file(project, (answer or {}).get("file"))
    except (ValueError, OSError):
        return None


def judge_chart(image: Path, items: list[str], *, model: str | None) -> dict[int, dict[str, Any]]:
    """Ask the judge about each checklist item from the figure alone, a second time if needed.

    The judge runs in a fresh folder that holds a copy of the image and nothing else.

    :param image: The agent's PNG.
    :param items: What the figure must show, one statement each.
    :param model: The judge model id; the harness default when ``None``.
    :return: The judge's marks by item number (from 1) as ``{yes, why}``, one for every item.
    :raises score.JudgeStalled: When the judge hits its usage limit.
    :raises JudgeFailed: When both answers lack a usable mark for some item."""
    sys.path.append(str(AGENTS))
    import score

    listed = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
    prompt = (
        "Read the image chart.png with the Read tool. It is a figure an analyst made from "
        "experiment logs. Answer each checklist item about what the figure shows, strictly: yes "
        f"only if the image clearly shows it.\n{listed}\n"
        'Answer with JSON only: {"items": [{"item": int, "yes": bool, "why": str}]}'
    )
    for _ in range(2):
        with tempfile.TemporaryDirectory(prefix="bt-judge-") as folder:
            shutil.copyfile(image, Path(folder) / "chart.png")
            answer = score.ask(prompt, Path(folder), tools="Read", model=model or score.JUDGE)
        if len(marks := judge_marks(answer, len(items))) == len(items):
            return marks
    raise JudgeFailed(f"marks for {sorted(marks)} of {len(items)} items: {str(answer)[:300]}")


def judge_marks(answer: dict[str, Any], count: int) -> dict[int, dict[str, Any]]:
    """Read the usable marks of a judge's answer.

    :param answer: The answer as ``score.ask`` parsed it.
    :param count: The number of checklist items.
    :return: The marks by item number in ``1..count`` as ``{yes, why}``; an item numbered as
        text counts, a mark that is neither a bool nor yes/no/true/false does not."""
    marks = {}
    for mark in answer.get("items") or []:
        if not isinstance(mark, dict):
            continue
        try:
            item = int(mark.get("item"))
        except (TypeError, ValueError):
            continue
        if isinstance(yes := mark.get("yes"), str):
            yes = MARKS.get(yes.strip().casefold())
        if isinstance(yes, bool) and 1 <= item <= count:
            marks[item] = {"yes": yes, "why": str(mark.get("why") or "")}
    return marks


def run_check(
    name: str, spec: dict[str, Any], answer: dict[str, Any], truth: dict[str, Any], project: Path
) -> float:
    """Run one check; an answer of the wrong shape scores 0.

    :param name: The check's name; the answer key it reads unless the spec has a ``key``.
    :param spec: The check from the task file.
    :param answer: The parsed answer.
    :param truth: The expected values of the task.
    :param project: The agent's folder.
    :return: 1 for a pass, 0 for a fail, the F1 for ``f1``."""
    given = answer.get(name if spec["kind"] == "keyed" else spec.get("key", name))
    expected = truth[spec["truth"]] if "truth" in spec else None
    try:
        match spec["kind"]:
            case "equal":
                return float(same(given, expected))
            case "close":
                return float(
                    close(given, expected, rel=spec.get("rel", 0.0), tol=spec.get("abs", 0.0))
                )
            case "set":
                return float(ids(given) == ids(expected))
            case "f1":
                return f1(ids(given), ids(expected))
            case "contains":
                low, high = sorted(number(v) for v in given)
                return float(len(given) == 2 and low <= number(expected) <= high)
            case "interval":
                low, high = sorted(number(v) for v in given)
                return float(
                    len(given) == 2
                    and all(
                        abs(g - t) <= spec["abs"]
                        for g, t in zip((low, high), expected, strict=True)
                    )
                )
            case "cause":
                return float(cause(given, expected, spec["patterns"]))
            case "rerun":
                return float(rerun(given, expected))
            case "file":
                return float(file_ok(project_file(project, given), spec["format"]))
            case "table_ids":
                rows = read_table(project_file(project, given))
                return float(
                    len(rows) == len(expected)
                    and {trail(r["run_id"]) for r in rows} == ids(expected)
                )
            case "table_values":
                return float(table_values(read_table(project_file(project, given)), expected, spec))
            case "keyed":
                return keyed(
                    given,
                    expected,
                    key=spec["key"],
                    field=spec["field"],
                    abs=spec.get("abs"),
                    rel=spec.get("rel"),
                )
            case "table_flag":
                rows = read_table(project_file(project, given))
                column = spec["column"]
                flags = {trail(r["run_id"]): r[column].strip().casefold() in YES for r in rows}
                return float(all(flags[t["id"]] == t[column] for t in expected))
            case _:
                raise ValueError(f"unknown check kind {spec['kind']!r}")
    except (TypeError, ValueError, KeyError, AttributeError, OSError):
        return 0.0


def keyed(
    given: Any,
    expected: Any,
    *,
    key: str,
    field: str,
    abs: float | None = None,
    rel: float | None = None,
) -> float:
    """Score a list of objects by key: per expected key, one field is compared.

    A field is compared with ``close`` when a tolerance is given, else with ``same``. A key given
    twice counts once (the first object); a key without the field is wrong.

    :param given: The answer's objects, or a dict of key to object.
    :param expected: The truth in the same shapes.
    :param key: The field that names an object, e.g. ``id``.
    :param field: The field to compare.
    :param abs: Absolute tolerance, if any.
    :param rel: Relative tolerance, if any.
    :return: The keys answered right over the larger of the given and the expected keys; 1 when both
        are empty.
    :raises TypeError: When given is neither a list nor a dict."""
    answered, wanted = keyed_rows(given, key), keyed_rows(expected, key)
    if not (answered or wanted):
        return 1.0
    right = 0
    for name, row in wanted.items():
        if name not in answered:
            continue
        try:
            if abs is None and rel is None:
                right += same(answered[name][field], row[field])
            else:
                right += close(answered[name][field], row[field], rel=rel or 0.0, tol=abs or 0.0)
        except (TypeError, ValueError, KeyError):
            continue
    return right / max(len(answered), len(wanted))


def keyed_rows(value: Any, key: str) -> dict[str, dict[str, Any]]:
    """Index objects by their key, run ids reduced to their last part; the first of a key wins.

    :param value: A list of objects, or a dict of key to object.
    :param key: The field that names an object.
    :return: The objects by key; entries without a key are left out.
    :raises TypeError: When it is neither a list nor a dict."""
    match value:
        case dict():
            pairs = [(k, v | {key: k} if isinstance(v, dict) else v) for k, v in value.items()]
        case list():
            pairs = [(v.get(key), v) for v in value if isinstance(v, dict)]
        case _:
            raise TypeError(f"not a list of objects: {value!r}")
    rows: dict[str, dict[str, Any]] = {}
    for name, row in pairs:
        if name is not None and isinstance(row, dict):
            rows.setdefault(trail(name), row)
    return rows


def number(value: Any) -> float:
    """Read a number, also from text such as ``3e-4``; a bool is not a number.

    :param value: A json value.
    :return: The float.
    :raises TypeError: For anything that is not a number or numeric text."""
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        raise TypeError(f"not a number: {value!r}")
    return float(value)


def same(given: Any, expected: Any) -> bool:
    """Compare equal: numbers as floats (1e-9 relative), booleans and text exactly.

    :param given: The answer's value.
    :param expected: The truth.
    :return: Whether they are equal."""
    if isinstance(expected, bool):
        return str(given).strip().casefold() == str(expected).casefold()
    if isinstance(expected, int | float):
        return math.isclose(number(given), expected, rel_tol=1e-9)
    return str(given).strip().casefold() == str(expected).strip().casefold()


def close(given: Any, expected: Any, *, rel: float, tol: float) -> bool:
    """Compare within a relative and an absolute tolerance; a dict is compared key by key.

    :param given: The answer's value, or a dict of them.
    :param expected: The truth, or a dict of them; every key must be answered.
    :param rel: Relative tolerance.
    :param tol: Absolute tolerance.
    :return: Whether every value is within the tolerance of either kind."""
    if isinstance(expected, dict):
        return all(k in given and close(given[k], v, rel=rel, tol=tol) for k, v in expected.items())
    return abs(number(given) - expected) <= max(rel * abs(expected), tol)


def trail(run_id: Any) -> str:
    """Reduce a run id to its last path part, so ``group/id`` and ``id`` match.

    :param run_id: A run id as the agent wrote it.
    :return: The id."""
    return str(run_id).strip().strip("`").rstrip("/").rsplit("/", 1)[-1]


def ids(value: Any) -> set[str]:
    """Read a list of run ids, or of dicts with an ``id``.

    :param value: The list.
    :return: The ids.
    :raises TypeError: When it is not a list."""
    if not isinstance(value, list):
        raise TypeError(f"not a list: {value!r}")
    return {trail(v["id"] if isinstance(v, dict) else v) for v in value}


def f1(given: set[str], expected: set[str]) -> float:
    """Score two sets by F1; two empty sets are a perfect match.

    :param given: The answered ids.
    :param expected: The true ids.
    :return: The F1 in [0, 1]."""
    hits = len(given & expected)
    if not given and not expected:
        return 1.0
    return 2 * hits / (len(given) + len(expected))


def cause(given: Any, expected: dict[str, str], patterns: dict[str, str]) -> bool:
    """Check that every run that stopped has a cause worded like the true one.

    :param given: The answer's list of ``{id, cause}``.
    :param expected: The run id mapped to the true cause (a key of ``patterns``).
    :param patterns: The cause mapped to the regex its wording must match.
    :return: Whether every true run has a matching cause."""
    said = {trail(r["id"]): str(r["cause"]) for r in given}
    return all(re.search(patterns[c], said.get(i, ""), re.IGNORECASE) for i, c in expected.items())


def rerun(given: Any, expected: dict[str, str | None]) -> bool:
    """Check that every run that stopped names its completed rerun, or none when there is none.

    :param given: The answer's list of ``{id, rerun}``.
    :param expected: The run id mapped to the id of its completed rerun, or ``None``.
    :return: Whether every true run has the right rerun."""
    said = {trail(r["id"]): r.get("rerun") for r in given}
    for run_id, later in expected.items():
        if run_id not in said:
            return False
        value = said[run_id]
        if later is None:
            if value is not None and str(value).strip().casefold() not in NONE:
                return False
        elif value is None or trail(value) != later:
            return False
    return True


def project_file(project: Path, value: Any) -> Path:
    """Resolve a file the answer names; it must exist inside the project.

    :param project: The agent's folder.
    :param value: The path as the agent wrote it, absolute or relative to the project.
    :return: The resolved path.
    :raises ValueError: When the file lies outside the project.
    :raises OSError: When it does not exist."""
    root = project.resolve()
    path = (root / str(value)).resolve()
    path.relative_to(root)
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def file_ok(path: Path, kind: str) -> bool:
    """Check that a file is a PNG image or a readable table.

    :param path: The file.
    :param kind: ``png`` or ``table``.
    :return: Whether it is."""
    match kind:
        case "png":
            return path.read_bytes().startswith(PNG)
        case "table":
            return bool(read_table(path))
        case _:
            raise ValueError(f"unknown file kind {kind!r}")


def read_table(path: Path) -> list[dict[str, str]]:
    """Read the table an agent wrote; header names are case-insensitive.

    :param path: The file.
    :return: One dict per row with the required columns.
    :raises ValueError: When a required column is missing."""
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [n.strip().casefold() for n in reader.fieldnames or []]
        if missing := set(COLUMNS) - set(reader.fieldnames):
            raise ValueError(f"missing columns {sorted(missing)}")
        return [{k: (v or "") for k, v in row.items() if k} for row in reader]


def table_values(
    rows: list[dict[str, str]], expected: list[dict[str, Any]], spec: dict[str, Any]
) -> bool:
    """Check lr, seed and final val/acc of every true row.

    :param rows: The agent's table.
    :param expected: The true rows (``id``, ``lr``, ``seed``, ``val_acc``).
    :param spec: The check; ``rel`` and ``abs`` bound the val/acc.
    :return: Whether every true row is there with the right values."""
    by_id = {trail(r["run_id"]): r for r in rows}
    for t in expected:
        row = by_id[t["id"]]
        if not (same(row["lr"], t["lr"]) and same(row["seed"], t["seed"])):
            return False
        cell = row["val_acc"].strip()
        if t["val_acc"] is None:
            if cell and not math.isnan(number(cell)):
                return False
        elif not close(cell, t["val_acc"], rel=spec["rel"], tol=spec["abs"]):
            return False
    return True
