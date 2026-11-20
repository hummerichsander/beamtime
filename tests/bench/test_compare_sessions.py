"""Tests of the benchmark's session runner (``compare/sessions.py``); no agent runs."""

import dataclasses
import json
import subprocess
import sys
import time
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

import pytest

BENCH = Path(__file__).resolve().parents[2] / "bench" / "agents"
sys.path.insert(0, str(BENCH / "compare"))
sys.path.insert(0, str(BENCH))

import data  # noqa: E402
import grade  # noqa: E402
import sessions  # noqa: E402
import setups  # noqa: E402
import truth  # noqa: E402
from score import JudgeStalled  # noqa: E402

MODEL = "claude-sonnet-5-5"
POPEN = subprocess.Popen
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 16
BEST = {"best_lr": 0.0003, "runner_up_lr": 0.001, "difference": 0.01, "significant": True}
RIGHT = f"Done.\n```json\n{json.dumps(BEST)}\n```"
USAGE = {
    "input_tokens": 10,
    "cache_creation_input_tokens": 200,
    "cache_read_input_tokens": 3000,
    "output_tokens": 40,
}


def init(model: str = MODEL) -> dict[str, Any]:
    """Make the init event of a transcript.

    :param model: The model it reports.
    :return: The event."""
    return {"type": "system", "subtype": "init", "model": model}


def assistant(
    mid: str, *parts: dict[str, Any], usage: dict[str, int] | None = None
) -> dict[str, Any]:
    """Make an assistant event.

    :param mid: The message id.
    :param parts: The content parts.
    :param usage: The message's usage.
    :return: The event."""
    message = {"id": mid, "content": list(parts), "usage": usage or {}}
    return {"type": "assistant", "message": message}


def use(tid: str, name: str, **tool_input: Any) -> dict[str, Any]:
    """Make a ``tool_use`` part.

    :param tid: The call id.
    :param name: The tool.
    :param tool_input: The call's input.
    :return: The part."""
    return {"type": "tool_use", "id": tid, "name": name, "input": tool_input}


def returned(tid: str, error: bool = False) -> dict[str, Any]:
    """Make the user event that carries a tool's result.

    :param tid: The call id.
    :param error: Whether the call failed.
    :return: The event."""
    part = {"type": "tool_result", "tool_use_id": tid, "is_error": error}
    return {"type": "user", "message": {"content": [part]}}


def result(text: str = RIGHT, **fields: Any) -> dict[str, Any]:
    """Make the result event.

    :param text: The final message.
    :param fields: Fields that replace the defaults.
    :return: The event."""
    event = {
        "type": "result",
        "is_error": False,
        "result": text,
        "num_turns": 3,
        "duration_api_ms": 4200,
        "total_cost_usd": 0.12,
        "usage": USAGE,
        "modelUsage": {MODEL: {}},
    }
    return event | fields


def transcript(events: list[dict[str, Any]]) -> str:
    """Write events as stream-json lines.

    :param events: The events.
    :return: The text."""
    return "".join(json.dumps(e) + "\n" for e in events)


def test_jobs() -> None:
    """168 sessions: fourteen tasks, four setups, three seeds; the order is fixed and shuffled."""
    tasks = grade.load_tasks()
    jobs = sessions.make_jobs(tasks, list(setups.SETUPS), [7, 8, 9], 1)

    assert len(jobs) == 168
    assert len({j.name for j in jobs}) == 168
    assert jobs == sessions.make_jobs(tasks, list(setups.SETUPS), [7, 8, 9], 1)
    assert [j.name for j in jobs] != sorted(j.name for j in jobs)
    assert len(sessions.make_jobs(tasks, ["mcp"], [7], 2)) == 28


def test_jobs_respect_task_setups() -> None:
    """A task that names setups runs in those only."""
    task = grade.Task(id="x", prompt="p", answer="a", checks={}, time_limit_s=1, setups=["mcp"])
    jobs = sessions.make_jobs({"x": task}, ["mcp", "cli"], [7], 1)

    assert [j.setup for j in jobs] == ["mcp"]


