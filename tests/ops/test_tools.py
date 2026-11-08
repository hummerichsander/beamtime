import json
import os
import threading
import time

import pytest

from beamtime.ops import call
from beamtime.ops.budget import MAX_CHARS
from beamtime.ops.context import Context, OpError
from beamtime.remote.route import routed


def run_ids(ctx: Context, group: str) -> list[str]:
    """List the ids of a group's runs.

    :param ctx: The operation context.
    :param group: The group.
    :return: The run ids."""
    found = call("runs", {"from": group, "select": ["run.id"], "limit": 100}, ctx)
    return [row[0] for row in found["rows"]]


def test_compare_two_groups_names_what_differs(ctx: Context) -> None:
    """Groups compare by config keys that differ, code identity, status counts and metrics."""
    a = call("compare", {"targets": ["scaling/lr-sweep", "tokenizer/bpe-vs-unigram"]}, ctx)
    assert [t["runs"] for t in a["targets"]] == [17, 6]
    assert a["targets"][0]["status"]["finished"] == 15
    differing = {d["key"] for d in a["differences"]}
    assert {"config.model", "config.tokenizer"} <= differing
    by_key = {d["key"]: d for d in a["differences"]}
    assert by_key["config.model"]["values"] == ["resnet18", None]
    assert "varies" in by_key["config.lr"]["values"][0]
    assert a["same_code"] is True
    loss = next(r for r in a["rows"] if r["metric"] == "train/loss")
    assert loss["delta"] == pytest.approx(loss["values"][1]["mean"] - loss["values"][0]["mean"])


def test_compare_two_runs_and_metric_choice(ctx: Context) -> None:
    """Two runs give plain numbers and a difference; ``metrics`` picks the table's rows."""
    first, second = run_ids(ctx, "scaling/lr-sweep")[:2]
    a = call("compare", {"targets": [first, second], "metrics": ["val/acc"]}, ctx)
    assert [r["metric"] for r in a["rows"]] == ["val/acc"]
    cells = a["rows"][0]["values"]
    assert all(isinstance(c, float) or c is None for c in cells)
    assert a["differences"] and all(len(d["values"]) == 2 for d in a["differences"])


def test_compare_needs_two_targets_and_one_source(ctx: Context) -> None:
    """One target is wrong usage; targets on two sources are refused with a pointer to ``pull``."""
    with pytest.raises(OpError, match="at least two"):
        call("compare", {"targets": ["scaling"]}, ctx)
    with pytest.raises(OpError, match="pull"):
        routed("compare", {"targets": ["@a/x", "@b/y"]}, ctx, lambda p: {})


def test_digest_is_one_page_on_a_group(ctx: Context, roles: dict[str, str]) -> None:
    """A digest has statuses, the check, the best per varying value, failures by signature, notes."""
    d = call("digest", {"group": "scaling/lr-sweep"}, ctx)
    assert d["runs"] == {"finished": 15, "failed": 1, "killed": 1}
    assert d["proposal"]["result"] == "pass" and not d["proposal"]["provisional"]
    assert {p["name"] for p in d["predictions"]} == {"converges", "mid-beats-high"}
    assert d["best"]["metric"] == "val/acc" and list(d["best"]["by"]) == ["config.lr"]
    best = max(d["best"]["by"]["config.lr"], key=lambda row: row["mean"])
    assert best["value"] == 0.0003 and best["runs"] == 3
    failed = next(f for f in d["failures"] if f["status"] == "failed")
    assert failed["signature"] == "FloatingPointError: train/loss is inf"
    assert failed["runs"] == [roles["diverging"]]
    assert d["notes"] and d["missing"]["missing"] == 0
    assert len(json.dumps(d)) < MAX_CHARS


def test_digest_without_proposal_or_metric(ctx: Context) -> None:
    """A group with no proposal still gets statuses, failures and notes; ``metric`` picks the table."""
    d = call("digest", {"group": "tokenizer"}, ctx)
    assert d["proposal"] is None and d["best"] is None and d["open_questions"]
    named = call("digest", {"group": "tokenizer/bpe-vs-unigram", "metric": "val/ppl"}, ctx)
    assert named["best"]["by"]["config.tokenizer"]
    with pytest.raises(OpError, match="no group"):
        call("digest", {"group": "nope"}, ctx)


def test_logs_group_tracebacks_by_signature(ctx: Context, roles: dict[str, str]) -> None:
    """Failed runs' last tracebacks are grouped by their exception line; runs show their tail."""
    a = call("logs", {"from": "scaling/lr-sweep", "tail": 2}, ctx)
    [crash] = a["tracebacks"]
    assert crash["signature"] == "FloatingPointError: train/loss is inf"
    assert crash["runs"] == [roles["diverging"]]
    assert crash["traceback"][0].startswith("Traceback") and crash["traceback"][-1].startswith("Floating")
    assert all(len(e["lines"]) <= 2 for e in a["entries"])
    assert a["meta"]["matched"] == 17


