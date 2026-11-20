"""The importer interface, the run writer and the CSV, MLflow, TensorBoard and W&B sources."""

import json
import math
import shutil
import sqlite3
import struct
import sys
import types
from pathlib import Path

import pytest

from beamtime import query
from beamtime.format import constants as c
from beamtime.format import moves
from beamtime.format.io import read_json
from beamtime.format.run import read_effective_metrics, read_run_info
from beamtime.format.tree import iter_runs
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.setup import importers
from beamtime.setup.importers import Imported
from beamtime.setup.importers import csv as csv_source
from beamtime.setup.importers import mlflow as mlflow_source
from beamtime.setup.importers import notes as notes_source
from beamtime.setup.importers import tensorboard as tb_source
from beamtime.setup.importers import wandb as wandb_source
from beamtime.setup.importers import write
from beamtime.setup.importers.beamtime import Copied, copy_logdir
from beamtime.setup.importers.write import write_run
from beamtime.views.library import Library

FIXTURES = Path(__file__).parent / "fixtures" / "csv"


@pytest.fixture
def logdir(tmp_path: Path) -> Path:
    """An empty log dir.

    :param tmp_path: The test's temporary directory.
    :return: The log dir."""
    d = tmp_path / "beamtime"
    d.mkdir()
    return d


def import_csv(logdir: Path, name: str) -> Path:
    """Import one CSV fixture under ``imported/<stem>/``.

    :param logdir: The log dir.
    :param name: The fixture's file name.
    :return: The run folder."""
    path = FIXTURES / name
    (imported,) = csv_source.runs(path)
    return write_run(
        logdir, f"imported/{path.stem}", imported, {"kind": "csv", "path": str(path.resolve())}
    )


def test_csv_import_reads_like_a_run(home: Path, logdir: Path) -> None:
    """A CSV run is answered by ``runs``, ``card`` and ``series`` like any run."""
    d = import_csv(logdir, "train.csv")
    runs = query.run({"runs": {"from": "imported/train"}}, logdir=logdir)
    assert [r[:3] for r in runs["rows"]] == [[d.name, "train", "finished"]]
    card = call("card", {"run": d.name}, Context.make(root=logdir.parent))
    assert card["metrics"]["acc"]["last"] == 0.55
    assert card["metrics"]["loss"]["nonfinite"] == 1
    series = query.run({"series": {"from": "imported/train", "y": ["acc"]}}, logdir=logdir)
    assert series["curves"][0]["y"] == [0.1, 0.25, 0.48, 0.55]


def test_csv_provenance(logdir: Path) -> None:
    """``_run.json`` records the kind and the absolute path of the original."""
    d = import_csv(logdir, "train.csv")
    origin = read_run_info(d).imported_from
    assert origin["kind"] == "csv"
    assert origin["path"] == str((FIXTURES / "train.csv").resolve())
    assert Path(origin["path"]).is_absolute()
    assert {"host", "at"} <= origin.keys() and "id" not in origin


def test_second_import_adds_nothing(logdir: Path) -> None:
    """A run whose original is in the log dir already is skipped."""
    first = import_csv(logdir, "train.csv")
    second = import_csv(logdir, "train.csv")
    assert first == second
    assert len(list((logdir / "imported").rglob(c.RUN))) == 1
    assert write.find_imported(logdir, str((FIXTURES / "train.csv").resolve()), "other") is None


def test_csv_no_step(logdir: Path) -> None:
    """A CSV without a step column uses the row index."""
    d = import_csv(logdir, "no_step.csv")
    rows = read_effective_metrics(d)
    assert [r["_step"] for r in rows] == [0, 1, 2]
    assert rows[2]["loss"] == 0.25


def test_csv_step_aliases_sorted(logdir: Path) -> None:
    """The epoch column is the step, and rows are written in step order."""
    d = import_csv(logdir, "epochs.csv")
    rows = read_effective_metrics(d)
    assert [(r["_step"], r["val/loss"]) for r in rows] == [(0, 0.9), (1, 0.7), (2, 0.5)]


def test_csv_text_columns(logdir: Path) -> None:
    """Text columns and empty cells are skipped; the step column is no metric."""
    d = import_csv(logdir, "train.csv")
    rows = read_effective_metrics(d)
    assert all(set(r) <= {"_step", "_t", "loss", "acc"} for r in rows)
    assert math.isnan(rows[-1]["loss"])
    assert read_json(d / c.CONFIG) == {"schema": 1}


