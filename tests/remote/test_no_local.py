"""A source is a named log dir; local is one only when this machine has runs (D1). These tests
run entirely from an empty directory with no ``beamtime.yaml`` and no local log dir, talking to a
remote over a plain command (the test transport, no ssh needed)."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from beamtime.ops.context import Context
from beamtime.remote import answer as call
from beamtime.synth import generate

COMMAND = f"{sys.executable} -m beamtime.cli"
SWEEP = "scaling/lr-sweep"


@pytest.fixture(autouse=True)
def _no_stale_connections():
    """One-shot calls cache a remote's connection by name in a module-level dict; close and drop
    it after each test, since several tests here name their remote ``box``."""
    from beamtime.remote.sources import opened

    yield
    for client in list(opened.values()):
        client.close()
    opened.clear()


@pytest.fixture
def empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A plain, empty directory: no git repository, no ``beamtime.yaml``, no log dir.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: The directory, as the working directory."""
    root = tmp_path / "empty"
    root.mkdir()
    monkeypatch.chdir(root)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    return root


@pytest.fixture
def remote_logdir(tmp_path: Path) -> Path:
    """A remote's log dir, with runs, reached over a plain command.

    :param tmp_path: Pytest's temporary directory.
    :return: Its log dir."""
    logdir = tmp_path / "remote" / "beamtime"
    generate(logdir, seed=3, now=datetime.now(timezone.utc))
    return logdir


def write_remotes(root: Path, remotes: dict[str, Path]) -> None:
    """Configure remotes in the project's ``beamtime.yaml``, over the command transport.

    :param root: The project root.
    :param remotes: Name to log dir."""
    lines = ["schema: 1", "remotes:"]
    for name, logdir in remotes.items():
        lines += [
            f"  {name}:",
            f"    path: {logdir}",
            f"    command: {COMMAND}",
            "    transport: command",
        ]
    (root / "beamtime.yaml").write_text("\n".join(lines) + "\n")


@pytest.fixture
def one_remote(empty: Path, remote_logdir: Path) -> Context:
    """One remote configured, no local log dir.

    :param empty: The empty project directory.
    :param remote_logdir: The remote's log dir.
    :return: The context."""
    write_remotes(empty, {"box": remote_logdir})
    return Context.make(caller="cli")


def test_has_local_is_false_without_a_log_dir(one_remote: Context) -> None:
    """``has_local`` is false when the log dir doesn't exist, even with no remotes."""
    assert one_remote.has_local is False
    bare = Context.make(caller="cli")
    assert bare.has_local is False


def test_has_local_follows_a_run_created_after_startup(one_remote: Context) -> None:
    """With remotes configured, a log dir with no runs isn't local yet; one run makes it so."""
    one_remote.logdir.mkdir(parents=True)
    assert one_remote.has_local is False
    generate(one_remote.logdir, seed=1, now=datetime.now(timezone.utc))
    assert one_remote.has_local is True


def test_has_local_true_without_remotes(empty: Path) -> None:
    """Without remotes configured, an existing log dir is local even with no runs yet."""
    ctx = Context.make(caller="cli")
    ctx.logdir.mkdir(parents=True)
    assert ctx.has_local is True


def test_default_source_is_the_sole_remote(one_remote: Context) -> None:
    """With no local source and one remote, unprefixed paths mean that remote."""
    assert one_remote.default_source == "box"


def test_default_source_is_none_with_several_remotes(
    empty: Path, remote_logdir: Path, tmp_path: Path
) -> None:
    """Two remotes and no local: ambiguous, so there is no default."""
    write_remotes(empty, {"box": remote_logdir, "other": tmp_path / "other" / "beamtime"})
    ctx = Context.make(caller="cli")
    assert ctx.default_source is None


def test_unprefixed_calls_route_to_the_default_source(one_remote: Context) -> None:
    """A plain ``runs`` call, with no ``@`` anywhere, answers from the sole remote."""
    answer = call("runs", {"from": ".", "select": ["run.group"], "limit": 3}, one_remote)
    assert answer["rows"]
    group = answer["columns"].index("run.group")
    assert all(r[group].startswith("@box/") for r in answer["rows"])
    assert answer["meta"]["source"] == "@box"


