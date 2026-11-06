import asyncio
import json
import time
from pathlib import Path

from beamtime.format.io import json_line
from beamtime.format.tree import iter_runs
from beamtime.index.daemon import Daemon
from beamtime.index.index import Index
from beamtime.serve.live import Hub, affects

ALL = ["metrics", "status", "authored"]


def test_affects() -> None:
    """A run's change reaches its groups; a group's change reaches what is below it."""
    run = "scaling/lr-sweep/20261020-080300-ysdn9hmc"
    assert affects(run, run) and affects(run, "scaling/lr-sweep") and affects(run, "scaling")
    assert affects(run, ".")
    assert not affects(run, "scaling/long-context") and not affects(run, "tokenizer")
    assert not affects(run, "scaling/lr")
    assert affects("scaling/lr-sweep", run) and affects("scaling/lr-sweep", "scaling")
    assert affects(".", "tokenizer")


def test_hub_sends_only_affected_calls_at_most_once_a_second() -> None:
    """Stale ids reach the page that watches them, merged and throttled."""

    async def scenario() -> list[str]:
        hub = Hub()
        hub.bind()
        hub.watch(
            "p",
            {"sweep": ["scaling/lr-sweep", ALL], "tok": ["tokenizer", ALL], "all": [".", ALL]},
        )
        stream = hub.stream("p")
        events = [await anext(stream)]
        hub.changed({"scaling/lr-sweep/r1": {"metrics"}})
        events.append(await asyncio.wait_for(anext(stream), 2))
        start = time.monotonic()
        hub.changed({"tokenizer/x/r2": {"status"}})
        await asyncio.sleep(0.05)
        hub.changed({"tokenizer/x/r3": {"status"}})
        events.append(await asyncio.wait_for(anext(stream), 3))
        assert time.monotonic() - start >= 0.9
        hub.close()
        await stream.aclose()
        assert hub.clients == {}
        return events

    hello, first, second = asyncio.run(scenario())
    assert hello.startswith("event: hello")
    assert json.loads(first.split("data: ")[1]) == ["all", "sweep"]
    assert json.loads(second.split("data: ")[1]) == ["all", "tok"]


def test_hub_filters_by_kind() -> None:
    """A page watching only authored changes doesn't wake for a metrics-only change."""

    async def scenario() -> set[str]:
        hub = Hub()
        hub.bind()
        hub.watch(
            "p",
            {"notes": ["scaling/lr-sweep", ["authored"]], "chart": ["scaling/lr-sweep", ["metrics"]]},
        )
        stream = hub.stream("p")
        await anext(stream)
        hub.changed({"scaling/lr-sweep/r1": {"metrics"}})
        event = await asyncio.wait_for(anext(stream), 2)
        hub.close()
        await stream.aclose()
        return set(json.loads(event.split("data: ")[1]))

    assert asyncio.run(scenario()) == {"chart"}


def test_daemon_reports_changed_runs_and_groups(project: Path) -> None:
    """New metric lines, new group and run notes and new proposal versions are reported by path
    and kind."""
    logdir = project / "beamtime"
    seen: list[dict[str, set[str]]] = []
    daemon = Daemon(logdir=logdir, on_change=seen.append, poll_s=0.1)
    assert daemon.start()
    try:
        wait_for(lambda: seen)
        seen.clear()
        run = next(r for r in iter_runs(logdir / "scaling" / "long-context")
                   if json.loads((r / "_run.json").read_text())["status"] == "running")  # fmt: skip
        with (run / "_metrics.jsonl").open("ab") as f:
            f.write(json_line({"_step": 9999, "_t": time.time(), "train/loss": 0.5}))
        (run / "_run.json").touch()
        rel = run.relative_to(logdir).as_posix()
        wait_for(lambda: any(rel in d and "metrics" in d[rel] for d in seen))

        seen.clear()
        notes = logdir / "tokenizer" / "notes"
        notes.mkdir(exist_ok=True)
        (notes / "20261027-120000-abcd.md").write_text(
            "---\nschema: 1\ntype: observation\ndescription: x\nauthor: t\nuser: t\n---\nx\n"
        )
        wait_for(lambda: any("tokenizer" in d and "authored" in d["tokenizer"] for d in seen))

        seen.clear()
        notes = run / "notes"
        notes.mkdir(exist_ok=True)
        (notes / "20261027-120000-efgh.md").write_text(
            "---\nschema: 1\ntype: observation\ndescription: x\nauthor: t\nuser: t\n---\nx\n"
        )
        wait_for(lambda: any(rel in d and "authored" in d[rel] for d in seen))

        seen.clear()
        proposal = logdir / "scaling" / "lr-sweep" / "proposal"
        (proposal / "20261027-120000-wxyz.yaml").write_text("schema: 1\nstatement: x\n")
        wait_for(lambda: any(
            "scaling/lr-sweep" in d and "authored" in d["scaling/lr-sweep"] for d in seen
        ))
    finally:
        daemon.stop()


def test_clients_collect_runs_but_not_groups(project: Path) -> None:
    """Outside the daemon, catch-up names ingested runs only."""
    index = Index(logdir=project / "beamtime")
    try:
        fresh = index.catch_up(".", budget_s=float("inf"))
        assert fresh.changed and all(len(p.split("/")) == 3 for p in fresh.changed)
        assert index.catch_up(".", budget_s=float("inf")).changed == {}
    finally:
        index.close()


def wait_for(condition, timeout: float = 10.0) -> None:
    """Poll a condition until it holds.

    :param condition: A function returning a truthy value when done.
    :param timeout: Seconds to wait at most."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return
        time.sleep(0.05)
    raise AssertionError("condition not met in time")