def test_dry_run(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """The dry run lists 168 sessions with their commands and builds nothing."""
    monkeypatch.setattr(sys, "argv", ["sessions.py", "--dry-run"])
    sessions.main()
    lines = capsys.readouterr().out.splitlines()

    assert lines[-1] == "168 sessions"
    assert len(lines) == 169
    assert sum("--mcp-config" in line for line in lines) == 42
    assert all(
        "--no-session-persistence" in line and "--model sonnet" in line for line in lines[:-1]
    )
    assert all(str(sessions.CLAUDE) in line for line in lines[:-1])


def test_summarize() -> None:
    """The record's measures: tokens, tool counts, errors and Beamtime calls."""
    events = [
        init(),
        assistant("m1", use("a", "mcp__beamtime__runs"), use("b", "Bash", command="ls beamtime/")),
        returned("a"),
        returned("b", error=True),
        assistant("m2", use("c", "Bash", command="cd p && beamtime runs --where x")),
        returned("c"),
        assistant("m3", use("d", "Bash", command="uv run beamtime query x")),
        result(),
    ]
    got = sessions.summarize(events, model=MODEL)

    assert got["model"] == MODEL
    assert got["models"] == [MODEL]
    assert got["tokens"] == {
        "input": 10,
        "cache_write": 200,
        "cache_read": 3000,
        "output": 40,
        "total": 3250,
    }
    assert got["tools"] == {"mcp__beamtime__runs": 1, "Bash": 3}
    assert got["tool_errors"] == 1
    assert got["beamtime_calls"] == 3
    assert (got["turns"], got["api_ms"], got["cost_usd"]) == (3, 4200, 0.12)
    assert got["answer"] == RIGHT
    assert not got["leak"] and not got["other_model"]


def test_timeout_tokens() -> None:
    """Without a result event the tokens come from the assistant messages, each message once."""
    one = {"input_tokens": 5, "cache_read_input_tokens": 100, "output_tokens": 2}
    again = {"input_tokens": 5, "cache_read_input_tokens": 100, "output_tokens": 9}
    two = {"input_tokens": 1, "cache_creation_input_tokens": 50, "output_tokens": 4}
    events = [
        init(),
        assistant("m1", use("a", "Read", file_path="x"), usage=one),
        assistant("m1", {"type": "text", "text": "hi"}, usage=again),
        assistant("m2", {"type": "text", "text": "more"}, usage=two),
    ]
    got = sessions.summarize(events, model=MODEL)

    assert got["tokens"] == {
        "input": 6,
        "cache_write": 50,
        "cache_read": 100,
        "output": 13,
        "total": 169,
    }
    assert got["turns"] == 2
    assert got["answer"] == ""


def test_flags_other_model() -> None:
    """Another model in the init event, or above 5 % of the output tokens, flags the session."""

    def used(haiku_output: int) -> dict[str, Any]:
        """Make a result with a helper model beside the pinned one.

        :param haiku_output: The helper's output tokens, against 100 of the pinned model.
        :return: The event."""
        return result(
            modelUsage={
                f"{MODEL}[1m]": {"outputTokens": 100, "costUSD": 0.1},
                "claude-haiku-5-5": {"inputTokens": 30, "outputTokens": haiku_output},
            }
        )

    helper = sessions.summarize([init(), used(5)], model=MODEL)
    assert not helper["other_model"]
    assert helper["model_usage"]["claude-haiku-5-5"] == {
        "input": 30,
        "cache_write": 0,
        "cache_read": 0,
        "output": 5,
        "cost_usd": None,
    }
    assert helper["model_usage"][f"{MODEL}[1m]"]["cost_usd"] == 0.1
    assert sessions.summarize([init(), used(10)], model=MODEL)["other_model"]
    assert sessions.summarize([init("claude-opus-4-1"), result()], model=MODEL)["other_model"]
    assert sessions.summarize([init(), result()], model=MODEL)["models"] == [MODEL]


@pytest.mark.parametrize(
    "tool_input",
    [
        {"command": f"ls {setups.REPO}/src"},
        {"command": "ls /somewhere/synth/seed7"},
        {"file_path": "/x/generate.py"},
    ],
)
def test_leak_flag(tool_input: dict[str, str]) -> None:
    """A tool input that names the repo, ``synth/`` or ``generate.py`` flags the session."""
    events = [init(), assistant("m1", use("a", "Bash", **tool_input)), result()]

    assert sessions.summarize(events, model=MODEL)["leak"]
    clean = [init(), assistant("m1", use("a", "Bash", command="ls runs/")), result()]
    assert not sessions.summarize(clean, model=MODEL)["leak"]


class Claude:
    """A stand-in for ``subprocess.run`` that answers ``claude`` commands from a transcript."""

    def __init__(self, events: list[dict[str, Any]], *, timeout: bool = False, code: int = 0):
        """Store what the fake claude does.

        :param events: The transcript it writes to stdout.
        :param timeout: Whether it runs past the time limit.
        :param code: Its exit code.
        :return: None."""
        self.events = events
        self.timeout = timeout
        self.code = code
        self.calls: list[dict[str, Any]] = []
        self.real = subprocess.run

    def __call__(self, command: list[str], **kwargs: Any) -> CompletedProcess:
        """Answer a ``claude`` command and run everything else.

        :param command: The command.
        :param kwargs: ``subprocess.run`` arguments.
        :return: The completed process."""
        if command[0] != sessions.CLAUDE:
            return self.real(command, **kwargs)
        self.calls.append({"command": command} | kwargs)
        if command[1] == "--version":
            return CompletedProcess(command, 0, "9.9.9 (Claude Code)\n", "")
        return CompletedProcess(command, self.code, transcript(self.events), "")

    def popen(self, command: list[str], **kwargs: Any) -> "Session | subprocess.Popen":
        """Start a session: write its transcript and stand in for it; start any other command.

        :param command: The ``claude`` command.
        :param kwargs: ``subprocess.Popen`` arguments.
        :return: The process."""
        if command[0] != sessions.CLAUDE:
            return POPEN(command, **kwargs)
        self.calls.append({"command": command} | kwargs)
        kwargs["stdout"].write(transcript(self.events))
        kwargs["stderr"].write("stderr text")
        return Session(code=self.code, timeout=self.timeout)


class Session:
    """A stand-in ``claude`` process: a real process group of its own that exits or hangs."""

    def __init__(self, *, code: int, timeout: bool):
        """Start the process.

        :param code: The exit code.
        :param timeout: Whether it runs past the time limit.
        :return: None."""
        self.timeout = timeout
        script = "sleep 30" if timeout else f"exit {code}"
        self.real = POPEN(["sh", "-c", script], start_new_session=True)
        self.pid = self.real.pid

    def poll(self) -> int | None:
        """Say whether the process has exited.

        :return: The exit code, or ``None`` while it runs."""
        return self.real.poll()

    def wait(self, timeout: float | None = None) -> int:
        """Wait for the process, or run past the time limit.

        :param timeout: The time limit.
        :return: The exit code."""
        if timeout is not None and self.timeout:
            raise subprocess.TimeoutExpired("claude", timeout)
        return self.real.wait()


def test_run_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A session runs in its project with its time limit and writes its record."""
    task = grade.load_tasks()["best-config"]
    project = setups.planned("cli", tmp_path / "s")
    project.root.mkdir(parents=True)
    project.env["X"] = "1"
    folder = tmp_path / "out"
    folder.mkdir()
    fake = Claude([init(), assistant("m1", use("a", "Read", file_path="x")), result()])
    monkeypatch.setattr(subprocess, "Popen", fake.popen)
    job = sessions.Job(task="best-config", setup="cli", seed=7, rep=0)

    record = sessions.run_session(job, task, project, folder, model=MODEL, version="9.9.9")
    call = fake.calls[0]

    assert call["start_new_session"]
    assert call["cwd"] == project.root and call["env"] == {"X": "1"}
    assert call["command"][call["command"].index("--model") + 1] == MODEL
    assert record["status"] == "ok" and record["claude_version"] == "9.9.9"
    assert record["tools"] == {"Read": 1}
    assert json.loads((folder / "record.json").read_text()) == record
    assert (folder / "transcript.jsonl").read_text() == transcript(fake.events)


def test_run_session_timeout_and_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A timeout keeps the tokens of the messages; a failing exit is an error."""
    task = dataclasses.replace(grade.load_tasks()["best-config"], time_limit_s=1)
    project = setups.planned("files", tmp_path / "s")
    project.root.mkdir(parents=True)
    job = sessions.Job(task="best-config", setup="files", seed=7, rep=0)
    usage = {"input_tokens": 7, "output_tokens": 3}
    events = [init(), assistant("m1", {"type": "text", "text": "x"}, usage=usage)]
    for name, fake, status in (
        ("a", Claude(events, timeout=True), "timeout"),
        ("b", Claude([init(), result(is_error=True)], code=1), "error"),
    ):
        folder = tmp_path / name
        folder.mkdir()
        monkeypatch.setattr(subprocess, "Popen", fake.popen)
        record = sessions.run_session(job, task, project, folder, model=MODEL, version="v")
        assert record["status"] == status
    assert json.loads((tmp_path / "a" / "record.json").read_text())["tokens"]["total"] == 10


# the exit is seen only at a poll every 0.5 s, so a 1 s limit left a loaded machine one poll to
# start the shell; the exiting case gets 2 s, still short of the child's 3 s.
@pytest.mark.parametrize(
    ("script", "status", "limit"),
    [("sleep 30", "timeout", 1), ("echo '{}'; exit 0", "error", 2)],
)
def test_session_children_are_stopped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, script: str, status: str, limit: int
) -> None:
    """A child the session left running neither holds it to its time limit nor outlives it.

    :param script: What the stand-in ``claude`` does after starting the child.
    :param status: The session's status.
    :param limit: The session's time limit in seconds."""
    claude = tmp_path / "claude"
    claude.write_text(f'#!/bin/sh\n(sleep 3; touch "$PWD/stray") &\n{script}\n')
    claude.chmod(0o755)
    monkeypatch.setattr(sessions, "CLAUDE", str(claude))
    task = grade.Task(id="x", prompt="p", answer="a", checks={}, time_limit_s=limit, setups=["files"])
    project = setups.planned("files", tmp_path / "s")
    project.root.mkdir(parents=True)
    folder = tmp_path / "out"
    folder.mkdir()
    job = sessions.Job(task="x", setup="files", seed=7, rep=0)

    record = sessions.run_session(job, task, project, folder, model=MODEL, version="v")
    time.sleep(3.5 - record["seconds"])

    assert record["status"] == status and record["seconds"] < 2.5
    assert not (project.root / "stray").exists()


