"""Tests of the benchmark's exporters in ``bench/agents/compare/formats.py``; no agent runs."""

import csv
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.format.run import read_effective_metrics
from beamtime.format.tree import iter_runs

COMPARE = Path(__file__).resolve().parents[2] / "bench" / "agents" / "compare"
sys.path.insert(0, str(COMPARE))

import data  # noqa: E402
import formats  # noqa: E402

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

    assert len(runs) == 47
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

    assert len(runs) == 47
    assert len({(r.group, r.id) for r in runs}) == 47
    assert {r.status for r in runs} >= {"finished"}
