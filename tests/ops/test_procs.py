import json
import os
import signal
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

from beamtime.cli.format import render
from beamtime.index.cache import log_hash
from beamtime.ops.context import Context
from beamtime.ops.procs import KINDS, ps, serves, used_here
from beamtime.ops.registry import BY_API, BY_TOOL, NoParams

CHILD = """
import json
import sys
import time
from pathlib import Path

from beamtime.index.cache import FileLock
from beamtime.index.procs import register

kind, fields, legacy, hold = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3], sys.argv[4]
lock = None
if "cache" in fields:
    cache = Path(fields["cache"])
    cache.mkdir(parents=True, exist_ok=True)
    lock = FileLock(path=cache / "serve.lock")
    assert lock.acquire()
    (cache / "serve.token").write_text("tok")
    if legacy == "json":
        data = {"pid": 1, "port": fields.get("port"), "version": "0.1.0", "logdir": fields["logdir"]}
        (cache / "serve.json").write_text(json.dumps(data | {"started": time.time() - 100}))
if hold == "record":
    register(kind, **fields)
print("ready", flush=True)
sys.stdin.readline()
"""


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A private runtime base, cache and home for the test and its subprocesses.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: The project root."""
    monkeypatch.setenv("BEAMTIME_RUNTIME", str(tmp_path / "rt"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    (tmp_path / "home").mkdir()
    root = tmp_path / "proj"
    (root / "beamtime").mkdir(parents=True)
    (root / "beamtime.yaml").write_text("{}\n")
    return root


@pytest.fixture
def project_ctx(isolated: Path) -> Context:
    """The context of the project.

    :param isolated: The project root.
    :return: The context."""
    return Context.make(root=isolated)


@pytest.fixture
def spawn() -> Iterator[Callable[..., subprocess.Popen]]:
    """Start helper processes that register themselves and wait for a line on stdin.

    :return: ``spawn(kind, fields, legacy="", hold="record")``; the processes end with the test."""
    procs: list[subprocess.Popen] = []

    def go(kind: str, fields: dict[str, Any], legacy: str = "", hold: str = "record") -> Any:
        proc = subprocess.Popen(
            [sys.executable, "-c", CHILD, kind, json.dumps(fields), legacy, hold],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )
        procs.append(proc)
        assert proc.stdout.readline().strip() == "ready"
        return proc

    yield go
    for proc in procs:
        if proc.poll() is None:
            proc.kill()
        proc.communicate()


def pids(answer: dict[str, Any], kind: str) -> list[int]:
    """List the pids of a group.

    :param answer: The ``ps`` answer.
    :param kind: The group.
    :return: The pids."""
    return [x["pid"] for x in answer["groups"][kind]]


def test_every_kind_is_grouped_in_order(
    isolated: Path, project_ctx: Context, spawn: Callable[..., subprocess.Popen], tmp_path: Path
) -> None:
    """Records of every kind are listed by kind, with root, URL, cache, uptime and client."""
    logdir = str(isolated / "beamtime")
    cache = str(tmp_path / "cache" / log_hash(isolated / "beamtime"))
    mcp = spawn("mcp", {"root": str(isolated), "logdir": logdir, "client": "claude"})
    remote = spawn("remote", {"logdir": "/r/log", "client": "10.0.0.1"})
    index = spawn("index", {"root": "/other", "logdir": "/other/log", "cache": str(tmp_path / "c2")})
    web = spawn(
        "serve",
        {"root": str(isolated), "logdir": logdir, "cache": cache, "cache_kind": "disk", "port": 8123},
    )
    answer = ps(project_ctx, NoParams())
    assert answer["kind"] == "ps" and list(answer["groups"]) == list(KINDS)
    assert pids(answer, "serve") == [web.pid] and pids(answer, "index") == [index.pid]
    assert pids(answer, "remote") == [remote.pid] and pids(answer, "mcp") == [mcp.pid]
    assert answer["groups"]["ssh"] == [] and answer["stale"] == [] and answer["lines"] == []
    (serve_row,) = answer["groups"]["serve"]
    assert serve_row["url"] == "http://localhost:8123/f/local?token=tok"
    assert 0 <= serve_row["uptime_s"] < 60 and serve_row["used_here"] == "live index, remote calls"
    assert answer["groups"]["mcp"][0]["used_here"] == "-" and answer["groups"]["mcp"][0]["url"] is None
    json.dumps(answer)
    text = render(answer)
    assert [line for line in text.splitlines() if not line.startswith(" ")] == [
        "serve", "index", "remote", "mcp",
    ]  # fmt: skip
    assert f"pid {web.pid}" in text and "url        http://localhost:8123/f/local?token=tok" in text
    assert f"cache      disk {cache}" in text and "used here  live index, remote calls" in text
    assert "client     claude" in text and "client     10.0.0.1" in text and " up " in text


def test_ps_without_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, spawn: Callable[..., subprocess.Popen]
) -> None:
    """Outside any project, ps still lists every process."""
    proc = spawn("mcp", {"root": "/x", "logdir": "/x/log", "client": "c"})
    bare = tmp_path / "bare"
    bare.mkdir()
    monkeypatch.chdir(bare)
    answer = ps(Context.make(), NoParams())
    assert pids(answer, "mcp") == [proc.pid]


def test_empty_registry_says_so(project_ctx: Context) -> None:
    """Without processes the answer says that nothing runs."""
    answer = ps(project_ctx, NoParams())
    assert all(rows == [] for rows in answer["groups"].values())
    assert render(answer) == "no Beamtime process runs"


def test_killed_process_is_stale_once(
    project_ctx: Context, spawn: Callable[..., subprocess.Popen]
) -> None:
    """After kill -9 the next ps lists the record under stale, the one after does not."""
    proc = spawn("mcp", {"root": "/x", "logdir": "/x/log", "client": "c"})
    proc.send_signal(signal.SIGKILL)
    proc.wait()
    first = ps(project_ctx, NoParams())
    assert [x["pid"] for x in first["stale"]] == [proc.pid] and first["groups"]["mcp"] == []
    assert "stale (removed)" in render(first)
    assert ps(project_ctx, NoParams())["stale"] == []


def test_stale_serve_json_is_removed(
    isolated: Path, project_ctx: Context, tmp_path: Path
) -> None:
    """A serve.json whose lock is free is reported once and deleted; the token stays."""
    cache = tmp_path / "cache" / "abc"
    cache.mkdir(parents=True)
    (cache / "serve.json").write_text(json.dumps({"pid": 7, "port": 9, "logdir": "/x"}))
    (cache / "serve.token").write_text("tok")
    first = ps(project_ctx, NoParams())
    assert [x["pid"] for x in first["stale"]] == [7] and first["groups"]["serve"] == []
    assert not (cache / "serve.json").exists() and (cache / "serve.token").exists()
    assert ps(project_ctx, NoParams())["stale"] == []


def test_legacy_serve_listed_once(
    isolated: Path, project_ctx: Context, spawn: Callable[..., subprocess.Popen], tmp_path: Path
) -> None:
    """A serve without a record is listed from its serve.json, and a serve with both once."""
    logdir = str(isolated / "beamtime")
    old = tmp_path / "cache" / "old"
    legacy = spawn("serve", {"logdir": logdir, "cache": str(old), "port": 8001}, "json", "no")
    new = tmp_path / "cache" / "new"
    both = spawn(
        "serve",
        {"root": str(isolated), "logdir": logdir, "cache": str(new), "cache_kind": "disk", "port": 8002},
        "json",
    )
    answer = ps(project_ctx, NoParams())
    assert sorted(pids(answer, "serve")) == sorted([1, both.pid]) and answer["stale"] == []
    (old_row,) = [x for x in answer["groups"]["serve"] if x["cache"] == str(old)]
    assert old_row["schema"] == 0 and old_row["version"] == "0.1.0" and old_row["url"].endswith("tok")
    assert 90 < old_row["uptime_s"] < 200 and legacy.poll() is None
    assert [x["pid"] for x in serves(project_ctx)].count(both.pid) == 1


def test_serves_lists_only_serves(
    project_ctx: Context, spawn: Callable[..., subprocess.Popen], tmp_path: Path
) -> None:
    """The shared helper returns the serve and index rows only."""
    spawn("mcp", {"root": "/x", "logdir": "/x/log", "client": "c"})
    index = spawn("index", {"logdir": "/y", "cache": str(tmp_path / "c")})
    assert [x["pid"] for x in serves(project_ctx)] == [index.pid]


def record(isolated: Path, kind: str, cache: Path, cache_kind: str) -> dict[str, Any]:
    """Make a serve record for this project's log dir.

    :param isolated: The project root.
    :param kind: ``serve`` or ``index``.
    :param cache: The serve's cache folder.
    :param cache_kind: ``disk`` or ``memory``.
    :return: The record."""
    return {
        "kind": kind,
        "logdir": str(isolated / "beamtime"),
        "cache": str(cache),
        "cache_kind": cache_kind,
    }


def test_used_here_words(isolated: Path, project_ctx: Context, tmp_path: Path) -> None:
    """A serve on this shell's cache says what the calls get from it; other kinds and log dirs show -."""
    disk = tmp_path / "cache" / log_hash(isolated / "beamtime")
    assert used_here(project_ctx, record(isolated, "serve", disk, "disk")) == "live index, remote calls"
    assert used_here(project_ctx, record(isolated, "index", disk, "disk")) == "live index"
    other = record(isolated, "serve", disk, "disk") | {"logdir": "/elsewhere"}
    assert used_here(project_ctx, other) == "-"
    assert used_here(project_ctx, record(isolated, "mcp", disk, "disk")) == "-"


