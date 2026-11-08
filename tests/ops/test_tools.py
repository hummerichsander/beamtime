import pytest

from beamtime.ops import call
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
