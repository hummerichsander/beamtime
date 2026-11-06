import json
import time
from pathlib import Path
from typing import Any

import pytest

from beamtime.format import constants as c
from beamtime.format.ids import new_run_id
from beamtime.format.io import json_line, write_replaced
from beamtime.format.run import read_run_info
from beamtime.format.times import iso
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.copy import TEMP_PREFIX, checkpoints


def make_run(
    logdir: Path,
    folder: str,
    *,
    status: str = "finished",
    artifacts: list[dict[str, Any]] | None = None,
    checkpoint_files: dict[str, bytes] | None = None,
    proposals: dict[str, str] | None = None,
    command: list[str] | None = None,
) -> Path:
    """Build a minimal run directory directly, for full control over its artifacts.

    :param logdir: The log dir.
    :param folder: The group below the log dir.
    :param status: The run's status.
    :param artifacts: Records for ``_artifacts.jsonl``.
    :param checkpoint_files: File name to content, written below ``checkpoints/``.
    :param proposals: The run's recorded proposal membership.
    :param command: The recorded command; defaults to a plain one with no ``--dirpath``.
    :return: The run directory."""
    run_dir = logdir / folder / new_run_id()
    run_dir.mkdir(parents=True)
    now = iso(time.time(), ms=True)
    info = {
        "schema": 1,
        "id": run_dir.name,
        "name": "test-run",
        "tags": [],
        "status": status,
        "created_at": now,
        "ended_at": now if status != "running" else None,
        "exit": None,
        "attempts": [{"started_at": now, "host": "h", "resume_step": None}],
        "proposals": proposals or {},
        "proposal_hashes": {},
        "job_key": None,
        "host": {"hostname": "h"},
        "scheduler": None,
        "git": None,
        "command": command or ["python", "train.py"],
        "cwd": "/home/x",
        "beamtime_version": "0.0.0",
    }
    write_replaced(run_dir / c.RUN, info)
    (run_dir / c.METRICS).write_bytes(b'{"_step":0,"_t":0.0,"x":1.0}\n{"_step":1,"_t":1.0,"x":2.0}\n')
    write_replaced(run_dir / c.CARD, {"schema": 1, "status": status, "steps": 2})
    if checkpoint_files:
        (run_dir / "checkpoints").mkdir()
        for name, data in checkpoint_files.items():
            (run_dir / "checkpoints" / name).write_bytes(data)
    if artifacts is not None:
        (run_dir / c.ARTIFACTS).write_bytes(b"".join(json_line(a) for a in artifacts))
    return run_dir


def test_copy_is_discovered_with_a_new_id_and_source_is_untouched(ctx: Context) -> None:
    """A run copy gets a fresh id, keeps its data, and the source is left exactly as it was."""
    source = make_run(ctx.logdir, "proj/a")
    before = (source / c.METRICS).read_bytes()
    answer = call("cp", {"source": source.name, "dest": "proj/b"}, ctx)
    copy_dir = ctx.logdir / answer["path"]
    assert answer["id"] != source.name
    assert copy_dir.name == answer["id"]
    assert read_run_info(copy_dir).id == answer["id"]
    assert (copy_dir / c.METRICS).read_bytes() == before
    assert (copy_dir / c.CARD).read_bytes() == (source / c.CARD).read_bytes()
    assert (source / c.METRICS).read_bytes() == before
    assert read_run_info(source).id == source.name
    found = call("runs", {"from": "proj/b"}, ctx)
    assert answer["id"] in [row[0] for row in found["rows"]]


def test_copy_updates_proposal_membership(ctx: Context) -> None:
    """A copy keeps its own proposal entry, drops the old group's, and gains the new one's."""
    call("proposal set", {"group": "proj/source", "proposal": {"statement": "The source's claim."}}, ctx)
    call("proposal set", {"group": "proj/dest", "proposal": {"statement": "The dest's claim."}}, ctx)
    source_version = call("proposal show", {"group": "proj/source"}, ctx)["version"]
    source = make_run(
        ctx.logdir, "proj/source", proposals={".": "own-1", "proj/source": source_version}
    )
    (source / c.PROPOSAL / "own-1.yaml").parent.mkdir(exist_ok=True)
    (source / c.PROPOSAL / "own-1.yaml").write_text("schema: 1\nstatement: own claim\n")
    answer = call("cp", {"source": source.name, "dest": "proj/dest"}, ctx)
    info = read_run_info(ctx.logdir / answer["path"])
    assert info.proposals["."] == "own-1"
    assert "proj/source" not in info.proposals
    dest_version = call("proposal show", {"group": "proj/dest"}, ctx)["version"]
    assert info.proposals["proj/dest"] == dest_version


