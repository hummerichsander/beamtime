"""Tests of the benchmark's session runner (``compare/sessions.py``); no agent runs."""

import json
import subprocess
import sys
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

import pytest

BENCH = Path(__file__).resolve().parents[2] / "bench" / "agents"
sys.path.insert(0, str(BENCH / "compare"))
sys.path.insert(0, str(BENCH))

import grade  # noqa: E402
import sessions  # noqa: E402
import setups  # noqa: E402
from score import JudgeStalled  # noqa: E402

MODEL = "claude-sonnet-5-5"
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
    """96 sessions: eight tasks, four setups, three seeds; the order is fixed and shuffled."""
    tasks = grade.load_tasks()
    jobs = sessions.make_jobs(tasks, list(setups.SETUPS), [7, 8, 9], 1)

    assert len(jobs) == 96
    assert len({j.name for j in jobs}) == 96
    assert jobs == sessions.make_jobs(tasks, list(setups.SETUPS), [7, 8, 9], 1)
    assert [j.name for j in jobs] != sorted(j.name for j in jobs)
    assert len(sessions.make_jobs(tasks, ["mcp"], [7], 2)) == 16


def test_jobs_respect_task_setups() -> None:
    """A task that names setups runs in those only."""
    task = grade.Task(id="x", prompt="p", answer="a", checks={}, time_limit_s=1, setups=["mcp"])
    jobs = sessions.make_jobs({"x": task}, ["mcp", "cli"], [7], 1)

    assert [j.setup for j in jobs] == ["mcp"]


def test_dry_run(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """The dry run lists 96 sessions with their commands and builds nothing."""
    monkeypatch.setattr(sys, "argv", ["sessions.py", "--dry-run"])
    sessions.main()
    lines = capsys.readouterr().out.splitlines()

    assert lines[-1] == "96 sessions"
    assert len(lines) == 97
    assert sum("--mcp-config" in line for line in lines) == 24
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
    """A second model in ``modelUsage``, or another one in the init event, flags the session."""
    other = result(modelUsage={MODEL: {}, "claude-haiku-4-5": {}})
    assert sessions.summarize([init(), other], model=MODEL)["other_model"]
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
        text = transcript(self.events)
        if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
            kwargs["stdout"].write(text)
            kwargs["stdout"].flush()
            if self.timeout:
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            return CompletedProcess(command, self.code, None, "stderr text")
        return CompletedProcess(command, self.code, text, "")


def test_run_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A session runs in its project with its time limit and writes its record."""
    task = grade.load_tasks()["best-config"]
    project = setups.planned("cli", tmp_path / "s")
    project.root.mkdir(parents=True)
    project.env["X"] = "1"
    folder = tmp_path / "out"
    folder.mkdir()
    fake = Claude([init(), assistant("m1", use("a", "Read", file_path="x")), result()])
    monkeypatch.setattr(subprocess, "run", fake)
    job = sessions.Job(task="best-config", setup="cli", seed=7, rep=0)

    record = sessions.run_session(job, task, project, folder, model=MODEL, version="9.9.9")
    call = fake.calls[0]

    assert call["timeout"] == task.time_limit_s
    assert call["cwd"] == project.root and call["env"] == {"X": "1"}
    assert call["command"][call["command"].index("--model") + 1] == MODEL
    assert record["status"] == "ok" and record["claude_version"] == "9.9.9"
    assert record["tools"] == {"Read": 1}
    assert json.loads((folder / "record.json").read_text()) == record
    assert (folder / "transcript.jsonl").read_text() == transcript(fake.events)


def test_run_session_timeout_and_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A timeout keeps the tokens of the messages; a failing exit is an error."""
    task = grade.load_tasks()["best-config"]
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
        monkeypatch.setattr(subprocess, "run", fake)
        record = sessions.run_session(job, task, project, folder, model=MODEL, version="v")
        assert record["status"] == status
    assert json.loads((tmp_path / "a" / "record.json").read_text())["tokens"]["total"] == 10


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
        sessions, "truth_for", lambda root, seed: {"best-config": BEST, "chart": {}}
    )
    marks = {i: {"yes": True, "why": f"ok {i}"} for i in range(1, 6)}
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
