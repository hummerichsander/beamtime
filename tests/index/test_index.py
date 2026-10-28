import json
import math
import os
import shutil
import time
from pathlib import Path

import pytest

from beamtime.format.io import json_line
from beamtime.format.run import read_effective_metrics
from beamtime.format.tree import iter_runs
from beamtime.index.cache import SERVE_LOCK, FileLock, cache_dir, daemon_status
from beamtime.index.columns import Column, ColumnWriter, open_columns
from beamtime.index.daemon import Daemon
from beamtime.index.index import Freshness, Index
from beamtime.synth import generate


@pytest.fixture
def logdir(tmp_path: Path) -> Path:
    """A fresh synthetic log dir per test, since tests change files.

    :param tmp_path: Pytest's temporary directory.
    :return: The log dir."""
    out = tmp_path / "beamtime"
    generate(out, seed=1)
    return out


@pytest.fixture
def index(logdir: Path, tmp_path: Path):
    """An index of the log dir with its own cache.

    :param logdir: The log dir.
    :param tmp_path: Pytest's temporary directory.
    :return: The open index."""
    idx = Index(logdir=logdir, cache=tmp_path / "cache")
    yield idx
    idx.close()


def columns(index: Index, run_id: str) -> dict[str, list[tuple[int, float]]]:
    """Read every indexed column of a run.

    :param index: The index.
    :param run_id: The run id.
    :return: Key to ``(step, value)`` points."""
    _, entries = open_columns(index.series / run_id)
    out = {}
    for key, e in entries.items():
        col = Column.open(index.series / run_id, e)
        out[key] = list(zip(col.steps.tolist(), col.values.tolist(), strict=True))
        col.close()
    return out


def expected(run: Path) -> dict[str, list[tuple[int, float]]]:
    """Compute what the columns of a run must hold, from the format readers.

    :param run: The run directory.
    :return: Key to ``(step, value)`` points."""
    out: dict[str, list] = {}
    for row in read_effective_metrics(run):
        for k, v in row.items():
            if not k.startswith("_"):
                out.setdefault(k, []).append((row["_step"], float(v)))
    return out


def same(a: list[tuple[int, float]], b: list[tuple[int, float]]) -> bool:
    """Compare points, treating NaN as equal to NaN.

    :param a: Points.
    :param b: Points.
    :return: Whether they are equal."""
    return len(a) == len(b) and all(
        x[0] == y[0] and (x[1] == y[1] or (math.isnan(x[1]) and math.isnan(y[1])))
        for x, y in zip(a, b, strict=True)
    )


def check_all(index: Index, logdir: Path) -> None:
    """Assert that every run's columns equal its effective metrics.

    :param index: The index.
    :param logdir: The log dir."""
    for run in iter_runs(logdir):
        got = columns(index, run.name)
        got.pop("_t", None)
        want = expected(run)
        assert got.keys() == want.keys(), run.name
        for k in want:
            assert same(got[k], want[k]), (run.name, k)


def test_full_ingest_matches_the_files(index: Index, logdir: Path) -> None:
    """Every run's columns, events, data and notes are indexed."""
    fresh = index.catch_up(".", budget_s=float("inf"))
    assert fresh.behind == 0 and not fresh.damaged
    check_all(index, logdir)
    db = index.store.db
    assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 26
    assert db.execute("SELECT count(*) FROM notes").fetchone()[0] == 6
    links = {tuple(r) for r in db.execute("SELECT kind, target FROM links")}
    assert ("prediction", "scaling/lr-sweep#converges") in links
    roles = json.loads((logdir / "_synth.json").read_text())["roles"]
    assert ("run", roles["diverging"]) in links
    assert db.execute("SELECT count(*) FROM events WHERE kind='requeue_requested'").fetchone()[0]


