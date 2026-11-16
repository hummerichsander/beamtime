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
    models = sorted((result.get("modelUsage") or {}).keys())
    used = {m.split("[")[0] for m in models} | ({init["model"]} if init.get("model") else set())
    assistant = {(e.get("message") or {}).get("id") for e in events if e.get("type") == "assistant"}
    return {
        "model": init.get("model"),
        "models": models,
        "other_model": bool(used - {model}),
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
    code: int | None = None
    stderr = ""
    with (folder / "transcript.jsonl").open("w") as out:
        try:
            done = subprocess.run(
                command(task.prompt, project, model),
                cwd=project.root,
                env=project.env,
                stdout=out,
                stderr=subprocess.PIPE,
                text=True,
                timeout=task.time_limit_s,
            )
            code, stderr = done.returncode, done.stderr[-2000:]
        except subprocess.TimeoutExpired:
            pass
    seconds = round(time.monotonic() - started, 1)
    events = read_events((folder / "transcript.jsonl").read_text())
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if code is None:
        status = "timeout"
    else:
        status = "ok" if code == 0 and result and not result.get("is_error") else "error"
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

    A session whose judge hits the usage limit stays ungraded with its project kept; run
    ``--grade-only`` again later. A timeout scores 0.

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
        text = final_text(read_events(transcript.read_text() if transcript.exists() else ""))
        if record["status"] == "error" and USAGE_LIMIT.search(text):
            print(f"{folder.name}: usage limit, left ungraded", flush=True)
            pending += 1
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
    if not pending and not keep and root.name == batch.name.removeprefix("compare-"):
        shutil.rmtree(root, ignore_errors=True)


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
