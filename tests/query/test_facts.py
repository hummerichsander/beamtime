import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from beamtime.format.run import read_config
from beamtime.index.index import Index
from beamtime.ops.context import Context, OpError
from beamtime.ops.reading import run_members
from beamtime.query import QueryError
from beamtime.query.distinguish import flatten
from beamtime.query.facts import RunFacts, failure_key, run_facts
from beamtime.query.resolve import resolve


@pytest.fixture
def index(ctx: Context) -> Iterator[Index]:
    """A fully caught-up index of the project's log dir.

    :param ctx: The operation context.
    :return: The index, closed after the test."""
    with Index(logdir=ctx.logdir) as index:
        index.catch_up(".", budget_s=float("inf"))
        yield index


def facts(index: Index, target: str = ".", **kwargs) -> list[RunFacts]:
    """Run ``run_facts`` on a target at the current time.

    :param index: The index.
    :param target: A group or run.
    :param kwargs: Further ``run_facts`` arguments.
    :return: The facts."""
    found = resolve(index, target)
    kwargs.setdefault("now", time.time())
    return run_facts(index, scope=found.path, run_id=found.run_id, **kwargs)


def test_facts_of_a_group_and_a_run(index: Index, roles: dict[str, str]) -> None:
    """A group lists all its runs; a run id lists the one run."""
    everything = facts(index)
    assert len(everything) == len({f.id for f in everything}) > 20
    one = facts(index, roles["killed"])
    assert [f.id for f in one] == [roles["killed"]]
    assert one[0].status == "killed" and one[0].dir == index.logdir / one[0].path
    assert facts(index, "scaling", depth=1) == []
    assert 0 < len(facts(index, "scaling", depth=2)) <= len(facts(index, "scaling"))


def test_status_is_derived_at_now(index: Index) -> None:
    """A running run is lost once its heartbeat is older than the lost rule at ``now``."""
    assert any(f.status == "running" for f in facts(index))
    later = facts(index, now=time.time() + 10**7)
    assert not any(f.status == "running" for f in later)
    assert any(f.status == "lost" for f in later)


def test_where_filters(index: Index) -> None:
    """``where`` keeps the runs that meet it, with the query language's conditions."""
    failed = facts(index, where={"run.status": "failed"})
    assert failed and {f.status for f in failed} == {"failed"}
    many = facts(index, where={"run.attempts": {"gt": 1}})
    assert many and all(f.attempts > 1 for f in many)


def test_config_and_metrics_only_when_asked(index: Index, roles: dict[str, str]) -> None:
    """Without the flags both are ``None``; with them they hold the run's values."""
    plain = facts(index, roles["resumed"])[0]
    assert plain.config is None and plain.metrics is None
    full = facts(index, roles["resumed"], config=True, metrics=True)[0]
    assert full.config and full.metrics
    assert all("last" in stats for stats in full.metrics.values())


def test_config_flattened(index: Index) -> None:
    """The config is flattened as ``read_config`` plus ``flatten`` do for the file."""
    for f in facts(index, "scaling/lr-sweep", config=True):
        assert f.config == flatten(read_config(f.dir))


def test_attempts_and_last_logged(index: Index, roles: dict[str, str]) -> None:
    """A resumed run counts two attempts; ``last_logged`` is the metrics file's mtime."""
    resumed = facts(index, roles["resumed"])[0]
    assert resumed.attempts == 2
    assert resumed.last_logged == (resumed.dir / "_metrics.jsonl").stat().st_mtime
    assert facts(index, roles["killed"])[0].attempts == 1


def test_a_bad_target_or_field_raises_query_error(index: Index) -> None:
    """An unknown group fails in ``resolve``, an unknown field in ``where`` in ``run_facts``."""
    with pytest.raises(QueryError):
        facts(index, "no-such-group")
    with pytest.raises(QueryError):
        facts(index, where={"run.nonsense": 1})


def test_run_members_maps_errors_to_op_errors(ctx: Context, roles: dict[str, str]) -> None:
    """``run_members`` resolves the target and speaks ``OpError``."""
    with pytest.raises(OpError) as e:
        run_members(ctx, "no-such-group")
    assert e.value.code == 4
    with pytest.raises(OpError) as e:
        run_members(ctx, ".", {"run.nonsense": 1})
    assert e.value.code == 2
    assert [f.id for f in run_members(ctx, roles["killed"])] == [roles["killed"]]