@pytest.mark.parametrize(
    ("events", "status"),
    [([init(), result()], "ok"), ([init(), result(is_error=True)], "error"), ([init()], "timeout")],
)
def test_result_ends_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, events: list[dict[str, Any]], status: str
) -> None:
    """A result ends a session although claude lingers on a child; without one it times out.

    :param events: What the stand-in ``claude`` writes before it waits on its child.
    :param status: The session's status."""
    lines = transcript(events).replace("'", "'\\''")
    claude = tmp_path / "claude"
    claude.write_text(f"#!/bin/sh\n(sleep 30) &\nprintf '%s' '{lines}'\nwait\n")
    claude.chmod(0o755)
    monkeypatch.setattr(sessions, "CLAUDE", str(claude))
    task = grade.Task(id="x", prompt="p", answer="a", checks={}, time_limit_s=4, setups=["files"])
    project = setups.planned("files", tmp_path / "s")
    project.root.mkdir(parents=True)
    folder = tmp_path / "out"
    folder.mkdir()
    job = sessions.Job(task="x", setup="files", seed=7, rep=0)

    record = sessions.run_session(job, task, project, folder, model=MODEL, version="v")

    assert record["status"] == status
    if status == "timeout":
        assert record["seconds"] >= 4 and record["answer"] == ""
    else:
        assert record["seconds"] < 2 and record["answer"] == RIGHT