def test_used_here_memory(
    isolated: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """With a memory cache a UI serve serves all reads and a --no-ui one nothing."""
    monkeypatch.setenv("BEAMTIME_CACHE", "memory")
    ctx = Context.make(root=isolated)
    from beamtime.index.cache import runtime_dir

    shared = runtime_dir(isolated / "beamtime")
    assert used_here(ctx, record(isolated, "serve", shared, "memory")) == "all reads"
    assert used_here(ctx, record(isolated, "index", shared, "memory")) == "no: memory, no UI"


def test_used_here_other_cache(isolated: Path, project_ctx: Context, tmp_path: Path) -> None:
    """A serve on another cache names this shell's cache and where the setting came from."""
    theirs = tmp_path / "elsewhere" / "abc"
    said = used_here(project_ctx, record(isolated, "serve", theirs, "disk"))
    mine = tmp_path / "cache" / log_hash(isolated / "beamtime")
    assert said == f"no: this shell's cache is {mine} (BEAMTIME_CACHE)"
    memory = used_here(project_ctx, record(isolated, "serve", tmp_path / "rt" / "x", "memory"))
    assert memory.startswith("no: this shell's cache is ")


def test_ssh_logins(tmp_path: Path, project_ctx: Context, monkeypatch: pytest.MonkeyPatch) -> None:
    """Hosts of Beamtime's marked ssh blocks are listed while their login is open."""
    from beamtime.setup.remotes import SSH_MARK

    ssh = tmp_path / "home" / ".ssh"
    ssh.mkdir()
    (ssh / "config").write_text(
        f"Host plain\n  User x\n\n{SSH_MARK} up\nHost up\n\n{SSH_MARK} down\nHost down\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "ssh"
    fake.write_text(
        '#!/bin/sh\n[ "$3" = up ] && { echo "Master running (pid=4242)" >&2; exit 0; }\nexit 255\n'
    )
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    answer = ps(project_ctx, NoParams())
    (login,) = answer["groups"]["ssh"]
    assert login["host"] == "up" and login["pid"] == 4242 and login["end"] == "ssh -O exit up"
    assert "ssh\n  up  pid 4242\n    end it     ssh -O exit up" in render(answer)


def test_not_an_mcp_tool_or_api_method() -> None:
    """ps is a user-only operation: no tool, no API method."""
    assert "ps" not in BY_TOOL and "ps" not in BY_API


def test_cli_json(isolated: Path, spawn: Callable[..., subprocess.Popen]) -> None:
    """beamtime ps --json prints the answer."""
    proc = spawn("mcp", {"root": "/x", "logdir": "/x/log", "client": "c"})
    done = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "ps", "--json"],
        cwd=isolated,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr
    answer = json.loads(done.stdout)
    assert [x["pid"] for x in answer["groups"]["mcp"]] == [proc.pid]
