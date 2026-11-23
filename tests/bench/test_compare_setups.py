"""Tests of the benchmark's setups in ``bench/agents/compare/setups.py``; no agent runs."""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from subprocess import CompletedProcess
from typing import Any

import pytest

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import setups  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A seeded log dir.

    :param tmp_path_factory: Makes the folder.
    :return: The folder holding ``beamtime/``."""
    dest = tmp_path_factory.mktemp("data")
    data.make_logdir(dest, seed=7, now=NOW)
    return dest


@pytest.fixture
def envs(tmp_path: Path) -> setups.Envs:
    """Environments without a build: ``beamtime`` is the test's own, ``base`` is an empty folder.

    :param tmp_path: Makes the folder.
    :return: The environments."""
    (tmp_path / "base" / "bin").mkdir(parents=True)
    return setups.Envs(base=tmp_path / "base", beamtime=Path(sys.prefix))


@pytest.fixture
def host_beamtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a ``beamtime`` executable on the host's PATH, as ``uv run`` does.

    :param tmp_path: Makes the folder.
    :param monkeypatch: Sets the PATH.
    :return: The folder."""
    folder = tmp_path / "host"
    folder.mkdir()
    (folder / "beamtime").write_text("#!/bin/sh\n", encoding="utf-8")
    (folder / "beamtime").chmod(0o755)
    monkeypatch.setenv("PATH", f"{folder}{os.pathsep}{os.environ['PATH']}")
    return folder


def prepare(name: str, tmp_path: Path, data_dir: Path, envs: setups.Envs, n: int = 0) -> Any:
    """Prepare one session.

    :param name: The setup.
    :param tmp_path: Holds the session folder.
    :param data_dir: The log dir's folder.
    :param envs: The environments.
    :param n: The session's number.
    :return: The project."""
    return setups.prepare(name, tmp_path / f"{name}-{n}", data_dir, envs)