def test_incremental_ingest(index: Index, logdir: Path) -> None:
    """Appended lines, including a partial one, are picked up on the next catch-up."""
    index.catch_up(".", budget_s=float("inf"))
    roles = json.loads((logdir / "_synth.json").read_text())["roles"]
    run = next(p for p in iter_runs(logdir) if p.name == roles["running"])
    metrics = run / "_metrics.jsonl"
    with metrics.open("ab") as f:
        f.write(json_line({"_step": 5000, "_t": 1.0, "train/loss": 0.1, "new": 1}))
        f.write(b'{"_step": 5001, "_t": 2.0, "train/lo')
    index.catch_up(".", budget_s=float("inf"))
    got = columns(index, run.name)
    assert got["new"] == [(5000, 1.0)] and got["train/loss"][-1] == (5000, 0.1)
    with metrics.open("ab") as f:
        f.write(b'ss": 0.05}\n')
    index.catch_up(".", budget_s=float("inf"))
    assert columns(index, run.name)["train/loss"][-1] == (5001, 0.05)


def test_resume_truncates_older_attempt(index: Index, logdir: Path) -> None:
    """A resumed attempt replaces the older attempt's points from its resume step."""
    run = next(p for p in iter_runs(logdir / "scaling" / "long-context"))
    index.catch_up(".", budget_s=float("inf"))
    check_all(index, logdir)
    resumed = [r for r in iter_runs(logdir) if len(json.loads((r / "_run.json").read_text())["attempts"]) > 1]
    assert resumed and run


def test_late_attempt_event_and_implicit_resume(index: Index, logdir: Path) -> None:
    """A decreasing step waits for its event while running; otherwise it is a resume."""
    run = next(iter_runs(logdir / "tokenizer"))
    info = json.loads((run / "_run.json").read_text())
    info["status"] = "running"
    (run / "_run.json").write_text(json.dumps(info))
    index.catch_up(".", budget_s=float("inf"))
    size = (run / "_metrics.jsonl").stat().st_size
    with (run / "_metrics.jsonl").open("ab") as f:
        for s in range(100, 103):
            f.write(json_line({"_step": s, "_t": 9.0, "train/loss": 42.0}))
    index.catch_up(".", budget_s=float("inf"))
    assert columns(index, run.name)["train/loss"][-1][1] != 42.0
    with (run / "_events.jsonl").open("ab") as f:
        f.write(json_line({"_t": 9.0, "kind": "attempt_started", "resume_step": 100,
                           "metrics_offset": size}))  # fmt: skip
    index.catch_up(".", budget_s=float("inf"))
    loss = columns(index, run.name)["train/loss"]
    assert loss[-3:] == [(100, 42.0), (101, 42.0), (102, 42.0)] and loss[-4][0] == 99

    other = next(iter_runs(logdir / "scaling" / "lr-sweep"))
    with (other / "_metrics.jsonl").open("ab") as f:
        f.write(json_line({"_step": 10, "_t": 9.0, "train/loss": 7.0}))
    # a finished run is re-read once its _run.json changes, as a resume would do.
    os.utime(other / "_run.json")
    index.catch_up(".", budget_s=float("inf"))
    loss = columns(index, other.name)["train/loss"]
    assert loss[-1] == (10, 7.0) and loss[-2][0] == 9


def test_columns_recover_to_the_manifest(tmp_path: Path) -> None:
    """Bytes written after the last published manifest are cut off on reopen."""
    w = ColumnWriter(dir=tmp_path)
    for s in range(5):
        w.append("x", s, float(s))
    w.commit(100)
    with (tmp_path / "x.0.steps").open("ab") as f:
        f.write(b"\x00" * 16)
    with (tmp_path / "x.0.values").open("ab") as f:
        f.write(b"\x00" * 8)
    ColumnWriter(dir=tmp_path)
    assert (tmp_path / "x.0.steps").stat().st_size == 40
    col = Column.open(tmp_path, open_columns(tmp_path)[1]["x"])
    assert col.steps.tolist() == [0, 1, 2, 3, 4]
    col.close()


def test_truncation_writes_a_new_generation(tmp_path: Path) -> None:
    """Truncating never shrinks a file a reader may have mapped."""
    w = ColumnWriter(dir=tmp_path)
    for s in range(10):
        w.append("x", s, float(s))
    w.commit(1)
    reader = Column.open(tmp_path, open_columns(tmp_path)[1]["x"])
    w.truncate_from(4)
    w.append("x", 4, 40.0)
    w.commit(2)
    assert reader.values.tolist() == [float(s) for s in range(10)]
    reader.close()
    entry = open_columns(tmp_path)[1]["x"]
    assert entry.file == "x.1"
    col = Column.open(tmp_path, entry)
    assert col.values.tolist() == [0.0, 1.0, 2.0, 3.0, 40.0]
    col.close()


