import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.synth import generate

BEAMTIME = Path(sys.executable).parent / ("beamtime.exe" if sys.platform == "win32" else "beamtime")


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A git project with a generated log dir, for the research-record commands.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The project root."""
    root = tmp_path_factory.mktemp("cli-record") / "proj"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    generate(root / "beamtime", seed=0, now=datetime.now(timezone.utc))
    return root


def beamtime(project: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    """Run the beamtime command in the project, with text on stdin.

    :param project: The project root.
    :param args: The arguments.
    :param stdin: What the command reads from stdin.
    :return: The finished process."""
    env = {k: v for k, v in os.environ.items() if k != "BEAMTIME_LOGDIR"}
    return subprocess.run(
        [str(BEAMTIME), *args], cwd=project, env=env, capture_output=True, text=True, input=stdin
    )


def test_groups_in_help(project: Path) -> None:
    """Two-word commands sit under their group; a bare group prints its help."""
    out = beamtime(project, "--help").stdout
    for name in ("notes", "check", "note", "proposal", "memory"):
        assert f"    {name}" in out
    assert "add" in beamtime(project, "note").stdout


def test_check_and_proposal_text(project: Path) -> None:
    """check and proposal show render compactly."""
    out = beamtime(project, "check", "scaling/lr-sweep").stdout
    assert "pass" in out and "15 of 15 grid points" in out and "converges" in out
    assert "95% t-intervals" in out
    shown = beamtime(project, "proposal", "show", "scaling/lr-sweep").stdout
    assert "statement: lr 0.0003" in shown and "frozen" in shown


def test_note_add_reads_stdin(project: Path) -> None:
    """The body comes from stdin; --verdict pairs and --evidence repeat."""
    version = (project / "beamtime/tokenizer/bpe-vs-unigram/proposal").iterdir().__next__().stem
    out = beamtime(
        project, "note", "add", "tokenizer/bpe-vs-unigram", "--type", "verdict",
        "--description", "Unigram wins.", "--proposal", version,
        "--verdict", "unigram-wins=confirmed", "--overall", "confirmed",
        "--evidence", "tokenizer/bpe-vs-unigram#unigram-wins", "--evidence", '{note: x}',
        "--author", "me", "--json", stdin="Clear gain.\n",
    )  # fmt: skip
    assert out.returncode == 3 and "evidence: no note 'x'" in out.stderr
    out = beamtime(
        project, "note", "add", "tokenizer/bpe-vs-unigram", "--type", "verdict",
        "--description", "Unigram wins.", "--proposal", version,
        "--verdict", "unigram-wins=confirmed", "--overall", "confirmed",
        "--evidence", "tokenizer/bpe-vs-unigram#unigram-wins", "--json", stdin="Clear gain.\n",
    )  # fmt: skip
    assert out.returncode == 0, out.stderr
    path = project / "beamtime" / json.loads(out.stdout)["path"]
    assert "Clear gain." in path.read_text() and "unigram-wins:" in path.read_text()
    notes = beamtime(project, "notes", "tokenizer", "--types", "verdict").stdout
    assert "verdict confirmed on" in notes and "Unigram wins." in notes


def test_proposal_set_from_file_and_errors(project: Path) -> None:
    """A proposal file is saved; validation errors exit with 3."""
    (project / "p.yaml").write_text("statement: More data helps.\nplan: {runs: 3}\n")
    out = beamtime(project, "proposal", "set", "data/size", "p.yaml")
    assert out.returncode == 0 and out.stdout.startswith("wrote data/size/proposal/")
    bad = beamtime(project, "proposal", "set", "data/size", stdin="statment: typo\n")
    assert bad.returncode == 3 and "Did you mean 'statement'" in bad.stderr
    frozen = beamtime(project, "proposal", "set", "scaling/lr-sweep", "p.yaml")
    assert frozen.returncode == 3 and "--reason" in frozen.stderr


def test_memory_commands(project: Path) -> None:
    """memory update reads a file or stdin; memory show prints the chain."""
    out = beamtime(project, "memory", "update", ".", stdin="## Current understanding\n- ok\n")
    assert out.returncode == 0, out.stderr
    shown = beamtime(project, "memory", "show", "tokenizer").stdout
    assert shown.startswith("# memory of .") and "- ok" in shown
