import pytest

from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL
from beamtime.remote.route import check_one_source, source_of, strip


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


def test_promote_routes_by_its_runs() -> None:
    """``run promote`` names its runs in a list; they route and strip like any target."""
    assert source_of({"runs": ["@box/20260101-aaaa"]}) == "box"
    assert strip({"runs": ["@box/20260101-aaaa"]}, "box") == {"runs": ["20260101-aaaa"]}


def test_promote_stays_on_one_source(ctx: Context) -> None:
    """Runs of two sources in one ``run promote`` are refused before anything is written."""
    with pytest.raises(OpError):
        check_one_source(BY_TOOL["run_promote"], {"runs": ["@box/a", "@other/b"]}, ctx)
