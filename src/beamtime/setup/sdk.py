"""Adding the Beamtime SDK to the project with the tool that manages its environment."""

import re
import shlex
import subprocess
from functools import partial
from pathlib import Path

from beamtime.setup.agents import conda_name
from beamtime.setup.plan import Change
from beamtime.setup.scan import PythonEnv

SDK_PYTHON = (3, 10)
REQUIREMENTS = "requirements.txt"


def sdk_change(
    env: PythonEnv, version: str, mcp_from_env: bool, *, root: Path, upgrade: bool = False
) -> Change | None:
    """Plan adding the SDK to the project's environment with its own tool.

    :param env: The project's Python environment.
    :param version: The Beamtime release that gets installed, for the review.
    :param mcp_from_env: Whether the MCP command runs from this environment.
    :param root: The project root, where the commands run.
    :param upgrade: Whether Beamtime is there already and ``version`` is the oldest to accept.
    :return: The change, or ``None`` when its Python is too old (see ``sdk_blocker``)."""
    if sdk_blocker(env) is not None:
        return None
    commands = sdk_commands(env, mcp_from_env, version if upgrade else None)
    requirements = root / REQUIREMENTS if env.tool == "pip" else None
    steps = [shlex.join(c) for c in commands]
    if requirements is not None:
        steps.append(f"add beamtime to {REQUIREMENTS}")
    return Change(
        where="project",
        label=f"Beamtime {version} in the {env.tool} environment",
        before=f"beamtime {env.beamtime_version}" if env.beamtime_version else None,
        after="\n".join(steps),
        run=partial(install, commands, root, requirements),
    )


def sdk_blocker(env: PythonEnv) -> str | None:
    """Say why the SDK cannot go into an environment.

    :param env: The project's Python environment.
    :return: The reason, or ``None`` when the SDK fits (an unknown Python counts as fitting)."""
    if env.python is None or not (match := re.match(r"(\d+)\.(\d+)", env.python)):
        return None
    found = (int(match[1]), int(match[2]))
    if found >= SDK_PYTHON:
        return None
    return f"the project's Python is {env.python}, and the SDK needs 3.10 or newer"


def sdk_commands(env: PythonEnv, mcp_from_env: bool, upgrade: str | None = None) -> list[list[str]]:
    """List the commands that install the SDK with the environment's tool.

    :param env: The project's Python environment.
    :param mcp_from_env: Whether the MCP command runs from this environment.
    :param upgrade: The oldest release to accept when Beamtime is installed already.
    :return: The argument lists, run in order in the project root."""
    need = f">={upgrade}" if upgrade else ""
    match env.tool:
        case "uv":
            commands = [["uv", "add", f"beamtime{need}"]]
            if mcp_from_env:
                commands.append(["uv", "add", "--dev", f"beamtime[serve]{need}"])
            return commands
        case "poetry":
            return [["poetry", "add", f"beamtime{need}"]]
        case "conda":
            name = conda_name(env.path) if env.path else "base"
            package = f"beamtime[serve]{need}" if mcp_from_env else f"beamtime{need}"
            pip = ["python", "-m", "pip", "install", *(["-U"] if upgrade else [])]
            return [["conda", "run", "-n", name, *pip, package]]
        case "pip":
            if env.path is None:
                return []
            windows = env.path / "Scripts" / "python.exe"
            python = windows if windows.is_file() else env.path / "bin" / "python"
            pip = ["-m", "pip", "install", *(["-U"] if upgrade else [])]
            return [[str(python), *pip, f"beamtime{need}"]]
        case _:
            raise ValueError(f"unknown tool {env.tool}")


def install(commands: list[list[str]], root: Path, requirements: Path | None) -> None:
    """Run the install commands, then add the requirements line, stopping at the first failure.

    :param commands: The argument lists.
    :param root: The folder the commands run in.
    :param requirements: The ``requirements.txt`` that gets a ``beamtime`` line, or ``None``."""
    for command in commands:
        subprocess.run(command, cwd=root, check=True)
    if requirements is None:
        return
    lines = requirements.read_text(encoding="utf-8").splitlines() if requirements.is_file() else []
    if not any(re.match(r"beamtime\b(?![-_.])", line) for line in lines):
        requirements.write_text("\n".join([*lines, "beamtime"]) + "\n", encoding="utf-8")
