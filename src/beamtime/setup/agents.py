"""The agent clients: how they start ``beamtime mcp``, and their config and rules files."""

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from beamtime.setup.plan import Change
from beamtime.setup.scan import PythonEnv

if TYPE_CHECKING:
    from beamtime.settings import AgentSettings

SERVE_PYTHON = (3, 11)
SERVER = "beamtime"
TOML_HEADER = re.compile(r"^\[mcp_servers\.beamtime\][ \t]*(?:#.*)?$", re.MULTILINE)
TOML_TABLE = re.compile(r"^\[", re.MULTILINE)


class ConfigError(Exception):
    """A client's config can't be edited; the message names the file and what to do."""


@dataclass(frozen=True, kw_only=True)
class Client:
    """One agent client: its MCP config, its rules file and how to start it with a prompt."""

    name: str
    label: str
    config: str
    key: str
    shared: bool
    rules: str
    start: list[str] | None
    skills: bool


CLIENTS = (
    Client(
        name="claude-code",
        label="Claude Code",
        config=".mcp.json",
        key="mcpServers",
        shared=True,
        rules="CLAUDE.md",
        start=["claude"],
        skills=True,
    ),
    Client(
        name="codex",
        label="Codex",
        config="~/.codex/config.toml",
        key="mcp_servers",
        shared=False,
        rules="AGENTS.md",
        start=["codex"],
        skills=False,
    ),
    Client(
        name="cursor",
        label="Cursor",
        config=".cursor/mcp.json",
        key="mcpServers",
        shared=True,
        rules="AGENTS.md",
        start=None,
        skills=False,
    ),
    Client(
        name="vscode",
        label="VS Code (Copilot)",
        config=".vscode/mcp.json",
        key="servers",
        shared=True,
        rules="AGENTS.md",
        start=None,
        skills=False,
    ),
    Client(
        name="gemini",
        label="Gemini CLI",
        config=".gemini/settings.json",
        key="mcpServers",
        shared=True,
        rules="GEMINI.md",
        start=["gemini", "-i"],
        skills=False,
    ),
    Client(
        name="opencode",
        label="opencode",
        config="opencode.json",
        key="mcp",
        shared=True,
        rules="AGENTS.md",
        start=None,
        skills=False,
    ),
    Client(
        name="windsurf",
        label="Windsurf",
        config="~/.codeium/windsurf/mcp_config.json",
        key="mcpServers",
        shared=False,
        rules="AGENTS.md",
        start=None,
        skills=False,
    ),
    Client(
        name="other",
        label="Another agent",
        config="",
        key="mcpServers",
        shared=False,
        rules="AGENTS.md",
        start=None,
        skills=False,
    ),
)


def client_named(name: str) -> Client:
    """Look a client up by name.

    :param name: The client's name, e.g. ``claude-code``.
    :return: The client."""
    return next(c for c in CLIENTS if c.name == name)


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