def test_data_per_setup(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """Beamtime setups get a log dir with its config, the files setup CSVs; the record stays out."""
    mcp = prepare("mcp", tmp_path, data_dir, envs)
    files = prepare("files", tmp_path, data_dir, envs)

    assert (mcp.root / "beamtime.yaml").is_file()
    assert len(list((mcp.root / "beamtime").rglob("_run.json"))) == 61
    assert not list(mcp.root.rglob("_synth.json"))
    assert len(list((files.root / "runs").rglob("metrics.csv"))) == 61
    assert not (files.root / "beamtime").exists()


def test_tensorboard_data(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """The TensorBoard setup gets event files and no Beamtime log dir."""
    pytest.importorskip("tensorboard")
    project = prepare("tensorboard", tmp_path, data_dir, envs)

    assert len(list((project.root / "tb").rglob("hparams.yaml"))) == 61
    assert list((project.root / "tb").rglob("*tfevents*"))
    assert not (project.root / "beamtime").exists()


def test_claude_md(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """The preamble is the same bytes everywhere; only the data section differs."""
    pytest.importorskip("tensorboard")
    texts = {n: prepare(n, tmp_path, data_dir, envs).claude_md.read_text(encoding="utf-8") for n in setups.SETUPS}
    head, tail = {}, {}
    for name, text in texts.items():
        head[name], _, tail[name] = text.partition("\n## Data\n")

    assert len(set(head.values())) == 1
    assert head["mcp"] == setups.PREAMBLE
    assert tail["mcp"] == tail["cli"]
    assert len(set(tail.values())) == 3
    assert "beamtime" in tail["mcp"] and "beamtime" not in tail["files"].lower()
    assert "numpy, pandas, scipy and\nmatplotlib" in head["files"]
    assert "record/" not in tail["files"] and "record/" not in tail["tensorboard"]


def test_claude_md_names_a_record(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """A data set with a record exports it and names ``record/`` in the files section."""
    with_record = tmp_path / "data"
    shutil.copytree(data_dir, with_record)
    (with_record / "beamtime" / "study" / "proposal").mkdir(parents=True)
    (with_record / "beamtime" / "study" / "proposal" / "p.yaml").write_text("schema: 1\n", encoding="utf-8")
    project = prepare("files", tmp_path, with_record, envs)

    assert (project.root / "record" / "study" / "proposal" / "p.yaml").is_file()
    assert "- `record/<group>/`, next to `runs/`:" in project.claude_md.read_text(encoding="utf-8")


def test_tools_and_mcp(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """Every setup has the same six tools; only mcp has a server, and it is the only one allowed."""
    mcp = prepare("mcp", tmp_path, data_dir, envs)
    cli = prepare("cli", tmp_path, data_dir, envs)
    files = prepare("files", tmp_path, data_dir, envs)

    assert mcp.tools == cli.tools == files.tools == "Bash,Read,Write,Edit,Glob,Grep"
    assert mcp.allowed == f"mcp__beamtime__*,{mcp.tools}"
    assert cli.allowed == files.allowed == files.tools
    assert cli.mcp_config is None and files.mcp_config is None
    server = json.loads(mcp.mcp_config.read_text(encoding="utf-8"))["mcpServers"]["beamtime"]
    assert server["args"] == ["--root", str(mcp.root), "mcp"]
    assert Path(server["command"]).name == "beamtime"


def test_command_flags(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """The user's skills, settings and MCP servers stay out of every session."""
    for name in ("mcp", "cli", "files"):
        flags = prepare(name, tmp_path, data_dir, envs).flags
        assert flags[flags.index("--setting-sources") + 1] == "project"
        assert "--disable-slash-commands" in flags
        assert "--strict-mcp-config" in flags
        assert "--no-session-persistence" in flags
    assert "--mcp-config" in prepare("mcp", tmp_path, data_dir, envs, 1).flags
    assert "--mcp-config" not in prepare("cli", tmp_path, data_dir, envs, 1).flags


def test_files_path_has_no_beamtime(
    tmp_path: Path, data_dir: Path, envs: setups.Envs, host_beamtime: Path
) -> None:
    """A host's ``beamtime`` is on no PATH; only the CLI setup has the environment's own."""
    files = prepare("files", tmp_path, data_dir, envs)
    mcp = prepare("mcp", tmp_path, data_dir, envs)
    cli = prepare("cli", tmp_path, data_dir, envs)

    assert str(host_beamtime) not in files.env["PATH"]
    assert shutil.which("beamtime", path=files.env["PATH"]) is None
    assert shutil.which("beamtime", path=mcp.env["PATH"]) is None
    assert files.env["PATH"].startswith(str(envs.base / "bin"))
    assert shutil.which("beamtime", path=cli.env["PATH"]) == str(
        Path(sys.prefix) / "bin" / "beamtime"
    )


def test_session_env(
    tmp_path: Path, data_dir: Path, envs: setups.Envs, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A host's BEAMTIME_* variables stay out, the cache is the session's, memory is off."""
    monkeypatch.setenv("BEAMTIME_LOGDIR", "/host/logs")
    monkeypatch.setenv("BEAMTIME_CACHE", "/host/cache")
    for name in ("cli", "files"):
        env = prepare(name, tmp_path, data_dir, envs).env
        assert [k for k in env if k.startswith("BEAMTIME_")] == ["BEAMTIME_CACHE"]
        assert env["BEAMTIME_CACHE"] != "/host/cache"
        assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"


@pytest.mark.parametrize("name", list(setups.SETUPS))
def test_planned_matches_prepared(
    tmp_path: Path, data_dir: Path, envs: setups.Envs, name: str
) -> None:
    """The dry run's project has the flags of the prepared one."""
    if name == "tensorboard":
        pytest.importorskip("tensorboard")
    session = tmp_path / "plan"
    assert (
        setups.planned(name, session).flags == setups.prepare(name, session, data_dir, envs).flags
    )


def test_cache_per_session(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """Each session has its own cache and config inside its folder; the cache is warmed."""
    a = prepare("cli", tmp_path, data_dir, envs, 0)
    b = prepare("cli", tmp_path, data_dir, envs, 1)
    m = prepare("mcp", tmp_path, data_dir, envs, 2)

    assert a.env["BEAMTIME_CACHE"] != b.env["BEAMTIME_CACHE"]
    for project in (a, b, m):
        cache = Path(project.env["BEAMTIME_CACHE"])
        assert project.root.parent in cache.parents
        assert any(cache.rglob("*")), "the index is warmed"
        assert project.root.parent in Path(project.env["XDG_CONFIG_HOME"]).parents
    server = json.loads(m.mcp_config.read_text(encoding="utf-8"))["mcpServers"]["beamtime"]
    assert server["env"]["BEAMTIME_CACHE"] == m.env["BEAMTIME_CACHE"]


@pytest.mark.parametrize("name", ["cli", "mcp"])
def test_warm_indexes_everything(
    tmp_path: Path, data_dir: Path, envs: setups.Envs, name: str
) -> None:
    """A prepared session has every run indexed, even one with a long series."""
    long_dir = tmp_path / "long"
    shutil.copytree(data_dir, long_dir)
    metrics = next((long_dir / "beamtime").rglob("_metrics.jsonl"))
    with metrics.open("a", encoding="utf-8") as f:
        f.writelines(
            json.dumps({"_step": s, "_t": 1.0, "training/loss": 1.0}) + "\n"
            for s in range(1_000_000, 1_100_000)
        )
    project = prepare(name, tmp_path, long_dir, envs)

    beamtime = str(Path(sys.prefix) / "bin" / "beamtime")
    out = subprocess.run(
        [beamtime, "--root", str(project.root), "status"],
        env=project.env,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "not yet indexed" not in out


def test_data_is_copied(tmp_path: Path, data_dir: Path, envs: setups.Envs) -> None:
    """A session's writes never reach the shared data, and run files keep their times."""
    project = prepare("cli", tmp_path, data_dir, envs)
    (project.root / "beamtime" / "note.txt").write_text("x", encoding="utf-8")
    card = next((data_dir / "beamtime").rglob("_run.json"))
    copy = project.root / "beamtime" / card.relative_to(data_dir / "beamtime")

    assert not list((data_dir / "beamtime").rglob("note.txt"))
    assert copy.stat().st_mtime == card.stat().st_mtime


def test_make_envs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two venvs are built with uv, the second with this checkout's beamtime; existing ones stay."""
    calls: list[list[str]] = []

    def fake(command: list[str], **kwargs: Any) -> CompletedProcess:
        calls.append(command)
        if command[:2] == ["uv", "venv"]:
            (Path(command[-1]) / "bin").mkdir(parents=True)
            (Path(command[-1]) / "bin" / "python").write_text("", encoding="utf-8")
        return CompletedProcess(command, 0)

    monkeypatch.setattr(setups.subprocess, "run", fake)
    envs = setups.make_envs(tmp_path)
    installs = [c for c in calls if c[:3] == ["uv", "pip", "install"]]

    assert len(installs) == 2
    assert all("tensorboard" in c and "pandas" in c for c in installs)
    assert not any("beamtime" in a for a in installs[0])
    assert any(a.endswith("[serve]") for a in installs[1])
    assert setups.make_envs(tmp_path) == envs
    assert len(calls) == 4


def test_make_envs_after_failed_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A venv whose install failed is built again, not reused without its packages."""
    calls: list[list[str]] = []
    fail = [True]

    def fake(command: list[str], **kwargs: Any) -> CompletedProcess:
        calls.append(command)
        if command[:2] == ["uv", "venv"]:
            (Path(command[-1]) / "bin").mkdir(parents=True, exist_ok=True)
            (Path(command[-1]) / "bin" / "python").write_text("", encoding="utf-8")
        if command[:3] == ["uv", "pip", "install"] and fail[0]:
            raise setups.subprocess.CalledProcessError(1, command)
        return CompletedProcess(command, 0)

    monkeypatch.setattr(setups.subprocess, "run", fake)
    with pytest.raises(setups.subprocess.CalledProcessError):
        setups.make_envs(tmp_path)
    fail[0] = False
    calls.clear()
    setups.make_envs(tmp_path)

    assert len([c for c in calls if c[:3] == ["uv", "pip", "install"]]) == 2
