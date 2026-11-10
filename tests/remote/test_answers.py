import pytest

from beamtime.ops.answers import merged, placed


def test_placed_leaves_what_users_wrote_alone() -> None:
    """Paths get the source; configs, proposals, logged tables and conditions keep their values."""
    card = {
        "kind": "card",
        "run": {"id": "r", "path": "g/r"},
        "config": {"group": "norm", "path": "data/cifar"},
        "proposals": [{"group": "g", "version": "v"}],
        "meta": {"source": "local", "from": "g"},
    }
    out = placed(card, "box")
    assert out["run"]["path"] == "@box/g/r" and out["proposals"][0]["group"] == "@box/g"
    assert out["config"] == {"group": "norm", "path": "data/cifar"}
    assert out["meta"] == {"source": "@box", "from": "@box/g"}
    data = {"entries": [{"run": "r", "step": 1, "path": "_data/x.png",
                         "columns": {"group": ["a"], "path": ["b"]}}]}  # fmt: skip
    entry = placed(data, "box")["entries"][0]
    assert entry["path"] == "_data/x.png" and entry["columns"] == {"group": ["a"], "path": ["b"]}
    shown = placed({"group": "g", "proposal": {"predictions": [{"where": {"group": "x"}}]}}, "box")
    assert shown["proposal"]["predictions"][0]["where"] == {"group": "x"}
    table = placed({"columns": ["path", "runs"], "rows": [[".", 1], ["g", 2]]}, "box")
    assert table["rows"] == [["@box", 1], ["@box/g", 2]]


def test_a_blocks_proposal_call_gets_the_source() -> None:
    """The proposal block's call is a place under a key of user content; its answer is not."""
    call = {"method": "proposal_show", "params": {"group": "exp/a"}, "scope": "exp/a"}
    data = {"proposal": call, "check": call | {"method": "check"}}
    out = placed({"blocks": [{"data": data}]}, "au")["blocks"][0]["data"]
    for found in out.values():
        assert found["params"]["group"] == "@au/exp/a" and found["scope"] == "@au/exp/a"
    shown = {"group": "exp/a", "proposal": {"yaml": "group: x\n", "group": "x"}}
    assert placed(shown, "au")["proposal"] == {"yaml": "group: x\n", "group": "x"}


def test_merged_sums_matches_and_refuses_what_does_not_federate() -> None:
    """A listing merges with local first; a kind that is not a listing raises."""
    one = {"kind": "groups", "rows": [["@a"]], "meta": {"matched": 1}}
    two = {"kind": "groups", "rows": [["@b"]], "meta": {"matched": 2}}
    out = merged("groups", [("local", one), ("b", two)], {}, "cli")
    assert out["rows"] == [["@a"], ["@b"]] and out["meta"] == {"matched": 3, "source": "."}
    with pytest.raises(ValueError, match="no merge for 'card'"):
        merged("card", [("local", one)], {}, "cli")
