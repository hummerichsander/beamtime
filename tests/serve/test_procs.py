import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("starlette")

import beamtime
from beamtime.index.procs import listed
from beamtime.serve.app import STATIC

SERVE = [sys.executable, "-m", "beamtime.cli", "serve"]


@pytest.fixture(autouse=True)
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A private runtime base for the test and its subprocesses.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: The runtime base."""
    monkeypatch.setenv("BEAMTIME_RUNTIME", str(tmp_path / "rt"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    return tmp_path / "rt"


@pytest.fixture
def start(project: Path) -> Iterator[Callable[..., subprocess.Popen]]:
    """Start ``beamtime serve`` in the project and wait for its first line on stderr.

    :param project: The project root.
    :return: ``start(*args, cwd=project, stdin=None) -> process``; the process is stopped at the end."""
    procs: list[subprocess.Popen] = []

    def go(*args: str, cwd: Path = project, stdin: Any = None) -> subprocess.Popen:
        proc = subprocess.Popen(
            [*SERVE, *args], cwd=cwd, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )  # fmt: skip
        procs.append(proc)
        return proc

    yield go
    for proc in procs:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(10)


def records(kind: str, timeout: float = 30) -> list[dict[str, Any]]:
    """Wait until at least one live record of a kind exists.

    :param kind: The process kind.
    :param timeout: Seconds to wait.
    :return: The live records of that kind."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if found := [r for r in listed()[0] if r["kind"] == kind]:
            return found
        time.sleep(0.1)
    pytest.fail(f"no {kind} record")


def test_serve_registers_with_port_cache_and_sources(project: Path, start) -> None:
    """A serve is listed as ``serve`` with its port and cache, and gone after a clean exit."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    proc = start("--port", "0")
    [record] = records("serve")
    assert record["pid"] == proc.pid and record["port"] > 0 and record["sources"] == []
    assert record["root"] == str(project.resolve()) and record["cache_kind"] == "disk"
    assert (Path(record["cache"]) / "serve.lock").exists()
    proc.send_signal(signal.SIGINT)
    proc.wait(15)
    assert listed() == ([], [])


def test_no_ui_registers_as_index_and_sigterm_cleans_up(project: Path, start) -> None:
    """``--no-ui`` is an ``index`` without a port; SIGTERM removes its record and ``serve.json``."""
    proc = start("--no-ui")
    [record] = records("index")
    assert record["port"] is None
    serve_json = Path(record["cache"]) / "serve.json"
    assert serve_json.exists()
    proc.terminate()
    proc.wait(15)
    assert listed() == ([], []) and not serve_json.exists()


def test_refused_serve_leaves_no_record(project: Path, start) -> None:
    """A second serve for a served log dir fails and registers nothing."""
    first = start("--no-ui")
    [record] = records("index")
    second = start("--no-ui")
    second.wait(15)
    assert second.returncode != 0
    assert [r["pid"] for r in listed()[0]] == [first.pid] == [record["pid"]]


def test_watch_restart_one_record(project: Path, start) -> None:
    """A ``--watch`` restart closes the old record before the new process registers its own."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    start("--port", "0", "--watch")
    [old] = records("serve")
    os.utime(Path(beamtime.__file__))
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        live = listed()[0]
        if live and live[0]["started"] != old["started"]:
            break
        time.sleep(0.2)
    assert [r["started"] for r in live] != [old["started"]] and len(live) == 1


def test_stdio_registers_as_remote_with_the_ssh_peer(project: Path, start, monkeypatch) -> None:
    """``serve --stdio`` is a ``remote`` with a temporary cache and the peer from SSH_CONNECTION."""
    monkeypatch.setenv("SSH_CONNECTION", "10.1.2.3 5000 10.9.9.9 22")
    proc = start("--stdio", "--logdir", str(project / "beamtime"), stdin=subprocess.PIPE)
    [record] = records("remote")
    assert record["cache_kind"] == "temporary" and record["client"] == "10.1.2.3"
    assert record["logdir"] == str((project / "beamtime").resolve())
    proc.stdin.close()
    proc.wait(15)
    assert listed() == ([], [])


def test_killed_process_leaves_a_stale_record(project: Path, start) -> None:
    """After ``kill -9`` the record stays until ``listed`` finds its lock free."""
    proc = start("--no-ui")
    [record] = records("index")
    proc.kill()
    proc.wait(15)
    live, stale = listed()
    assert live == [] and [r["pid"] for r in stale] == [record["pid"]]
