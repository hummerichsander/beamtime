"""The command that agent clients run to start ``beamtime mcp``."""

import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from beamtime.setup.scan import PythonEnv

SERVE_PYTHON = (3, 11)


def mcp_command(
    env: PythonEnv | None,
    root: Path,
    *,
    shared: bool,
    which: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    """Pick the command that starts ``beamtime mcp``, the first that applies.

    A command that names this machine (an absolute path) is returned only if ``shared`` is false.
    The caller adds ``--root`` and passes an ``env`` with the serve extra if ``--sdk`` adds it.

    :param env: The project's Python environment, or ``None``.
    :param root: The project root.
    :param shared: Whether the command goes into a file that git shares.
    :param which: Looks up a program on ``PATH``.
    :return: The command, or ``None`` when only an absolute path works and ``shared`` is true."""
    hosts_serve = env is not None and env.has_serve and python_hosts_serve(env)

    if hosts_serve and env.tool == "uv" and which("uv"):
        return ["uv", "run", "--project", "." if shared else str(root), "beamtime", "mcp"]
    if hosts_serve and env.tool == "conda" and env.path and which("conda"):
        name = conda_name(env.path)
        return ["conda", "run", "--no-capture-output", "-n", name, "beamtime", "mcp"]

    if (launcher := which("beamtime")) and not inside(Path(launcher), root, env):
        if check_command([launcher, "mcp"])[1]:
            return ["beamtime", "mcp"] if shared else [launcher, "mcp"]

    if which("uv"):
        return ["uvx", "--from", "beamtime[serve]", "beamtime", "mcp"]

    if not shared and hosts_serve and (script := env_launcher(env)):
        return [str(script), "mcp"]
    return None


def check_command(cmd: list[str]) -> tuple[str | None, bool]:
    """Ask a candidate command for its version and whether it has the serve extra.

    :param cmd: The command that starts the server, ending in ``mcp``.
    :return: The version and whether the serve extra is present; ``(None, False)`` when it fails."""
    try:
        out = subprocess.run(
            [*cmd[:-1], "--version"], capture_output=True, text=True, timeout=5, check=True
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None, False
    if not (match := re.match(r"beamtime (\S+)(.*)", out.strip())):
        return None, False
    return match[1], "no serve extra" not in match[2]


def conda_name(prefix: Path) -> str:
    """Name a conda environment by its prefix.

    :param prefix: The environment's folder.
    :return: ``base`` for the conda install itself, else the folder's name."""
    return "base" if (prefix / "condabin").is_dir() else prefix.name


def python_hosts_serve(env: PythonEnv) -> bool:
    """Tell whether the environment's Python is new enough for the MCP server.

    :param env: The project's Python environment.
    :return: ``False`` for a known Python older than 3.11."""
    if env.python is None:
        return True
    major, _, minor = env.python.partition(".")
    return (int(major), int(minor or 0)) >= SERVE_PYTHON if major.isdigit() else True


def inside(launcher: Path, root: Path, env: PythonEnv | None) -> bool:
    """Tell whether a launcher lives in the project or in its environment.

    :param launcher: The launcher found on ``PATH``.
    :param root: The project root.
    :param env: The project's Python environment, or ``None``.
    :return: ``True`` when the launcher would break with the environment."""
    launcher = launcher.resolve()
    folders = [root.resolve(), *([env.path.resolve()] if env and env.path else [])]
    return any(launcher.is_relative_to(folder) for folder in folders)


def env_launcher(env: PythonEnv) -> Path | None:
    """Find the ``beamtime`` launcher of an environment.

    :param env: The project's Python environment.
    :return: The launcher, or ``None`` when the environment has none."""
    if env.path is None:
        return None
    candidates = (env.path / "bin" / "beamtime", env.path / "Scripts" / "beamtime.exe")
    return next((c for c in candidates if c.is_file()), None)
