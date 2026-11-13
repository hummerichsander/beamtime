"""Tests of adding the SDK with the project's tool."""

import subprocess
from pathlib import Path

import pytest

from beamtime.setup.sdk import sdk_blocker, sdk_change, sdk_commands
from beamtime.setup.scan import PythonEnv


def env_of(tool: str, root: Path, *, python: str | None = "3.12", path: bool = True) -> PythonEnv:
    """Build a Python environment of the scan.

    :param tool: The environment tool.
    :param root: The folder holding the environment.
    :param python: The Python version.
    :param path: Whether the environment exists on disk.
    :return: The environment."""
    folder = root / "envs" / "exp" if tool == "conda" else root / ".venv"
    return PythonEnv(tool, folder if path else None, python, None, False)


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch) -> list[tuple[list[str], Path]]:
    """Record the subprocesses of the SDK module instead of running them.

    :param monkeypatch: The patcher.
    :return: The list that fills with the argument lists and working folders."""
    recorded = []

    def fake(command: list[str], *, cwd: Path, check: bool) -> None:
        assert check
        recorded.append((command, cwd))

    monkeypatch.setattr(subprocess, "run", fake)
    return recorded


def test_uv_adds_the_package(tmp_path: Path) -> None:
    """uv adds beamtime to the dependencies only."""
    assert sdk_commands(env_of("uv", tmp_path), False) == [["uv", "add", "beamtime"]]


def test_uv_adds_the_serve_extra_to_the_dev_group(tmp_path: Path) -> None:
    """When the MCP command uses the project env, the dev group gets the serve extra."""
    assert sdk_commands(env_of("uv", tmp_path), True) == [
        ["uv", "add", "beamtime"],
        ["uv", "add", "--dev", "beamtime[serve]"],
    ]


def test_poetry(tmp_path: Path) -> None:
    """Poetry adds the package."""
    assert sdk_commands(env_of("poetry", tmp_path), True) == [["poetry", "add", "beamtime"]]


def test_conda_names_the_environment(tmp_path: Path) -> None:
    """Conda installs with pip inside the named environment, with the extra when MCP runs there."""
    env = env_of("conda", tmp_path)
    run = ["conda", "run", "-n", "exp", "python", "-m", "pip", "install"]
    assert sdk_commands(env, False) == [[*run, "beamtime"]]
    assert sdk_commands(env, True) == [[*run, "beamtime[serve]"]]


def test_pip_uses_the_venv_python(tmp_path: Path) -> None:
    """Pip runs the virtualenv's own interpreter."""
    python = str(tmp_path / ".venv" / "bin" / "python")
    assert sdk_commands(env_of("pip", tmp_path), False) == [
        [python, "-m", "pip", "install", "beamtime"]
    ]


def test_pip_without_a_venv_only_writes_the_requirements(tmp_path: Path) -> None:
    """A project with requirements but no virtualenv gets no install command."""
    env = env_of("pip", tmp_path, path=False)
    assert sdk_commands(env, False) == []
    assert "requirements.txt" in sdk_change(env, "0.3.0", False, root=tmp_path).after


def test_change_runs_the_commands_in_the_root(
    tmp_path: Path, calls: list[tuple[list[str], Path]]
) -> None:
    """The change lands in the project and runs each command with the root as working folder."""
    change = sdk_change(env_of("uv", tmp_path), "0.3.0", True, root=tmp_path)
    assert change.where == "project"
    assert change.before is None
    assert "0.3.0" in change.label
    assert change.after == "uv add beamtime\nuv add --dev 'beamtime[serve]'"
    assert calls == []

    change.run()

    assert calls == [
        (["uv", "add", "beamtime"], tmp_path),
        (["uv", "add", "--dev", "beamtime[serve]"], tmp_path),
    ]


def test_change_shows_the_installed_version(tmp_path: Path) -> None:
    """An installed Beamtime shows as the before of the change."""
    env = PythonEnv("poetry", tmp_path / ".venv", "3.11", "0.2.0", False)
    assert sdk_change(env, "0.3.0", False, root=tmp_path).before == "beamtime 0.2.0"


def test_pip_appends_a_requirements_line_once(
    tmp_path: Path, calls: list[tuple[list[str], Path]]
) -> None:
    """The requirements line is added after the install, and a second run leaves it alone."""
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("numpy\nbeamtime-extras\n")
    change = sdk_change(env_of("pip", tmp_path), "0.3.0", False, root=tmp_path)

    change.run()
    change.run()

    assert requirements.read_text() == "numpy\nbeamtime-extras\nbeamtime\n"
    assert len(calls) == 2


def test_failed_install_stops_before_the_requirements(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failing command raises and leaves requirements.txt alone."""

    def fail(command: list[str], **_: object) -> None:
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(subprocess, "run", fail)
    change = sdk_change(env_of("pip", tmp_path), "0.3.0", False, root=tmp_path)

    with pytest.raises(subprocess.CalledProcessError):
        change.run()

    assert not (tmp_path / "requirements.txt").exists()


@pytest.mark.parametrize("python", ["3.9", "3.8", "2.7"])
def test_python_older_than_3_10_gives_none_with_a_reason(tmp_path: Path, python: str) -> None:
    """An environment that cannot host the SDK gets no change, and the reason names the version."""
    env = env_of("uv", tmp_path, python=python)
    assert sdk_change(env, "0.3.0", False, root=tmp_path) is None
    assert python in sdk_blocker(env)


@pytest.mark.parametrize("python", ["3.10", "3.12", "3.13", None])
def test_python_3_10_and_newer_or_unknown_fits(tmp_path: Path, python: str | None) -> None:
    """3.10 is the oldest Python the SDK supports, and an unknown one is not blocked."""
    env = env_of("uv", tmp_path, python=python)
    assert sdk_blocker(env) is None
    assert sdk_change(env, "0.3.0", False, root=tmp_path) is not None