def test_partial_import(logdir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A crash before the last file leaves no ``_run.json``, and a rerun imports the run."""
    real = write.write_replaced

    def crash(path: Path, obj: object, **kw: object) -> None:
        if path.name == c.RUN:
            raise OSError("disk gone")
        real(path, obj, **kw)

    monkeypatch.setattr(write, "write_replaced", crash)
    with pytest.raises(OSError):
        import_csv(logdir, "train.csv")
    assert not list(logdir.rglob(c.RUN))

    monkeypatch.setattr(write, "write_replaced", real)
    d = import_csv(logdir, "train.csv")
    assert (d / c.RUN).exists()
    assert len(list(logdir.rglob(c.RUN))) == 1


def test_source_id_tells_runs_of_one_path_apart(logdir: Path) -> None:
    """Two runs of one original with different source ids are both written."""
    (imported,) = csv_source.runs(FIXTURES / "train.csv")
    origin = {"kind": "csv", "path": "/x/db"}
    imported.source_id = "a"
    first = write_run(logdir, "imported/x", imported, origin)
    imported.source_id = "b"
    second = write_run(logdir, "imported/x", imported, origin)
    assert first != second
    assert read_json(first / c.RUN)["imported_from"]["id"] == "a"


def test_attempt_carries_source_host(logdir: Path) -> None:
    """The first attempt names the host the source ran on, like an SDK run."""
    (imported,) = csv_source.runs(FIXTURES / "train.csv")
    imported.host = {"hostname": "node07"}
    d = write_run(logdir, "imported/x", imported, {"kind": "csv", "path": "/x/a.csv"})
    assert read_json(d / c.RUN)["attempts"][0]["host"] == "node07"


def test_detect_csv(tmp_path: Path) -> None:
    """A CSV file is one run; a folder counts its CSV files."""
    assert importers.detect(FIXTURES / "train.csv") == importers.Found(
        kind="csv", path=FIXTURES / "train.csv", n=1, label="1 CSV run"
    )
    found = importers.detect(FIXTURES)
    assert (found.kind, found.n) == ("csv", 3)
    assert importers.detect(tmp_path) is None


def touch(root: Path, *names: str) -> None:
    """Create empty files, and the folders around them.

    :param root: The folder they go below.
    :param names: Paths relative to ``root``."""
    for name in names:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).touch()


def test_detect_every_kind(tmp_path: Path) -> None:
    """Each kind is recognized by its file names alone."""
    touch(tmp_path / "tb", "v0/events.out.tfevents.1.host", "v1/events.out.tfevents.2.host")
    touch(tmp_path / "wb", "offline-run-20260101_000000-abc/run-abc.wandb")
    touch(tmp_path / "ml", "mlruns/0/r1/meta.yaml", "mlruns/0/meta.yaml")
    (tmp_path / "ml" / "mlruns" / "0" / "r1" / "metrics").mkdir()
    touch(tmp_path / "db", "mlflow.db")
    touch(tmp_path / "bt", "g/r1/_run.json", "g/r2/_run.json", "g/r1/_metrics.jsonl")
    found = {p: importers.detect(tmp_path / p) for p in ("tb", "wb", "ml", "db", "bt")}
    assert [(f.kind, f.n) for f in found.values()] == [
        ("tensorboard", 2),
        ("wandb", 1),
        ("mlflow", 1),
        ("mlflow", 1),
        ("beamtime", 2),
    ]
    assert found["tb"].label == "2 TensorBoard runs"
    assert found["wb"].label == "1 W&B offline run"


def test_detect_skips_environments(tmp_path: Path) -> None:
    """Folders such as ``.venv`` are not searched."""
    touch(tmp_path, ".venv/lib/data.csv", "node_modules/x/events.out.tfevents.1")
    assert importers.detect(tmp_path) is None
    shutil.copy(FIXTURES / "train.csv", tmp_path / "train.csv")
    assert importers.detect(tmp_path).n == 1


MLRUNS = Path(__file__).parent / "fixtures" / "mlruns"


def mlflow_db(path: Path) -> Path:
    """Build an ``mlflow.db`` holding the experiments and runs of the file store fixture.

    :param path: The folder the database goes into.
    :return: The database file."""
    t = 1700000000000
    db = path / "mlflow.db"
    con = sqlite3.connect(db)
    con.executescript(
        """
        CREATE TABLE experiments (experiment_id INTEGER, name TEXT, lifecycle_stage TEXT);
        CREATE TABLE runs (run_uuid TEXT, name TEXT, experiment_id INTEGER, status TEXT,
            start_time INTEGER, end_time INTEGER, lifecycle_stage TEXT);
        CREATE TABLE params (key TEXT, value TEXT, run_uuid TEXT);
        CREATE TABLE tags (key TEXT, value TEXT, run_uuid TEXT);
        CREATE TABLE metrics (key TEXT, value REAL, timestamp INTEGER, run_uuid TEXT,
            step INTEGER, is_nan INTEGER);
        """
    )
    con.executemany(
        "INSERT INTO experiments VALUES (?, ?, ?)",
        [(0, "Default", "active"), (1, "scaling", "active"), (2, "old", "deleted")],
    )
    con.executemany(
        "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            ("r1", "baseline", 1, "FINISHED", t, t + 60000, "active"),
            ("r2", "wide", 1, "FAILED", t + 100000, t + 160000, "active"),
            ("r3", None, 1, "KILLED", t + 200000, t + 230000, "active"),
            ("r4", "removed", 1, "FINISHED", t + 400000, t + 460000, "deleted"),
            ("r5", "in an old experiment", 2, "FINISHED", t, t + 1000, "active"),
        ],
    )
    con.executemany(
        "INSERT INTO params VALUES (?, ?, ?)",
        [("lr", "0.001", "r1"), ("optimizer", "adam", "r1"), ("lr", "0.01", "r2")],
    )
    con.executemany(
        "INSERT INTO tags VALUES (?, ?, ?)",
        [
            ("mlflow.source.git.commit", "9e41c2a7d3b0", "r1"),
            ("mlflow.runName", "huge", "r3"),
        ],
    )
    con.executemany(
        "INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("loss", 2.5, t + 1000, "r1", 0, 0),
            ("loss", 1.5, t + 2000, "r1", 1, 0),
            ("loss", 1.0, t + 3000, "r1", 2, 0),
            ("acc", 0.5, t + 2000, "r1", 1, 0),
            ("loss", 3.0, t + 101000, "r2", 0, 0),
            ("loss", 0.0, t + 102000, "r2", 1, 1),
        ],
    )
    con.commit()
    con.close()
    return db


def by_name(path: Path) -> dict[str, Imported]:
    """Read the MLflow runs at a path.

    :param path: A file store or a database.
    :return: The runs by name."""
    return {r.name: r for r in mlflow_source.runs(path)}


def test_mlflow_file_store() -> None:
    """The file store imports params as config, metrics with steps, status, git and group."""
    runs = by_name(MLRUNS)
    assert list(runs) == ["baseline", "wide", "big", "duplicate"]
    base = runs["baseline"]
    assert base.group == "scaling"
    assert base.status == "finished"
    assert base.config == {"lr": 0.001, "optimizer": "adam", "layers": 4, "amp": True}
    assert base.git == {"commit": "9e41c2a7d3b0"}
    assert (base.created_at, base.ended_at) == (1700000000.0, 1700000060.0)
    assert base.source_id == "a1f3c5e7b9d14f60a2c8e0b4d6f81357"
    assert [(r["_step"], r.get("loss"), r.get("val/loss")) for r in base.rows] == [
        (0, 2.5, None),
        (1, 1.5, 1.8),
        (2, 1.0, None),
    ]
    assert base.rows[1]["_t"] == 1700000002.0
    assert (runs["wide"].status, runs["big"].status) == ("failed", "killed")
    assert runs["wide"].git is None
    assert math.isnan(runs["wide"].rows[1]["loss"])


def test_mlflow_sqlite_store(tmp_path: Path) -> None:
    """The SQLite store imports the same fields, and the run name falls back to the tag."""
    runs = by_name(mlflow_db(tmp_path))
    assert list(runs) == ["baseline", "wide", "huge"]
    base = runs["baseline"]
    assert (base.group, base.status, base.source_id) == ("scaling", "finished", "r1")
    assert base.config == {"lr": 0.001, "optimizer": "adam"}
    assert base.git == {"commit": "9e41c2a7d3b0"}
    assert [(r["_step"], r["loss"], r.get("acc")) for r in base.rows] == [
        (0, 2.5, None),
        (1, 1.5, 0.5),
        (2, 1.0, None),
    ]
    assert (runs["wide"].status, runs["huge"].status) == ("failed", "killed")
    assert math.isnan(runs["wide"].rows[1]["loss"])


def test_mlflow_duplicate_step(logdir: Path) -> None:
    """A metric logged twice at one step keeps both lines in order."""
    dup = by_name(MLRUNS)["duplicate"]
    assert [(r["_step"], r["loss"], r.get("acc")) for r in dup.rows] == [
        (0, 2.0, None),
        (1, 1.0, 0.4),
        (1, 0.5, None),
    ]
    d = write_run(logdir, "imported/scaling", dup, {"kind": "mlflow", "path": str(MLRUNS)})
    lines = (d / c.METRICS).read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["loss"] for line in lines] == [2.0, 1.0, 0.5]


def test_mlflow_deleted(tmp_path: Path) -> None:
    """Deleted runs and runs of deleted experiments are skipped, in both stores and in the count."""
    assert "removed" not in by_name(MLRUNS)
    assert "in an old experiment" not in by_name(MLRUNS)
    db = by_name(mlflow_db(tmp_path))
    assert "removed" not in db and "in an old experiment" not in db
    assert mlflow_source.detect(MLRUNS).n == 4
    assert mlflow_source.detect(tmp_path / "mlflow.db").n == 3


def test_mlflow_trash(tmp_path: Path) -> None:
    """Experiments in ``.trash`` are not read."""
    shutil.copytree(MLRUNS, tmp_path / "mlruns")
    shutil.copytree(tmp_path / "mlruns" / "1", tmp_path / "mlruns" / ".trash" / "9")
    assert len(list(mlflow_source.runs(tmp_path / "mlruns"))) == 4


def test_mlflow_import_groups_by_experiment(logdir: Path) -> None:
    """Runs written below ``imported/<experiment>`` answer ``runs`` like any run."""
    for imported in mlflow_source.runs(MLRUNS):
        write_run(
            logdir,
            f"imported/{imported.group}",
            imported,
            {"kind": "mlflow", "path": str(MLRUNS)},
        )
    rows = query.run({"runs": {"from": "imported/scaling"}}, logdir=logdir)["rows"]
    assert sorted((r[1], r[2]) for r in rows) == [
        ("baseline", "finished"),
        ("big", "killed"),
        ("duplicate", "finished"),
        ("wide", "failed"),
    ]


def varint(n: int) -> bytes:
    """Encode a protobuf varint.

    :param n: A non-negative integer.
    :return: The bytes."""
    out = bytearray()
    while n > 0x7F:
        out.append(n & 0x7F | 0x80)
        n >>= 7
    return bytes(out + bytes([n]))


def field(number: int, wire: int, payload: bytes) -> bytes:
    """Encode one protobuf field.

    :param number: The field number.
    :param wire: The wire type, 0, 1, 2 or 5.
    :param payload: The value's bytes, a length-delimited payload without its length.
    :return: The bytes."""
    key = varint(number << 3 | wire)
    return key + (varint(len(payload)) + payload if wire == 2 else payload)


def tag_value(tag: str, *rest: bytes) -> bytes:
    """Encode a ``Summary.Value``.

    :param tag: The tag.
    :param rest: Further encoded fields.
    :return: The bytes."""
    return field(1, 2, tag.encode()) + b"".join(rest)


def simple(tag: str, value: float) -> bytes:
    """Encode a scalar in the old ``simple_value`` style.

    :param tag: The tag.
    :param value: The value.
    :return: The ``Summary.Value`` bytes."""
    return tag_value(tag, field(2, 5, struct.pack("<f", value)))


def tensor(tag: str, plugin: str, *proto: bytes) -> bytes:
    """Encode a ``Summary.Value`` that carries a ``TensorProto``.

    :param tag: The tag.
    :param plugin: The plugin name in the summary's metadata.
    :param proto: The ``TensorProto``'s encoded fields.
    :return: The bytes."""
    metadata = field(1, 2, field(1, 2, plugin.encode()))
    return tag_value(tag, field(8, 2, b"".join(proto)), field(9, 2, metadata))


def event(wall: float, step: int, *values: bytes) -> bytes:
    """Encode an ``Event`` with a summary.

    :param wall: The wall time.
    :param step: The step.
    :param values: Encoded ``Summary.Value`` messages.
    :return: The bytes."""
    summary = field(5, 2, b"".join(field(1, 2, v) for v in values)) if values else b""
    return field(1, 1, struct.pack("<d", wall)) + field(2, 0, varint(step)) + summary


def write_events(path: Path, *events: bytes) -> Path:
    """Write an event file; the checksums are zeros, as the reader ignores them.

    :param path: The file.
    :param events: Encoded events.
    :return: The file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(struct.pack("<QI", len(e), 0) + e + b"\0\0\0\0" for e in events))
    return path