def test_unstarted_session_is_not_scored(batch: "Batch") -> None:
    """A session whose project could not be prepared has no transcript and stays ungraded."""
    folder = batch.add("best-config", [], status="error")
    (folder / "transcript.jsonl").unlink()
    sessions.grade_batch(batch.dir)

    assert not (folder / "grade.json").exists()


def test_crash_is_not_scored_but_max_turns_is(batch: "Batch") -> None:
    """An error without a result event stays ungraded and is counted; one with a result scores 0."""
    crashed = batch.add(
        "best-config", [init(), assistant("m1", {"type": "text", "text": "x"})], status="error"
    )
    turns = batch.add(
        "chart", [init(), result("", is_error=True, subtype="error_max_turns")], status="error"
    )
    sessions.grade_batch(batch.dir)

    assert not (crashed / "grade.json").exists()
    assert json.loads((crashed / "record.json").read_text())["ungraded"] == "crashed"
    assert json.loads((turns / "grade.json").read_text())["score"] == 0
    assert json.loads((batch.dir / "batch.json").read_text())["ungraded"] == {"crashed": 1}
    assert not batch.root.exists()


def test_resolve_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """An alias is resolved from the init event of a probe session; a full id is kept."""
    fake = Claude([init("claude-sonnet-5-5"), result()])
    monkeypatch.setattr(subprocess, "run", fake)

    assert sessions.resolve_model("sonnet") == "claude-sonnet-5-5"
    assert fake.calls[0]["command"][fake.calls[0]["command"].index("--model") + 1] == "sonnet"
    assert sessions.resolve_model("claude-opus-9") == "claude-opus-9"
    assert len(fake.calls) == 1


