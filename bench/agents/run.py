"""Run the agent tasks: python bench/agents/run.py [--smoke] [--models ...] [--guide DIR].

Tasks come in kinds (proposal, verdict, notes, view, analysis, lifecycle). Each task × model ×
repetition gets a fresh project with a generated log dir, Beamtime's agent rules in CLAUDE.md, and
Beamtime's MCP server; the agent is headless Claude Code (`claude -p`) with file tools for drafts.
Transcripts and timings go to bench/agents/runs/<stamp>/; score.py scores them and report.py
writes RESULTS.md.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).parent
RUNS = HERE / "runs"
TIME_LIMIT_S = 900
TOOLS = "Read,Write,Edit,Glob,Grep"
TAIL = {"view": " When the page is done, save it as the view with Beamtime's tools."}
# the MCP server with parts of the guide read from a directory (argv[1]), to test text unreleased.
GUIDE_SERVER = (
    "import sys; from pathlib import Path; import beamtime.guide as g; "
    "d = Path(sys.argv.pop(1)); read = g.read; "
    "g.read = lambda n: (d / n).read_text() if (d / n).is_file() else read(n); "
    "from beamtime.cli import main; main()"
)


@dataclass(kw_only=True)
class Task:
    """One task: a page to build, what it must get right, and the checklist it is judged by."""

    id: str
    category: str
    prompt: str
    facts: dict[str, Any]
    smoke: bool = False
    kind: str = "view"
    page: str = ""
    checklist: list[str] = field(default_factory=list)
    seed: int = 7
    # a third of the tasks are not looked at while refining the guide; run them with --heldout.
    heldout: bool = False
    # the name of a second log dir the project reaches as a remote of that name.
    remote: str | None = None
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


def tasks(
    smoke: bool,
    only: list[str] | None = None,
    kinds: list[str] | None = None,
    heldout: bool = False,
) -> list[Task]:
    """Load the tasks.

    :param smoke: Only those marked for every change.
    :param only: Task ids to keep, if given.
    :param kinds: Task kinds to keep, if given.
    :param heldout: Run the held-out tasks instead of the others.
    :return: The tasks, by id."""
    out = [Task.load(f) for f in sorted((HERE / "tasks").glob("*.yaml"))]
    return [
        t
        for t in out
        if (not smoke or t.smoke)
        and (not only or t.id in only)
        and (not kinds or t.kind in kinds)
        and t.heldout == heldout
    ]


def project(task: Task, folder: Path, guide: Path | None) -> tuple[Path, dict[str, str]]:
    """Set up a project for a task: a generated log dir, the agent rules, the MCP server.

    :param task: The task.
    :param folder: The run's folder.
    :param guide: A directory of guide parts that replace the shipped ones, or ``None``.
    :return: The project root and the generated runs by role."""
    from beamtime.ops.admin import END, START, instructions
    from beamtime.synth import generate

    root = folder / "proj"
    now = datetime.now(timezone.utc)
    manifest = generate(root / "beamtime", seed=task.seed, now=now)
    config = "logdir: beamtime\n"
    if task.remote:
        box = root / task.remote
        generate(box / "beamtime", seed=task.seed, now=now)
        (box / "beamtime.yaml").write_text("logdir: beamtime\n")
        command = f"{sys.executable} -m beamtime.cli"
        remote = {"path": str(box / "beamtime"), "command": command, "transport": "command"}
        config += json.dumps({"remotes": {task.remote: remote}}) + "\n"
    (root / "beamtime.yaml").write_text(config)
    instructions(root, root / "CLAUDE.md")
    if guide is not None and (rules := guide / "instructions.md").is_file():
        (root / "CLAUDE.md").write_text(f"{START}\n{rules.read_text().strip()}\n{END}\n")
    beamtime = Path(sys.executable).parent / "beamtime"
    args = ["--root", str(root), "mcp"]
    server = {
        "command": str(beamtime) if guide is None else sys.executable,
        "args": args if guide is None else ["-c", GUIDE_SERVER, str(guide), *args],
        "env": {"BEAMTIME_CACHE": str(folder / "cache")},
    }
    (folder / "mcp.json").write_text(json.dumps({"mcpServers": {"beamtime": server}}))
    return root, manifest.roles


def run_one(task: Task, model: str, rep: int, stamp: Path, guide: Path | None) -> dict[str, Any]:
    """Give one task to one agent and record what it did.

    :param task: The task.
    :param model: The model, as ``claude --model`` takes it.
    :param rep: The repetition.
    :param stamp: The run batch's folder.
    :param guide: A directory of guide parts that replace the shipped ones, or ``None``.
    :return: The record, also written to ``record.json``."""
    folder = stamp / f"{task.id}-{model}-{rep}"
    folder.mkdir(parents=True)
    root, roles = project(task, folder, guide)
    prompt = task.resolve(task.prompt.strip(), roles, root / "beamtime") + TAIL.get(task.kind, "")
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
    page = task.resolve(task.page, roles, root / "beamtime") if task.page else ""
    record = {
        "task": task.id,
        "model": model,
        "rep": rep,
        "kind": task.kind,
        "guide": str(guide) if guide else None,
        "remote": task.remote,
        "page": page,
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
    :return: Tool calls in order (name, input, whether it failed), validation and render rounds,
        turns, tokens and cost."""
    calls: list[dict[str, Any]] = []
    result: dict[str, Any] = {}
    for line in transcript.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        content = (event.get("message") or {}).get("content")
        if not isinstance(content, list):
            content = []
        for part in content:
            if part.get("type") == "tool_use":
                name = part["name"].removeprefix("mcp__beamtime__")
                calls.append({"id": part["id"], "name": name, "input": part.get("input") or {}})
            elif part.get("type") == "tool_result":
                for c in calls:
                    if c["id"] == part.get("tool_use_id"):
                        c["error"] = bool(part.get("is_error"))
        if event.get("type") == "result":
            result = event
    names = [c["name"] for c in calls]
    usage = result.get("usage") or {}
    tokens = {k: v for k, v in usage.items() if k.endswith("tokens")}
    return {
        "tools": names,
        "calls": calls,
        "validations": names.count("view_validate"),
        "renders": names.count("view_render"),
        "tool_errors": sum(bool(c.get("error")) for c in calls),
        "turns": result.get("num_turns"),
        "tokens": tokens,
        "total_tokens": sum(v for v in tokens.values() if isinstance(v, int)),
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
    parser.add_argument("--kinds", nargs="*", help="task kinds; default all")
    parser.add_argument("--heldout", action="store_true", help="the held-out tasks, not the others")
    parser.add_argument("--guide", type=Path, help="a directory of guide parts to test unreleased")
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--no-score", action="store_true", help="only run the agents")
    args = parser.parse_args()
    stamp = RUNS / datetime.now().strftime("%Y%m%d-%H%M%S")
    stamp.mkdir(parents=True)
    chosen = tasks(args.smoke, args.tasks, args.kinds, args.heldout)
    jobs = [(t, m, r) for t in chosen for m in args.models for r in range(args.reps)]
    print(f"{len(jobs)} agent runs into {stamp}", flush=True)
    with ThreadPoolExecutor(args.parallel) as pool:
        for record in pool.map(
            lambda j: run_one(*j, stamp, args.guide and args.guide.resolve()), jobs
        ):
            what = f"{record['status']}, {record['seconds']} s, {len(record['tools'])} tool calls"
            print(f"{record['task']} {record['model']} {record['rep']}: {what}", flush=True)
    if not args.no_score:
        from report import report
        from score import score_batch

        score_batch(stamp)
        report(stamp)


if __name__ == "__main__":
    main()
