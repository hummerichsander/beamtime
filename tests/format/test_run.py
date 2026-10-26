import math
import time
from pathlib import Path

import pytest

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

FINISHED = "scaling/lr-sweep/20261024-101532-k3m9xq2a"
RESUMED = "scaling/lr-sweep/20261024-111500-r3s4m5d6"
FAILED = "scaling/lr-sweep/20261024-121500-f4a1ed00"


@pytest.fixture
def finished(golden: Path) -> Path:
    """The finished golden run.

    :param golden: The golden log dir.
    :return: The run directory."""
    return golden / FINISHED


def test_run_info(finished: Path) -> None:
    """``_run.json`` reads with every field; unknown fields are ignored."""
    info = read_run_info(finished)
    assert info.id == "20261024-101532-k3m9xq2a" and info.name == "boosted-kaon-42"
    assert info.status == "finished" and info.tags == ["resnet18", "cifar10"]
    assert info.proposals == {"scaling": "20261020-140000-q7w3"}
    assert info.attempts[0].host == "gpu042" and info.attempts[0].resume_step is None
    assert info.scheduler["array_task_id"] == "45"
    assert info.job_key == "slurm:8812300:45"


def test_config(finished: Path) -> None:
    """The config comes back nested and without ``schema``."""
    assert read_config(finished) == {
        "lr": 0.0003,
        "seed": 0,
        "warmup": 500,
        "model": {"name": "resnet18", "width": 64},
    }


def test_card(finished: Path) -> None:
    """The card reads its statistics and ignores unknown metric fields."""
    card = read_card(finished)
    m = card.metrics["train/loss"]
    assert (m.first, m.last, m.min_step, m.count) == (2.31, 1.18, 9, 10)
    assert m.slope_last10pct is None
    assert card.values == {"test/acc": 0.931}


def test_preview(finished: Path) -> None:
    """Empty preview buckets are ``None``."""
    p = read_preview(finished).metrics["val/acc"]
    assert p.bucket_width == 1 and p.mean == [0.1, None, None, 0.37]


def test_metrics_sparse_keys(finished: Path) -> None:
    """Metric records are sparse and complete."""
    chunk = read_metrics(finished)
    assert len(chunk.rows) == 10 and chunk.bad == 0
    assert "val/acc" in chunk.rows[0] and "val/acc" not in chunk.rows[1]


def test_data_events_artifacts(finished: Path) -> None:
    """Data entries, events and artifacts read with their fields."""
    data = {d.key: d for d in read_data(finished)}
    assert data["val/per_class"].columns["acc"] == [0.9, 0.8]
    assert (finished / data["samples"].path).read_bytes().startswith(b"\x89PNG")
    assert data["samples/text"].text == "a beam of kaons"
    events = read_events(finished)
    assert [e.kind for e in events] == ["created", "attempt_started", "user", "finished"]
    assert events[2].message == "lr decayed" and events[2].data == {"factor": 0.5}
    arts = read_artifacts(finished)
    assert arts[0].path == "artifacts/best.ckpt" and arts[1].uri.endswith("final.ckpt")


def test_output_head_and_tails(finished: Path) -> None:
    """Output is head, previous tail and tail, in that order; ranks have their own."""
    out = read_output(finished)
    assert out.index("head line 2") < out.index("prev line") < out.index("tail line")
    assert read_output(finished, rank=1) == "rank 1 says hi\n"
    assert read_output(finished, rank=2) == ""


def test_resumed_newer_attempt_wins(golden: Path) -> None:
    """Steps from the resume step on come from the newer attempt only."""
    run = golden / RESUMED
    assert [a.resume_step for a in read_run_info(run).attempts] == [None, 4]
    rows = read_effective_metrics(run)
    assert [r["_step"] for r in rows] == list(range(8))
    assert rows[3]["train/loss"] == pytest.approx(1.7)
    assert rows[4]["train/loss"] == pytest.approx(8.6)


def test_failed_run_with_damaged_metrics(golden: Path) -> None:
    """NaN and Infinity read; a corrupt line is counted; a partial line waits."""
    run = golden / FAILED
    chunk = read_metrics(run)
    assert [r["_step"] for r in chunk.rows] == [0, 1, 3] and chunk.bad == 1
    assert math.isnan(chunk.rows[1]["train/loss"])
    assert chunk.rows[2]["train/loss"] == math.inf
    assert chunk.end < (run / "_metrics.jsonl").stat().st_size
    assert read_events(run)[-1].data["traceback"].endswith("loss is inf\n")
    assert read_run_info(run).exit == {"code": 1}


def test_missing_streams_are_empty(golden: Path) -> None:
    """Runs without data or artifacts read as empty."""
    run = golden / FAILED
    assert read_data(run) == [] and read_artifacts(run) == []


def test_lost_is_derived(finished: Path, golden: Path) -> None:
    """A running run with a heartbeat older than 5 minutes is lost."""
    info = read_run_info(finished)
    now = time.time()
    assert run_status(info, heartbeat=now - 3600, now=now) == "finished"
    running = info.__class__(**{**info.__dict__, "status": "running"})
    assert run_status(running, heartbeat=now - 3600, now=now) == "lost"
    assert run_status(running, heartbeat=now - 10, now=now) == "running"
