"""Tests of the benchmark's exporters in ``bench/agents/compare/formats.py``; no agent runs."""

import csv
import json
import math
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from beamtime.format.run import read_effective_metrics
from beamtime.format.tree import iter_runs

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import formats  # noqa: E402
import wide  # noqa: E402

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def made(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, dict[str, str]]:
    """The seed 7 log dir and its plain-files export.

    :param tmp_path_factory: Makes the folders.
    :return: The log dir, the export folder and the manifest's roles."""
    root = tmp_path_factory.mktemp("seed7")
    manifest = data.make_logdir(root, seed=7, now=NOW)
    out = tmp_path_factory.mktemp("files")
    formats.export_files(root / "beamtime", out)
    return root / "beamtime", out, manifest.roles


def read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    """Read an exported CSV.

    :param path: The file.
    :return: The header and the rows."""
    with path.open(newline="") as f:
        header, *rows = csv.reader(f)
    return header, rows


def cell(text: str) -> float | None:
    """Parse a CSV cell back to a number.

    :param text: The cell.
    :return: The value, or ``None`` for an empty cell."""
    return float(text) if text else None


def test_files_layout(made: tuple[Path, Path, dict[str, str]]) -> None:
    """Every run has a folder per group with the three files, named by its folder name."""
    logdir, out, _ = made
    runs = list(iter_runs(logdir))

    assert len(runs) == 61
    for run in runs:
        folder = out / "runs" / run.parent.relative_to(logdir) / run.name
        assert sorted(p.name for p in folder.iterdir()) == [
            "config.json",
            "metrics.csv",
            "output.log",
        ]


def test_files_config_equals_record(made: tuple[Path, Path, dict[str, str]]) -> None:
    """``config.json`` is ``_config.json`` without ``schema``."""
    logdir, out, _ = made
    for run in iter_runs(logdir):
        want = json.loads((run / "_config.json").read_text())
        want.pop("schema")
        got = json.loads(
            (out / "runs" / run.parent.relative_to(logdir) / run.name / "config.json").read_text()
        )
        assert got == want


def test_files_csv_header(made: tuple[Path, Path, dict[str, str]]) -> None:
    """The header is ``step,time`` and the sorted metric keys; no reserved key leaks."""
    logdir, out, _ = made
    for run in iter_runs(logdir):
        header, _ = read_csv(
            out / "runs" / run.parent.relative_to(logdir) / run.name / "metrics.csv"
        )
        assert header[:2] == ["step", "time"]
        assert header[2:] == sorted(header[2:])
        assert not any(k.startswith("_") for k in header)


def test_files_roundtrip(made: tuple[Path, Path, dict[str, str]]) -> None:
    """The CSV holds every logged value of every run, at its step."""
    logdir, out, _ = made
    for run in iter_runs(logdir):
        rows = read_effective_metrics(run)
        header, cells = read_csv(
            out / "runs" / run.parent.relative_to(logdir) / run.name / "metrics.csv"
        )
        assert len(cells) == len(rows)
        for row, line in zip(rows, cells, strict=True):
            assert int(line[0]) == row["_step"]
            assert float(line[1]) == row["_t"]
            for key, text in zip(header[2:], line[2:], strict=True):
                if key in row:
                    assert cell(text) == row[key] or (math.isnan(row[key]) and text == "nan")
                else:
                    assert text == ""


def test_files_nonfinite_roundtrip(made: tuple[Path, Path, dict[str, str]]) -> None:
    """The diverging run's ``nan`` and ``inf`` are in the CSV and parse back with ``float``."""
    logdir, out, roles = made
    run = next(r for r in iter_runs(logdir) if r.name == roles["diverging"].split("/")[-1])
    header, cells = read_csv(
        out / "runs" / run.parent.relative_to(logdir) / run.name / "metrics.csv"
    )
    col = [line[2 + header[2:].index("train/loss")] for line in cells]
    values = [float(t) for t in col if t]

    assert "nan" in col and "inf" in col
    assert any(math.isnan(v) for v in values) and any(math.isinf(v) for v in values)


def test_files_resumed_run_has_one_row_per_step(made: tuple[Path, Path, dict[str, str]]) -> None:
    """The resumed run's discarded attempt tail is gone: its steps are unique."""
    logdir, out, roles = made
    run = next(r for r in iter_runs(logdir) if r.name == roles["resumed"].split("/")[-1])
    _, cells = read_csv(out / "runs" / run.parent.relative_to(logdir) / run.name / "metrics.csv")
    steps = [int(line[0]) for line in cells]
    raw = [json.loads(t)["_step"] for t in (run / "_metrics.jsonl").read_text().splitlines()]

    assert len(raw) > len(set(raw))
    assert steps == sorted(set(steps))


