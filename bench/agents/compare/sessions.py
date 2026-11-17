"""Run the comparison: python bench/agents/compare/sessions.py [--dry-run] [--grade-only BATCH]

Every task runs in every setup on every data seed, one headless Claude Code session each. The data
is built once per seed, a session gets its own project (``setups.prepare``) and a time limit, and
the reply is graded after all sessions ran, against truth computed from the same data. A batch
lands in bench/agents/runs/compare-<stamp>/<task>-<setup>-<seed>-<rep>/ with ``record.json``,
``grade.json``, ``transcript.jsonl`` and the file the answer names. Projects, data and venvs live
outside the repo under ``$BT_COMPARE_ROOT/<stamp>/`` (default ``$TMPDIR/bt-compare/``).
"""

import argparse
import json
import os
import random
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
AGENTS = HERE.parent
RUNS = AGENTS / "runs"
SEEDS = [7, 8, 9]
SHUFFLE_SEED = 0
LEAKS = ("synth/", "generate.py")
JUDGE_FAILED = ("ungraded", "judge_error")
# a helper model (Claude Code's own small calls) below this share of output tokens is not a flag.
OTHER_MODEL_SHARE = 0.05
# how often a running session's transcript is checked for its result event.
POLL_S = 0.5
BEAMTIME_CALL = re.compile(r"(?:^|[;&|(]\s*)(?:uv run\s+)?beamtime\s+\S", re.MULTILINE)
# the host's claude, found before a session's PATH drops the folders that hold a beamtime.
CLAUDE = shutil.which("claude") or "claude"

sys.path.append(str(AGENTS))

import data  # noqa: E402
import formats  # noqa: E402
import grade  # noqa: E402
import setups  # noqa: E402
import truth  # noqa: E402
from score import USAGE_LIMIT, JudgeStalled  # noqa: E402


@dataclass(kw_only=True)
class Job:
    """One session to run: a task in a setup on a data seed."""

    task: str
    setup: str
    seed: int
    rep: int

    @property
    def name(self) -> str:
        """Give the session's folder name.

        :return: ``<task>-<setup>-<seed>-<rep>``."""
        return f"{self.task}-{self.setup}-{self.seed}-{self.rep}"


def make_jobs(
    tasks: dict[str, grade.Task], chosen_setups: list[str], seeds: list[int], reps: int
) -> list[Job]:
    """List the sessions of a batch in a fixed shuffled order, so contention hits all setups alike.

    :param tasks: The tasks to run; each runs in the setups it names.
    :param chosen_setups: The setups to run.
    :param seeds: The data seeds.
    :param reps: The repetitions of each session.
    :return: The jobs."""
    jobs = [
        Job(task=t.id, setup=s, seed=seed, rep=rep)
        for t in tasks.values()
        for s in chosen_setups
        if s in t.setups
        for seed in seeds
        for rep in range(reps)
    ]
    random.Random(SHUFFLE_SEED).shuffle(jobs)
    return jobs


def command(prompt: str, project: setups.Project, model: str) -> list[str]:
    """Build the ``claude`` command of a session.

    :param prompt: The task's prompt.
    :param project: The prepared project.
    :param model: The pinned model id.
    :return: The command line."""
    return [
        CLAUDE,
        "-p",
        prompt,
        "--model",
        model,
        *project.flags,
        "--output-format",
        "stream-json",
        "--verbose",
    ]


def read_events(text: str) -> list[dict[str, Any]]:
    """Parse a stream-json transcript, skipping lines that are not JSON (a killed run's last one).

    :param text: The transcript.
    :return: The events."""
    events = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def message_tokens(events: list[dict[str, Any]]) -> dict[str, int]:
    """Sum the tokens of the assistant messages, each message once.

    A message arrives as several events (one per content block) with the same id; the largest count
    of each kind is the final one.

    :param events: The transcript's events.
    :return: The tokens as ``token_counts`` gives them."""
    per_message: dict[str, dict[str, int]] = {}
    for event in events:
        if event.get("type") != "assistant":
            continue
        message = event.get("message") or {}
        seen = per_message.setdefault(message.get("id") or "", {})
        for key, value in (message.get("usage") or {}).items():
            if isinstance(value, int):
                seen[key] = max(seen.get(key, 0), value)
    kinds = {k for seen in per_message.values() for k in seen}
    return token_counts({k: sum(seen.get(k, 0) for seen in per_message.values()) for k in kinds})