def test_checkpoint_path_is_unchanged_since_artifacts_travel_with_the_run(ctx: Context) -> None:
    """A checkpoint copied into ``artifacts/`` keeps its plain ``path`` record."""
    source = make_run(
        ctx.logdir,
        "proj/a",
        artifacts=[{"name": "best.ckpt", "path": "artifacts/best.ckpt", "kind": "checkpoint"}],
    )
    (source / "artifacts").mkdir()
    (source / "artifacts" / "best.ckpt").write_bytes(b"weights")
    answer = call("cp", {"source": source.name, "dest": "proj/b"}, ctx)
    copy_dir = ctx.logdir / answer["path"]
    rows = checkpoints(ctx, copy_dir)
    assert rows == [
        {
            "name": "best.ckpt",
            "kind": "checkpoint",
            "score": None,
            "location": str(copy_dir / "artifacts" / "best.ckpt"),
            "exists": True,
            "via": "path",
        }
    ]


def test_checkpoint_uri_outside_the_run_is_unchanged_by_default(ctx: Context) -> None:
    """A checkpoint referenced outside the run (``uri``) is left exactly as recorded."""
    external = ctx.logdir / "elsewhere.ckpt"
    external.write_bytes(b"weights")
    source = make_run(
        ctx.logdir,
        "proj/a",
        artifacts=[{"name": "x.ckpt", "uri": str(external), "kind": "checkpoint"}],
    )
    answer = call("cp", {"source": source.name, "dest": "proj/b"}, ctx)
    rows = checkpoints(ctx, ctx.logdir / answer["path"])
    assert rows[0] == {
        "name": "x.ckpt",
        "kind": "checkpoint",
        "score": None,
        "location": str(external),
        "exists": True,
        "via": "uri",
    }


def test_checkpoint_uri_outside_with_checkpoints_copies_the_file_in(ctx: Context) -> None:
    """``--with-checkpoints`` copies an externally referenced file in and rewrites to ``path``."""
    external = ctx.logdir / "elsewhere.ckpt"
    external.write_bytes(b"weights")
    source = make_run(
        ctx.logdir,
        "proj/a",
        artifacts=[{"name": "x.ckpt", "uri": str(external), "kind": "checkpoint"}],
    )
    answer = call("cp", {"source": source.name, "dest": "proj/b", "with_checkpoints": True}, ctx)
    copy_dir = ctx.logdir / answer["path"]
    rows = checkpoints(ctx, copy_dir)
    assert rows[0]["via"] == "path" and rows[0]["exists"]
    assert Path(rows[0]["location"]).read_bytes() == b"weights"
    assert copy_dir in Path(rows[0]["location"]).parents


def test_checkpoint_inside_source_checkpoints_gains_origin_by_default(ctx: Context) -> None:
    """A checkpoint inside the source's own ``checkpoints/`` keeps ``uri`` and gains ``origin``."""
    source = make_run(
        ctx.logdir,
        "proj/a",
        checkpoint_files={"last.ckpt": b"weights"},
    )
    (source / c.ARTIFACTS).write_bytes(
        json_line(
            {
                "name": "last.ckpt",
                "uri": str(source / "checkpoints" / "last.ckpt"),
                "kind": "checkpoint",
                "score": 0.9,
                "monitor": "val/acc",
            }
        )
    )
    answer = call("cp", {"source": source.name, "dest": "proj/b"}, ctx)
    copy_dir = ctx.logdir / answer["path"]
    rows = checkpoints(ctx, copy_dir)
    assert rows[0]["via"] == "origin" and rows[0]["exists"] and rows[0]["score"] == 0.9
    assert rows[0]["location"] == str(source / "checkpoints" / "last.ckpt")