def test_files_sparse_columns(tmp_path: Path) -> None:
    """A key logged every third record keeps its value on its row and is empty elsewhere."""
    rows = [{"_step": i, "_t": 1.0 + i, "a": i * 0.5} for i in range(7)]
    for i in (0, 3, 6):
        rows[i]["b/val"] = float(i)
    formats.write_metrics_csv(tmp_path / "m.csv", rows)
    header, cells = read_csv(tmp_path / "m.csv")

    assert header == ["step", "time", "a", "b/val"]
    assert [line[3] for line in cells] == ["0.0", "", "", "3.0", "", "", "6.0"]
    assert [line[2] for line in cells] == [str(i * 0.5) for i in range(7)]


def test_files_export_runs_status(made: tuple[Path, Path, dict[str, str]]) -> None:
    """``export_runs`` yields every run once with its recorded status and group."""
    logdir, _, _ = made
    runs = list(formats.export_runs(logdir))

    assert len(runs) == 61
    assert len({(r.group, r.id) for r in runs}) == 61
    assert {r.status for r in runs} >= {"finished"}


@pytest.fixture(scope="module")
def tb_made(
    made: tuple[Path, Path, dict[str, str]], tmp_path_factory: pytest.TempPathFactory
) -> Path:
    """The seed 7 log dir exported as TensorBoard event files.

    :param made: The seed 7 log dir.
    :param tmp_path_factory: Makes the folder.
    :return: The export folder."""
    pytest.importorskip("tensorboard")
    logdir, _, _ = made
    out = tmp_path_factory.mktemp("tb")
    assert formats.export_tensorboard(logdir, out) == 61
    return out


def read_events(folder: Path) -> Any:
    """Load a run's event files.

    :param folder: The run's export folder.
    :return: The loaded ``EventAccumulator``."""
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    acc = EventAccumulator(str(folder), size_guidance={"scalars": 0})
    acc.Reload()
    return acc


def test_tensorboard_layout(made: tuple[Path, Path, dict[str, str]], tb_made: Path) -> None:
    """Every run has an event file, ``hparams.yaml`` and ``output.log`` in its group folder."""
    logdir, _, _ = made
    for run in iter_runs(logdir):
        folder = tb_made / "tb" / run.parent.relative_to(logdir) / run.name
        names = sorted(p.name for p in folder.iterdir())
        assert len(names) == 3 and names[0].startswith("events.out.tfevents.")
        assert names[1:] == ["hparams.yaml", "output.log"]


def test_tensorboard_scalars_roundtrip(
    made: tuple[Path, Path, dict[str, str]], tb_made: Path
) -> None:
    """``EventAccumulator`` reads back every logged scalar with its step and wall time."""
    logdir, _, _ = made
    for run in iter_runs(logdir):
        rows = read_effective_metrics(run)
        acc = read_events(tb_made / "tb" / run.parent.relative_to(logdir) / run.name)
        keys = {k for row in rows for k in row if not k.startswith("_")}
        assert set(acc.Tags()["scalars"]) == keys
        for key in keys:
            want = [(r["_step"], r["_t"], r[key]) for r in rows if key in r]
            got = [(e.step, e.wall_time, e.value) for e in acc.Scalars(key)]
            assert len(got) == len(want)
            for (s, t, v), (gs, gt, gv) in zip(want, got, strict=True):
                assert gs == s and gt == t
                assert (math.isnan(v) and math.isnan(gv)) or gv == pytest.approx(
                    v, rel=1e-6, abs=1e-30
                )


def test_tensorboard_nonfinite(made: tuple[Path, Path, dict[str, str]], tb_made: Path) -> None:
    """The diverging run's ``nan`` stays ``nan`` and ``inf`` stays ``inf``."""
    logdir, _, roles = made
    run = next(r for r in iter_runs(logdir) if r.name == roles["diverging"].split("/")[-1])
    acc = read_events(tb_made / "tb" / run.parent.relative_to(logdir) / run.name)
    values = [e.value for e in acc.Scalars("train/loss")]

    assert any(math.isnan(v) for v in values) and any(math.isinf(v) for v in values)


def test_tensorboard_float32_close(made: tuple[Path, Path, dict[str, str]], tb_made: Path) -> None:
    """``simple_value`` is float32: values differ from the record by less than 1e-6 relative."""
    logdir, _, _ = made
    worst = 0.0
    for run in iter_runs(logdir):
        rows = read_effective_metrics(run)
        acc = read_events(tb_made / "tb" / run.parent.relative_to(logdir) / run.name)
        for key in acc.Tags()["scalars"]:
            want = [r[key] for r in rows if key in r]
            for v, e in zip(want, acc.Scalars(key), strict=True):
                if math.isfinite(v) and v != 0:
                    worst = max(worst, abs(e.value - v) / abs(v))

    assert worst < 1e-6


