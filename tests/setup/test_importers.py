"""The importer interface, the run writer and the CSV, MLflow and TensorBoard sources."""

import json
import math
import shutil
import sqlite3
import struct
from pathlib import Path

import pytest

from beamtime import query
from beamtime.format import constants as c
from beamtime.format.io import read_json
from beamtime.format.run import read_effective_metrics, read_run_info
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.setup import importers
from beamtime.setup.importers import Imported
from beamtime.setup.importers import csv as csv_source
from beamtime.setup.importers import mlflow as mlflow_source
from beamtime.setup.importers import tensorboard as tb_source
from beamtime.setup.importers import write
from beamtime.setup.importers.write import write_run

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
    lines = (d / c.METRICS).read_text().splitlines()
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
    (tmp_path / "hparams.yaml").write_text("lr: 0.001\nlayers: 4\nname: mlp\n")
    assert only(tmp_path).config == {"lr": 0.001, "layers": 4, "name": "mlp"}
    (tmp_path / "hparams.yaml").write_text("{unclosed")
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
        (root / f"version_{n}" / "hparams.yaml").write_text(f"seed: {n}\n")
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
