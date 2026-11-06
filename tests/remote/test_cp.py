from pathlib import Path

import pytest

from beamtime.format import constants as c
from beamtime.format.run import read_run_info
from beamtime.ops.context import Context, OpError
from beamtime.remote import answer as call

SWEEP = "scaling/lr-sweep"


def finished_run(ctx: Context, group: str) -> str:
    """Find a finished run of a remote group.

    :param ctx: The context, with ``box`` as a source.
    :param group: The group below the remote's log dir.
    :return: Its id."""
    rows = call("runs", {"from": f"@box/{group}", "select": ["run.status"], "limit": 50}, ctx)[
        "rows"
    ]
    return next(row[0] for row in rows if row[1] == "finished")


def test_a_copy_on_a_remote_is_made_by_the_remote(box: Path, ctx: Context, project: Path) -> None:
    """``cp @box/a @box/b`` copies inside box's log dir; nothing lands on this machine."""
    run = finished_run(ctx, SWEEP)
    before = {p.name for p in (project / "beamtime").rglob("*") if p.is_dir()}
    answer = call("cp", {"source": f"@box/{run}", "dest": "@box/copies"}, ctx)
    assert answer["path"] == f"@box/copies/{answer['id']}"
    assert f"to {answer['path']} " in answer["lines"][0]
    copy = box / "copies" / answer["id"]
    assert read_run_info(copy).id == answer["id"] and answer["id"] != run
    assert {p.name for p in (project / "beamtime").rglob("*") if p.is_dir()} == before
    assert (copy / c.METRICS).read_bytes() == next(
        (box / SWEEP).glob(f"{run}/{c.METRICS}")
    ).read_bytes()
    found = call("runs", {"from": "@box/copies"}, ctx)
    assert [row[0] for row in found["rows"]] == [answer["id"]]


def test_a_group_copy_on_a_remote_keeps_its_subfolders(box: Path, ctx: Context) -> None:
    """A group copied between remote groups arrives below the destination."""
    answer = call("cp", {"source": f"@box/{SWEEP}", "dest": "@box/copies/sweep"}, ctx)
    assert answer["path"].startswith("@box/")
    assert any((box / "copies" / "sweep").rglob(c.RUN))


@pytest.mark.parametrize(
    ("source", "dest"),
    [
        (f"@box/{SWEEP}", "elsewhere"),
        (SWEEP, "@box/copies"),
    ],
)
def test_a_copy_across_sources_points_to_pull(
    box: Path, ctx: Context, source: str, dest: str
) -> None:
    """A copy between this machine and a remote is refused, and nothing is written."""
    with pytest.raises(OpError, match="beamtime pull"):
        call("cp", {"source": source, "dest": dest}, ctx)
    assert not (box / "copies").exists()
