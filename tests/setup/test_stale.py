"""The update checks on fixture projects set up with older releases."""

import json
import re
import shutil
import stat
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import msgspec
import pytest

from beamtime import __version__
from beamtime.cli import main
from beamtime.guide.rules import END, RELEASES, RULES_FILES, START, render, write_block
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.settings import resolve_agent
from beamtime.setup.agents import CLIENTS
from beamtime.setup.changes import since
from beamtime.ops.registry import SetupParams
from beamtime.setup.plan import Answers, flags
from beamtime.setup.scan import scan
from beamtime.setup.stale import Stale, stale_remote

USER_ONLY = ["setup", "serve"]
posix = pytest.mark.skipif(sys.platform == "win32", reason="the fake programs are shell scripts")


def fake_program(folder: Path, name: str, *, output: str = "") -> Path:
    """Write a program that answers every call with a line.

    :param folder: Where it goes.
    :param name: Its file name.
    :param output: What it prints; default ``beamtime <this release>``.
    :return: The file."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(f"#!/bin/sh\necho '{output or f'beamtime {__version__}'}'\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return path


def old_rules(name: str) -> str:
    """Read a release's rules text, its placeholders filled.

    :param name: The history file, e.g. ``0.1.0.md``.
    :return: The block's text."""
    text = (files("beamtime.guide") / "rules" / "history" / name).read_text(encoding="utf-8")
    return re.sub(r"\{\{\w+\}\}", "x", text).strip()


@pytest.fixture
def bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A folder with a fake ``uv``, the only program on ``PATH``.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :return: The folder."""
    folder = tmp_path / "bin"
    fake_program(folder, "uv")
    monkeypatch.setenv("PATH", str(folder))
    monkeypatch.setenv("DISPLAY", ":0")
    return folder


@pytest.fixture
def old(project_tree: Path, home: Path, bin: Path) -> Path:
    """A project set up with 0.1.1: old rules, skills and MCP entry, a gone colormap, an old SDK
    and Beamtime runs outside the log dir.

    :param project_tree: The uv project.
    :param home: The fake home.
    :param bin: The fake ``uv``.
    :return: The project root."""
    root = project_tree
    packages = root / ".venv" / "lib" / "python3.11" / "site-packages"
    shutil.rmtree(packages / f"beamtime-{__version__}.dist-info")
    (packages / "beamtime-0.1.1.dist-info").mkdir()
    (root / "beamtime.yaml").write_text("schema: 1\ncolormap: viridis\n", encoding="utf-8")
    (root / "beamtime").mkdir()
    write_block(root / "CLAUDE.md", old_rules("0.1.0.md"))
    skill = root / ".claude" / "skills" / "beamtime-views" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("old\n", encoding="utf-8")
    (root / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"beamtime": {"command": "/gone/bin/beamtime", "args": ["mcp"]}}})
    , encoding="utf-8")
    for name in ("r-1", "r-2"):
        (root / "runs-old" / name).mkdir(parents=True)
        (root / "runs-old" / name / "_run.json").write_text(json.dumps({"schema": 1, "id": name}), encoding="utf-8")
    return root


def look(root: Path, home: Path):
    """Scan a project with the test's environment and the fake home.

    :param root: The project root.
    :param home: The fake home.
    :return: The scan."""
    import os

    return scan(root, home=home, mounts=Path("/nonexistent/mounts"), env=dict(os.environ))


@posix
def test_0_1_1_lists_every_stale_item(old: Path, home: Path) -> None:
    """Each item of an old setup is named with what it is and what it becomes."""
    found = look(old, home)
    items = {s.item: s for s in found.stale}
    assert list(items) == ["rules", "mcp", "skills", "settings", "sdk", "runs"]
    assert items["rules"].before == f"CLAUDE.md has the {RELEASES['0.1.0.md']} rules"
    assert items["rules"].after == f"the {__version__} rules" and items["rules"].ticked
    assert items["mcp"].before == "Claude Code: /gone/bin/beamtime mcp does not start"
    assert items["mcp"].after == "uv run --project . beamtime mcp"
    assert items["skills"].before == "0 of 3 skills current in .claude/skills/"
    assert items["settings"].before == "beamtime.yaml sets colormap"
    assert items["sdk"].before == "beamtime 0.1.1 in the uv environment"
    assert items["sdk"].after == f"beamtime {__version__}"
    assert items["runs"].before == "2 Beamtime runs in runs-old/, outside the log dir"
    assert items["runs"].path == "runs-old/"
    assert found.flow == "update"


@posix
def test_0_2_0_setup_names_its_release(old: Path, home: Path) -> None:
    """The 0.2.0 rules are older than this release's, and the rest of that setup is current."""
    write_block(old / "CLAUDE.md", old_rules("0.2.0.md"))
    (old / ".mcp.json").unlink()
    shutil.rmtree(old / ".claude")
    (old / "beamtime.yaml").write_text("schema: 1\n", encoding="utf-8")
    shutil.rmtree(old / "runs-old")
    packages = old / ".venv" / "lib" / "python3.11" / "site-packages"
    shutil.rmtree(packages / "beamtime-0.1.1.dist-info")
    (packages / f"beamtime-{__version__}.dist-info").mkdir()
    (stale,) = look(old, home).stale
    assert stale.item == "rules"
    assert stale.before == f"CLAUDE.md has the {RELEASES['0.2.0.md']} rules"