class Batch:
    """A batch folder with sessions to grade, and the project folders outside the repo."""

    def __init__(self, tmp_path: Path):
        """Make the folders.

        :param tmp_path: An empty folder.
        :return: None."""
        self.root = tmp_path / "bt" / "20260101-000000"
        self.dir = tmp_path / "runs" / "compare-20260101-000000"
        self.dir.mkdir(parents=True)
        self.root.mkdir(parents=True)
        (self.dir / "batch.json").write_text(json.dumps({"model": MODEL, "root": str(self.root)}))

    def add(self, task: str, events: list[dict[str, Any]], status: str = "ok") -> Path:
        """Add a session with a project holding a PNG.

        :param task: The task id.
        :param events: The transcript.
        :param status: The record's status.
        :return: The session's folder in the batch."""
        name = f"{task}-files-7-0"
        folder = self.dir / name
        folder.mkdir()
        (folder / "transcript.jsonl").write_text(transcript(events))
        record = {"task": task, "setup": "files", "seed": 7, "rep": 0, "status": status}
        (folder / "record.json").write_text(json.dumps(record))
        project = self.root / "sessions" / name / "proj"
        project.mkdir(parents=True)
        (project / "fig.png").write_bytes(PNG)
        return folder


@pytest.fixture
def batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Batch:
    """A batch with the truth stubbed and the judge answering yes.

    :param tmp_path: An empty folder.
    :param monkeypatch: Replaces the truth and the judge.
    :return: The batch."""
    monkeypatch.setattr(
        sessions, "truth_for", lambda root, dataset, seed: {"best-config": BEST, "chart": {}}
    )
    marks = {i: {"yes": True, "why": f"ok {i}"} for i in range(1, 8)}
    monkeypatch.setattr(grade, "judge_chart", lambda image, items, *, model: marks)
    return Batch(tmp_path)