def float_tensor(dtype: int, *dims: int) -> list[bytes]:
    """Encode the dtype and shape of a ``TensorProto``.

    :param dtype: The ``DataType`` number, 1 for float32 and 2 for float64.
    :param dims: The shape; none for a scalar.
    :return: The encoded fields."""
    shape = b"".join(field(2, 2, field(1, 0, varint(d))) for d in dims)
    return [field(1, 0, varint(dtype)), field(2, 2, shape)]


def start(wall: float) -> bytes:
    """Encode the ``file_version`` event every event file begins with.

    :param wall: The wall time.
    :return: The bytes."""
    return field(1, 1, struct.pack("<d", wall)) + field(3, 2, b"brain.Event:2")


def only(path: Path) -> Imported:
    """Read the one run at a path.

    :param path: An event file or a folder.
    :return: The run."""
    (imported,) = tb_source.runs(path)
    return imported


def test_tb_scalars(tmp_path: Path) -> None:
    """Scalars as ``simple_value`` and as float32 and float64 tensors import with step and time."""
    f32 = field(5, 2, struct.pack("<f", 0.5))
    f64 = field(4, 2, struct.pack("<d", 0.25))
    write_events(
        tmp_path / "events.out.tfevents.1700000000.host",
        start(1700000000.0),
        event(
            1700000001.0, 0, simple("loss", 2.5), tensor("f32", "scalars", *float_tensor(1), f32)
        ),
        event(
            1700000002.0, 1, simple("loss", 1.5), tensor("f64", "scalars", *float_tensor(2), f64)
        ),
        event(1700000003.0, 2, simple("loss", 1.0)),
    )
    run = only(tmp_path)
    assert (run.created_at, run.ended_at, run.status) == (1700000000.0, 1700000003.0, "finished")
    assert [(r["_step"], r["_t"], r.get("loss"), r.get("f32"), r.get("f64")) for r in run.rows] == [
        (0, 1700000001.0, 2.5, 0.5, None),
        (1, 1700000002.0, 1.5, None, 0.25),
        (2, 1700000003.0, 1.0, None, None),
    ]
    assert run.skipped == {}


