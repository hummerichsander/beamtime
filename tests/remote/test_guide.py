"""A remote group's guide is the remote project's, read with its settings."""

from pathlib import Path

from beamtime.ops.context import Context
from beamtime.remote import answer

SWEEP = "scaling/lr-sweep"


def test_guide_remote_settings(ctx: Context, box: Path) -> None:
    """The guide for ``@box/...`` carries the remote's agent settings, not the local ones.

    :param ctx: The local context with ``box`` as a source.
    :param box: The remote's log dir."""
    (box.parent / "beamtime.yaml").write_text("agent: {style: hands-on, seeds: 7}\n", encoding="utf-8")
    local = answer("guide", {}, ctx)["text"]
    remote = answer("guide", {"group": f"@box/{SWEEP}"}, ctx)["text"]
    assert "You may launch runs." in remote and "7 seeds per point" in remote
    assert "Ask before you launch a run." in local and "7 seeds" not in local
    assert "{{agent." not in remote
