"""Tests of the portable MCP command."""

import json
import os
import stat
import sys
from pathlib import Path

import pytest

from beamtime.guide.rules import END, START
from beamtime.settings import Settings
from beamtime.setup.agents import (
    CLIENTS,
    ConfigError,
    check_command,
    client_named,
    machine_config,
    mcp_command,
    register,
    rules_change,
)
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
def test_conda_base(bins: Path, tmp_path: Path) -> None:
    """The conda install itself is named ``base``, not by its folder."""
    launcher(bins, "conda")
    prefix = tmp_path / "miniconda3"
    (prefix / "condabin").mkdir(parents=True)
    env = PythonEnv("conda", prefix, "3.12", "0.3.0", True)
    cmd = mcp_command(env, tmp_path / "project", shared=True)
    assert cmd == ["conda", "run", "--no-capture-output", "-n", "base", "beamtime", "mcp"]


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
    for tool in ("uv", "poetry", "conda", "pip"):
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


@pytest.fixture
def uv_project(bins: Path, tmp_path: Path, home: Path) -> tuple[Path, PythonEnv]:
    """Make a uv project whose command is portable.

    :param bins: The folder on ``PATH``, holding a fake ``uv``.
    :param tmp_path: The test's temporary directory.
    :param home: The fake home directory.
    :return: The project root and its environment."""
    launcher(bins, "uv")
    root = tmp_path / "project"
    root.mkdir()
    return root.resolve(), env_of("uv", root)


@pytest.fixture
def pip_project(bins: Path, tmp_path: Path, home: Path) -> tuple[Path, PythonEnv]:
    """Make a pip project whose command names this machine.

    :param bins: The folder on ``PATH``, empty.
    :param tmp_path: The test's temporary directory.
    :param home: The fake home directory.
    :return: The project root and its environment."""
    root = tmp_path / "project"
    launcher(root / ".venv" / "bin", "beamtime")
    return root.resolve(), env_of("pip", root)


@posix
def test_every_client_registers(uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """Each client's config is written as data, in its own shape, and read back."""
    root, env = uv_project
    for client in CLIENTS:
        change = register(client, root, env, home=home)
        change.run()
        if client.name == "other":
            assert json.loads(change.after)["mcpServers"]["beamtime"]["command"] == "uv"
            continue
        path = root / client.config if client.shared else home / client.config.removeprefix("~/")
        assert path.is_file(), client.name
        assert change.where == ("project" if client.shared else "machine")
        if client.name == "codex":
            assert "[mcp_servers.beamtime]" in path.read_text()
        else:
            assert "beamtime" in json.loads(path.read_text())[client.key]


@posix
def test_entry_shapes(uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """VS Code says stdio, opencode takes one command list, the rest split command and args."""
    root, env = uv_project
    register(client_named("vscode"), root, env, home=home).run()
    register(client_named("opencode"), root, env, home=home).run()
    register(client_named("cursor"), root, env, home=home).run()
    uv = ["uv", "run", "--project", "."]
    vscode = json.loads((root / ".vscode" / "mcp.json").read_text())["servers"]["beamtime"]
    assert vscode == {
        "type": "stdio",
        "command": "uv",
        "args": [*uv[1:], "beamtime", "--root", "${workspaceFolder}", "mcp"],
    }
    opencode = json.loads((root / "opencode.json").read_text())["mcp"]["beamtime"]
    assert opencode == {"type": "local", "command": [*uv, "beamtime", "mcp"], "enabled": True}
    cursor = json.loads((root / ".cursor" / "mcp.json").read_text())["mcpServers"]["beamtime"]
    assert cursor["args"][-3:] == ["--root", "${workspaceFolder}", "mcp"]


@posix
def test_mcp_json_merges(uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """An existing .mcp.json keeps its other servers and keys."""
    root, env = uv_project
    (root / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"other": {"command": "x"}}, "keep": 1})
    )
    register(client_named("claude-code"), root, env, home=home).run()
    config = json.loads((root / ".mcp.json").read_text())
    assert config["keep"] == 1 and config["mcpServers"]["other"] == {"command": "x"}
    assert config["mcpServers"]["beamtime"]["command"] == "uv"


@posix
def test_codex_table_replaced(uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """Codex's beamtime table is replaced between its header and the next, never duplicated."""
    root, env = uv_project
    path = home / ".codex" / "config.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        'model = "o3"\n\n[mcp_servers.beamtime]\ncommand = "old"\nargs = []\n\n'
        '[mcp_servers.other]\ncommand = "keep"\n'
    )
    codex = client_named("codex")
    for _ in range(2):
        register(codex, root, env, home=home).run()
    text = path.read_text()
    assert text.count("[mcp_servers.beamtime]") == 1 and 'command = "old"' not in text
    assert 'model = "o3"' in text and '[mcp_servers.other]\ncommand = "keep"' in text
    assert f'"--root", "{root}"' in text