def test_one_index_and_one_catch_up_per_call(
    ctx: Context, roles: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A call opens the index once and catches up once, whatever the target."""
    opened, caught = [], []
    init, catch_up = Index.__init__, Index.catch_up

    def counting_init(self: Index, *args, **kwargs) -> None:
        opened.append(1)
        init(self, *args, **kwargs)

    def counting_catch_up(self: Index, *args, **kwargs):
        caught.append(1)
        return catch_up(self, *args, **kwargs)

    with Index(logdir=ctx.logdir) as warm:
        warm.catch_up(".", budget_s=float("inf"))
    monkeypatch.setattr(Index, "__init__", counting_init)
    monkeypatch.setattr(Index, "catch_up", counting_catch_up)
    for target in (".", "scaling", roles["killed"]):
        opened.clear()
        caught.clear()
        run_members(ctx, target, config=True, metrics=True)
        assert (len(opened), len(caught)) == (1, 1)


def test_facts_from_index_only(
    ctx: Context, index: Index, roles: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Config and metrics come from the index: they survive deleting the run files."""
    before = facts(index, "scaling/lr-sweep", config=True, metrics=True)
    for path in ctx.logdir.rglob("_run_card.json"):
        path.unlink()
    for path in ctx.logdir.rglob("_config.json"):
        path.unlink()
    monkeypatch.setattr(Index, "catch_up", lambda self, *args, **kwargs: None)
    after = facts(index, "scaling/lr-sweep", config=True, metrics=True)
    assert after == before and any(f.metrics for f in after)


def test_failure_key() -> None:
    """The recorded error leads; the traceback's exception line is the fallback."""
    trace = ["Traceback (most recent call last):", "FloatingPointError: loss is inf at step 12"]
    assert (
        failure_key("RuntimeError: out of memory 40 GB", trace)
        == "RuntimeError: out of memory # GB"
    )
    assert failure_key(None, trace) == "FloatingPointError: loss is inf at step #"
    assert failure_key("", trace) == "FloatingPointError: loss is inf at step #"
    assert failure_key(None, None) == "" and failure_key(None, []) == ""
    assert failure_key("a\nValueError: x 0x1f", None) == "ValueError: x #"


def test_failure_signature_ignores_paths_and_quotes() -> None:
    """Runs of one failure share a signature whatever paths and quotes their message holds."""
    quoted = "FileNotFoundError: [Errno 2] No such file or directory: '/scratch/a/run{}.pt'"
    assert failure_key(quoted.format(1), None) == failure_key(quoted.format(2), None)
    assert failure_key("No such file: /scratch/a/run1.pt", None) == failure_key(
        "No such file: /scratch/b/run2.pt", None
    )
    assert failure_key('KeyError: "a"', None) == failure_key("KeyError: 'b'", None)
    assert failure_key("Missing C:\\data\\x.csv or ~/y or ../z", None) == (
        "Missing <path> or <path> or <path>"
    )


def test_failure_signature_sees_through_a_bare_exception() -> None:
    """A bare type on the last line carries the line before it."""
    trace = ["Traceback (most recent call last):", '  File "x.py", line 3, in f', "KeyError"]
    assert failure_key(None, trace) == "KeyError (after: File <str>, line #, in f)"
    other = [*trace[:1], '  File "x.py", line 9, in g', "KeyError"]
    assert failure_key(None, other) != failure_key(None, trace)
    assert failure_key("KeyError", None) == "KeyError"


def test_metric_names_are_no_paths() -> None:
    """A metric name without a leading slash stays as it is."""
    assert failure_key("RuntimeError: val/loss is nan", None) == "RuntimeError: val/loss is nan"


def test_apostrophe() -> None:
    """An apostrophe in prose does not eat the line."""
    assert failure_key("RuntimeError: can't find 3 files", None) == (
        "RuntimeError: can't find # files"
    )
    assert failure_key("Error: can't find 'x' in 3", None) == "Error: can't find <str> in #"


def test_logdir_is_untouched_by_facts(index: Index, ctx: Context) -> None:
    """Reading facts writes nothing under the log dir."""
    before = sorted(p for p in Path(ctx.logdir).rglob("*") if p.is_file())
    facts(index, config=True, metrics=True)
    assert sorted(p for p in Path(ctx.logdir).rglob("*") if p.is_file()) == before