def test_at_local_is_accepted_and_stripped(ctx: Context) -> None:
    """``@local/...`` reads like the bare local path (``ctx`` here has a real local project and
    ``box`` as a remote, from ``tests/remote/conftest.py``)."""
    bare = call("runs", {"from": SWEEP, "select": ["run.name"], "limit": 3}, ctx)
    prefixed = call("runs", {"from": "@local/" + SWEEP, "select": ["run.name"], "limit": 3}, ctx)
    # not full equality: freshness (meta.freshness.behind_s) is live catch-up timing, not identity.
    assert prefixed["columns"] == bare["columns"] and prefixed["rows"] == bare["rows"]
    assert prefixed["meta"]["source"] == bare["meta"]["source"] == "local"


def test_nothing_is_created_in_the_empty_directory(one_remote: Context, empty: Path) -> None:
    """Working from an empty directory with only a remote writes nothing there."""
    before = set(empty.iterdir())
    call("status", {}, one_remote)
    call("runs", {"from": ".", "limit": 1}, one_remote)
    assert set(empty.iterdir()) == before


def test_serve_refuses_only_with_no_source_at_all(empty: Path) -> None:
    """``serve`` refuses when there is neither a local log dir nor any remote."""
    from beamtime.ops import registry as r
    from beamtime.ops.context import OpError
    from beamtime.serve.server import serve

    ctx = Context.make(caller="cli")
    with pytest.raises(OpError, match="no log dir.*no remotes configured"):
        serve(ctx, r.ServeParams(no_ui=True, port=0))


def test_cli_answers_with_only_a_remote(empty: Path, remote_logdir: Path) -> None:
    """A plain CLI call from an empty directory with one remote configured just works."""
    write_remotes(empty, {"box": remote_logdir})
    out = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "runs", "--json", "--limit", "2"],
        cwd=empty,
        capture_output=True,
        text=True,
        env=dict(os.environ),
        timeout=30,
    )
    assert out.returncode == 0, out.stderr
    answer = json.loads(out.stdout)
    assert answer["rows"] and answer["meta"]["source"] == "@box"


