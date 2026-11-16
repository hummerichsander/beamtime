"""The comparison's tasks and their grader: an agent's last json block against the truth."""

import csv
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

TASKS = Path(__file__).resolve().parent / "tasks"
SETUPS = ["mcp", "cli", "files", "tensorboard"]
PNG = b"\x89PNG\r\n\x1a\n"
COLUMNS = ("run_id", "lr", "seed", "finished", "val_acc")
YES = {"yes", "y", "true", "1", "finished", "completed", "complete", "done"}
KINDS = {
    "equal",
    "close",
    "set",
    "f1",
    "contains",
    "cause",
    "file",
    "table_ids",
    "table_values",
    "table_finished",
}


@dataclass(kw_only=True)
class Task:
    """One researcher task: the prompt, the answer shape, the checks and the limits."""

    id: str
    prompt: str
    answer: str
    checks: dict[str, dict[str, Any]]
    time_limit_s: int
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


def grade(task: Task, answer_text: str, truth: dict[str, Any], project: Path) -> Grade:
    """Grade a reply: the score is the share of checks passed, a missing block fails all of them.

    :param task: The task.
    :param answer_text: The agent's last message.
    :param truth: The expected values of this task (``truth.compute(...)[task.id]``).
    :param project: The folder the agent worked in; files it names must lie inside.
    :return: The grade."""
    answer = answer_json(answer_text)
    checks = {
        name: 0.0 if answer is None else run_check(name, spec, answer, truth, project)
        for name, spec in task.checks.items()
    }
    score = sum(checks.values()) / len(checks)
    return Grade(score=score, correct=score == 1, checks=checks)


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
    given = answer.get(spec.get("key", name))
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
            case "cause":
                return float(cause(given, expected, spec["patterns"]))
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
            case "table_finished":
                rows = read_table(project_file(project, given))
                flags = {trail(r["run_id"]): r["finished"].strip().casefold() in YES for r in rows}
                return float(all(flags[t["id"]] == t["finished"] for t in expected))
            case _:
                raise ValueError(f"unknown check kind {spec['kind']!r}")
    except (TypeError, ValueError, KeyError, AttributeError, OSError):
        return 0.0


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
