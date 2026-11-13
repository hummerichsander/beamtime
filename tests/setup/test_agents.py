"""Tests of the portable MCP command."""

from pathlib import Path
import os
import stat
import sys

import pytest

from beamtime.setup.agents import check_command, mcp_command
from beamtime.setup.scan import PythonEnv

posix = pytest.mark.skipif(sys.platform == "win32", reason="the fake launchers are shell scripts")


def launcher(folder: Path, name: str, *, serve: bool = True) -> Path:
    """Write a fake program that answers ``--version`` like the CLI.

    :param folder: The folder to put it in.
    :param name: The program's name.
    :param serve: Whether it reports the serve extra.
    :return: The program's path."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    word = "" if serve else " (no serve extra)"
    path.write_text(f'#!/bin/sh\necho "beamtime 0.3.0{word}"\n')
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def env_of(tool: str, root: Path, *, python: str = "3.12", serve: bool = True) -> PythonEnv:
    """Build a Python environment of the scan.

    :param tool: The environment tool.
    :param root: The folder holding the environment.
    :param python: The Python version.
    :param serve: Whether the serve extra is installed.
    :return: The environment."""
    path = root / ".venv" if tool != "conda" else root / "envs" / "exp"
    return PythonEnv(tool, path, python, "0.3.0", serve)


@pytest.fixture
def bins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``PATH`` at an empty folder, so only the programs a test adds are found.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :return: The folder on ``PATH``."""
    folder = tmp_path / "bin"
    folder.mkdir()
    monkeypatch.setenv("PATH", str(folder))
    return folder


@posix
def test_uv_project(bins: Path, tmp_path: Path) -> None:
    """A uv project with the serve extra runs through ``uv run``, relative in shared files."""
    launcher(bins, "uv")
    root = tmp_path / "project"
    env = env_of("uv", root)
    assert mcp_command(env, root, shared=True) == ["uv", "run", "--project", ".", "beamtime", "mcp"]
    assert mcp_command(env, root, shared=False)[2:4] == ["--project", str(root)]


@posix
def test_conda(bins: Path, tmp_path: Path) -> None:
    """A conda environment with the serve extra runs through ``conda run``."""
    launcher(bins, "conda")
    cmd = mcp_command(env_of("conda", tmp_path), tmp_path, shared=True)
    assert cmd == ["conda", "run", "--no-capture-output", "-n", "exp", "beamtime", "mcp"]


@posix
def test_conda_no_serve(bins: Path, tmp_path: Path) -> None:
    """A conda environment without the serve extra falls through to the tool install."""
    launcher(bins, "conda")
    launcher(bins, "beamtime")
    root = tmp_path / "project"
    cmd = mcp_command(env_of("conda", root, serve=False), root, shared=True)
    assert cmd == ["beamtime", "mcp"]


@posix
def test_py310_project_falls_through(bins: Path, tmp_path: Path) -> None:
    """A project on Python 3.10 cannot host the server and uses the tool install."""
    launcher(bins, "uv")
    path = launcher(tmp_path / "tools", "beamtime")
    os.environ["PATH"] += os.pathsep + str(path.parent)
    cmd = mcp_command(env_of("uv", tmp_path / "p", python="3.10"), tmp_path / "p", shared=False)
    assert cmd == [str(path), "mcp"]


@posix
def test_tool_install(bins: Path, tmp_path: Path) -> None:
    """A tool install is ``beamtime mcp`` when shared and its absolute path otherwise."""
    path = launcher(bins, "beamtime")
    root = tmp_path / "project"
    assert mcp_command(None, root, shared=True) == ["beamtime", "mcp"]
    assert mcp_command(None, root, shared=False) == [str(path), "mcp"]


@posix
def test_tool_without_serve_is_skipped(bins: Path, tmp_path: Path) -> None:
    """A tool install without the serve extra gives way to uvx."""
    launcher(bins, "beamtime", serve=False)
    launcher(bins, "uv")
    cmd = mcp_command(None, tmp_path, shared=True)
    assert cmd == ["uvx", "--from", "beamtime[serve]", "beamtime", "mcp"]


@posix
def test_launcher_in_project_is_skipped(bins: Path, tmp_path: Path) -> None:
    """A launcher inside the project's environment is never taken as the tool install."""
    root = tmp_path / "project"
    launcher(root / ".venv" / "bin", "beamtime")
    os.environ["PATH"] += os.pathsep + str(root / ".venv" / "bin")
    assert mcp_command(env_of("pip", root), root, shared=True) is None


@posix
def test_uvx(bins: Path, tmp_path: Path) -> None:
    """Without an install, uv alone is enough."""
    launcher(bins, "uv")
    cmd = mcp_command(None, tmp_path, shared=True)
    assert cmd == ["uvx", "--from", "beamtime[serve]", "beamtime", "mcp"]


@posix
def test_venv_not_shared(bins: Path, tmp_path: Path) -> None:
    """A pip virtualenv gives its absolute launcher in machine files and nothing in shared ones."""
    root = tmp_path / "project"
    script = launcher(root / ".venv" / "bin", "beamtime")
    env = env_of("pip", root)
    assert mcp_command(env, root, shared=True) is None
    assert mcp_command(env, root, shared=False) == [str(script), "mcp"]


@posix
def test_nothing(bins: Path, tmp_path: Path) -> None:
    """With no environment, no install and no uv there is no command."""
    assert mcp_command(None, tmp_path, shared=False) is None


@posix
def test_shared_is_never_absolute(bins: Path, tmp_path: Path) -> None:
    """Whatever applies, a shared command holds no absolute path."""
    launcher(bins, "uv")
    launcher(bins, "conda")
    launcher(bins, "beamtime")
    root = tmp_path / "project"
    for tool in ("uv", "conda", "pip"):
        cmd = mcp_command(env_of(tool, root), root, shared=True)
        assert cmd and not any(Path(part).is_absolute() for part in cmd)


@posix
def test_check_command(tmp_path: Path) -> None:
    """The probe reads the version and the serve extra, and survives a missing program."""
    ok = launcher(tmp_path, "ok")
    bare = launcher(tmp_path, "bare", serve=False)
    assert check_command([str(ok), "mcp"]) == ("0.3.0", True)
    assert check_command([str(bare), "mcp"]) == ("0.3.0", False)
    assert check_command([str(tmp_path / "missing"), "mcp"]) == (None, False)
