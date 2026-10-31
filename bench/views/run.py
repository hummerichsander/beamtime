"""Run the view-building tasks with agents: python bench/views/run.py [--smoke] [--models ...].

Each task × model × repetition gets a fresh project with a generated log dir, Beamtime's agent
rules in CLAUDE.md, and Beamtime's MCP server; the agent is headless Claude Code (`claude -p`) with
file tools for the draft. Transcripts and timings go to bench/views/runs/<stamp>/; score.py scores
them and report.py writes RESULTS.md.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).parent
RUNS = HERE / "runs"
TIME_LIMIT_S = 900
TOOLS = "Read,Write,Edit,Glob,Grep"
TAIL = " When the page is done, save it as the view with Beamtime's tools."


@dataclass(kw_only=True)
class Task:
    """One task: a page to build, what it must get right, and the checklist it is judged by."""

    id: str
    category: str
    smoke: bool
    page: str
    prompt: str
    facts: dict[str, Any]
    checklist: list[str]
    seed: int = 7
    # whether the view should also work on other pages (a run, a subgroup, an empty group).
    robust: bool = True

    @classmethod
    def load(cls, file: Path) -> "Task":
        """Read a task file.

        :param file: ``tasks/<id>.yaml``.
        :return: The task."""
        data = yaml.safe_load(file.read_text())
        return cls(id=file.stem, **data)

    def resolve(self, text: str, roles: dict[str, str], logdir: Path) -> str:
        """Fill ``{run:<role>}`` with the generated run's id and ``run:<role>`` pages with its path.

        :param text: A prompt or a page.
        :param roles: Run ids by role, from the generator.
        :param logdir: The log dir.
        :return: The text."""
        if text.startswith("run:"):
            run = roles[text.removeprefix("run:")]
            return next(logdir.rglob(run)).relative_to(logdir).as_posix()
        for role, run in roles.items():
            text = text.replace(f"{{run:{role}}}", run)
        return text


def tasks(smoke: bool, only: list[str] | None = None) -> list[Task]:
    """Load the tasks.

    :param smoke: Only those marked for every change.
    :param only: Task ids to keep, if given.
    :return: The tasks, by id."""
    out = [Task.load(f) for f in sorted((HERE / "tasks").glob("*.yaml"))]
    return [t for t in out if (not smoke or t.smoke) and (not only or t.id in only)]


def project(task: Task, folder: Path) -> tuple[Path, dict[str, str]]:
    """Set up a project for a task: a generated log dir, the agent rules, the MCP server.

    :param task: The task.
    :param folder: The run's folder.
    :return: The project root and the generated runs by role."""
    from beamtime.ops.admin import instructions
    from beamtime.synth import generate

    root = folder / "proj"
    manifest = generate(root / "beamtime", seed=task.seed, now=datetime.now(timezone.utc))
    (root / "beamtime.yaml").write_text("logdir: beamtime\n")
    instructions(root, root / "CLAUDE.md")
    beamtime = Path(sys.executable).parent / "beamtime"
    server = {
        "command": str(beamtime),
        "args": ["--root", str(root), "mcp"],
        "env": {"BEAMTIME_CACHE": str(folder / "cache")},
    }
    (folder / "mcp.json").write_text(json.dumps({"mcpServers": {"beamtime": server}}))
    return root, manifest.roles


def run_one(task: Task, model: str, rep: int, stamp: Path) -> dict[str, Any]:
    """Give one task to one agent and record what it did.

    :param task: The task.
    :param model: The model, as ``claude --model`` takes it.
    :param rep: The repetition.
    :param stamp: The run batch's folder.
    :return: The record, also written to ``record.json``."""
    folder = stamp / f"{task.id}-{model}-{rep}"
    folder.mkdir(parents=True)
    root, roles = project(task, folder)
    prompt = task.resolve(task.prompt.strip(), roles, root / "beamtime") + TAIL
    command = [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--mcp-config",
        str(folder / "mcp.json"),
        "--strict-mcp-config",
        "--tools",
        TOOLS,
        "--allowedTools",
        f"mcp__beamtime__*,{TOOLS}",
        "--setting-sources",
        "project",
        "--no-session-persistence",
        "--output-format",
        "stream-json",
        "--verbose",
    ]
    env = os.environ | {"BEAMTIME_CACHE": str(folder / "cache")}
    started = time.monotonic()
    with (folder / "transcript.jsonl").open("w") as out:
        try:
            done = subprocess.run(
                command,
                cwd=root,
                env=env,
                stdout=out,
                stderr=subprocess.PIPE,
                text=True,
                timeout=TIME_LIMIT_S,
            )
            status, stderr = done.returncode, done.stderr[-2000:]
        except subprocess.TimeoutExpired:
            status, stderr = "timeout", ""
    record = {
        "task": task.id,
        "model": model,
        "rep": rep,
        "page": task.resolve(task.page, roles, root / "beamtime"),
        "roles": roles,
        "status": status,
        "stderr": stderr,
        "seconds": round(time.monotonic() - started, 1),
    } | summary(folder / "transcript.jsonl")
    (folder / "record.json").write_text(json.dumps(record, indent=2))
    return record


def summary(transcript: Path) -> dict[str, Any]:
    """Count what the agent did from its stream-json transcript.

    :param transcript: The transcript.
    :return: Tool calls in order, validation and render rounds, turns, tokens and cost."""
    calls, result = [], {}
    for line in transcript.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant":
            for part in event.get("message", {}).get("content", []):
                if part.get("type") == "tool_use":
                    calls.append(part["name"].removeprefix("mcp__beamtime__"))
        elif event.get("type") == "result":
            result = event
    usage = result.get("usage") or {}
    return {
        "tools": calls,
        "validations": calls.count("view_validate"),
        "renders": calls.count("view_render"),
        "turns": result.get("num_turns"),
        "tokens": {k: v for k, v in usage.items() if k.endswith("tokens")},
        "cost_usd": result.get("total_cost_usd"),
        "answer": (result.get("result") or "")[-1500:],
    }


def main() -> None:
    """Run the tasks and score them."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--smoke", action="store_true", help="only the tasks run on every change")
    parser.add_argument("--models", nargs="+", default=["sonnet", "haiku"])
    parser.add_argument("--reps", type=int, default=1)
    parser.add_argument("--tasks", nargs="*", help="task ids; default all")
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--no-score", action="store_true", help="only run the agents")
    args = parser.parse_args()
    stamp = RUNS / datetime.now().strftime("%Y%m%d-%H%M%S")
    stamp.mkdir(parents=True)
    chosen = tasks(args.smoke, args.tasks)
    jobs = [(t, m, r) for t in chosen for m in args.models for r in range(args.reps)]
    print(f"{len(jobs)} agent runs into {stamp}", flush=True)
    with ThreadPoolExecutor(args.parallel) as pool:
        for record in pool.map(lambda j: run_one(*j, stamp), jobs):
            what = f"{record['status']}, {record['seconds']} s, {len(record['tools'])} tool calls"
            print(f"{record['task']} {record['model']} {record['rep']}: {what}", flush=True)
    if not args.no_score:
        from report import report
        from score import score_batch

        score_batch(stamp)
        report(stamp)


if __name__ == "__main__":
    main()