@posix
def test_current_and_rule_less_projects_are_not_stale(old: Path, home: Path) -> None:
    """A project with this release's setup, or with no rules block at all, has nothing stale."""
    (old / ".mcp.json").unlink()
    shutil.rmtree(old / ".claude")
    shutil.rmtree(old / "runs-old")
    (old / "beamtime.yaml").write_text("schema: 1\n", encoding="utf-8")
    packages = old / ".venv" / "lib" / "python3.11" / "site-packages"
    shutil.rmtree(packages / "beamtime-0.1.1.dist-info")
    (packages / f"beamtime-{__version__}.dist-info").mkdir()
    (old / "CLAUDE.md").unlink()
    assert look(old, home).stale == ()
    write_block(old / "CLAUDE.md", render(resolve_agent({}), USER_ONLY))
    assert look(old, home).stale == ()


@posix
def test_edited_block_unticked(old: Path, home: Path) -> None:
    """A rules block edited by hand is reported, left out of the default update and never replaced."""
    write_block(old / "CLAUDE.md", "Written by hand.")
    found = look(old, home)
    rules = next(s for s in found.stale if s.item == "rules")
    assert rules.before == "CLAUDE.md was edited by hand" and not rules.ticked
    assert "rules" not in Answers.defaults(found).update
    assert "mcp" in Answers.defaults(found).update


@posix
def test_mcp_that_starts_and_is_picked_is_current(old: Path, home: Path, bin: Path) -> None:
    """An entry that starts and equals this release's pick is not stale; one that differs is."""
    entry = {"command": "uv", "args": ["run", "--project", ".", "beamtime", "mcp", "--root", "."]}
    (old / ".mcp.json").write_text(json.dumps({"mcpServers": {"beamtime": entry}}), encoding="utf-8")
    assert "mcp" not in [s.item for s in look(old, home).stale]
    other = fake_program(bin, "mine")
    entry = {"command": str(other), "args": ["mcp"]}
    (old / ".mcp.json").write_text(json.dumps({"mcpServers": {"beamtime": entry}}), encoding="utf-8")
    mcp = next(s for s in look(old, home).stale if s.item == "mcp")
    assert mcp.before == f"Claude Code: {other} mcp is not what this release picks"