def test_checkpoint_file_with_no_record_gets_one(ctx: Context) -> None:
    """A file sitting in ``checkpoints/`` with no artifact record gets a synthetic one."""
    source = make_run(ctx.logdir, "proj/a", checkpoint_files={"stray.ckpt": b"weights"}, artifacts=[])
    answer = call("cp", {"source": source.name, "dest": "proj/b"}, ctx)
    rows = checkpoints(ctx, ctx.logdir / answer["path"])
    assert rows[0]["name"] == "stray.ckpt" and rows[0]["via"] == "origin" and rows[0]["exists"]


def test_copy_of_a_copy_resolves_to_the_original_holder(ctx: Context) -> None:
    """Copying a copy keeps citing the run that truly holds the checkpoint file."""
    source = make_run(ctx.logdir, "proj/a", checkpoint_files={"stray.ckpt": b"weights"}, artifacts=[])
    b = ctx.logdir / call("cp", {"source": source.name, "dest": "proj/b"}, ctx)["path"]
    c_ = ctx.logdir / call("cp", {"source": b.name, "dest": "proj/c"}, ctx)["path"]
    rows = checkpoints(ctx, c_)
    assert rows[0]["via"] == "origin" and rows[0]["location"] == str(
        source / "checkpoints" / "stray.ckpt"
    )
    assert rows[0]["exists"]


def test_checkpoint_resolves_after_the_source_group_moves(ctx: Context) -> None:
    """An ``origin`` reference is by id, so it survives moving the source's group."""
    source = make_run(ctx.logdir, "proj/a", checkpoint_files={"stray.ckpt": b"weights"}, artifacts=[])
    copy = ctx.logdir / call("cp", {"source": source.name, "dest": "proj/b"}, ctx)["path"]
    call("mv", {"source": "proj/a", "to": "proj/moved"}, ctx)
    rows = checkpoints(ctx, copy)
    assert rows[0]["exists"] and rows[0]["location"] == str(
        ctx.logdir / "proj" / "moved" / source.name / "checkpoints" / "stray.ckpt"
    )


def test_deleted_source_gives_exists_false_and_rm_lists_the_copy(ctx: Context) -> None:
    """Removing the source doesn't block its copies, but ``rm`` names the ones that reference it."""
    source = make_run(ctx.logdir, "proj/a", checkpoint_files={"stray.ckpt": b"weights"}, artifacts=[])
    copy = ctx.logdir / call("cp", {"source": source.name, "dest": "proj/b"}, ctx)["path"]
    removed = call("rm", {"target": source.name}, ctx)
    assert any(copy.name in line for line in removed["lines"])
    rows = checkpoints(ctx, copy)
    assert rows[0]["exists"] is False


def test_with_checkpoints_leaves_no_reference_to_the_source(ctx: Context) -> None:
    """``--with-checkpoints`` always produces a self-contained copy, from any starting case."""
    source = make_run(ctx.logdir, "proj/a", checkpoint_files={"last.ckpt": b"weights"})
    (source / c.ARTIFACTS).write_bytes(
        json_line(
            {
                "name": "last.ckpt",
                "uri": str(source / "checkpoints" / "last.ckpt"),
                "kind": "checkpoint",
            }
        )
    )
    answer = call("cp", {"source": source.name, "dest": "proj/b", "with_checkpoints": True}, ctx)
    copy_dir = ctx.logdir / answer["path"]
    rows = checkpoints(ctx, copy_dir)
    assert rows[0]["via"] == "path" and rows[0]["exists"]
    record = json.loads((copy_dir / c.ARTIFACTS).read_bytes())
    assert "origin" not in record and "uri" not in record and record["path"] == "checkpoints/last.ckpt"


def test_resume_warns_about_a_shared_dirpath(ctx: Context) -> None:
    """``resume`` warns when its recorded ``--dirpath`` is where a referenced checkpoint lives."""
    shared = ctx.logdir / "scratch" / "ckpt"
    shared.mkdir(parents=True)
    (shared / "last.ckpt").write_bytes(b"weights")
    source = make_run(
        ctx.logdir,
        "proj/a",
        artifacts=[{"name": "last.ckpt", "uri": str(shared / "last.ckpt"), "kind": "checkpoint"}],
        command=["python", "train.py", "--dirpath", str(shared)],
    )
    answer = call("cp", {"source": source.name, "dest": "proj/b"}, ctx)
    resumed = call("resume", {"run": answer["id"]}, ctx)
    assert "where the source's are" in resumed["warning"]


