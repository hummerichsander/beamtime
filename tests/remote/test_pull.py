import json
from pathlib import Path

import pytest

from beamtime import remote
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.remote.client import Spec
from beamtime.remote.pull import snapshots_dir
from beamtime.remote.sources import Sources

SWEEP = "scaling/lr-sweep"


def test_pull_copies_a_group_incrementally(box: Path, ctx: Context) -> None:
    """A pull copies the group and its ancestors' memory; a second one only what grew."""
    first = call("pull", {"target": f"box:{SWEEP}"}, ctx)
    folder = snapshots_dir(ctx) / "box"
    assert first["copied"] > 0 and (folder / SWEEP / "proposal").is_dir()
    assert any((folder / SWEEP).glob("*/_run.json"))
    record = json.loads((folder / "_snapshot.json").read_text())
    assert record["groups"] == [SWEEP]
    again = call("pull", {"target": f"@box/{SWEEP}"}, ctx)
    assert again["copied"] == 0 and again["grown"] == 0 and again["unchanged"] == first["copied"]
    metrics = next((box / SWEEP).glob("*/_metrics.jsonl"))
    with metrics.open("a") as f:
        f.write('{"step": 99999, "t": 1.0, "val/acc": 0.5}\n')
    grown = call("pull", {"target": f"box:{SWEEP}"}, ctx)
    assert grown["grown"] == 1
    copy = folder / metrics.relative_to(box)
    assert copy.read_bytes() == metrics.read_bytes()


def test_a_snapshot_answers_while_the_remote_is_away(box: Path, ctx: Context) -> None:
    """Without the remote, its snapshot answers reads and refuses writes."""
    call("pull", {"target": f"box:{SWEEP}"}, ctx)
    remote.active.close()
    away = Spec(name="box", path=str(box), command="false", transport="command")
    remote.active = Sources([away])
    runs = call("runs", {"from": f"@box/{SWEEP}", "select": ["run.group"]}, ctx)
    assert runs["meta"]["snapshot"] and {r[1] for r in runs["rows"]} == {f"@box/{SWEEP}"}
    with pytest.raises(OpError, match="read-only"):
        call("note add", {"group": f"@box/{SWEEP}", "type": "idea", "description": "x"}, ctx)
    groups = call("groups", {"from": "."}, ctx)
    assert {"name": "@box", "state": "snapshot"}.items() <= groups["meta"]["sources"][-1].items()
    assert f"@box/{SWEEP}" in [r[0] for r in groups["rows"]]


def test_drop_and_errors(box: Path, ctx: Context) -> None:
    """Dropping removes the snapshot; unknown groups and remotes say so."""
    call("pull", {"target": f"box:{SWEEP}"}, ctx)
    call("pull", {"target": f"box:{SWEEP}", "drop": True}, ctx)
    assert not (snapshots_dir(ctx) / "box").exists()
    with pytest.raises(OpError, match="no group"):
        call("pull", {"target": "box:no/such"}, ctx)
    with pytest.raises(OpError, match="no snapshot"):
        call("pull", {"target": "box:x", "drop": True}, ctx)


def test_doctor_and_status_cover_remotes(box: Path, project: Path) -> None:
    """doctor checks a configured remote; status lists its snapshot."""
    from tests.remote.conftest import COMMAND

    (project / "beamtime.yaml").write_text(
        f"remotes:\n  box: {{path: {box}, transport: command, command: '{COMMAND}'}}\n"
        "  gone: {path: /nowhere, transport: command, command: 'false'}\n"
    )
    ctx = Context.make(caller="cli")
    rows = {r[0]: r[1:] for r in call("doctor", {}, ctx)["rows"]}
    assert rows["@box beamtime"][0] and rows["@box log dir"][0]
    assert rows["@box cache"][1].startswith("temporary")
    assert rows["@gone beamtime"][0] is False
    call("pull", {"target": f"box:{SWEEP}"}, ctx)
    snaps = call("status", {}, ctx)["snapshots"]
    assert snaps[0]["name"] == "@box" and snaps[0]["groups"] == [SWEEP]