def test_mcp_answers_with_only_a_remote(empty: Path, remote_logdir: Path) -> None:
    """``beamtime mcp`` from an empty directory with one remote configured answers tool calls."""
    anyio = pytest.importorskip("anyio")
    pytest.importorskip("mcp")
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    write_remotes(empty, {"box": remote_logdir})
    name = "beamtime.exe" if sys.platform == "win32" else "beamtime"
    beamtime = Path(sys.executable).parent / name

    async def work() -> Any:
        params = StdioServerParameters(
            command=str(beamtime), args=["mcp"], cwd=str(empty), env=dict(os.environ)
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                return await s.call_tool("runs", {"from": ".", "limit": 2})

    result = anyio.run(work)
    assert not result.is_error, result.content[0].text
    answer = json.loads(result.content[0].text)
    assert answer["rows"] and answer["meta"]["source"] == "@box"


def test_a_served_tree_names_only_the_remote(one_remote: Context) -> None:
    """In a serve with one remote and no local runs, the UI's tree listing still fans out, so
    ``meta.sources`` names the remote and no empty local root appears."""
    import dataclasses

    from beamtime.remote.sources import Sources, spec_of
    from beamtime.serve.api import dispatch

    sources = Sources([spec_of("box", one_remote.settings.get("remotes")["box"])])
    try:
        ctx = dataclasses.replace(one_remote, caller="view", sources=sources)
        answer = dispatch(ctx, "groups", {"from": ".", "everywhere": True})
    finally:
        sources.close()
    assert [s["name"] for s in answer["meta"]["sources"]] == ["@box"]
    assert all(r[0].startswith("@box") for r in answer["rows"])


def test_a_view_draft_for_an_unprefixed_group_goes_to_the_default_source(
    one_remote: Context,
) -> None:
    """``view new scaling/lr-sweep`` with only one remote drafts for ``@box/scaling/lr-sweep``."""
    new = call("view new", {"group": SWEEP, "name": "plain"}, one_remote)
    assert new["group"] == f"@box/{SWEEP}"
    assert call("view validate", {"draft": "plain", "render": False}, one_remote)["ok"]


def test_the_daemon_waits_for_a_log_dir_created_later(empty: Path) -> None:
    """A serve started without a local log dir indexes it once a first run creates it."""
    import threading

    from beamtime.index.daemon import Daemon

    changed = threading.Event()
    logdir = empty / "beamtime"
    daemon = Daemon(logdir=logdir, on_change=lambda _: changed.set(), poll_s=0.05)
    assert daemon.start()
    try:
        generate(logdir, seed=1, now=datetime.now(timezone.utc))
        assert changed.wait(30)
    finally:
        daemon.stop()


def test_serve_and_its_ui_with_only_a_remote(empty: Path, remote_logdir: Path) -> None:
    """``beamtime serve`` from an empty directory with one remote: ``/`` and ``/f/local`` lead to
    the remote, the tree names only it, a CLI call goes through this serve, and the directory
    stays empty."""
    import http.client
    import socket

    write_remotes(empty, {"box": remote_logdir})
    before = set(empty.iterdir())
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = subprocess.Popen(
        [sys.executable, "-m", "beamtime.cli", "serve", "--port", str(port)],
        cwd=empty, env=dict(os.environ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )  # fmt: skip
    try:
        line = ""
        while "token=" not in line:
            line = server.stdout.readline()
            assert line or server.poll() is None, "serve ended"
        token = line.strip().rsplit("token=", 1)[1]
        auth = {"authorization": f"Bearer {token}", "content-type": "application/json"}

        def request(method: str, path: str, body: dict | None = None) -> http.client.HTTPResponse:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=60)
            conn.request(method, path, json.dumps(body) if body is not None else None, auth)
            return conn.getresponse()

        for path in ("/", "/f/local/scaling"):
            response = request("GET", path)
            assert response.status == 307
            assert response.getheader("location").startswith("/f/@box")
        tree = json.loads(request("POST", "/api/groups", {"from": ".", "everywhere": True}).read())
        assert [s["name"] for s in tree["meta"]["sources"]] == ["@box"]
        meta = json.loads(request("POST", "/api/meta", {}).read())
        assert [s["name"] for s in meta["sources"]] == ["@box"]
        out = subprocess.run(
            [sys.executable, "-m", "beamtime.cli", "runs", "--json", "--limit", "2"],
            cwd=empty, capture_output=True, text=True, env=dict(os.environ), timeout=60,
        )  # fmt: skip
        assert out.returncode == 0, out.stderr
        # answered by the serve: only a federated listing names its sources.
        assert json.loads(out.stdout)["meta"]["sources"][0]["name"] == "@box"
    finally:
        server.terminate()
        server.wait(timeout=30)
    assert set(empty.iterdir()) == before


def test_the_tree_names_a_remote_that_is_down(empty: Path, tmp_path: Path) -> None:
    """With no local runs and the only remote down, the tree is empty but still names the remote
    and why, so the sidebar can mark it unreachable."""
    import dataclasses

    from beamtime.remote.client import Spec
    from beamtime.remote.sources import Sources
    from beamtime.serve.api import dispatch

    gone = Spec(name="gone", path=str(tmp_path), command="false", transport="command")
    sources = Sources([gone])
    try:
        ctx = dataclasses.replace(Context.make(caller="view"), sources=sources)
        answer = dispatch(ctx, "groups", {"from": ".", "everywhere": True})
    finally:
        sources.close()
    assert answer["rows"] == []
    assert [(s["name"], s["state"]) for s in answer["meta"]["sources"]] == [("@gone", "unreachable")]
