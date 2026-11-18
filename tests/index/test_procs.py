import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from beamtime.index.cache import FileLock
from beamtime.index.procs import listed, procs_dir, register

CHILD = """
import sys
from pathlib import Path
from beamtime.index.procs import register

reg = register("mcp", logdir="/x/log", cache="/x/cache", cache_kind="memory", client="claude")
print("ready", flush=True)
sys.stdin.readline()
if sys.argv[1] == "close":
    reg.close()
"""


@pytest.fixture(autouse=True)
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A private runtime base for the test and its subprocesses.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: The runtime base."""
    monkeypatch.setenv("BEAMTIME_RUNTIME", str(tmp_path / "rt"))
    return tmp_path / "rt"


def spawn(how: str) -> subprocess.Popen:
    """Start a process that registers as an MCP server and waits for a line on stdin.

    :param how: ``close`` to unregister before exiting, ``kill`` to leave without it.
    :return: The running process, after its registration."""
    proc = subprocess.Popen(
        [sys.executable, "-c", CHILD, how],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert proc.stdout.readline().strip() == "ready"
    return proc


def test_subprocess_is_listed_with_every_field() -> None:
    """A registered process shows every field of the record."""
    proc = spawn("close")
    try:
        live, stale = listed()
        assert stale == []
        (record,) = live
        assert record["schema"] == 1 and record["kind"] == "mcp"
        assert record["pid"] == proc.pid and record["ppid"] == os.getpid()
        assert record["version"] and abs(time.time() - record["started"]) < 60
        assert record["logdir"] == "/x/log" and record["cache"] == "/x/cache"
        assert record["cache_kind"] == "memory" and record["client"] == "claude"
        assert record["root"] is None
    finally:
        proc.communicate("\n")


def test_exit_removes_files() -> None:
    """After a normal exit nothing is left in the registry."""
    proc = spawn("close")
    assert len(list(procs_dir().iterdir())) == 2
    proc.communicate("\n")
    assert list(procs_dir().iterdir()) == []
    assert listed() == ([], [])


def test_killed_process_is_stale_once() -> None:
    """After kill -9 the next listing reports the record as stale and removes both files."""
    proc = spawn("kill")
    proc.send_signal(signal.SIGKILL if hasattr(signal, "SIGKILL") else signal.SIGTERM)
    proc.wait()
    live, stale = listed()
    assert live == [] and [r["pid"] for r in stale] == [proc.pid]
    assert list(procs_dir().iterdir()) == []
    assert listed() == ([], [])


def test_registering_is_not_stale() -> None:
    """A record without a lock file, and a young lock without a record, are left alone."""
    folder = procs_dir()
    folder.mkdir(parents=True)
    (folder / "mcp-1-aaaaaa.json").write_text(json.dumps({"kind": "mcp", "started": 1}))
    (folder / "mcp-2-bbbbbb.lock").write_text("")
    assert listed() == ([], [])
    assert sorted(p.name for p in folder.iterdir()) == ["mcp-1-aaaaaa.json", "mcp-2-bbbbbb.lock"]
    old = time.time() - 120
    os.utime(folder / "mcp-2-bbbbbb.lock", (old, old))
    assert listed() == ([], [])
    assert [p.name for p in folder.iterdir()] == ["mcp-1-aaaaaa.json"]


def test_names_are_unique() -> None:
    """Registering twice in one process never shares a file."""
    with register("mcp") as one, register("mcp") as two:
        assert one.record != two.record and one.lock.path != two.lock.path
        assert len(listed()[0]) == 2
    assert listed() == ([], [])


def test_broken_record_skipped() -> None:
    """An unreadable or half-written record is skipped, not raised."""
    folder = procs_dir()
    folder.mkdir(parents=True)
    (folder / "mcp-1-aaaaaa.json").write_text('{"kind": "mc')
    (folder / "mcp-1-aaaaaa.lock").write_text("")
    (folder / "mcp-3-cccccc.json").write_text("[1]")
    (folder / "mcp-3-cccccc.lock").write_text("")
    with register("serve", port=1):
        live, stale = listed()
    assert [r["kind"] for r in live] == ["serve"] and stale == []
    assert (folder / "mcp-1-aaaaaa.json").exists()


def test_list_reads_only(runtime: Path) -> None:
    """Listing creates no procs/ folder."""
    assert listed() == ([], [])
    assert not (runtime / "procs").exists()


def test_update_and_modes(runtime: Path) -> None:
    """update rewrites the record; files are private."""
    with register("serve", port=0) as reg:
        reg.update(port=8080)
        (record,) = listed()[0]
        assert record["port"] == 8080 and record["sources"] == []
        assert reg.record.stat().st_mode & 0o777 == 0o600
        assert (runtime / "procs").stat().st_mode & 0o777 == 0o700
        assert FileLock(path=reg.lock.path).held_elsewhere()


def test_failed_open_releases_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    """A record that cannot be written leaves no held lock and no files behind."""

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(json, "dump", fail)
    with pytest.raises(OSError, match="disk full"):
        register("mcp")
    assert list(procs_dir().iterdir()) == []
