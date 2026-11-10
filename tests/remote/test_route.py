from beamtime.remote.route import source_of, strip


def test_strip_and_source() -> None:
    """A target names its source; stripping gives the remote's own path."""
    assert source_of({"group": "@box/g", "description": "@alice said"}) == "box"
    assert source_of({"description": "@alice said"}) is None
    assert strip({"from": "@box", "run": "@box/r"}, "box") == {"from": ".", "run": "r"}
    assert strip({"query": {"runs": {"from": "@box/g"}}}, "box")["query"]["runs"]["from"] == "g"
    assert strip({"group": "@local/g", "run": "@local", "path": "h"}, None) == {
        "group": "g",
        "run": ".",
        "path": "h",
    }
    assert strip({"group": "@boxer/g"}, "box") == {"group": "@boxer/g"}
    assert source_of({"group": "@local/g"}) is None


def test_only_targets_name_a_remote() -> None:
    """A description starting with @ is text, not a remote."""
    from beamtime.remote import targets

    assert targets({"group": "@box/g"}) and targets({"query": {"runs": {"from": "@box"}}})
    assert not targets({"group": "g", "description": "@alice found it"})
