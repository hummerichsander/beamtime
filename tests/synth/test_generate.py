import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import pytest

from beamtime.format.authored import newest, read_markdown_doc, read_yaml_doc
from beamtime.format.io import read_json
from beamtime.format.run import (
    read_artifacts,
    read_card,
    read_config,
    read_data,
    read_effective_metrics,
    read_events,
    read_metrics,
    read_output,
    read_preview,
    read_run_info,
    run_status,
)
from beamtime.format.tree import iter_runs
from beamtime.synth import Manifest, generate
from beamtime.synth.summary import card_and_preview

NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)


def by_role(logdir: Path, manifest: Manifest, role: str) -> Path:
    """Find the run with a role.

    :param logdir: The log dir.
    :param manifest: The generator's manifest.
    :param role: E.g. ``diverging``.
    :return: The run directory."""
    return next(p for p in iter_runs(logdir) if p.name == manifest.roles[role])


def test_every_file_reads_back(synth: tuple[Path, Manifest]) -> None:
    """Every generated run reads with every reader, without damaged lines."""
    logdir, manifest = synth
    runs = list(iter_runs(logdir))
    assert len(runs) == manifest.runs == 26
    for run in runs:
        info = read_run_info(run)
        assert info.id == run.name
        assert read_config(run)
        assert read_card(run).status == info.status
        assert read_preview(run).metrics
        assert read_metrics(run).bad == 0
        assert read_events(run)[0].kind == "created"
        assert read_output(run)
        read_data(run), read_artifacts(run)
    assert read_json(logdir / "_synth.json")["roles"] == manifest.roles


def test_authored_files_read_back(synth: tuple[Path, Manifest]) -> None:
    """Proposals, notes and memory are valid authored files."""
    logdir, manifest = synth
    sweep = logdir / "scaling" / "lr-sweep"
    proposal = read_yaml_doc(newest(sweep / "proposal"), kind="proposal")
    assert {p["name"] for p in proposal.meta["predictions"]} == {
        "converges",
        "mid-beats-high",
    }
    note = read_markdown_doc(newest(sweep / "notes"), kind="note")
    assert note.meta["evidence"] == [manifest.roles["diverging"]]
    assert read_markdown_doc(newest(logdir / "memory"), kind="memory").body
    for run in iter_runs(sweep):
        assert read_run_info(run).proposals == {"scaling/lr-sweep": proposal.id}


def test_deterministic(tmp_path: Path) -> None:
    """The same seed gives byte-identical files; another seed does not."""
    a = generate(tmp_path / "a", seed=7, now=NOW)
    b = generate(tmp_path / "b", seed=7, now=NOW)
    files = sorted(p.relative_to(tmp_path / "a") for p in (tmp_path / "a").rglob("*"))
    assert files == sorted(
        p.relative_to(tmp_path / "b") for p in (tmp_path / "b").rglob("*")
    )
    for rel in files:
        if (tmp_path / "a" / rel).is_file():
            assert (tmp_path / "a" / rel).read_bytes() == (tmp_path / "b" / rel).read_bytes()
    assert a.roles == b.roles
    assert generate(tmp_path / "c", seed=8, now=NOW).roles != a.roles


def test_planted_best_lr(synth: tuple[Path, Manifest]) -> None:
    """The best final val/acc mean over seeds is at lr 3e-4."""
    logdir, manifest = synth
    finals: dict[float, list[float]] = {}
    for run in iter_runs(logdir / "scaling" / "lr-sweep"):
        if read_run_info(run).status == "finished":
            lr = read_config(run)["lr"]
            finals.setdefault(lr, []).append(read_card(run).metrics["val/acc"].last)
    assert all(len(v) == 3 for v in finals.values())
    best = max(finals, key=lambda lr: mean(finals[lr]))
    assert best == manifest.effects[0]["best"]["config.lr"]


def test_planted_tokenizer_gap(synth: tuple[Path, Manifest]) -> None:
    """Unigram ends with lower validation perplexity than BPE."""
    logdir, _ = synth
    ppl: dict[str, list[float]] = {}
    for run in iter_runs(logdir / "tokenizer"):
        ppl.setdefault(read_config(run)["tokenizer"], []).append(
            read_card(run).metrics["val/ppl"].last
        )
    assert 0.2 < mean(ppl["bpe"]) - mean(ppl["unigram"]) < 0.6


def test_special_runs(synth: tuple[Path, Manifest]) -> None:
    """Diverging, killed, resumed, lost and running runs look as they should."""
    logdir, manifest = synth
    run = by_role(logdir, manifest, "diverging")
    card = read_card(run)
    assert card.status == "failed" and card.error.startswith("FloatingPointError")
    assert card.metrics["train/loss"].nonfinite == 10
    assert "Traceback" in read_output(run)

    run = by_role(logdir, manifest, "killed")
    assert read_events(run)[-1].data["signal"] == "SIGTERM"
    assert read_run_info(run).exit == {"signal": "SIGTERM"}

    run = by_role(logdir, manifest, "resumed")
    assert [a.resume_step for a in read_run_info(run).attempts] == [None, 1000]
    steps = [r["_step"] for r in read_effective_metrics(run)]
    assert steps == list(range(2000))
    assert len(read_metrics(run).rows) > 2000
    times = [e.t for e in read_events(run)]
    assert times == sorted(times)

    now = NOW.timestamp()
    for role, status in (("lost", "lost"), ("running", "running")):
        run = by_role(logdir, manifest, role)
        beat = (run / "_run.json").stat().st_mtime
        assert run_status(read_run_info(run), heartbeat=beat, now=now) == status


def test_card_and_preview_agree(synth: tuple[Path, Manifest]) -> None:
    """Preview widths are powers of two with at most 512 buckets, and match the card."""
    logdir, _ = synth
    for run in iter_runs(logdir):
        card, preview = read_card(run), read_preview(run)
        for key, p in preview.metrics.items():
            m = card.metrics[key]
            w = p.bucket_width
            assert w & (w - 1) == 0 and len(p.count) <= 512
            assert w == 1 or len(p.count) > 256
            assert sum(n for n in p.count if n) == m.count
            assert min(v for v in p.min if v is not None) == m.min
            assert max(v for v in p.max if v is not None) == m.max


def test_summary_of_nonfinite_and_empty() -> None:
    """Statistics skip non-finite values; a metric with none finite has no preview."""
    rows = [
        {"_step": 0, "_t": 0.0, "x": 1.0, "y": math.nan},
        {"_step": 1, "_t": 1.0, "x": math.inf},
        {"_step": 2, "_t": 2.0, "x": 3.0},
    ]
    card, preview = card_and_preview(rows, status="finished", duration_s=2.0)
    x = card["metrics"]["x"]
    assert (x["count"], x["nonfinite"], x["mean"], x["max_step"]) == (2, 1, 2.0, 2)
    assert x["ema_last"] == pytest.approx(0.9 * 1.0 + 0.1 * 3.0) and x["slope_last10pct"] is None
    assert card["metrics"]["y"] == {"count": 0, "nonfinite": 1, "last_step": 0}
    assert "y" not in preview["metrics"]
    assert preview["metrics"]["x"]["count"] == [1, None, 1]
