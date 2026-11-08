import json

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