def test_logs_grep_shows_matches_with_context(ctx: Context, roles: dict[str, str]) -> None:
    """``grep`` keeps matching lines, numbered, with ``context`` lines around them."""
    a = call("logs", {"from": roles["diverging"], "grep": "Error", "context": 2}, ctx)
    [entry] = a["entries"]
    assert entry["lines"][-1].startswith(("25: Floating", "26: Floating"))
    assert entry["lines"][0].split("-")[0].isdigit() and len(entry["lines"]) == 3
    with pytest.raises(OpError, match="regular expression"):
        call("logs", {"from": roles["diverging"], "grep": "("}, ctx)


def test_logs_is_cut_at_the_budget_not_dropped(ctx: Context) -> None:
    """A whole project's output is cut at whole runs, and the cursor continues after them."""
    first = call("logs", {"tail": 0}, ctx)
    assert first["meta"]["cut"] and len(json.dumps(first)) < MAX_CHARS + 2000
    second = call("logs", {"tail": 0, "cursor": first["meta"]["next"]}, ctx)
    assert second["entries"][0]["run"] != first["entries"][0]["run"]


def test_wait_returns_at_once_when_nothing_runs(ctx: Context) -> None:
    """A group with no running run is done, and no run changed."""
    a = call("wait", {"from": "tokenizer"}, ctx)
    assert a["met"] and a["waited_s"] < 1 and a["changed"] == []
    assert a["runs"] == {"finished": 6}


def test_wait_condition_names_the_matching_runs(ctx: Context) -> None:
    """A condition ends the wait as soon as one run meets it, together with ``where``."""
    a = call("wait", {"from": "scaling/lr-sweep", "until": "metric.val/acc.max>0.93"}, ctx)
    assert a["met"] and a["matching"]
    b = call(
        "wait",
        {"from": "scaling/lr-sweep", "where": {"config.lr": 0.001}, "until": "metric.val/acc.max>0.9"},
        ctx,
    )
    assert len(b["matching"]) == 3
    with pytest.raises(OpError, match="until"):
        call("wait", {"until": "val/acc"}, ctx)


def test_wait_times_out_and_reports_what_changed(ctx: Context, roles: dict[str, str]) -> None:
    """A run that finishes during the wait ends it and shows as changed; otherwise it times out."""
    running = next(p for p in ctx.logdir.rglob(roles["running"]) if p.is_dir())
    stuck = call("wait", {"from": roles["running"], "timeout": 0.3}, ctx)
    assert stuck["timed_out"] and not stuck["met"] and not stuck["capped"]

    def finish() -> None:
        time.sleep(0.5)
        info = json.loads((running / "_run.json").read_text())
        (running / "_run.json").write_text(json.dumps(info | {"status": "finished"}))

    thread = threading.Thread(target=finish)
    thread.start()
    done = call("wait", {"from": roles["running"], "timeout": 20}, ctx)
    thread.join()
    assert done["met"] and done["changed"][0]["from"] == "running"
    assert done["changed"][0]["to"] == "finished"


def test_wait_over_mcp_never_blocks_past_its_cap(
    ctx: Context, roles: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Over MCP the wait ends at the cap, says so, and the agent calls again."""
    monkeypatch.setattr("beamtime.ops.reading.MCP_WAIT_S", 0.3)
    ctx.caller = "mcp"
    start = time.monotonic()
    a = call("wait", {"from": roles["running"], "timeout": 600}, ctx)
    assert time.monotonic() - start < 10
    assert a["timed_out"] and a["capped"]


def test_diagnose_flags_what_went_wrong(ctx: Context, roles: dict[str, str]) -> None:
    """Non-finite and diverging metrics, a restart, a short run and a missing metric are flagged."""
    a = call("diagnose", {"from": "scaling/lr-sweep"}, ctx)
    flagged = {e["run"]: e["flags"] for e in a["entries"]}
    assert flagged[roles["diverging"]]["nonfinite"] == ["train/loss"]
    assert flagged[roles["diverging"]]["diverging"] == ["train/loss"]
    assert "stopped_early" in flagged[roles["killed"]]
    assert a["meta"]["matched"] == 17 and a["meta"]["by_flag"]["nonfinite"] == 1
    # healthy runs of the sweep carry no flag.
    assert len(flagged) == 2
    resumed = call("diagnose", {"from": roles["resumed"]}, ctx)
    assert resumed["entries"][0]["flags"]["restarts"] >= 1
    lacking = call("diagnose", {"from": "tokenizer", "metrics": ["nope/metric"]}, ctx)
    assert all(e["flags"]["missing"] == ["nope/metric"] for e in lacking["entries"])
    assert lacking["meta"]["flagged"] == 6


def test_diagnose_flags_a_running_run_that_stopped_logging(
    ctx: Context, roles: dict[str, str]
) -> None:
    """A running run whose metrics file has not changed for a long time is stalled."""
    run = next(p for p in ctx.logdir.rglob(roles["running"]) if p.is_dir())
    before = call("diagnose", {"from": roles["running"]}, ctx)["entries"]
    assert not any("stalled" in e["flags"] for e in before)
    old = time.time() - 3600
    os.utime(run / "_metrics.jsonl", (old, old))
    [entry] = call("diagnose", {"from": roles["running"]}, ctx)["entries"]
    assert entry["flags"]["stalled"].startswith("no new metrics for 60 min")
