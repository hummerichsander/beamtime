import json
from pathlib import Path

import pytest

from beamtime.format import constants as c
from beamtime.ops import call
from beamtime.ops.authored import save
from beamtime.ops.context import Context, OpError
from beamtime.ops.record import dump

TOKENIZER = "tokenizer/bpe-vs-unigram"
CONTEXT = "scaling/long-context"
NEW = {"statement": "A replacement nobody recorded yet."}


def runs_of(logdir: Path, group: str) -> list[Path]:
    """List the run directories directly in a group.

    :param logdir: The log dir.
    :param group: The group.
    :return: The run directories, sorted."""
    return sorted(p.parent for p in (logdir / group).glob("*/_run.json"))


def seed_of(run_dir: Path) -> int:
    """Read a run's seed.

    :param run_dir: The run directory.
    :return: ``config.seed``."""
    return json.loads((run_dir / "_config.json").read_text(encoding="utf-8"))["seed"]


def set_hidden(run_dir: Path, hidden: bool) -> None:
    """Write a new visibility version for a run.

    :param run_dir: The run directory.
    :param hidden: The state it should have."""
    text = dump({"schema": 1, "hidden": hidden, "author": "test", "user": "test"})
    save(run_dir / c.VISIBILITY, ".yaml", text)


def hide_seeds(logdir: Path, *, keep: int) -> list[Path]:
    """Hide the runs of the tokenizer group whose seed is not below ``keep``.

    :param logdir: The log dir.
    :param keep: How many seeds per arm stay visible.
    :return: The hidden runs."""
    hidden = [r for r in runs_of(logdir, TOKENIZER) if seed_of(r) >= keep]
    for run_dir in hidden:
        set_hidden(run_dir, True)
    return hidden


def test_hidden_seed_is_not_counted(ctx: Context) -> None:
    """A hidden third seed leaves two runs per arm, and its promotion brings the third back."""
    hidden = hide_seeds(ctx.logdir, keep=2)
    assert len(hidden) == 2
    result = call("check", {"group": TOKENIZER}, ctx)
    assert result["predictions"][0]["n"] == {"a": 2, "b": 2}
    assert call("proposal show", {"group": TOKENIZER}, ctx)["versions"][0]["runs"] == 4
    for run_dir in hidden:
        set_hidden(run_dir, False)
    result = call("check", {"group": TOKENIZER}, ctx)
    assert result["predictions"][0]["n"] == {"a": 3, "b": 3}


def test_hidden_runs_leave_the_check_insufficient(ctx: Context) -> None:
    """With one visible run per arm the compare is insufficient; promoting changes the check."""
    hidden = hide_seeds(ctx.logdir, keep=1)
    first = call("check", {"group": TOKENIZER}, ctx)["predictions"][0]
    assert first["result"] == "insufficient" and first["n"] == {"a": 1, "b": 1}
    for run_dir in hidden:
        set_hidden(run_dir, False)
    after = call("check", {"group": TOKENIZER}, ctx)["predictions"][0]
    assert after["result"] != "insufficient" and after["n"] == {"a": 3, "b": 3}


def test_group_of_hidden_runs_is_proposed_and_unfrozen(ctx: Context) -> None:
    """A group whose only runs are hidden has no members: its proposal can be replaced freely,
    and after a visibility file the version is frozen."""
    runs = runs_of(ctx.logdir, CONTEXT)
    for run_dir in runs:
        set_hidden(run_dir, True)
    shown = call("proposal show", {"group": CONTEXT}, ctx)
    assert shown["status"] == "proposed" and shown["versions"][0]["frozen"] is False
    assert shown["versions"][0]["runs"] == 0
    for run_dir in runs:
        set_hidden(run_dir, False)
    shown = call("proposal show", {"group": CONTEXT}, ctx)
    assert shown["versions"][0]["frozen"] is True and shown["versions"][0]["runs"] == len(runs)
    with pytest.raises(OpError, match="frozen") as e:
        call("proposal set", {"group": CONTEXT, "proposal": NEW}, ctx)
    assert e.value.code == 3


def test_hidden_only_group_takes_a_new_proposal_without_reason(ctx: Context) -> None:
    """``proposal set`` without ``--reason`` replaces a version only hidden runs recorded."""
    for run_dir in runs_of(ctx.logdir, CONTEXT):
        set_hidden(run_dir, True)
    out = call("proposal set", {"group": CONTEXT, "proposal": NEW}, ctx)
    assert any("which no run had recorded" in line for line in out["lines"])


def test_hidden_reference(ctx: Context) -> None:
    """A ``ref`` naming a hidden run reads as missing."""
    from beamtime.index.index import Index
    from beamtime.record.check import reference
    from beamtime.record.proposals import Target

    run_dir = runs_of(ctx.logdir, TOKENIZER)[0]
    with Index(logdir=ctx.logdir, settings=ctx.settings) as index:
        index.catch_up(".", budget_s=float("inf"))
        target = Target(index=index, rel=TOKENIZER, run_id=None)
        assert reference(target, run_dir.name, "metric.val/ppl.last") is not None
        set_hidden(run_dir, True)
        index.catch_up(".", budget_s=float("inf"))
        assert reference(target, run_dir.name, "metric.val/ppl.last") is None


def test_hidden_plan_point(ctx: Context) -> None:
    """A grid point whose only run is hidden is still missing, and progress ignores the run."""
    before = call("plan missing", {"group": TOKENIZER}, ctx)
    assert before["missing"] == 0
    hidden = [r for r in runs_of(ctx.logdir, TOKENIZER) if seed_of(r) == 0]
    for run_dir in hidden:
        set_hidden(run_dir, True)
    after = call("plan missing", {"group": TOKENIZER}, ctx)
    assert after["missing"] == 2
    assert {e["config"]["seed"] for e in after["entries"]} == {0}


def test_hidden_run_own_proposal(ctx: Context) -> None:
    """A hidden run named by id still answers for its own proposal, which freezes only once the
    run is promoted."""
    run_dir = runs_of(ctx.logdir, TOKENIZER)[0]
    set_hidden(run_dir, True)
    call("proposal set", {"group": run_dir.name, "proposal": NEW}, ctx)
    shown = call("proposal show", {"group": run_dir.name}, ctx)
    assert shown["status"] != "open" and shown["versions"][0]["frozen"] is False
    call("proposal set", {"group": run_dir.name, "proposal": NEW}, ctx)
    set_hidden(run_dir, False)
    shown = call("proposal show", {"group": run_dir.name}, ctx)
    assert shown["versions"][0]["frozen"] is True
    with pytest.raises(OpError, match="frozen"):
        call("proposal set", {"group": run_dir.name, "proposal": NEW}, ctx)