def token_counts(usage: dict[str, Any]) -> dict[str, int]:
    """Name the four kinds of tokens of a usage record and their total.

    :param usage: A ``usage`` dict of the API.
    :return: ``input``, ``cache_write``, ``cache_read``, ``output`` and ``total``."""
    counts = {
        "input": usage.get("input_tokens") or 0,
        "cache_write": usage.get("cache_creation_input_tokens") or 0,
        "cache_read": usage.get("cache_read_input_tokens") or 0,
        "output": usage.get("output_tokens") or 0,
    }
    return counts | {"total": sum(counts.values())}


def summarize(events: list[dict[str, Any]], *, model: str) -> dict[str, Any]:
    """Count what a session did from its transcript.

    :param events: The transcript's events.
    :param model: The pinned model; a session that used another is flagged ``other_model``.
    :return: The record's measures: model, models, turns, tokens, cost, tools, errors, Beamtime
        calls, leak flag and answer."""
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    init = next((e for e in events if e.get("subtype") == "init"), {})
    calls: dict[str, dict[str, Any]] = {}
    for event in events:
        for part in (event.get("message") or {}).get("content") or []:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "tool_use":
                calls[part["id"]] = part
            elif part.get("type") == "tool_result" and part.get("tool_use_id") in calls:
                calls[part["tool_use_id"]]["failed"] = bool(part.get("is_error"))
    names = [c["name"] for c in calls.values()]
    usage = model_usage(result.get("modelUsage") or {})
    assistant = {(e.get("message") or {}).get("id") for e in events if e.get("type") == "assistant"}
    return {
        "model": init.get("model"),
        "models": sorted(usage),
        "model_usage": usage,
        "other_model": other_model(init.get("model"), usage, model=model),
        "api_ms": result.get("duration_api_ms"),
        "turns": result.get("num_turns") or len(assistant - {None}),
        "tokens": token_counts(result["usage"]) if "usage" in result else message_tokens(events),
        "cost_usd": result.get("total_cost_usd"),
        "tools": dict(Counter(names)),
        "tool_errors": sum(bool(c.get("failed")) for c in calls.values()),
        "beamtime_calls": sum(is_beamtime_call(c) for c in calls.values()),
        "leak": any(leaks(c.get("input")) for c in calls.values()),
        "answer": final_text(events)[-4000:],
    }


