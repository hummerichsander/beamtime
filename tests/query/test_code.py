import time
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.ids import new_run_id
from beamtime.format.io import write_replaced
from beamtime.format.times import iso
from beamtime.ops import call
from beamtime.ops.context import Context


def make_run(logdir: Path, folder: str, *, git: dict[str, Any], proposals: dict[str, str]) -> Path:
    """Build a minimal finished run with a given git block and proposal membership.

    :param logdir: The log dir.
    :param folder: The group below the log dir.
    :param git: The run's ``git`` block.
    :param proposals: Group (``.`` for its own) to recorded proposal version.
    :return: The run directory."""
    run_dir = logdir / folder / new_run_id()
    run_dir.mkdir(parents=True)
    now = iso(time.time(), ms=True)
    write_replaced(
        run_dir / c.RUN,
        {
            "schema": 1,
            "id": run_dir.name,
            "name": "test-run",
            "tags": [],
            "status": "finished",
            "created_at": now,
            "ended_at": now,
            "exit": None,
            "attempts": [{"started_at": now, "host": "h", "resume_step": None}],
            "proposals": proposals,
            "proposal_hashes": {},
            "job_key": None,
            "host": {"hostname": "h"},
            "scheduler": None,
            "git": git,
            "command": ["python"],
            "cwd": "/x",
            "beamtime_version": "0.0.0",
        },
    )
    (run_dir / c.METRICS).write_bytes(b'{"_step":0,"_t":0.0,"x":1.0}\n')
    return run_dir


def test_keys_names_a_group_fact_only_when_code_differs(ctx: Context) -> None:
    """``keys`` lists code versions by count, but only when a group's runs don't agree."""
    same = {"commit": "f385eda0", "branch": "main", "dirty": False}
    make_run(ctx.logdir, "same", git=same, proposals={})
    make_run(ctx.logdir, "same", git=same, proposals={})
    assert call("keys", {"from": "same"}, ctx)["codes"] == {}

    make_run(ctx.logdir, "mixed", git=same, proposals={})
    make_run(
        ctx.logdir,
        "mixed",
        git={"commit": "f385eda0", "branch": "main", "dirty": True, "diff_sha": "1a2b3c4d"},
        proposals={},
    )
    codes = call("keys", {"from": "mixed"}, ctx)["codes"]
    assert codes == {"f385eda": 1, "f385eda+1a2b3c4d": 1}


def test_check_notes_differing_code_among_members(ctx: Context) -> None:
    """A proposal's check names it when its members didn't all run on the same code."""
    saved = call("proposal set", {"group": "codegroup", "proposal": {"statement": "s"}}, ctx)
    version = saved["version"]
    make_run(
        ctx.logdir,
        "codegroup",
        git={"commit": "f385eda0", "branch": "main", "dirty": False},
        proposals={".": "own-a", "codegroup": version},
    )
    make_run(
        ctx.logdir,
        "codegroup",
        git={"commit": "1a2b3c4d", "branch": "main", "dirty": False},
        proposals={".": "own-b", "codegroup": version},
    )
    result = call("check", {"group": "codegroup"}, ctx)
    assert result["note"] == "its members ran on 2 different code versions"