@posix
def test_check_exits_3_then_0_after_yes(
    old: Path, home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``setup --check`` prints a line per item and exits 3; ``setup --yes`` brings everything up to date."""

    def upgraded(commands: list[list[str]], root: Path, requirements: Path | None) -> None:
        packages = root / ".venv" / "lib" / "python3.11" / "site-packages"
        shutil.rmtree(packages / "beamtime-0.1.1.dist-info")
        (packages / f"beamtime-{__version__}.dist-info").mkdir()

    monkeypatch.setattr("beamtime.setup.sdk.install", upgraded)
    with pytest.raises(SystemExit) as stop:
        main(["--root", str(old), "setup", "--check"])
    assert stop.value.code == 3
    lines = capsys.readouterr().out.strip().splitlines()
    assert [line.split(":")[0] for line in lines] == [
        "rules", "mcp", "skills", "settings", "sdk", "runs"
    ]  # fmt: skip
    assert not (old / "beamtime" / "imported").exists()

    main(["--root", str(old), "setup", "--yes"])
    capsys.readouterr()
    assert START in (old / "CLAUDE.md").read_text(encoding="utf-8") and "0.1.0" not in (old / "CLAUDE.md").read_text(encoding="utf-8")
    assert "colormap" not in (old / "beamtime.yaml").read_text(encoding="utf-8")
    assert (old / "beamtime" / "imported").is_dir()
    assert json.loads((old / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["beamtime"]["command"] == "uv"

    main(["--root", str(old), "setup", "--check"])
    assert capsys.readouterr().out.strip() == "nothing is stale"


@posix
def test_stale_runs_are_the_default_import_and_can_be_declined(old: Path, home: Path) -> None:
    """The runs outside the log dir are imported by default; ``--import ''`` says none."""
    found = look(old, home)
    assert Answers.defaults(found).imports == ["runs-old/"]
    none = Answers.from_params(msgspec.convert({"import": [""]}, SetupParams), found)
    assert none.imports == [] and flags(none, found) == ["--import ''"]
    assert Answers.from_params(msgspec.convert({}, SetupParams), found).imports == ["runs-old/"]


@posix
def test_check_json_lists_the_items(old: Path, home: Path) -> None:
    """The answer carries each item's fields and asks for exit code 3."""
    answer = call("setup", {"check": True}, Context.make(root=old, caller="cli"))
    assert answer["meta"] == {"exit": 3}
    assert {s["item"] for s in answer["stale"]} >= {"rules", "mcp", "skills"}
    assert answer["written"] == []


@posix
def test_status_line(old: Path, home: Path) -> None:
    """``status`` names the release of an old rules block, and says nothing for current or no rules."""
    context = Context.make(root=old, caller="cli")
    assert call("status", {}, context)["setup"] == (
        f"set up with {RELEASES['0.1.0.md']}; `beamtime setup` updates it"
    )
    write_block(old / "CLAUDE.md", "Written by hand.")
    assert call("status", {}, context)["setup"] is None
    (old / "CLAUDE.md").unlink()
    assert call("status", {}, context)["setup"] is None
    write_block(old / "CLAUDE.md", render(resolve_agent({}), USER_ONLY))
    assert call("status", {}, context)["setup"] is None


def test_status_does_not_load_the_setup_package(tmp_path: Path, home: Path) -> None:
    """The status line reads two small files and imports nothing of ``beamtime.setup``."""
    write_block(tmp_path / "CLAUDE.md", old_rules("0.1.0.md"))
    code = (
        "import sys, pathlib\n"
        "from beamtime.ops import call\n"
        "from beamtime.ops.context import Context\n"
        f"call('status', {{}}, Context.make(root=pathlib.Path({str(tmp_path)!r}), caller='cli'))\n"
        "print([m for m in sys.modules if m.startswith('beamtime.setup')])\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    ).stdout
    assert out.strip() == "[]"


def test_rules_files_cover_the_clients() -> None:
    """The files ``status`` reads are the rules files of the client table."""
    assert {c.rules for c in CLIENTS} <= set(RULES_FILES)
    assert END and START


def test_remote_is_stale_when_older() -> None:
    """A probed remote with an older Beamtime is an item; a current or unknown one is not."""
    old = stale_remote("juwels", "0.1.1")
    assert old == Stale(
        item="remote:juwels", before="beamtime 0.1.1 on juwels", after=f"beamtime {__version__}"
    )
    assert stale_remote("juwels", __version__) is None and stale_remote("juwels", None) is None


def test_changes_since_a_release() -> None:
    """The noticeable changes are those of the releases after the setup's, up to the current one."""
    lines = since("0.1.1", "0.3.0")
    assert len(lines) == 6 and lines[0].startswith("Charts")
    assert "The setup command is now `beamtime setup`; `init` is gone." in lines
    assert since("0.2.1", "0.3.0") == lines[3:]
    assert since("0.3.0", "0.3.0") == []