def test_tb_hparams(tmp_path: Path) -> None:
    """``hparams.yaml`` beside the events is the config; an unreadable one is no config."""
    write_events(tmp_path / "events.out.tfevents.1", event(1.0, 0, simple("loss", 1.0)))
    (tmp_path / "hparams.yaml").write_text("lr: 0.001\nlayers: 4\nname: mlp\n", encoding="utf-8")
    assert only(tmp_path).config == {"lr": 0.001, "layers": 4, "name": "mlp"}
    (tmp_path / "hparams.yaml").write_text("{unclosed", encoding="utf-8")
    assert only(tmp_path).config == {}


def test_tb_lightning_versions(logdir: Path, tmp_path: Path) -> None:
    """Each ``version_<n>`` folder is a run under ``imported/<name>/version_<n>``."""
    root = tmp_path / "lightning_logs"
    for n in range(2):
        write_events(
            root / f"version_{n}" / "events.out.tfevents.1",
            start(1700000000.0 + n),
            event(1700000010.0 + n, 0, simple("train_loss", 1.0 + n)),
        )
        (root / f"version_{n}" / "hparams.yaml").write_text(f"seed: {n}\n", encoding="utf-8")
    assert tb_source.detect(root).n == 2
    found = list(tb_source.runs(root))
    assert [(r.name, r.group, r.config) for r in found] == [
        ("version_0", "version_0", {"seed": 0}),
        ("version_1", "version_1", {"seed": 1}),
    ]
    for r in found:
        write_run(
            logdir,
            f"imported/lightning_logs/{r.group}",
            r,
            {"kind": "tensorboard", "path": str(root.resolve())},
        )
    rows = query.run({"runs": {"from": "imported/lightning_logs"}}, logdir=logdir)["rows"]
    assert sorted(r[1] for r in rows) == ["version_0", "version_1"]
    series = query.run(
        {"series": {"from": "imported/lightning_logs/version_1", "y": ["train_loss"]}},
        logdir=logdir,
    )
    assert series["curves"][0]["y"] == [2.0]


def test_tb_nested_group(tmp_path: Path) -> None:
    """A run below deeper folders keeps them as its group."""
    write_events(tmp_path / "exp" / "a" / "events.out.tfevents.1", event(1.0, 0, simple("x", 1.0)))
    run = only(tmp_path)
    assert (run.name, run.group, run.source_id) == ("a", "exp/a", "exp/a")


