import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

import pytest

pytest.importorskip("starlette")

import beamtime
from beamtime.index.cache import FileLock
from beamtime.index.procs import listed, register
from beamtime.ops import procs
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


def test_stdio_runs_without_a_registry(project: Path, start, monkeypatch, tmp_path: Path) -> None:
    """A runtime base that can't be written costs the record, not the session."""
    blocker = tmp_path / "file"
    blocker.write_text("")
    monkeypatch.setenv("BEAMTIME_RUNTIME", str(blocker / "rt"))
    proc = start("--stdio", "--logdir", str(project / "beamtime"), stdin=subprocess.PIPE)
    proc.stdin.write('{"id": 1, "op": "hello"}\n')
    proc.stdin.close()
    err = proc.stderr.read()
    assert proc.wait(15) == 0 and "not listed in the process registry" in err


def test_killed_process_leaves_a_stale_record(project: Path, start) -> None:
    """After ``kill -9`` the record stays until ``listed`` finds its lock free."""
    proc = start("--no-ui")
    [record] = records("index")
    proc.kill()
    proc.wait(15)
    live, stale = listed()
    assert live == [] and [r["pid"] for r in stale] == [record["pid"]]


def run_stop(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    """Run ``beamtime stop`` in a folder.

    :param args: Its arguments.
    :param cwd: The working directory.
    :return: The finished process, with text output."""
    return subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "stop", *args],
        cwd=cwd, capture_output=True, text=True, timeout=60,
    )  # fmt: skip


def other_project(tmp_path: Path) -> Path:
    """A second project with an empty log dir.

    :param tmp_path: Pytest's temporary directory.
    :return: Its root."""
    root = tmp_path / "other"
    (root / "beamtime").mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


def test_stop_uses_the_token(project: Path, start) -> None:
    """``stop`` ends a UI serve through ``/api/shutdown``; its files are gone."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    proc = start("--port", "0")
    [record] = records("serve")
    began = time.monotonic()
    done = run_stop(cwd=project)
    assert done.returncode == 0 and "through the token" in done.stdout, done.stderr
    proc.wait(5)
    assert time.monotonic() - began < 5
    assert listed() == ([], []) and not (Path(record["cache"]) / "serve.json").exists()


def test_stop_no_ui_by_sigterm(project: Path, start) -> None:
    """A serve without a port has no token route: ``stop`` sends SIGTERM."""
    proc = start("--no-ui")
    [record] = records("index")
    done = run_stop(cwd=project)
    assert done.returncode == 0 and "with SIGTERM" in done.stdout, done.stderr
    proc.wait(5)
    assert listed() == ([], []) and not (Path(record["cache"]) / "serve.json").exists()


def test_stop_all_stops_two_projects(project: Path, start, tmp_path: Path) -> None:
    """``--all`` stops the serves of every project, from any folder."""
    other = other_project(tmp_path)
    first = start("--no-ui")
    second = start("--no-ui", cwd=other)
    deadline = time.monotonic() + 30
    while len(listed()[0]) < 2 and time.monotonic() < deadline:
        time.sleep(0.1)
    assert len(listed()[0]) == 2
    done = run_stop("--all", cwd=tmp_path)
    assert done.returncode == 0, done.stderr
    first.wait(5)
    second.wait(5)
    assert listed() == ([], [])


def test_stop_by_root_and_pid_only_touches_that_serve(project: Path, start, tmp_path: Path) -> None:
    """A root names one serve, a pid another; the third stays."""
    other = other_project(tmp_path)
    a = start("--no-ui")
    b = start("--no-ui", cwd=other)
    deadline = time.monotonic() + 30
    while len(listed()[0]) < 2 and time.monotonic() < deadline:
        time.sleep(0.1)
    assert run_stop(str(project), cwd=tmp_path).returncode == 0
    a.wait(5)
    assert b.poll() is None
    assert run_stop(str(b.pid), cwd=tmp_path).returncode == 0
    b.wait(5)


def test_stop_refuses_an_mcp_pid(project: Path, tmp_path: Path) -> None:
    """The pid of a process that is only listed exits 2 with ``listed, not stopped``."""
    registration = register("mcp", root=str(project), client="some-agent")
    try:
        done = run_stop(str(os.getpid()), cwd=tmp_path)
    finally:
        registration.close()
    assert done.returncode == 2 and "listed, not stopped" in done.stderr + done.stdout
    assert "some-agent" in done.stderr + done.stdout


def test_stop_with_nothing_to_stop(project: Path) -> None:
    """No serve for this project: a line, exit 0."""
    done = run_stop(cwd=project)
    assert done.returncode == 0 and f"no serve runs for {project}" in done.stdout


def test_shutdown_needs_token(project: Path, start) -> None:
    """Without the token, or with a wrong one, ``/api/shutdown`` is 401 and the serve runs on."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    proc = start("--port", "0")
    [record] = records("serve")
    url = f"http://127.0.0.1:{record['port']}/api/shutdown"
    for headers in ({}, {"authorization": "Bearer wrong"}):
        with pytest.raises(OSError, match="401"):
            urlopen(Request(url, data=b"{}", headers=headers, method="POST"), timeout=5)
    assert proc.poll() is None


def test_shutdown_replies_first(project: Path, start) -> None:
    """The client receives the answer, then the serve exits."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    proc = start("--port", "0")
    [record] = records("serve")
    token = (Path(record["cache"]) / "serve.token").read_text().strip()
    request = Request(
        f"http://127.0.0.1:{record['port']}/api/shutdown",
        data=b"{}", headers={"authorization": f"Bearer {token}"}, method="POST",
    )  # fmt: skip
    with urlopen(request, timeout=10) as reply:
        assert json.load(reply) == {"kind": "stop", "pid": proc.pid}
    assert proc.wait(15) == 0


def test_stop_falls_back_to_sigterm(project: Path, start, monkeypatch) -> None:
    """A serve that takes the request and stays is ended by SIGTERM after the wait."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    proc = start("--port", "0")
    [record] = records("serve")
    monkeypatch.setattr(procs, "shutdown_request", lambda x: True)
    assert procs.stop_serve(record, wait_s=1.0) == "sigterm"
    proc.wait(10)


def test_stop_reports_a_serve_that_keeps_its_lock(tmp_path: Path) -> None:
    """A holder that survives SIGTERM is reported as running; nothing sends SIGKILL."""
    sleeper = subprocess.Popen(["sleep", "30"])
    lock = FileLock(path=tmp_path / "serve.lock")
    assert lock.acquire()
    try:
        row = {"pid": sleeper.pid, "cache": str(tmp_path), "port": None}
        assert procs.stop_serve(row, wait_s=0.5) == "running"
        assert sleeper.wait(5) == -signal.SIGTERM
    finally:
        lock.release()
        if sleeper.poll() is None:
            sleeper.kill()