def register(
    client: Client,
    root: Path,
    env: PythonEnv | None,
    *,
    home: Path | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> Change:
    """Plan registering ``beamtime mcp`` with a client, keeping every other server in its config.

    Claude Code, Cursor and VS Code fall back to this machine's own config when the command isn't
    portable; Codex and Windsurf are user-wide and name the root; ``other`` prints its JSON.

    :param client: The agent client.
    :param root: The project root.
    :param env: The project's Python environment, or ``None``.
    :param home: The home directory; default the user's.
    :param which: Looks up a program on ``PATH``.
    :return: The change; its ``run`` writes the config.
    :raises ConfigError: When no command works or the client's config is not valid."""
    home = home or Path.home()
    root = root.resolve()
    command = mcp_command(env, root, shared=True, which=which) if client.shared else None
    scope = "project" if command else "machine"
    if command is None:
        command = mcp_command(env, root, shared=False, which=which)
    if command is None:
        raise ConfigError(
            "no command starts `beamtime mcp`: install it with `uv tool install 'beamtime[serve]'`"
        )

    keys = [client.key]
    match client.name:
        case "cursor" | "vscode" if scope == "project":
            roots = ["${workspaceFolder}"]
            path = root / client.config
        case "claude-code" | "cursor" | "vscode" if scope == "machine":
            roots = [str(root)]
            path = machine_config(client, home)
            if client.name == "claude-code":
                keys = ["projects", str(root), client.key]
        case "gemini" | "opencode" if scope == "machine":
            raise ConfigError(
                f"the command for {client.label} would name this machine, which a file shared "
                "through git must not: install beamtime with `uv tool install 'beamtime[serve]'`"
            )
        case "claude-code" | "gemini" | "opencode":
            roots = []
            path = root / client.config
        case _:
            roots = [str(root)]
            path = expand_home(client.config, home) if client.config else None
    full = command[:-1] + [x for r in roots for x in ("--root", r)] + command[-1:]

    if client.name == "other":
        text = json.dumps({client.key: {SERVER: server_entry(client, full)}}, indent=2)
        return Change(
            where="machine",
            label=f"MCP config for {client.label}, to paste",
            before=None,
            after=text,
            run=lambda: None,
        )

    if path.suffix == ".toml":
        before = read_toml(path)
        run = lambda: put_toml(path, full)  # noqa: E731
    else:
        before = read_json(path)
        run = lambda: put_json(path, keys, server_entry(client, full), client)  # noqa: E731
    return Change(
        where="project" if scope == "project" and client.shared else "machine",
        label=f"MCP server for {client.label}",
        before="registered" if before else None,
        after=f"{display(path, root, home)}: {' '.join(full)}",
        run=run,
    )


def rules_change(
    client: Client, root: Path, agent: "AgentSettings", user_only: Iterable[str]
) -> Change:
    """Plan writing Beamtime's rules block into a client's rules file.

    :param client: The agent client.
    :param root: The project root.
    :param agent: The project's agent settings, which the block is generated from.
    :param user_only: The names of the user-only commands.
    :return: The change; its ``run`` returns ``added``, ``updated`` or ``unchanged``."""
    from beamtime.guide.rules import read_block, release_of, render, write_block

    file = root / client.rules
    block = render(agent, user_only)
    old = read_block(file)
    return Change(
        where="project",
        label=f"Agent rules in {client.rules}",
        before=(release_of(old) or "unversioned") if old is not None else None,
        after=release_of(block) or "unversioned",
        run=lambda: write_block(file, block),
    )


def server_entry(client: Client, command: list[str]) -> dict[str, Any]:
    """Shape the server entry the way a client reads it.

    :param client: The agent client.
    :param command: The command with its arguments.
    :return: The entry for the client's servers table."""
    match client.name:
        case "opencode":
            return {"type": "local", "command": command, "enabled": True}
        case "vscode":
            return {"type": "stdio", "command": command[0], "args": command[1:]}
        case _:
            return {"command": command[0], "args": command[1:]}


def machine_config(client: Client, home: Path) -> Path:
    """Find a client's machine-level config, the one git never sees.

    :param client: Claude Code, Cursor or VS Code.
    :param home: The home directory.
    :return: The file."""
    match client.name:
        case "claude-code":
            return home / ".claude.json"
        case "cursor":
            return home / ".cursor" / "mcp.json"
        case "vscode" if sys.platform == "darwin":
            return home / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
        case "vscode" if sys.platform == "win32":
            appdata = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
            return appdata / "Code" / "User" / "mcp.json"
        case "vscode":
            config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
            return config / "Code" / "User" / "mcp.json"
        case _:
            raise ValueError(f"{client.name} has no machine-level config")


def expand_home(config: str, home: Path) -> Path:
    """Resolve a client's config path against the home directory.

    :param config: The path, possibly starting with ``~/``.
    :param home: The home directory.
    :return: The absolute path."""
    return home / config.removeprefix("~/") if config.startswith("~/") else Path(config)


def display(path: Path, root: Path, home: Path) -> str:
    """Show a path relative to the project or as ``~/...``, as the review reads best.

    :param path: The file.
    :param root: The project root.
    :param home: The home directory.
    :return: The short form."""
    for base, prefix in ((root, ""), (home, "~/")):
        if path.is_relative_to(base):
            return prefix + path.relative_to(base).as_posix()
    return str(path)


def read_json(path: Path) -> dict[str, Any]:
    """Read a client's JSON config, which may not exist yet.

    :param path: The file.
    :return: The content; empty when the file is missing or empty.
    :raises ConfigError: When the file is not a JSON object."""
    if not path.exists() or not (text := path.read_text()).strip():
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ConfigError(f"{path} is not valid JSON ({e}); fix it and run this again") from e
    if not isinstance(data, dict):
        raise ConfigError(f"{path} is not a JSON object; fix it and run this again")
    return data


def put_json(path: Path, keys: list[str], entry: dict[str, Any], client: Client) -> None:
    """Set the beamtime server in a client's JSON config, keeping everything else.

    :param path: The file.
    :param keys: The nested keys of the servers table.
    :param entry: The server entry.
    :param client: The agent client."""
    data = read_json(path)
    if client.name == "opencode" and not data:
        data["$schema"] = "https://opencode.ai/config.json"
    table = data
    for key in keys:
        if not isinstance(table.setdefault(key, {}), dict):
            raise ConfigError(f"{path} has a {key!r} that is not an object; fix it by hand")
        table = table[key]
    table[SERVER] = entry
    write_file(path, json.dumps(data, indent=2) + "\n")


def read_toml(path: Path) -> bool:
    """Tell whether a TOML config lists the beamtime server, after checking it parses.

    :param path: The file.
    :return: ``True`` when ``[mcp_servers.beamtime]`` is there.
    :raises ConfigError: When the file is not valid TOML."""
    import tomllib

    if not path.exists():
        return False
    text = path.read_text()
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ConfigError(f"{path} is not valid TOML ({e}); fix it and run this again") from e
    return TOML_HEADER.search(text) is not None


def put_toml(path: Path, command: list[str]) -> None:
    """Write the beamtime table into Codex's config, replacing a previous one.

    :param path: The file.
    :param command: The command with its arguments."""
    read_toml(path)
    text = path.read_text() if path.exists() else ""
    table = (
        f"[mcp_servers.beamtime]\ncommand = {json.dumps(command[0])}\n"
        f"args = {json.dumps(command[1:])}\n"
    )
    if found := TOML_HEADER.search(text):
        following = TOML_TABLE.search(text, found.end())
        rest = "\n" + text[following.start() :] if following else ""
        text = text[: found.start()] + table + rest
    else:
        text = f"{text.rstrip(chr(10))}\n\n{table}" if text.strip() else table
    write_file(path, text)


def write_file(path: Path, text: str) -> None:
    """Write a file whole, so a client never reads half a config.

    :param path: The file; its folder is created.
    :param text: The content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.beamtime")
    tmp.write_text(text)
    tmp.replace(path)
