import dataclasses
import json
import os
import time
from pathlib import Path

import pytest

from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.remote import answer
from beamtime.remote.client import Spec
from beamtime.remote.pull import snapshots_dir
from beamtime.remote.sources import Sources

GROUP = "scaling/long-context"
DAY = 86400.0


@pytest.fixture
def away(box: Path, ctx: Context) -> Context:
    """The context after ``box`` was pulled a month ago and became unreachable.

    :param box: The remote's log dir.
    :param ctx: The context with ``box`` as a source.
    :return: A context whose only way to ``box`` is its snapshot."""
    call("pull", {"target": f"box:{GROUP}"}, ctx)
    ctx.sources.close()
    folder = snapshots_dir(ctx) / "box"
    record = json.loads((folder / "_snapshot.json").read_text(encoding="utf-8"))
    record["at"] = then = time.time() - 30 * DAY
    (folder / "_snapshot.json").write_text(json.dumps(record), encoding="utf-8")

    roles = json.loads((box / "_synth.json").read_text(encoding="utf-8"))["roles"]
    run = next(p for p in (folder / GROUP).iterdir() if p.name == roles["running"])
    os.utime(run / "_run.json", (then - 10, then - 10))
    metrics = run / "_metrics.jsonl"
    os.utime(metrics, (then - 3600, then - 3600))

    gone = Spec(name="box", path=str(box), command="false", transport="command")
    return dataclasses.replace(ctx, sources=Sources([gone]))


def test_digest_runs_on_a_snapshot_at_its_time(away: Context, box: Path) -> None:
    """Runs are counted as they stood when the snapshot was taken: still running, none lost."""
    d = answer("digest", {"group": f"@box/{GROUP}"}, away)
    assert d["meta"]["snapshot"] < time.time() - 29 * DAY
    # the run the remote calls lost had a fresh heartbeat then.
    assert d["runs"]["running"] == 2 and "lost" not in d["runs"]
    assert sum(d["runs"].values()) == len(list((box / GROUP).glob("*/_run.json")))


def test_diagnose_judges_a_stall_at_the_snapshots_time(away: Context, box: Path) -> None:
    """A run silent for an hour before the snapshot is stalled, not lost, though the pull is old."""
    roles = json.loads((box / "_synth.json").read_text(encoding="utf-8"))["roles"]
    a = answer("diagnose", {"from": f"@box/{GROUP}"}, away)
    flagged = {e["run"].split("/")[-1]: e for e in a["entries"]}
    entry = flagged[roles["running"]]
    assert entry["status"] == "running"
    assert entry["flags"]["stalled"].startswith("no new metrics for 60 min")
    assert a["meta"]["snapshot"]
