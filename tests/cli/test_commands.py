import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.synth import generate

BEAMTIME = Path(sys.executable).parent / ("beamtime.exe" if sys.platform == "win32" else "beamtime")


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A git project with a generated log dir.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The project root."""
    root = tmp_path_factory.mktemp("cli") / "proj"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    generate(root / "beamtime", seed=0, now=datetime.now(timezone.utc))
    return root


def beamtime(project: Path, *args: str) -> subprocess.CompletedProcess:
    """Run the beamtime command in the project.

    :param project: The project root.
    :param args: The arguments.
    :return: The finished process."""
    env = {k: v for k, v in os.environ.items() if k != "BEAMTIME_LOGDIR"}
    return subprocess.run(
        [str(BEAMTIME), *args], cwd=project, env=env, capture_output=True, text=True
    )


def test_help_lists_operations(project: Path) -> None:
    """--help lists reading and user-only commands, marked as such."""
    out = beamtime(project, "--help").stdout
    for name in ("runs", "series", "card", "output", "timeline", "doctor", "gc", "mcp"):
        assert f"    {name}" in out
    assert "(user only)" in out


def test_json_equals_the_operation(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """--json prints the canonical answer of the operation."""
    out = beamtime(project, "runs", "scaling/lr-sweep", "--select", "config.lr", "--json")
    monkeypatch.chdir(project)
    expected = call("runs", {"from": "scaling/lr-sweep", "select": ["config.lr"]}, Context.make())
    assert json.loads(out.stdout)["rows"] == expected["rows"]


def test_flags_map_onto_queries(project: Path) -> None:
    """--where, --sort with a leading minus, --select and --limit."""
    out = beamtime(
        project, "runs", "scaling/lr-sweep",
        "--where", "config.lr<1e-3", "--where", "run.status=finished",
        "--select", "run.name,config.lr,metric.val/acc.last",
        "--sort", "-metric.val/acc.last", "--limit", "3",
    )  # fmt: skip
    lines = out.stdout.splitlines()
    assert lines[0].split() == ["run", "config.lr", "val/acc.last", "id"]
    assert all(line.split()[1] == "3e-4" for line in lines[1:4])
    assert lines[-1].startswith("3 of 9 runs")


def test_series_steps_and_query_argument(project: Path) -> None:
    """--steps takes first:last; query takes inline YAML flow or JSON."""
    out = beamtime(project, "series", "tokenizer", "-y", "val/ppl", "--steps", "0:500", "--json")
    assert all(max(c["x"]) <= 500 for c in json.loads(out.stdout)["curves"])
    out = beamtime(project, "query", "{folders: {from: tokenizer}}")
    assert "bpe-vs-unigram" in out.stdout
    query = project / "q.yaml"
    query.write_text("keys:\n  from: tokenizer\n")
    assert "6 runs" in beamtime(project, "query", str(query)).stdout


@pytest.mark.parametrize(
    "args, code, text",
    [
        (["runs", "nope"], 4, "no folder 'nope'"),
        (["runs", "--select", "metric.val/acc.mx"], 2, "metric field"),
        (["runs", "--where", "config.lr"], 2, "operator"),
        (["card", "20200101-000000-zzzzzzzz"], 4, "no run"),
        (["runs", "--limit", "x"], 2, "invalid int"),
        (["frobnicate"], 2, "invalid choice"),
    ],
)
def test_exit_codes(project: Path, args: list[str], code: int, text: str) -> None:
    """Errors exit with 2 (usage) or 4 (not found) and say what to do."""
    out = beamtime(project, *args)
    assert out.returncode == code and text in out.stderr


def test_root_flag(project: Path, tmp_path: Path) -> None:
    """--root answers for another project from anywhere."""
    out = beamtime(tmp_path, "--root", str(project), "keys", ".")
    assert out.returncode == 0 and out.stdout.startswith("26 runs")


def test_mcp_without_extra_explains(project: Path, tmp_path: Path) -> None:
    """Without the MCP SDK, beamtime mcp says how to install it."""
    code = (
        "import sys; sys.modules['anyio'] = None; "
        "from beamtime.mcp import serve; sys.exit(serve())"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 1 and "beamtime[serve]" in out.stderr
