"""Tests of the agent harness in ``bench/agents`` that need no agent."""

import json
import sys
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[2] / "bench" / "agents"
sys.path.insert(0, str(BENCH))

import run  # noqa: E402
import score  # noqa: E402

START, END = "<!-- beamtime:start -->", "<!-- beamtime:end -->"


@pytest.fixture
def task() -> run.Task:
    """A task of the harness.

    :return: The first task with a plain log dir."""
    return run.Task.load(BENCH / "tasks" / "analysis-best-lr.yaml")


def test_project_writes_rules(task: run.Task, tmp_path: Path) -> None:
    """The project's CLAUDE.md holds the marked rules block, rendered from its settings."""
    root, _ = run.project(task, tmp_path, None)
    text = (root / "CLAUDE.md").read_text()

    assert text.startswith(START) and text.rstrip().endswith(END)
    assert "{{" not in text
    assert any(line in text for line in ("Never launch runs yourself.", "Ask before you launch a run."))


def test_guide_override_replaces_block(task: run.Task, tmp_path: Path) -> None:
    """``instructions.md`` of a guide folder replaces the text between the markers."""
    guide = tmp_path / "guide"
    guide.mkdir()
    (guide / "instructions.md").write_text("Custom rules.\n")

    root, _ = run.project(task, tmp_path / "run", guide)

    assert (root / "CLAUDE.md").read_text() == f"{START}\nCustom rules.\n{END}\n"


def test_summary_counts_rounds_through_tools_more(tmp_path: Path) -> None:
    """A validate or render call made through ``tools_more`` counts as a round of its own tool."""
    uses = [
        ("tools_more", {"family": "views"}),
        ("tools_more", {"family": "views", "tool": "view_validate", "args": {"draft": "d"}}),
        ("mcp__beamtime__tools_more", {"tool": "view_render", "args": {"draft": "d"}}),
        ("mcp__beamtime__view_validate", {"draft": "d"}),
    ]
    events = [
        {"message": {"content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": args}]}}
        for i, (name, args) in enumerate(uses)
    ]
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text("\n".join(json.dumps(e) for e in events))

    got = run.summary(transcript)

    assert got["validations"] == 2 and got["renders"] == 1
    assert got["tools"] == ["tools_more", "view_validate", "view_render", "view_validate"]


def test_violations_only_count_the_runs_log_dir() -> None:
    """The repository checkout named beamtime around the run is not the log dir."""
    repo = "/home/u/Sidequests/beamtime/bench/agents/runs/20260101-000000/view-x-sonnet-0/proj"
    calls = [
        {"name": "Read", "input": {"file_path": f"{repo}/external/jax-sweep.csv"}},
        {"name": "Write", "input": {"file_path": f"{repo}/.beamtime/drafts/d/data/a.csv"}},
        {"name": "Edit", "input": {"file_path": f"{repo}/.beamtime/drafts/d/view.yaml"}},
        {"name": "Grep", "input": {"pattern": "x", "path": f"{repo}/beamtime/scaling/lr-sweep"}},
        {"name": "Read", "input": {"file_path": "beamtime/scaling/lr-sweep/_run.json"}},
        {"name": "Write", "input": {"file_path": f"{repo}/beamtime/scaling/x/notes/n.md"}},
    ]

    got = score.violations({"calls": calls})

    assert got == {"raw_reads": 2, "log_edits": 1, "user_only": 0}