def test_tensorboard_hparams_without_tf(
    made: tuple[Path, Path, dict[str, str]], tb_made: Path
) -> None:
    """The hparams plugin entry is written and read without TensorFlow or PyTorch."""
    from tensorboard.plugins.hparams import plugin_data_pb2

    logdir, _, _ = made
    run = next(iter(iter_runs(logdir)))
    acc = read_events(tb_made / "tb" / run.parent.relative_to(logdir) / run.name)
    content = acc.PluginTagToContent("hparams")["_hparams_/session_start_info"]
    info = plugin_data_pb2.HParamsPluginData.FromString(content).session_start_info

    assert len(info.hparams) > 0
    assert "tensorflow" not in sys.modules and "torch" not in sys.modules


def test_tensorboard_nested_hparams(made: tuple[Path, Path, dict[str, str]], tb_made: Path) -> None:
    """Nested config keys are listed flattened with ``.``; ``hparams.yaml`` keeps them nested."""
    import yaml
    from tensorboard.plugins.hparams import plugin_data_pb2

    logdir, _, _ = made
    checked = 0
    for run in iter_runs(logdir):
        config = json.loads((run / "_config.json").read_text())
        config.pop("schema")
        folder = tb_made / "tb" / run.parent.relative_to(logdir) / run.name
        assert yaml.safe_load((folder / "hparams.yaml").read_text()) == config

        content = read_events(folder).PluginTagToContent("hparams")["_hparams_/session_start_info"]
        info = plugin_data_pb2.HParamsPluginData.FromString(content).session_start_info
        assert set(info.hparams) == set(formats.hparam_values(config))
        checked += any(isinstance(v, dict) for v in config.values())

    assert checked > 0


def test_tensorboard_hparam_values() -> None:
    """Nested dicts are joined with ``.``; lists and ``None`` become JSON text."""
    flat = formats.hparam_values({"a": 1, "b": {"c": 0.5, "d": {"e": "x"}}, "f": [1, 2], "g": None})

    assert flat == {"a": 1, "b.c": 0.5, "b.d.e": "x", "f": "[1, 2]", "g": "null"}


@pytest.fixture(scope="module")
def study(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    """A log dir holding only the study group and the project memory, and its plain-files export.

    :param tmp_path_factory: Makes the folders.
    :return: The log dir and the export folder."""
    logdir = tmp_path_factory.mktemp("study") / "beamtime"
    logdir.mkdir()
    wide.WideGenerator(logdir=logdir, seed=7, now=NOW).study()
    files = tmp_path_factory.mktemp("study-files")
    formats.export_files(logdir, files)
    return logdir, files


def record_files(folder: Path) -> dict[str, bytes]:
    """Read every file in a proposal, notes or memory folder of a tree.

    :param folder: A log dir or the ``record`` folder of an export.
    :return: Path relative to ``folder`` to bytes."""
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file() and p.parent.name in formats.RECORD
    }


def test_record_export_equals_logdir(study: tuple[Path, Path]) -> None:
    """The plain-files export holds the log dir's proposal, notes and memory byte for byte."""
    logdir, files = study
    original = record_files(logdir)

    assert len(original) == 3
    assert record_files(files / "record") == original


def test_record_export_tensorboard(study: tuple[Path, Path], tmp_path: Path) -> None:
    """The TensorBoard export holds the same record files."""
    pytest.importorskip("tensorboard")
    logdir, _ = study
    formats.export_tensorboard(logdir, tmp_path)

    assert record_files(tmp_path / "record") == record_files(logdir)


def test_record_export_skips_runs(study: tuple[Path, Path], tmp_path: Path) -> None:
    """A folder named like record inside a run is not exported."""
    logdir = tmp_path / "beamtime"
    shutil.copytree(study[0], logdir)
    run = next(iter_runs(logdir))
    (run / "notes").mkdir()
    (run / "notes" / "stray.md").write_text("not record\n")
    formats.export_record(logdir, tmp_path / "out")

    assert not list((tmp_path / "out").rglob("stray.md"))
    assert not (tmp_path / "out" / "record" / "study" / "optimizer" / run.name).exists()


def test_s_has_no_record(made: tuple[Path, Path, dict[str, str]]) -> None:
    """The ``s`` log dir has no record, so its export has no ``record`` folder."""
    _, out, _ = made

    assert not (out / "record").exists()
