import sys
import time
from pathlib import Path

import pytest

from beamtime import remote
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.remote.client import Spec
from beamtime.remote.sources import Sources
from beamtime.serve.api import dispatch

SWEEP = "scaling/lr-sweep"
COMMAND = f"{sys.executable} -m beamtime.cli"


def test_a_prefixed_target_runs_on_its_source(box: Path, ctx: Context) -> None:
    """@box/... goes to box; paths in the answer carry the prefix."""
    answer = call("runs", {"from": f"@box/{SWEEP}", "select": ["run.group"], "limit": 3}, ctx)
    assert {r[1] for r in answer["rows"]} == {f"@box/{SWEEP}"}
    assert answer["meta"]["source"] == "@box" and answer["meta"]["from"] == f"@box/{SWEEP}"
    local = call("runs", {"from": SWEEP, "limit": 3}, ctx)
    assert {r[0] for r in local["rows"]}.isdisjoint(r[0] for r in answer["rows"])


def test_listings_of_everything_merge(box: Path, ctx: Context) -> None:
    """Groups, runs, timeline, notes and keys over . come from both sources."""
    paths = [r[0] for r in call("groups", {"from": "."}, ctx)["rows"]]
    assert "scaling" in paths and "@box" in paths and f"@box/{SWEEP}" in paths
    runs = call("runs", {"from": ".", "select": ["run.group"], "limit": 1000}, ctx)
    groups = {r[1].split("/", 1)[0] for r in runs["rows"]}
    assert "@box" in groups and any(not g.startswith("@") for g in groups)
    assert runs["meta"]["sources"] == [{"name": "local", "state": "connected"},
                                       {"name": "@box", "state": "connected"}]  # fmt: skip
    # each source sends its newest rows; merged and cut, they are the newest of both.
    top = call("runs", {"from": ".", "limit": 4}, ctx)["rows"]
    every = sorted((r[0] for r in runs["rows"]), reverse=True)
    assert [r[0] for r in top] == every[:4]
    timeline = call("timeline", {"from": ".", "limit": 50}, ctx)["entries"]
    assert [e["t"] for e in timeline] == sorted(e["t"] for e in timeline)
    keys = call("keys", {"from": "."}, ctx)
    held, remote.active = remote.active, None
    alone = call("keys", {"from": "."}, ctx)
    remote.active = held
    assert keys["runs"] > 0 and keys["runs"] == runs["meta"]["matched"]
    assert alone["runs"] < keys["runs"]


def test_aggregates_are_labelled_by_source(box: Path, ctx: Context) -> None:
    """Curves aggregated over a field are computed per source and say which."""
    curves = call("series", {"from": ".", "y": ["val/acc"], "by": ["config.lr"]}, ctx)["curves"]
    sources = {c["by"].get("source") for c in curves}
    assert sources == {"local", "box"}


def test_writes_land_on_the_remote(box: Path, ctx: Context, project: Path) -> None:
    """A note on @box is written by box into its own files, with this machine's author."""
    answer = call("note add", {"group": f"@box/{SWEEP}", "type": "observation",
                               "description": "Seen from the laptop."}, ctx)  # fmt: skip
    assert answer["path"].startswith(f"@box/{SWEEP}/notes/")
    written = box / answer["path"].removeprefix("@box/")
    assert "Seen from the laptop." in written.read_text()
    assert not (project / "beamtime" / answer["path"].removeprefix("@box/")).exists()
    notes = call("notes", {"from": ".", "limit": 5}, ctx)["entries"]
    assert notes[0]["description"] == "Seen from the laptop." and notes[0]["group"] == f"@box/{SWEEP}"


def test_runs_are_found_wherever_they_are(box: Path, ctx: Context) -> None:
    """A run id this machine doesn't know is looked up on the remotes."""
    run = call("runs", {"from": f"@box/{SWEEP}", "limit": 1}, ctx)["rows"][0][0]
    card = call("card", {"run": run}, ctx)
    assert card["run"]["id"] == run and card["run"]["path"].startswith(f"@box/{SWEEP}/")


