from beamtime.remote.route import prefix, source_of, strip


def test_prefix_leaves_what_users_wrote_alone() -> None:
    """Paths get the source; configs, proposals, logged tables and conditions keep their values."""
    card = {
        "kind": "card",
        "run": {"id": "r", "path": "g/r"},
        "config": {"group": "norm", "path": "data/cifar"},
        "proposals": [{"group": "g", "version": "v"}],
        "meta": {"source": "local", "from": "g"},
    }
    out = prefix(card, "box")
    assert out["run"]["path"] == "@box/g/r" and out["proposals"][0]["group"] == "@box/g"
    assert out["config"] == {"group": "norm", "path": "data/cifar"}
    assert out["meta"] == {"source": "@box", "from": "@box/g"}
    data = {"entries": [{"run": "r", "step": 1, "path": "_data/x.png",
                         "columns": {"group": ["a"], "path": ["b"]}}]}  # fmt: skip
    entry = prefix(data, "box")["entries"][0]
    assert entry["path"] == "_data/x.png" and entry["columns"] == {"group": ["a"], "path": ["b"]}
    shown = prefix({"group": "g", "proposal": {"predictions": [{"where": {"group": "x"}}]}}, "box")
    assert shown["proposal"]["predictions"][0]["where"] == {"group": "x"}
    table = prefix({"columns": ["path", "runs"], "rows": [[".", 1], ["g", 2]]}, "box")
    assert table["rows"] == [["@box", 1], ["@box/g", 2]]


def test_strip_and_source() -> None:
    """A target names its source; stripping gives the remote's own path."""
    assert source_of({"group": "@box/g", "description": "@alice said"}) == "box"
    assert source_of({"description": "@alice said"}) is None
    assert strip({"from": "@box", "run": "@box/r"}, "box") == {"from": ".", "run": "r"}
    assert strip({"query": {"runs": {"from": "@box/g"}}}, "box")["query"]["runs"]["from"] == "g"


def test_only_targets_name_a_remote() -> None:
    """A description starting with @ is text, not a remote."""
    from beamtime.remote import targets

    assert targets({"group": "@box/g"}) and targets({"query": {"runs": {"from": "@box"}}})
    assert not targets({"group": "g", "description": "@alice found it"})
