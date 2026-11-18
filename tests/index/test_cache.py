import getpass
import http.server
import json
import tempfile
import threading
from pathlib import Path

import pytest

from beamtime.index import cache as cache_module
from beamtime.index.cache import Cache, cache_dir, daemon_status, resolve_cache, runtime_base, runtime_dir
from beamtime.index.daemon import Daemon
from beamtime.index.index import Index
from beamtime.ops.context import Context
from beamtime.remote import pull, via_serve
from beamtime.serve.auth import TOKEN_FILE
from beamtime.settings import Settings, expand_path, read_level


def configured(value: str, level: str = "project") -> Settings:
    """Settings with one ``cache`` value.

    :param value: The value.
    :param level: The level it came from.
    :return: The settings."""
    return Settings(values={"cache": value}, levels={"cache": level})


@pytest.fixture
def clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """No cache environment, a private temporary directory and no network mounts.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: A folder for the test's logdirs."""
    monkeypatch.delenv("BEAMTIME_CACHE", raising=False)
    monkeypatch.delenv("BEAMTIME_RUNTIME", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    (tmp_path / "tmp").mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "tmp"))
    monkeypatch.setattr(cache_module, "MOUNTS", tmp_path / "mounts")
    logdir = tmp_path / "logdir"
    logdir.mkdir()
    return logdir


def mount_nfs(tmp_path: Path, where: Path) -> None:
    """Pretend a folder is an NFS mount.

    :param tmp_path: Pytest's temporary directory.
    :param where: The mount point."""
    (tmp_path / "mounts").write_text(f"server:/export {where.resolve()} nfs rw 0 0\n")


def test_expand_path() -> None:
    """{user}, ${VAR} and ~ expand on this machine."""
    assert expand_path("/s/{user}/bt", user="ada") == "/s/ada/bt"
    assert expand_path("/s/{user}") == f"/s/{getpass.getuser()}"
    assert expand_path("~/bt") == str(Path.home() / "bt")


def test_env_overrides_setting(clean: Path, tmp_path: Path, monkeypatch) -> None:
    """BEAMTIME_CACHE wins over the setting; a --cache flag wins over both."""
    settings = configured(str(tmp_path / "setting"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "env"))
    assert resolve_cache(clean, settings).path.parent == tmp_path / "env"
    assert resolve_cache(clean, settings).source == "BEAMTIME_CACHE"
    flag = configured(str(tmp_path / "flag"), "flag")
    assert resolve_cache(clean, flag).path.parent == tmp_path / "flag"
    monkeypatch.delenv("BEAMTIME_CACHE")
    assert resolve_cache(clean, settings).path.parent == tmp_path / "setting"
    assert resolve_cache(clean, settings).source == "project settings"
    assert resolve_cache(clean).path.parent == tmp_path / "xdg" / "beamtime"
    assert resolve_cache(clean).source == "default"


def test_setting_reaches_every_consumer(clean: Path, tmp_path: Path) -> None:
    """A placeholder path resolves to <path>/<hash> for Index, Daemon, cache_dir, pull and doctor."""
    settings = configured(f"{tmp_path}/{{user}}/bt")
    expected = resolve_cache(clean, settings).path
    assert expected.parent == tmp_path / getpass.getuser() / "bt"
    assert expected == cache_dir(clean, settings)
    with Index(logdir=clean, settings=settings) as index:
        assert index.cache == expected and index.scratch is None
    assert Daemon(logdir=clean, settings=settings).cache == expected
    ctx = Context(root=tmp_path, root_reason="test", settings=settings, logdir=clean, caller="cli")
    assert pull.snapshots_dir(ctx) == expected / "pulled"
    from beamtime.ops.admin import doctor
    from beamtime.ops.registry import NoParams

    rows = {row[0]: row[2] for row in doctor(ctx, NoParams())["rows"]}
    assert str(expected) in rows["cache"] and "project settings" in rows["cache"]


def test_nfs_is_refused(clean: Path, tmp_path: Path) -> None:
    """A configured path whose mount is nfs resolves to memory and says which filesystem."""
    target = tmp_path / "scratch"
    target.mkdir()
    mount_nfs(tmp_path, target)
    resolved = resolve_cache(clean, configured(str(target / "bt")))
    assert resolved == Cache(runtime_dir(clean), "memory", "nfs", "project settings")


def test_default_on_nfs_is_memory(clean: Path, tmp_path: Path) -> None:
    """A user cache dir on a network home falls back to memory without any setting."""
    (tmp_path / "xdg").mkdir()
    mount_nfs(tmp_path, tmp_path / "xdg")
    resolved = resolve_cache(clean)
    assert resolved.kind == "memory" and resolved.refused == "nfs" and resolved.source == "default"


def test_runtime_dir_is_private(clean: Path, tmp_path: Path) -> None:
    """The memory cache's serve files live in <tmp>/beamtime-<uid>/<hash>, mode 0700."""
    path = runtime_dir(clean)
    assert path.parent.parent == tmp_path / "tmp"
    assert path.parent == runtime_base()
    assert path.name == cache_module.log_hash(clean)
    assert path.stat().st_mode & 0o777 == 0o700 and path.parent.stat().st_mode & 0o777 == 0o700


def test_memory_is_per_process(clean: Path) -> None:
    """With memory, each Index gets its own temporary folder, removed at close()."""
    settings = configured("memory")
    one, two = Index(logdir=clean, settings=settings), Index(logdir=clean, settings=settings)
    assert one.scratch != two.scratch
    assert one.cache == two.cache == runtime_dir(clean)
    assert one.scratch.is_dir() and (one.scratch / "index.sqlite").exists()
    one.close()
    assert not one.scratch.exists() and two.scratch.is_dir()
    two.close()
    assert not two.scratch.exists()


