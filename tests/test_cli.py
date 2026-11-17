import os
import subprocess
import sys
from pathlib import Path

import pytest

from beamtime import __version__


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_version() -> None:
    """The CLI reports the installed package version."""
    out = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert __version__ in out.stdout


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_version_without_serve_extra() -> None:
    """The version gains a note when the serve extra's ``mcp`` package is missing."""
    code = (
        "import sys; sys.modules['mcp'] = None; sys.argv = ['beamtime', '--version'];"
        "from beamtime.cli import main; main()"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert f"beamtime {__version__} (no serve extra)" in out.stdout


@pytest.mark.skipif(sys.version_info >= (3, 11), reason="only on Python 3.10")
def test_cli_refuses_python_310() -> None:
    """On Python 3.10 the CLI explains that it needs 3.11 and the SDK still works."""
    out = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert out.returncode == 1 and "needs Python 3.11" in out.stderr


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_tool_names_split() -> None:
    """An MCP tool name becomes its spaced command, also after global flags."""
    from beamtime.cli import tool_names

    assert tool_names(["memory_show"]) == ["memory", "show"]
    assert tool_names(["proposal_show", "g"]) == ["proposal", "show", "g"]
    assert tool_names(["--root", "P", "note_add", "g", "x"]) == [
        "--root",
        "P",
        "note",
        "add",
        "g",
        "x",
    ]
    assert tool_names(["--json", "note_add", "g"]) == ["--json", "note", "add", "g"]


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_tool_names_skip_root_value() -> None:
    """A ``--root`` value containing an underscore is a value, not a command."""
    from beamtime.cli import tool_names

    assert tool_names(["--root", "memory_show", "runs"]) == ["--root", "memory_show", "runs"]
    assert tool_names(["--root", "my_proj", "runs"]) == ["--root", "my_proj", "runs"]


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_tool_names_only_first_word() -> None:
    """Only the first positional is rewritten; plain commands and later words stay."""
    from beamtime.cli import tool_names

    assert tool_names(["runs", "memory_show"]) == ["runs", "memory_show"]
    assert tool_names(["runs", "g"]) == ["runs", "g"]
    assert tool_names(["not_a_tool"]) == ["not_a_tool"]
    assert tool_names([]) == []


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_no_log_dir_names_root(tmp_path: Path) -> None:
    """Outside a project, ``runs`` and a tool-named command say how to fix it and exit 4."""
    for argv in (["runs"], ["memory_show"]):
        out = subprocess.run(
            [sys.executable, "-m", "beamtime.cli", *argv],
            capture_output=True,
            text=True,
            cwd=tmp_path,
            env={**os.environ, "BEAMTIME_LOGDIR": ""},
        )
        assert out.returncode == 4, out.stderr
        assert "no log dir at" in out.stderr
        assert "run from the project folder or pass `--root <project>`" in out.stderr