def test_tb_non_scalar_counted(tmp_path: Path) -> None:
    """Images, histograms, text and array tensors are left out, counted by kind and tag."""
    write_events(
        tmp_path / "events.out.tfevents.1",
        event(
            1.0,
            0,
            simple("loss", 1.0),
            tag_value("img/a", field(4, 2, b"png")),
            tag_value("hist/old", field(5, 2, b"")),
            tensor("img/b", "images", *float_tensor(1, 3)),
            tensor("txt", "text", field(1, 0, varint(7))),
            tensor("vec", "scalars", *float_tensor(1, 4)),
            tensor("plain", "", *float_tensor(1, 2)),
        ),
        event(
            2.0,
            1,
            simple("loss", 0.5),
            tag_value("img/a", field(4, 2, b"png")),
            tensor("hist/new", "histograms", *float_tensor(1, 30, 3)),
        ),
    )
    run = only(tmp_path)
    assert run.skipped == {
        "histograms": 2,
        "images": 2,
        "scalars": 1,
        "tensors": 1,
        "text": 1,
    }
    assert [r["loss"] for r in run.rows] == [1.0, 0.5]


def test_tb_truncated(tmp_path: Path) -> None:
    """A truncated last record ends the stream quietly; the points before it are kept."""
    f = write_events(
        tmp_path / "events.out.tfevents.1",
        start(1.0),
        event(2.0, 0, simple("loss", 1.0)),
        event(3.0, 1, simple("loss", 0.5)),
    )
    data = f.read_bytes()
    for cut in (1, 3, 8):
        f.write_bytes(data[:-cut])
        assert [r["loss"] for r in only(tmp_path).rows] == [1.0]
    f.write_bytes(data[:5])
    assert only(tmp_path).rows == []


def test_tb_wrong_wire_type(tmp_path: Path) -> None:
    """A record whose fields carry the wrong wire type is skipped, as checksums are not checked."""
    write_events(
        tmp_path / "events.out.tfevents.1",
        field(1, 0, varint(5)),
        field(5, 0, varint(5)),
        field(5, 2, field(1, 0, varint(5))),
        event(2.0, 0, simple("loss", 1.0)),
    )
    assert [r["loss"] for r in only(tmp_path).rows] == [1.0]


def test_tb_multiple_files(tmp_path: Path) -> None:
    """Several event files in one folder merge by step, and a repeated step keeps both points."""
    write_events(
        tmp_path / "events.out.tfevents.1",
        event(1.0, 0, simple("loss", 2.0)),
        event(2.0, 1, simple("loss", 1.0)),
    )
    write_events(
        tmp_path / "events.out.tfevents.2",
        event(3.0, 1, simple("acc", 0.25)),
        event(4.0, 2, simple("loss", 0.5), simple("acc", 0.75)),
        event(5.0, 1, simple("loss", 0.125)),
    )
    run = only(tmp_path)
    assert [(r["_step"], r.get("loss"), r.get("acc")) for r in run.rows] == [
        (0, 2.0, None),
        (1, 1.0, 0.25),
        (1, 0.125, None),
        (2, 0.5, 0.75),
    ]
    assert (run.created_at, run.ended_at) == (1.0, 5.0)


def test_tb_detect(tmp_path: Path) -> None:
    """``detect`` counts the folders with event files and ignores environments."""
    assert tb_source.detect(tmp_path) is None
    for name in ("a", "b", ".venv/c"):
        write_events(tmp_path / name / "events.out.tfevents.1", start(1.0))
    write_events(tmp_path / "a" / "events.out.tfevents.2", start(2.0))
    found = tb_source.detect(tmp_path)
    assert (found.kind, found.n, found.label) == ("tensorboard", 2, "2 TensorBoard runs")
    assert importers.detect(tmp_path).kind == "tensorboard"


def test_tb_negative_step_and_no_events(tmp_path: Path) -> None:
    """A step stored as a two's-complement varint reads as negative; an empty file is a run with no rows."""
    write_events(tmp_path / "events.out.tfevents.1", event(1.0, (1 << 64) - 1, simple("x", 1.0)))
    assert only(tmp_path).rows[0]["_step"] == -1
    (tmp_path / "events.out.tfevents.1").write_bytes(b"")
    run = only(tmp_path)
    assert run.rows == [] and run.created_at > 0


WANDB = Path(__file__).parent / "fixtures" / "wandb"


def fake_reader(monkeypatch: pytest.MonkeyPatch, *records: dict) -> None:
    """Stand in for the ``wandb`` package's datastore reader.

    :param monkeypatch: The patcher.
    :param records: The history records every ``.wandb`` file yields."""
    monkeypatch.setattr(wandb_source, "reader", lambda: lambda path: iter(records))


def wandb_runs() -> dict[str, Imported]:
    """Read the W&B fixtures.

    :return: The runs by source id."""
    return {r.source_id: r for r in wandb_source.runs(WANDB)}