def test_moved_and_deleted_runs(index: Index, logdir: Path) -> None:
    """Moved runs keep their columns under the new path; deleted runs are forgotten."""
    index.catch_up(".", budget_s=float("inf"))
    runs = list(iter_runs(logdir / "scaling" / "lr-sweep"))
    moved, deleted = runs[0], runs[1]
    (logdir / "archive").mkdir()
    shutil.move(moved, logdir / "archive" / moved.name)
    shutil.rmtree(deleted)
    time.sleep(0.01)
    index.catch_up(".", budget_s=float("inf"))
    assert index.store.run(moved.name)["path"] == f"archive/{moved.name}"
    assert columns(index, moved.name)
    assert index.store.run(deleted.name) is None
    assert not (index.series / deleted.name).exists()


def test_unchanged_folders_are_not_listed_again(index: Index, logdir: Path, monkeypatch) -> None:
    """A second walk lists only folders whose modification time changed."""
    index.catch_up(".", budget_s=float("inf"))
    old = time.time() - 60
    for d in [logdir, *[p for p in logdir.rglob("*") if p.is_dir()]]:
        os.utime(d, (old, old))
    index.store.db.execute("UPDATE folders SET walked = ?", (time.time(),))
    index.catch_up(".", budget_s=float("inf"))
    listed = []
    real = os.scandir
    monkeypatch.setattr(os, "scandir", lambda p: listed.append(p) or real(p))
    index.catch_up(".", budget_s=float("inf"))
    assert listed == []


def test_budget_reports_runs_behind(index: Index) -> None:
    """With no time to spare, streams wait and the answer says so; metadata is complete."""
    fresh = index.catch_up(".", budget_s=0.0)
    assert fresh.behind > 0 and "not yet indexed" in fresh.text()
    assert index.store.db.execute("SELECT count(*) FROM runs").fetchone()[0] == 26


def test_deferred_streams_are_read_later(index: Index, logdir: Path) -> None:
    """Runs whose streams a budget deferred are read by the next catch-up with time."""
    assert index.catch_up(".", budget_s=0.0).behind > 0
    assert index.catch_up(".", budget_s=float("inf")).behind == 0
    check_all(index, logdir)


def test_damaged_run_is_skipped(index: Index, logdir: Path) -> None:
    """A run with a broken _run.json is reported, the others are indexed."""
    run = next(iter_runs(logdir / "tokenizer"))
    (run / "_run.json").write_text("{broken")
    fresh = index.catch_up(".", budget_s=float("inf"))
    assert len(fresh.damaged) == 1 and run.name in fresh.damaged[0]


def test_locks_and_daemon(logdir: Path, tmp_path: Path) -> None:
    """One daemon per cache; while it runs, clients don't ingest and say live."""
    cache = tmp_path / "cache"
    daemon = Daemon(logdir=logdir, cache=cache)
    assert daemon.start()
    try:
        assert not Daemon(logdir=logdir, cache=cache).start()
        deadline = time.time() + 30
        client = Index(logdir=logdir, cache=cache)
        while time.time() < deadline:
            n = client.store.db.execute("SELECT count(*) FROM runs").fetchone()[0]
            if n == 26 and client.store.db.execute("SELECT count(*) FROM events").fetchone()[0]:
                break
            time.sleep(0.1)
        assert client.catch_up(".") == Freshness(daemon=True)
        assert daemon_status(cache)["pid"] == os.getpid()
        client.close()
    finally:
        daemon.stop()
    assert daemon_status(cache) is None
    assert not FileLock(path=cache / SERVE_LOCK).held_elsewhere()


def test_cache_dir_respects_environment(tmp_path: Path, monkeypatch) -> None:
    """BEAMTIME_CACHE wins over XDG_CACHE_HOME; different log dirs get different caches."""
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "a"))
    assert cache_dir(tmp_path / "x").parent == tmp_path / "a"
    monkeypatch.delenv("BEAMTIME_CACHE")
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg"))
    assert cache_dir(tmp_path / "x").parent == tmp_path / "xdg" / "beamtime"
    assert cache_dir(tmp_path / "x") != cache_dir(tmp_path / "y")