@posix
def test_codex_appends_to_a_new_file(uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """Without a config, Codex's file holds just the table."""
    root, env = uv_project
    register(client_named("codex"), root, env, home=home).run()
    text = (home / ".codex" / "config.toml").read_text()
    assert text.startswith("[mcp_servers.beamtime]\ncommand = ")


@posix
@pytest.mark.parametrize("name", ["claude-code", "cursor", "codex", "windsurf"])
def test_bad_client_json(name: str, uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """A config that doesn't parse is an error naming the file, and it is left as it was."""
    root, env = uv_project
    client = client_named(name)
    path = root / client.config if client.shared else home / client.config.removeprefix("~/")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not valid")
    with pytest.raises(ConfigError, match=path.name):
        register(client, root, env, home=home).run()
    assert path.read_text() == "{ not valid"


@posix
def test_machine_scope(pip_project: tuple[Path, PythonEnv], home: Path) -> None:
    """A command that names this machine goes into the client's machine config, never the repo."""
    root, env = pip_project
    script = str(root / ".venv" / "bin" / "beamtime")
    for name in ("claude-code", "cursor", "vscode"):
        client = client_named(name)
        change = register(client, root, env, home=home)
        assert change.where == "machine"
        change.run()
        assert not (root / client.config).exists()
        data = json.loads(machine_config(client, home).read_text())
        if name == "claude-code":
            data = data["projects"][str(root)]
        entry = data[client.key]["beamtime"]
        assert script in (entry["command"], *entry.get("args", []))
        assert entry["args"][-3:] == ["--root", str(root), "mcp"]


@posix
def test_machine_scope_keeps_claude_json(pip_project: tuple[Path, PythonEnv], home: Path) -> None:
    """Claude Code's local scope sits beside the other projects in ~/.claude.json."""
    root, env = pip_project
    path = home / ".claude.json"
    path.write_text(json.dumps({"projects": {"/elsewhere": {"x": 1}}, "userID": "u"}))
    register(client_named("claude-code"), root, env, home=home).run()
    data = json.loads(path.read_text())
    assert data["projects"]["/elsewhere"] == {"x": 1} and data["userID"] == "u"


@posix
def test_unportable_without_machine_scope(pip_project: tuple[Path, PythonEnv], home: Path) -> None:
    """Gemini CLI and opencode have no machine scope, so a non-portable command is refused."""
    root, env = pip_project
    for name in ("gemini", "opencode"):
        with pytest.raises(ConfigError, match="uv tool install"):
            register(client_named(name), root, env, home=home)


@posix
def test_no_command(bins: Path, tmp_path: Path, home: Path) -> None:
    """With nothing to start the server, registering says what to install."""
    with pytest.raises(ConfigError, match="uv tool install"):
        register(client_named("cursor"), tmp_path, None, home=home)


@posix
def test_windsurf_and_codex_name_the_root(uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """User-wide configs hold the absolute root, since they serve every project."""
    root, env = uv_project
    register(client_named("windsurf"), root, env, home=home).run()
    path = home / ".codeium" / "windsurf" / "mcp_config.json"
    args = json.loads(path.read_text())["mcpServers"]["beamtime"]["args"]
    assert args[-3:] == ["--root", str(root), "mcp"]


@posix
def test_other_prints_json(uv_project: tuple[Path, PythonEnv], home: Path) -> None:
    """Another agent gets the JSON to paste and nothing is written."""
    root, env = uv_project
    change = register(client_named("other"), root, env, home=home)
    change.run()
    assert json.loads(change.after)["mcpServers"]["beamtime"]["args"][-3:] == [
        "--root",
        str(root),
        "mcp",
    ]
    assert not any(home.iterdir()) and not any(root.iterdir())


def test_rules_change(tmp_path: Path) -> None:
    """The rules block goes into the client's file, keeps the user's text and reports the release."""
    agent = Settings().agent
    file = tmp_path / "GEMINI.md"
    file.write_text("# Mine\n")
    change = rules_change(client_named("gemini"), tmp_path, agent, ["setup"])
    assert change.before is None and change.where == "project" and change.after
    assert change.run() == "added"
    text = file.read_text()
    assert text.startswith("# Mine\n") and text.count(START) == text.count(END) == 1
    again = rules_change(client_named("gemini"), tmp_path, agent, ["setup"])
    assert again.before == again.after and again.run() == "unchanged"
    assert not (tmp_path / "AGENTS.md").exists()