def test_wandb_without_package(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without the package, config, metadata and the summary import as a one-step run."""
    monkeypatch.setattr(wandb_source, "reader", lambda: None)
    found = importers.detect(WANDB)
    assert (found.kind, found.n, found.label) == ("wandb", 2, "2 W&B offline runs")
    assert found.note == "history needs the wandb package"
    run = wandb_runs()["a1b2c3d4"]
    assert run.config == {"lr": 0.001, "model": "mlp", "layers": [64, 64]}
    assert run.host == {"hostname": "node042", "os": "Linux-5.15.0-x86_64", "python": "3.11.9"}
    assert run.git == {"remote": "git@example.org:lab/mlp.git", "commit": "9f2c1ab"}
    assert run.command == ["/usr/bin/python3", "train.py", "--lr", "0.001"]
    assert run.rows == [{"_step": 0, "_t": 1767608142.5, "loss": 0.21, "acc": 0.93}]
    assert run.skipped == {"image-file": 1}
    assert (run.created_at, run.ended_at, run.status) == (1767608100.0, 1767608142.5, "finished")


def test_wandb_history_through_the_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    """With a reader, the history rows replace the summary row; media and text are left out."""
    fake_reader(
        monkeypatch,
        {"_step": 0, "_timestamp": 1767608110.0, "loss": 1.0, "_runtime": 10, "tag": "x"},
        {"_step": 1, "_timestamp": 1767608120.0, "loss": 0.5, "ok": True},
        {"loss": 0.25, "img": {"_type": "image-file"}},
    )
    assert importers.detect(WANDB).note == ""
    run = wandb_runs()["a1b2c3d4"]
    assert run.rows == [
        {"_step": 0, "_t": 1767608110.0, "loss": 1.0},
        {"_step": 1, "_t": 1767608120.0, "loss": 0.5},
        {"_step": 2, "_t": run.created_at, "loss": 0.25},
    ]
    assert run.skipped == {"image-file": 1}


def test_wandb_status_from_exit_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """A non-zero exit code is a failed run; the summary's wins over the metadata's."""
    monkeypatch.setattr(wandb_source, "reader", lambda: None)
    runs = wandb_runs()
    assert (runs["a1b2c3d4"].status, runs["e5f6a7b8"].status) == ("finished", "failed")
    assert wandb_source.status_of({"exitcode": 1}, {"exit_code": 0}) == "finished"
    assert wandb_source.status_of({}, {}) == "finished"


def test_wandb_sparse_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """A run with little metadata still imports: times from the summary, no host, git or command."""
    monkeypatch.setattr(wandb_source, "reader", lambda: None)
    run = wandb_runs()["e5f6a7b8"]
    assert run.config == {"lr": 0.1}
    assert (run.git, run.command) == (None, ["train.py"])
    assert (run.created_at, run.ended_at) == (1767686400.0, 1767686403.0)
    assert run.host == {"hostname": "node007"}


def test_wandb_import_reads_like_a_run(logdir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An imported W&B run is an ordinary run with provenance, and a rerun adds nothing."""
    monkeypatch.setattr(wandb_source, "reader", lambda: None)
    for _ in range(2):
        for imported in wandb_source.runs(WANDB):
            write_run(
                logdir, "imported/wandb", imported, {"kind": "wandb", "path": str(WANDB.resolve())}
            )
    folders = list((logdir / "imported" / "wandb").iterdir())
    assert len(folders) == 2
    origins = {read_json(d / c.RUN)["imported_from"]["id"]: d for d in folders}
    assert read_run_info(origins["e5f6a7b8"]).status == "failed"
    assert read_json(origins["a1b2c3d4"] / c.RUN)["imported_from"]["kind"] == "wandb"


def test_wandb_history_without_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A folder without files/ still imports from the history alone."""
    touch(tmp_path, "offline-run-20260101_000000-zz/run-zz.wandb")
    fake_reader(monkeypatch, {"_step": 3, "_timestamp": 5.0, "x": 2.0})
    (run,) = wandb_source.runs(tmp_path)
    assert run.config == {} and run.rows == [{"_step": 3, "_t": 5.0, "x": 2.0}]
    assert run.status == "finished" and run.created_at > 0


def test_wandb_reader_decodes_datastore_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """The reader scans the datastore, keeps history records and joins nested keys."""

    class Item:
        def __init__(self, key: str, value: object, nested: tuple[str, ...] = ()) -> None:
            self.key, self.nested_key, self.value_json = key, list(nested), json.dumps(value)

    class Record:
        def ParseFromString(self, data: tuple[str, list[Item]]) -> None:
            self.kind, self.history = data[0], types.SimpleNamespace(item=data[1])

        def WhichOneof(self, _: str) -> str:
            return self.kind

    class DataStore:
        def open_for_scan(self, path: str) -> None:
            self.left = [("run", []), ("history", [Item("loss", 1.5), Item("", 2, ("a", "b"))])]

        def scan_data(self) -> tuple[str, list[Item]] | None:
            return self.left.pop(0) if self.left else None

    modules = {
        "wandb": types.ModuleType("wandb"),
        "wandb.proto": types.ModuleType("wandb.proto"),
        "wandb.proto.wandb_internal_pb2": types.SimpleNamespace(Record=Record),
        "wandb.sdk": types.ModuleType("wandb.sdk"),
        "wandb.sdk.internal": types.ModuleType("wandb.sdk.internal"),
        "wandb.sdk.internal.datastore": types.SimpleNamespace(DataStore=DataStore),
    }
    modules["wandb.proto"].wandb_internal_pb2 = modules["wandb.proto.wandb_internal_pb2"]
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    read = wandb_source.reader()
    assert list(read(Path("run.wandb"))) == [{"loss": 1.5, "a.b": 2}]


def beamtime_run(group: Path, run_id: str, proposals: dict[str, str] | None = None) -> Path:
    """Write a minimal run folder.

    :param group: The group folder.
    :param run_id: The run id, which is the folder's name.
    :param proposals: The recorded proposal membership, by group path.
    :return: The run folder."""
    d = group / run_id
    d.mkdir(parents=True)
    info = {
        "schema": 1,
        "id": run_id,
        "name": "r",
        "status": "finished",
        "proposals": proposals or {},
        "proposal_hashes": dict.fromkeys(proposals or {}, "0123456789abcdef"),
    }
    (d / c.RUN).write_text(json.dumps(info), encoding="utf-8")
    return d


def normalized(answer: object, prefix: str) -> str:
    """Dump an answer with the import's folder taken off every path.

    Freshness is left out.

    :param answer: An operation's answer.
    :param prefix: The folder the import went into, e.g. ``imported/demo``.
    :return: JSON text."""

    def keep(value: object) -> object:
        if isinstance(value, dict):
            return {k: keep(v) for k, v in value.items() if k != "meta"}
        return [keep(v) for v in value] if isinstance(value, list) else value

    text = json.dumps(keep(answer), sort_keys=True)
    return text.replace(f'"{prefix}/', '"').replace(f'"{prefix}"', '"."')


@pytest.fixture
def imported_synth(
    tmp_path: Path, home: Path, synth: tuple[Path, object]
) -> tuple[Context, Context, Path]:
    """Import the synthetic log dir into an empty project as ``imported/demo``.

    :param tmp_path: The test's temporary directory.
    :param home: The fake home.
    :param synth: The synthetic log dir and its manifest.
    :return: The original's context, the project's context and the project's log dir."""
    logdir, _ = synth
    root = tmp_path / "project"
    (root / "beamtime").mkdir(parents=True)
    copied = copy_logdir(root / "beamtime", logdir, "demo")
    assert copied.skipped == 0 and copied.runs > 0
    return Context.make(root=logdir.parent), Context.make(root=root), root / "beamtime"


def test_import_answers_like_the_original(
    imported_synth: tuple[Context, Context, Path],
) -> None:
    """Groups, checks, notes and memory of the copy match the original's, ids included."""
    original, project, _ = imported_synth
    for name, here, there in (
        ("groups", {"from": "."}, {"from": "imported/demo"}),
        ("notes", {"from": "."}, {"from": "imported/demo"}),
        ("check", {"group": "scaling/lr-sweep"}, {"group": "imported/demo/scaling/lr-sweep"}),
        (
            "check",
            {"group": "tokenizer/bpe-vs-unigram"},
            {"group": "imported/demo/tokenizer/bpe-vs-unigram"},
        ),
        ("memory show", {"group": "scaling/lr-sweep"}, {"group": "imported/demo/scaling/lr-sweep"}),
    ):
        a, b = call(name, here, original), call(name, there, project)
        a, b = normalized(a, "imported/demo"), normalized(b, "imported/demo")
        assert a == b, name


def test_import_keeps_ids_and_records_provenance(
    synth: tuple[Path, object], imported_synth: tuple[Context, Context, Path]
) -> None:
    """Run ids stay; ``_run.json`` gains ``imported_from`` and prefixed membership."""
    logdir, _ = synth
    *_, dest = imported_synth
    for run in iter_runs(logdir):
        (copy,) = (dest / "imported" / "demo").rglob(run.name)
        original, copied = read_json(run / c.RUN), read_json(copy / c.RUN)
        assert copied["id"] == run.name
        assert copied["imported_from"]["kind"] == "beamtime"
        assert (copied["imported_from"]["path"], copied["imported_from"]["id"]) == (
            str(run.resolve()),
            run.name,
        )
        assert {k.removeprefix("imported/demo/") for k in copied["proposals"]} == set(
            original["proposals"]
        )
        assert (copy / c.RUN).stat().st_mtime == (run / c.RUN).stat().st_mtime
        original.pop("proposals"), copied.pop("proposals")
        original.pop("proposal_hashes"), copied.pop("proposal_hashes")
        copied.pop("imported_from")
        assert copied == original


def test_import_records_one_move_per_group(
    synth: tuple[Path, object], imported_synth: tuple[Context, Context, Path]
) -> None:
    """Each top-level group gets a move scoped to the import; a native group is untouched."""
    logdir, _ = synth
    *_, dest = imported_synth
    groups = sorted(d.name for d in logdir.iterdir() if d.is_dir() and not d.name.startswith("_"))
    groups.remove("memory")
    recorded = moves.read(dest)
    assert [(m.old, m.new, m.within) for m in recorded] == [
        (g, f"imported/demo/{g}", "imported/demo") for g in groups
    ]
    assert (
        moves.current(dest, "scaling", "imported/demo/scaling/lr-sweep") == "imported/demo/scaling"
    )
    assert moves.current(dest, "scaling", "scaling/lr-sweep") == "scaling"
    assert moves.current(dest, "scaling", None) == "scaling"


def test_import_leaves_a_native_group_alone(
    imported_synth: tuple[Context, Context, Path], synth: tuple[Path, object]
) -> None:
    """A native group of the same name keeps its own answers after the import."""
    _, project, dest = imported_synth
    logdir, _ = synth
    native = dest / "scaling" / "native"
    beamtime_run(native, "20260101-000000-aaaaaaaa")
    answer = call("groups", {"from": "scaling"}, project)
    assert [r[0] for r in answer["rows"]] == ["scaling", "scaling/native"]
    assert not any(r[0].startswith("imported") for r in answer["rows"])
    assert {p.name for p in (dest / "imported" / "demo").iterdir()} >= {"scaling", "tokenizer"}
    assert (logdir / "scaling").is_dir()


def test_import_skips_known_ids(tmp_path: Path) -> None:
    """A second import copies nothing; a run id found anywhere in the log dir is skipped."""
    src, dest = tmp_path / "src", tmp_path / "beamtime"
    beamtime_run(src / "a", "20260101-000000-aaaaaaaa")
    beamtime_run(src / "a", "20260101-000001-bbbbbbbb")
    beamtime_run(dest / "elsewhere", "20260101-000001-bbbbbbbb")
    assert copy_logdir(dest, src, "demo") == Copied(runs=1, skipped=1)
    assert copy_logdir(dest, src, "demo") == Copied(runs=0, skipped=2)
    beamtime_run(src / "a", "20260101-000002-cccccccc")
    assert copy_logdir(dest, src, "demo") == Copied(runs=1, skipped=2)
    assert len(moves.read(dest)) == 1


def test_import_carries_moves(tmp_path: Path) -> None:
    """The source's own moves are appended with prefixed paths and the import's scope."""
    src, dest = tmp_path / "src", tmp_path / "beamtime"
    beamtime_run(src / "b", "20260101-000000-aaaaaaaa", {"a": "20260101-000000-p1p1"})
    moves.record(src, "a", "b")
    copy_logdir(dest, src, "demo")
    assert [(m.old, m.new, m.within) for m in moves.read(dest)] == [
        ("b", "imported/demo/b", "imported/demo"),
        ("a", "imported/demo/a", "imported/demo"),
        ("imported/demo/a", "imported/demo/b", "imported/demo"),
    ]
    named_in = "imported/demo/b"
    assert moves.current(dest, "a/x", named_in) == "imported/demo/b/x"
    assert moves.current(dest, "a/x", "a") == "a/x"
    run = read_json(next((dest / "imported" / "demo").rglob(c.RUN)))
    assert run["proposals"] == {"imported/demo/a": "20260101-000000-p1p1"}


def test_import_library_blocks(tmp_path: Path, home: Path) -> None:
    """Blocks at the source root are found by views of the imported groups, pinned versions too."""
    src, dest = tmp_path / "src", tmp_path / "project" / "beamtime"
    dest.mkdir(parents=True)
    beamtime_run(src / "a", "20260101-000000-aaaaaaaa")
    block = src / "blocks" / "pm"
    block.mkdir(parents=True)
    (block / "20260101-000000-b1b1.yaml").write_text(
        "schema: 1\nname: pm\ndescription: d\ncode: code/pm.js\n"
    , encoding="utf-8")
    copy_logdir(dest, src, "demo")
    ctx = Context.make(root=dest.parent)
    found = Library(ctx=ctx, path="imported/demo/a").get("pm", "20260101-000000-b1b1")
    assert (found.group, found.version) == ("imported/demo", "20260101-000000-b1b1")
    assert Library(ctx=ctx, path="a").names == []


def test_import_skips_machine_files_and_trash(tmp_path: Path) -> None:
    """Trash, the index folder and machine-written files at group level are left behind."""
    src, dest = tmp_path / "src", tmp_path / "beamtime"
    beamtime_run(src / "a", "20260101-000000-aaaaaaaa")
    beamtime_run(src / "_trash" / "20260101-000000" / "b", "20260101-000001-bbbbbbbb")
    (src / ".beamtime").mkdir()
    (src / ".beamtime" / "x").write_text("x", encoding="utf-8")
    (src / "_moves.jsonl").write_text("", encoding="utf-8")
    notes = src / "a" / "notes"
    notes.mkdir()
    (notes / "20260101-000000-n1n1.md").write_text("---\ntype: observation\n---\nbody\n", encoding="utf-8")
    assert copy_logdir(dest, src, "demo") == Copied(runs=1, skipped=0)
    names = {
        p.relative_to(dest / "imported" / "demo").as_posix()
        for p in (dest / "imported" / "demo").rglob("*")
    }
    assert "a/notes/20260101-000000-n1n1.md" in names
    assert not any(n.startswith(("_trash", ".beamtime", "_moves")) for n in names)


def test_import_a_single_run(tmp_path: Path) -> None:
    """A path that is one run copies that run."""
    src, dest = tmp_path / "src", tmp_path / "beamtime"
    run = beamtime_run(src, "20260101-000000-aaaaaaaa")
    assert copy_logdir(dest, run, "one") == Copied(runs=1, skipped=0)
    assert (dest / "imported" / "one" / run.name / c.RUN).is_file()


def test_import_citations_stay_apart(imported_synth: tuple[Context, Context, Path]) -> None:
    """A copied note's citation reaches the imported group; a native note's stays with its path."""
    _, project, dest = imported_synth
    notes = dest / "scaling" / c.NOTES
    notes.mkdir(parents=True)
    (notes / "20990101-000000-n1n1.md").write_text(
        "---\nschema: 1\ntype: observation\ndescription: native\n---\n"
        "See [[scaling/lr-sweep#converges]].\n"
    , encoding="utf-8")
    answer = call("check", {"group": "imported/demo/scaling/lr-sweep"}, project)
    (converges,) = [p for p in answer["predictions"] if p["name"] == "converges"]
    assert converges["cited_by"]
    assert "native" not in [n["description"] for n in converges["cited_by"]]


def test_notes_come_in_as_observations_on_the_log_dir(
    home: Path, logdir: Path, tmp_path: Path
) -> None:
    """Each text file is one observation note: the first heading or the file name describes it.

    :param home: The throwaway home.
    :param logdir: The log dir.
    :param tmp_path: The test's temporary directory."""
    src = tmp_path / "notes"
    src.mkdir()
    (src / "a.md").write_text("intro\n\n## Learning rate sweep\n\nlr 3e-4 wins.\n", encoding="utf-8")
    (src / "b.md").write_text("no heading here\n", encoding="utf-8")
    (src / "blob.bin").write_bytes(b"\x00\x01\x02")
    ctx = Context.make(root=logdir.parent)

    done = notes_source.import_notes(ctx, [src])

    assert len(done.notes) == 2
    assert done.skipped == [src / "blob.bin"]
    listed = call("notes", {"from": "."}, ctx)
    rows = {n["description"]: n for n in listed["entries"]}
    assert set(rows) == {"Learning rate sweep", "b.md"}
    assert {n["type"] for n in rows.values()} == {"observation"}
    text = (logdir / done.notes[0]).read_text(encoding="utf-8")
    assert "lr 3e-4 wins." in text and "author:" in text and "user:" in text


def test_notes_take_a_single_file(home: Path, logdir: Path, tmp_path: Path) -> None:
    """A path that is a file is one note.

    :param home: The throwaway home.
    :param logdir: The log dir.
    :param tmp_path: The test's temporary directory."""
    f = tmp_path / "NOTES.md"
    f.write_text("# Journal\n\nfirst\n", encoding="utf-8")
    done = notes_source.import_notes(Context.make(root=logdir.parent), [f])
    assert len(done.notes) == 1 and not done.skipped
