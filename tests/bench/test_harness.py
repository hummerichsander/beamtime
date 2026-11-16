"""Tests of the agent harness in ``bench/agents`` that need no agent."""

import sys
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[2] / "bench" / "agents"
sys.path.insert(0, str(BENCH))

import run  # noqa: E402

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