def test_grade_batch(batch: Batch) -> None:
    """A right answer scores 1, a timeout 0; projects and the root go once all are graded."""
    ok = batch.add("best-config", [init(), result()])
    timed = batch.add("chart", [init()], status="timeout")
    sessions.grade_batch(batch.dir)

    assert json.loads((ok / "grade.json").read_text())["correct"] is True
    timeout = json.loads((timed / "grade.json").read_text())
    assert timeout["score"] == 0 and not timeout["correct"]
    assert not batch.root.exists()


def test_answer_file_and_notes(batch: Batch) -> None:
    """The chart the answer names is copied beside the record, with the judge's reasons."""
    text = 'Saved.\n```json\n{"file": "fig.png"}\n```'
    folder = batch.add("chart", [init(), result(text)])
    sessions.grade_batch(batch.dir, keep=True)
    got = json.loads((folder / "grade.json").read_text())

    assert (folder / "answer.png").read_bytes() == PNG
    assert got["score"] == 1 and got["notes"]["judge1"] == "ok 1"
    assert (batch.root / "sessions").is_dir()


def test_stalled_judge_leaves_session_ungraded(
    batch: Batch, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stalled judge leaves the chart session ungraded with its project; others are graded."""

    def stalled(image: Path, items: list[str], *, model: str) -> dict[int, Any]:
        raise JudgeStalled("usage limit")

    monkeypatch.setattr(grade, "judge_chart", stalled)
    text = 'Saved.\n```json\n{"file": "fig.png"}\n```'
    chart = batch.add("chart", [init(), result(text)])
    best = batch.add("best-config", [init(), result()])
    sessions.grade_batch(batch.dir)

    assert not (chart / "grade.json").exists()
    assert (best / "grade.json").exists()
    assert (batch.root / "sessions" / chart.name / "proj").is_dir()
    assert batch.root.exists()


def test_failed_judge_leaves_session_ungraded(
    batch: Batch, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A judge without usable marks leaves the chart ungraded and counted, never scored 0; a later
    ``--grade-only`` with a working judge grades it and clears the mark."""

    def failed(image: Path, items: list[str], *, model: str) -> dict[int, Any]:
        raise grade.JudgeFailed("marks for [] of 7 items")

    working = grade.judge_chart
    monkeypatch.setattr(grade, "judge_chart", failed)
    text = 'Saved.\n```json\n{"file": "fig.png"}\n```'
    chart = batch.add("chart", [init(), result(text)])
    sessions.grade_batch(batch.dir)
    record = json.loads((chart / "record.json").read_text())

    assert not (chart / "grade.json").exists()
    assert record["ungraded"] == "judge failed" and "marks for" in record["judge_error"]
    assert json.loads((batch.dir / "batch.json").read_text())["ungraded"] == {"judge failed": 1}
    assert (batch.root / "sessions" / chart.name / "proj").is_dir()

    monkeypatch.setattr(grade, "judge_chart", working)
    sessions.grade_batch(batch.dir)

    assert json.loads((chart / "grade.json").read_text())["score"] == 1
    assert "ungraded" not in json.loads((chart / "record.json").read_text())
    assert json.loads((batch.dir / "batch.json").read_text())["ungraded"] == {}


def test_timeout_scores_zero_with_an_answer(batch: Batch) -> None:
    """A session recorded as a timeout scores 0 even when its transcript holds a right answer."""
    folder = batch.add("best-config", [init(), result()], status="timeout")
    sessions.grade_batch(batch.dir)

    assert json.loads((folder / "grade.json").read_text())["score"] == 0


def test_usage_limit_error_is_not_scored(batch: Batch) -> None:
    """A session that ended on the usage limit is left ungraded, not scored 0."""
    events = [init(), result("You've hit your usage limit.", is_error=True)]
    folder = batch.add("best-config", events, status="error")
    sessions.grade_batch(batch.dir)

    assert not (folder / "grade.json").exists()


def test_run_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One session end to end: data, project, a stubbed claude, grade, cleanup."""
    fake = Claude(
        [init(), assistant("m1", use("a", "Bash", command="cat runs/x"), usage=USAGE), result()]
    )
    monkeypatch.setattr(subprocess, "run", fake)
    monkeypatch.setattr(subprocess, "Popen", fake.popen)
    monkeypatch.setattr(sessions, "RUNS", tmp_path / "runs")
    monkeypatch.setenv("BT_COMPARE_ROOT", str(tmp_path / "bt"))
    (tmp_path / "base" / "bin").mkdir(parents=True)
    envs = setups.Envs(base=tmp_path / "base", beamtime=Path(sys.prefix))
    monkeypatch.setattr(setups, "make_envs", lambda root: envs)
    monkeypatch.setattr(
        sys,
        "argv",
        ["sessions.py", "--tasks", "best-config", "--setups", "files", "--seeds", "7"]
        + ["--model", "sonnet"],
    )
    sessions.main()
    (batch,) = (tmp_path / "runs").iterdir()
    meta = json.loads((batch / "batch.json").read_text())
    folder = batch / "best-config-files-7-0"
    run = [c for c in fake.calls if "--version" not in c["command"] and "-p" in c["command"]]

    assert meta["model"] == MODEL and meta["claude_version"] == "9.9.9 (Claude Code)"
    assert run[-1]["command"][run[-1]["command"].index("--model") + 1] == MODEL
    assert {p.name for p in folder.iterdir()} == {"record.json", "grade.json", "transcript.jsonl"}
    assert 0 <= json.loads((folder / "grade.json").read_text())["score"] <= 1
    assert not Path(meta["root"]).exists()


def test_stop_group_tolerates_eperm(monkeypatch):
    """macOS refuses ``killpg`` for a group with only the exited leader; that is not an error."""

    def refuse(pid, sig):
        raise PermissionError(1, "Operation not permitted")

    process = subprocess.Popen(["true"], start_new_session=True)
    process.wait()
    monkeypatch.setattr(sessions.os, "killpg", refuse)
    sessions.stop_group(process)


def other_task() -> grade.Task:
    """A task on the data set ``other``.

    :return: The task."""
    return grade.Task(
        id="other-task",
        prompt="p",
        answer="{}",
        checks={"x": {"kind": "equal", "truth": "x"}},
        time_limit_s=1,
        data="other",
    )


def test_task_data_defaults_to_s() -> None:
    """A shipped task without ``data`` runs on ``s``; only the wide tasks name their data set."""
    tasks = grade.load_tasks()

    assert {t.data for t in tasks.values()} == {"s", "wide"}
    assert {i for i, t in tasks.items() if t.data == "wide"} == {
        "drivers",
        "leaderboard",
        "divergence",
        "best-checkpoint",
        "check-all",
        "stale-verdicts",
    }
    assert sessions.data_dir(Path("r"), "s", 7) == Path("r/data/7")
    assert sessions.data_dir(Path("r"), "other", 7) == Path("r/data-other/7")


def test_truth_per_dataset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two data sets with the same seed keep their own export and their own truth."""
    seen = []

    def compute(name: str) -> Any:
        def inner(files: Path, logdir: Path) -> dict[str, dict[str, Any]]:
            seen.append((name, files, logdir))
            return {"t": {"name": name}}

        return inner

    monkeypatch.setitem(truth.TRUTHS, "s", compute("s"))
    monkeypatch.setitem(truth.TRUTHS, "other", compute("other"))
    monkeypatch.setattr(sessions.formats, "export_files", lambda logdir, dest: None)

    a = sessions.truth_for(tmp_path, "s", 7)
    b = sessions.truth_for(tmp_path, "other", 7)

    assert a["t"]["name"] == "s" and b["t"]["name"] == "other"
    assert seen[0][1:] == (tmp_path / "truth" / "7", tmp_path / "data" / "7" / "beamtime")
    assert seen[1][1:] == (
        tmp_path / "truth-other" / "7",
        tmp_path / "data-other" / "7" / "beamtime",
    )


def test_only_needed_datasets_built(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A batch of ``s`` tasks builds no other data set; one with an ``other`` task builds it too."""
    built = []
    real, other = grade.load_tasks()["best-config"], other_task()

    def builder(name: str) -> Any:
        return lambda dest, *, seed, now: built.append((name, dest.parent.name, dest.name))

    monkeypatch.setitem(data.DATASETS, "s", builder("s"))
    monkeypatch.setitem(data.DATASETS, "other", builder("other"))
    monkeypatch.setattr(grade, "load_tasks", lambda: {"best-config": real, "other-task": other})
    monkeypatch.setattr(sessions, "claude_version", lambda: "9")
    monkeypatch.setattr(sessions, "resolve_model", lambda alias: MODEL)
    monkeypatch.setattr(setups, "make_envs", lambda root: None)
    monkeypatch.setattr(sessions, "run_job", lambda *a, **k: {})
    monkeypatch.setattr(sessions, "grade_batch", lambda *a, **k: None)

    def run(*tasks: str) -> list[tuple[str, str, str]]:
        built.clear()
        monkeypatch.setattr(sessions, "RUNS", tmp_path / "runs" / str(len(tasks)))
        monkeypatch.setenv("BT_COMPARE_ROOT", str(tmp_path / "bt" / str(len(tasks))))
        argv = ["sessions.py", "--setups", "files", "--seeds", "7", "8", "--tasks", *tasks]
        monkeypatch.setattr(sys, "argv", argv + ["--model", "sonnet"])
        sessions.main()
        return sorted(built)

    only_s = run("best-config")
    assert only_s == [("s", "data", "7"), ("s", "data", "8")]

    assert run("best-config", "other-task") == [
        ("other", "data-other", "7"),
        ("other", "data-other", "8"),
        ("s", "data", "7"),
        ("s", "data", "8"),
    ]


def test_other_dataset_session_and_grade(batch: Batch, monkeypatch: pytest.MonkeyPatch) -> None:
    """A session prepares its project from its task's data set; grading uses that set's truth."""
    other = other_task()
    monkeypatch.setattr(grade, "load_tasks", lambda: {"other-task": other})
    asked = []
    monkeypatch.setattr(
        sessions,
        "truth_for",
        lambda root, dataset, seed: asked.append(dataset) or {"other-task": {"x": 1}},
    )
    prepared = []
    monkeypatch.setattr(
        setups, "prepare", lambda setup, session, data_dir, envs: prepared.append(data_dir)
    )
    monkeypatch.setattr(
        sessions, "run_session", lambda *a, **k: (_ for _ in ()).throw(KeyError("stop"))
    )

    job = sessions.Job(task="other-task", setup="files", seed=7, rep=5)
    sessions.run_job(
        job, other, batch=batch.dir, root=batch.root, envs=None, model=MODEL, version="9"
    )
    folder = batch.add("other-task", [init(), result('```json\n{"x": 1}\n```')])
    sessions.grade_batch(batch.dir, keep=True)

    assert prepared == [batch.root / "data-other" / "7"]
    assert asked == ["other"]
    assert json.loads((folder / "grade.json").read_text())["score"] == 1.0