def test_pages_of_remote_groups(box: Path, ctx: Context) -> None:
    """A remote group's view comes from the remote; its blocks' calls point back there."""
    page = dispatch(Context.make(caller="view"), "view", {"path": f"@box/{SWEEP}"})
    assert page["path"] == f"@box/{SWEEP}"
    calls = [n["data"]["main"] for n in walk(page["view"]) if n.get("data", {}).get("main")]
    assert calls and all(c["scope"].startswith("@box") for c in calls)
    first = calls[0]
    answer = dispatch(Context.make(caller="view"), first["method"], first["params"])
    assert answer["meta"].get("source", "@box") == "@box"


def test_errors_name_the_source(box: Path, ctx: Context, tmp_path: Path) -> None:
    """Unknown sources, unreachable ones and draft work on remote groups say what to do."""
    with pytest.raises(OpError, match="no source @nowhere"):
        call("runs", {"from": "@nowhere/x"}, ctx)
    with pytest.raises(OpError, match="works on drafts"):
        call("view new", {"group": f"@box/{SWEEP}"}, ctx)
    with pytest.raises(OpError, match="user command"):
        call("rm", {"target": f"@box/{SWEEP}"}, ctx)
    broken = Spec(name="gone", path=str(tmp_path), command="false", transport="command")
    remote.active.clients.update(Sources([broken]).clients)
    started = time.monotonic()
    for _ in range(3):
        with pytest.raises(OpError, match="@gone is unreachable since"):
            call("runs", {"from": "@gone/x"}, ctx)
    # a remote end that exits at once fails at once, also when asked again.
    assert time.monotonic() - started < 10
    # a listing of everything still answers, and says which source is missing.
    sources = call("groups", {"from": "."}, ctx)["meta"]["sources"]
    assert {"name": "@gone", "state": "unreachable"}.items() <= sources[-1].items()


def walk(t: dict) -> list[dict]:
    """List a block tree's nodes.

    :param t: The root.
    :return: The nodes, depth first."""
    return [t, *(n for c in t.get("children", []) for n in walk(c))]


def test_ssh_command_leaves_the_command_to_the_remote_shell() -> None:
    """The configured command reaches the remote shell as written; paths are quoted."""
    spec = Spec(name="c", host="login.hpc", command="~/venvs/bt/bin/beamtime", path="${SCRATCH}/p b",
                cache="/tmp/{user}")  # fmt: skip
    argv = spec.argv()
    assert argv[0] == "ssh" and "BatchMode=yes" in argv and argv[-2] == "login.hpc"
    assert argv[-1] == "~/venvs/bt/bin/beamtime serve --stdio --logdir '${SCRATCH}/p b' --cache '/tmp/{user}'"


def test_remote_paths_expand_on_the_remote(monkeypatch: pytest.MonkeyPatch) -> None:
    """~, ${VAR} and {user} expand where the remote end runs."""
    import getpass

    from beamtime.serve.stdio import expand

    monkeypatch.setenv("SCRATCH", "/scratch/x")
    assert expand("${SCRATCH}/{user}/bt") == f"/scratch/x/{getpass.getuser()}/bt"
    assert expand("~/bt") == str(Path.home() / "bt")


def test_a_run_copied_to_a_remote_is_told_apart(box: Path, ctx: Context, project: Path) -> None:
    """With the same run on both machines, @box/<id> names the remote's copy, a bare id this one."""
    import shutil

    local = next((project / "beamtime" / SWEEP).glob("*/_run.json")).parent
    shutil.copytree(local, box / "copied" / local.name)
    run = local.name
    assert call("card", {"run": run}, ctx)["run"]["path"] == f"{SWEEP}/{run}"
    there = call("card", {"run": f"@box/{run}"}, ctx)["run"]["path"]
    assert there == f"@box/copied/{run}"
    page = dispatch(Context.make(caller="view"), "view", {"path": f"@box/{run}"})
    assert page["path"] == f"@box/copied/{run}"