def test_serve_with_memory_shares_one_index(clean: Path) -> None:
    """A memory serve's requests see the runs its daemon indexed, and serve.json stays in runtime_dir."""
    from beamtime.serve.server import share_memory

    run = clean / "g" / "20260101-000000-abcdefgh"
    run.mkdir(parents=True)
    (run / "_run.json").write_text(
        json.dumps({"schema": 1, "id": run.name, "name": "a", "status": "finished"})
    )
    ctx = Context(root=clean.parent, root_reason="--root", settings=configured("memory"), logdir=clean)
    daemon = Daemon(logdir=clean, settings=ctx.settings)
    own = share_memory(ctx, daemon)
    assert daemon.cache == runtime_dir(clean) and own is not None
    with Index(logdir=clean, settings=ctx.settings) as index:
        index.catch_up(".", budget_s=float("inf"))
    with Index(logdir=clean, settings=ctx.settings) as request:
        assert request.run_path(run.name) == run


def test_serve_with_memory_is_found_by_via_serve(clean: Path, tmp_path: Path) -> None:
    """A daemon with a memory cache publishes serve.json under runtime_dir, and via_serve.call finds it."""

    class Handler(http.server.BaseHTTPRequestHandler):
        """Answers every post with the token it was sent."""

        def do_POST(self) -> None:  # noqa: N802
            """Echo the authorization header."""
            self.rfile.read(int(self.headers.get("content-length", 0)))
            body = json.dumps({"auth": self.headers["authorization"]}).encode()
            self.send_response(200)
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args) -> None:
            """Stay quiet."""

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    settings = configured("memory")
    daemon = Daemon(logdir=clean, settings=settings, port=server.server_port, poll_s=0.05)
    assert daemon.start()
    try:
        assert daemon.cache == runtime_dir(clean)
        assert daemon_status(daemon.cache)["port"] == server.server_port
        (daemon.cache / TOKEN_FILE).write_text("secret\n")
        ctx = Context(
            root=tmp_path, root_reason="test", settings=settings, logdir=clean, caller="cli"
        )
        assert via_serve.call(ctx, "runs", {}) == {"auth": "Bearer secret"}
    finally:
        daemon.stop()
        server.shutdown()


def test_invalid_cache_setting_is_reported(tmp_path: Path) -> None:
    """A cache that is not a string is ignored with a problem."""
    path = tmp_path / "beamtime.yaml"
    path.write_text("schema: 1\ncache: [a, b]\n")
    problems: list[str] = []
    assert read_level(path, "project", problems) == {}
    assert "cache" in problems[0]
    path.write_text("schema: 1\ncache: memory\n")
    assert read_level(path, "project", problems) == {"cache": "memory"}


def test_index_records_its_logdir(clean: Path, tmp_path: Path, monkeypatch) -> None:
    """Opening an index records its log dir, and known_logdirs finds it and drops deleted ones.

    :param clean: A clean log dir.
    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch."""
    from beamtime.index.cache import known_logdirs

    root = tmp_path / "root"
    monkeypatch.setenv("BEAMTIME_CACHE", str(root))
    with Index(logdir=clean):
        pass
    assert known_logdirs(root) == [clean.resolve()]
    assert known_logdirs() == [clean.resolve()]
    gone = tmp_path / "gone"
    gone.mkdir()
    with Index(logdir=gone):
        pass
    gone.rmdir()
    assert known_logdirs(root) == [clean.resolve()]


def test_store_rewrites_a_changed_logdir(tmp_path: Path) -> None:
    """A database that now indexes another log dir records the new one.

    :param tmp_path: Pytest's temporary directory."""
    from beamtime.index.store import Store

    path = tmp_path / "index.sqlite"
    Store(path=path, logdir=tmp_path / "one").db.close()
    store = Store(path=path, logdir=tmp_path / "two")
    assert store.db.execute("SELECT value FROM meta WHERE key = 'logdir'").fetchone()[0] == str(
        tmp_path / "two"
    )
    store.db.close()


def test_known_skips_locked(tmp_path: Path) -> None:
    """A cache that is locked is skipped, not waited on.

    :param tmp_path: Pytest's temporary directory."""
    import sqlite3
    import time

    from beamtime.index.cache import known_logdirs

    db = tmp_path / "root" / "abc" / "index.sqlite"
    db.parent.mkdir(parents=True)
    writer = sqlite3.connect(db, isolation_level=None)
    writer.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    writer.execute("INSERT INTO meta VALUES ('logdir', ?)", (str(tmp_path),))
    writer.execute("BEGIN EXCLUSIVE")
    start = time.monotonic()
    assert known_logdirs(tmp_path / "root") == []
    assert time.monotonic() - start < 5
    writer.execute("COMMIT")
    writer.close()


def test_known_reads_only(tmp_path: Path) -> None:
    """Listing known log dirs never creates a cache folder.

    :param tmp_path: Pytest's temporary directory."""
    from beamtime.index.cache import known_logdirs

    root = tmp_path / "missing"
    assert known_logdirs(root) == []
    assert not root.exists()


def test_runtime_base_honors_environment(clean: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """BEAMTIME_RUNTIME replaces <tmp>/beamtime-<uid>, and runtime_dir moves with it."""
    monkeypatch.setenv("BEAMTIME_RUNTIME", str(tmp_path / "rt"))
    assert runtime_base() == tmp_path / "rt"
    assert runtime_dir(clean) == tmp_path / "rt" / cache_module.log_hash(clean)
    assert (tmp_path / "rt").stat().st_mode & 0o777 == 0o700