def model_usage(by_model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Name each model's tokens and cost from a result's ``modelUsage``.

    :param by_model: ``modelUsage`` as the result event gives it.
    :return: Per model: ``input``, ``cache_write``, ``cache_read``, ``output`` and ``cost_usd``."""
    return {
        name: {
            "input": u.get("inputTokens") or 0,
            "cache_write": u.get("cacheCreationInputTokens") or 0,
            "cache_read": u.get("cacheReadInputTokens") or 0,
            "output": u.get("outputTokens") or 0,
            "cost_usd": u.get("costUSD"),
        }
        for name, u in by_model.items()
        if isinstance(u, dict)
    }


def other_model(init_model: str | None, usage: dict[str, dict[str, Any]], *, model: str) -> bool:
    """Say whether a session ran on another model than the pinned one.

    :param init_model: The model of the init event.
    :param usage: The per-model usage from ``model_usage``.
    :param model: The pinned model.
    :return: Whether the init event names another model, or another model wrote more than
        ``OTHER_MODEL_SHARE`` of the output tokens."""
    if init_model and init_model != model:
        return True
    total = sum(u["output"] for u in usage.values())
    other = sum(u["output"] for name, u in usage.items() if name.split("[")[0] != model)
    return total > 0 and other / total > OTHER_MODEL_SHARE


def final_text(events: list[dict[str, Any]]) -> str:
    """Give the agent's last message; a session without a result event has none.

    :param events: The transcript's events.
    :return: The text, empty when the session ended without a result."""
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    return str(result.get("result") or "")


def is_beamtime_call(call: dict[str, Any]) -> bool:
    """Say whether a tool call used Beamtime: one of its MCP tools or the ``beamtime`` command.

    :param call: A ``tool_use`` part.
    :return: Whether it did."""
    if str(call["name"]).startswith("mcp__beamtime__"):
        return True
    return call["name"] == "Bash" and bool(
        BEAMTIME_CALL.search(str((call.get("input") or {}).get("command", "")))
    )


def leaks(tool_input: Any) -> bool:
    """Say whether a tool call reached for the answers: the repo, the generator or its folders.

    :param tool_input: The call's input.
    :return: Whether it names the repo path, ``synth/`` or ``generate.py``."""
    text = json.dumps(tool_input)
    return str(setups.REPO) in text or any(leak in text for leak in LEAKS)


def run_session(
    job: Job, task: grade.Task, project: setups.Project, folder: Path, *, model: str, version: str
) -> dict[str, Any]:
    """Run one session with its time limit and write its transcript and record.

    :param job: The session.
    :param task: Its task.
    :param project: The prepared project.
    :param folder: The session's folder in the batch.
    :param model: The pinned model id.
    :param version: ``claude --version``.
    :return: The record, also written to ``record.json``."""
    started = time.monotonic()
    transcript = folder / "transcript.jsonl"
    # stderr goes to a file: a child left running would hold a pipe open until the time limit.
    with transcript.open("w") as out, tempfile.TemporaryFile("w+") as err:
        process = subprocess.Popen(
            command(task.prompt, project, model),
            cwd=project.root,
            env=project.env,
            stdout=out,
            stderr=err,
            text=True,
            start_new_session=True,
        )
        seconds = wait_session(process, transcript, started=started, limit=task.time_limit_s)
        stop_group(process)
        err.seek(0)
        stderr = err.read()[-2000:]
    events = read_events(transcript.read_text())
    status = session_status(events, ended=seconds is not None)
    if seconds is None:
        seconds = round(time.monotonic() - started, 1)
    return write_record(
        folder,
        {
            "task": job.task,
            "setup": job.setup,
            "seed": job.seed,
            "rep": job.rep,
            "claude_version": version,
            "status": status,
            "seconds": seconds,
        }
        | summarize(events, model=model)
        | {"stderr": stderr},
    )


def wait_session(
    process: subprocess.Popen, transcript: Path, *, started: float, limit: float
) -> float | None:
    """Wait until the session's result event arrives, its process exits or its time runs out.

    The result ends a session even while ``claude`` keeps running: it waits for the background
    tasks a session left behind (a Bash command Claude Code moved there), which may never end.

    :param process: The ``claude`` process.
    :param transcript: The file its stream-json output goes to.
    :param started: ``time.monotonic()`` at the start of the session.
    :param limit: The time limit in seconds.
    :return: The wall seconds up to the result or the exit, ``None`` when the time ran out."""
    while (seconds := time.monotonic() - started) < limit:
        if process.poll() is not None or has_result(read_events(transcript.read_text())):
            return round(seconds, 1)
        time.sleep(POLL_S)
    return None


def has_result(events: list[dict[str, Any]]) -> bool:
    """Say whether a transcript has its result event.

    :param events: The transcript's events.
    :return: Whether one of them is the result."""
    return any(e.get("type") == "result" for e in events)


def session_status(events: list[dict[str, Any]], *, ended: bool) -> str:
    """Tell a session's status from its transcript: the result event decides, if there is one.

    :param events: The transcript's events.
    :param ended: Whether the session ended (a result or an exit) before its time limit.
    :return: ``ok`` or ``error`` from the result's ``is_error``; without a result ``timeout`` when
        it ran out of time, else ``error`` (``claude`` exited without one)."""
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if result is not None:
        return "error" if result.get("is_error") else "ok"
    return "error" if ended else "timeout"


def stop_group(process: subprocess.Popen) -> None:
    """Kill a session's process group, so nothing it started keeps running into later sessions.

    :param process: The ``claude`` process, started in a new session."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    # macOS answers EPERM when only the exited, unreaped leader is left in the group.
    except (ProcessLookupError, PermissionError):
        pass
    process.wait()


def write_record(folder: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Write a session's ``record.json``.

    :param folder: The session's folder.
    :param record: The record.
    :return: The record."""
    (folder / "record.json").write_text(json.dumps(record, indent=2))
    return record


def run_job(
    job: Job,
    task: grade.Task,
    *,
    batch: Path,
    root: Path,
    envs: setups.Envs,
    model: str,
    version: str,
) -> dict[str, Any]:
    """Prepare and run one session; a failed preparation is recorded as an error, not raised.

    :param job: The session.
    :param task: Its task.
    :param batch: The batch's folder.
    :param root: The batch's folder outside the repo.
    :param envs: The environments.
    :param model: The pinned model id.
    :param version: ``claude --version``.
    :return: The record."""
    folder = batch / job.name
    folder.mkdir(parents=True)
    try:
        project = setups.prepare(
            job.setup, root / "sessions" / job.name, root / "data" / str(job.seed), envs
        )
        record = run_session(job, task, project, folder, model=model, version=version)
    except Exception as e:  # one broken session must not end a batch of 96
        record = write_record(
            folder,
            {"task": job.task, "setup": job.setup, "seed": job.seed, "rep": job.rep}
            | {"status": "error", "stderr": f"{type(e).__name__}: {e}"},
        )
    print(f"{job.name}: {record['status']}, {record.get('seconds')} s", flush=True)
    return record


def resolve_model(alias: str) -> str:
    """Resolve a model alias to the full id Claude Code reports in its init event.

    :param alias: ``sonnet``, or a full id, which is used as given.
    :return: The full id.
    :raises RuntimeError: When the probe session reports no model."""
    if alias.startswith("claude-"):
        return alias
    flags = ["--tools", "", "--setting-sources", "project", "--strict-mcp-config"]
    flags += ["--disable-slash-commands", "--no-session-persistence"]
    with tempfile.TemporaryDirectory() as tmp:
        done = subprocess.run(
            [CLAUDE, "-p", "Reply with ok.", "--model", alias, *flags]
            + ["--output-format", "stream-json", "--verbose"],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=180,
        )
    for event in read_events(done.stdout):
        if event.get("subtype") == "init" and event.get("model"):
            return str(event["model"])
    raise RuntimeError(f"no model in the init event for {alias!r}: {done.stderr[-300:]}")


def claude_version() -> str:
    """Ask ``claude --version``.

    :return: The version line."""
    done = subprocess.run([CLAUDE, "--version"], capture_output=True, text=True, timeout=60)
    return done.stdout.strip()


def truth_for(root: Path, seed: int) -> dict[str, dict[str, Any]]:
    """Compute a seed's truth from a plain-files export made outside every session's reach.

    :param root: The batch's folder outside the repo.
    :param seed: The data seed.
    :return: The expected values of every task."""
    logdir = root / "data" / str(seed) / "beamtime"
    files = root / "truth" / str(seed)
    if not (files / "runs").is_dir():
        formats.export_files(logdir, files)
    return truth.compute(files, logdir)


def grade_batch(batch: Path, *, keep: bool = False) -> None:
    """Grade every session of a batch that has no grade yet, then delete what is no longer needed.

    A session that ended on the usage limit, or whose judge hits it, stays ungraded with its
    project kept; run ``--grade-only`` again later. So does one whose judge gave no usable mark
    twice, marked ``ungraded: judge failed``. One that never started or crashed stays ungraded for
    good, marked ``ungraded`` in its record. Both are counted in ``batch.json``. A timeout and an
    error with a result event (max turns) score 0.

    :param batch: The batch's folder.
    :param keep: Keep the projects and data."""
    meta = json.loads((batch / "batch.json").read_text())
    root = Path(meta["root"])
    tasks = grade.load_tasks()
    truths: dict[int, dict[str, dict[str, Any]]] = {}
    stalled = False
    pending = 0
    for folder in sorted(p.parent for p in batch.glob("*/record.json")):
        if (folder / "grade.json").exists():
            continue
        record = json.loads((folder / "record.json").read_text())
        task = tasks[record["task"]]
        project = root / "sessions" / folder.name / "proj"
        transcript = folder / "transcript.jsonl"
        events = read_events(transcript.read_text()) if transcript.exists() else []
        # a timeout scores 0 (Decision 11), whatever the transcript holds.
        text = "" if record["status"] == "timeout" else final_text(events)
        if (reason := unscored(record, events, started=transcript.exists())) is not None:
            write_record(folder, record | {"ungraded": reason})
            print(f"{folder.name}: {reason}, left ungraded", flush=True)
            if reason == "usage limit":
                pending += 1
            elif not keep:
                shutil.rmtree(root / "sessions" / folder.name, ignore_errors=True)
            continue
        if not project.is_dir() or (stalled and task.judge):
            print(f"{folder.name}: ungraded, run --grade-only again later", flush=True)
            pending += 1
            continue
        seed = record["seed"]
        if seed not in truths:
            truths[seed] = truth_for(root, seed)
        try:
            result = grade.grade(task, text, truths[seed][task.id], project, model=meta["model"])
        except JudgeStalled as e:
            print(f"{folder.name}: judge stalled, {e}", flush=True)
            stalled = True
            pending += 1
            continue
        except grade.JudgeFailed as e:
            write_record(folder, record | {"ungraded": "judge failed", "judge_error": str(e)})
            print(f"{folder.name}: judge failed, left ungraded: {e}", flush=True)
            pending += 1
            continue
        if "ungraded" in record:
            write_record(folder, {k: v for k, v in record.items() if k not in JUDGE_FAILED})
        keep_answer_file(project, text, folder)
        (folder / "grade.json").write_text(
            json.dumps(
                {
                    "score": result.score,
                    "correct": result.correct,
                    "checks": result.checks,
                    "notes": result.notes,
                },
                indent=2,
            )
        )
        print(f"{folder.name}: {result.score:.2f}", flush=True)
        if not keep:
            shutil.rmtree(root / "sessions" / folder.name, ignore_errors=True)
    ungraded = Counter(
        r["ungraded"]
        for r in (json.loads(f.read_text()) for f in batch.glob("*/record.json"))
        if "ungraded" in r
    )
    (batch / "batch.json").write_text(json.dumps(meta | {"ungraded": dict(ungraded)}, indent=2))
    if not pending and not keep and root.name == batch.name.removeprefix("compare-"):
        shutil.rmtree(root, ignore_errors=True)


def unscored(record: dict[str, Any], events: list[dict[str, Any]], *, started: bool) -> str | None:
    """Say why a session is left ungraded, if it is: only the agent's own failures score 0.

    :param record: The session's record.
    :param events: Its transcript's events.
    :param started: Whether it has a transcript.
    :return: ``not started`` (preparation failed), ``usage limit``, ``crashed`` (an error without
        a result event: a ``claude`` crash, an API or network error), or ``None`` to grade it."""
    if not started:
        return "not started"
    if record["status"] != "error":
        return None
    if USAGE_LIMIT.search(final_text(events)):
        return "usage limit"
    if not any(e.get("type") == "result" for e in events):
        return "crashed"
    return None


def keep_answer_file(project: Path, text: str, folder: Path) -> None:
    """Copy the file an answer names (the chart, the table) into the session's folder.

    :param project: The agent's project.
    :param text: The agent's last message.
    :param folder: The session's folder in the batch."""
    answer = grade.answer_json(text) or {}
    try:
        path = grade.project_file(project, answer["file"])
    except (KeyError, ValueError, OSError):
        return
    shutil.copy(path, folder / f"answer{path.suffix}")


def run_batch(args: argparse.Namespace) -> Path:
    """Build the data and environments, run every session and grade them.

    :param args: The parsed command line.
    :return: The batch's folder."""
    tasks = {k: t for k, t in grade.load_tasks().items() if not args.tasks or k in args.tasks}
    jobs = make_jobs(tasks, args.setups, args.seeds, args.reps)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    batch = RUNS / f"compare-{stamp}"
    root = Path(os.environ.get("BT_COMPARE_ROOT") or Path(tempfile.gettempdir()) / "bt-compare")
    root = root.resolve() / stamp
    if setups.REPO in root.parents:
        raise SystemExit(f"{root} is inside the repo; projects must live outside it")
    batch.mkdir(parents=True)
    model, version = resolve_model(args.model), claude_version()
    now = datetime.now(timezone.utc)
    (batch / "batch.json").write_text(
        json.dumps(
            {
                "model": model,
                "alias": args.model,
                "claude_version": version,
                "root": str(root),
                "started": now.isoformat(),
                "setups": args.setups,
                "tasks": sorted(tasks),
                "seeds": args.seeds,
                "reps": args.reps,
            },
            indent=2,
        )
    )
    print(f"{len(jobs)} sessions with {model} into {batch}, projects in {root}", flush=True)
    envs = setups.make_envs(root / "envs")
    for seed in args.seeds:
        data.make_logdir(root / "data" / str(seed), seed=seed, now=now)
    with ThreadPoolExecutor(args.parallel) as pool:
        list(
            pool.map(
                lambda j: run_job(
                    j,
                    tasks[j.task],
                    batch=batch,
                    root=root,
                    envs=envs,
                    model=model,
                    version=version,
                ),
                jobs,
            )
        )
    grade_batch(batch, keep=args.keep)
    return batch


def dry_run(args: argparse.Namespace) -> None:
    """List the sessions with their commands; nothing is built or started.

    :param args: The parsed command line."""
    tasks = {k: t for k, t in grade.load_tasks().items() if not args.tasks or k in args.tasks}
    jobs = make_jobs(tasks, args.setups, args.seeds, args.reps)
    for job in jobs:
        project = setups.planned(job.setup, Path("<session>"))
        line = shlex.join(command("<prompt>", project, args.model))
        print(f"{job.name} (limit {tasks[job.task].time_limit_s} s): {line}")
    print(f"{len(jobs)} sessions")


def main() -> None:
    """Run the comparison, or list it, or grade a finished batch."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--setups", nargs="+", default=list(setups.SETUPS), choices=list(setups.SETUPS)
    )
    parser.add_argument("--tasks", nargs="*", help="task ids; default all")
    parser.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--model", default="sonnet", help="an alias is pinned to its full id")
    parser.add_argument("--keep", action="store_true", help="keep projects, data and venvs")
    parser.add_argument("--dry-run", action="store_true", help="list the sessions, run none")
    parser.add_argument("--grade-only", type=Path, help="grade the ungraded sessions of a batch")
    args = parser.parse_args()
    if args.grade_only:
        batch = args.grade_only if args.grade_only.exists() else RUNS / args.grade_only
        grade_batch(batch, keep=args.keep)
    elif args.dry_run:
        dry_run(args)
    else:
        run_batch(args)


if __name__ == "__main__":
    main()