def test_resume_does_not_warn_when_dirpath_differs(ctx: Context) -> None:
    """No warning when the resumed run's ``--dirpath`` isn't where a checkpoint lives."""
    elsewhere = ctx.logdir / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "last.ckpt").write_bytes(b"weights")
    source = make_run(
        ctx.logdir,
        "proj/a",
        artifacts=[{"name": "last.ckpt", "uri": str(elsewhere / "last.ckpt"), "kind": "checkpoint"}],
        command=["python", "train.py", "--dirpath", str(ctx.logdir / "scratch" / "ckpt")],
    )
    answer = call("cp", {"source": source.name, "dest": "proj/b"}, ctx)
    resumed = call("resume", {"run": answer["id"]}, ctx)
    assert resumed["warning"] is None


def test_cp_refuses_a_running_run(ctx: Context) -> None:
    """A running run can't be copied, like ``mv``."""
    source = make_run(ctx.logdir, "proj/a", status="running")
    with pytest.raises(OpError, match="running"):
        call("cp", {"source": source.name, "dest": "proj/b"}, ctx)


def test_cp_refuses_inside_a_run_or_a_reserved_name(ctx: Context) -> None:
    """The destination can't be a reserved name or land inside an existing run."""
    source = make_run(ctx.logdir, "proj/a")
    other = make_run(ctx.logdir, "proj/other")
    with pytest.raises(OpError, match="reserved"):
        call("cp", {"source": source.name, "dest": "notes"}, ctx)
    with pytest.raises(OpError, match="inside a run"):
        call("cp", {"source": source.name, "dest": f"proj/other/{other.name}/x"}, ctx)


def test_cp_refuses_across_sources(ctx: Context) -> None:
    """``cp`` works within one source for now; across sources, ``pull`` is pointed to."""
    with pytest.raises(OpError, match="pull"):
        call("cp", {"source": "@cluster/a", "dest": "proj/b"}, ctx)


def test_a_crash_before_the_rename_leaves_nothing_visible_and_gc_removes_it(ctx: Context) -> None:
    """A ``cp`` working directory that never got renamed is invisible, and ``gc`` clears it."""
    stray = ctx.logdir / "proj" / f"{TEMP_PREFIX}leftover"
    stray.mkdir(parents=True)
    (stray / "file.txt").write_text("partial")
    found = call("runs", {"from": "proj"}, ctx)
    assert all("leftover" not in row[0] for row in found["rows"])
    preview = call("gc", {}, ctx)
    assert str(stray.relative_to(ctx.logdir)) in preview["lines"]
    done = call("gc", {"yes": True}, ctx)
    assert not stray.exists()
    assert done["deleted"]


def test_group_copy_gets_new_ids_and_keeps_subfolders(ctx: Context) -> None:
    """Copying a group copies every run below it, under new ids, in the same subfolders."""
    a = make_run(ctx.logdir, "proj/sweep/sub")
    b = make_run(ctx.logdir, "proj/sweep")
    answer = call("cp", {"source": "proj/sweep", "dest": "proj/archive"}, ctx)
    dest_root = ctx.logdir / answer["path"]
    assert dest_root.name == "sweep"
    assert (dest_root / "sub").is_dir()
    found = call("runs", {"from": "proj/archive"}, ctx)
    ids = {row[0] for row in found["rows"]}
    assert ids == set(answer["runs"]) and a.name not in ids and b.name not in ids


def test_group_copy_with_record_copies_authored_folders(ctx: Context) -> None:
    """``--with-record`` also copies the group's own notes, still citing the old run ids."""
    make_run(ctx.logdir, "proj/sweep")
    call("note add", {"group": "proj/sweep", "type": "idea", "description": "a note"}, ctx)
    answer = call(
        "cp", {"source": "proj/sweep", "dest": "proj/archive", "with_record": True}, ctx
    )
    dest_root = ctx.logdir / answer["path"]
    assert (dest_root / c.NOTES).is_dir()
    assert list((dest_root / c.NOTES).glob("*.md"))


def test_group_copy_reports_a_name_for_the_destination(ctx: Context) -> None:
    """``--name`` picks the destination group's own folder name."""
    make_run(ctx.logdir, "proj/sweep")
    answer = call(
        "cp", {"source": "proj/sweep", "dest": "proj/archive", "name": "renamed"}, ctx
    )
    assert answer["path"] == "proj/archive/renamed"
