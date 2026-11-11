import dataclasses
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from beamtime.ops import budget
from beamtime.ops.context import Context, OpError
from beamtime.remote import answer as call
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
    assert runs["meta"]["sources"] == [{"name": ".", "state": "connected"},
                                       {"name": "@box", "state": "connected"}]  # fmt: skip
    # each source sends its newest rows; merged and cut, they are the newest of both.
    top = call("runs", {"from": ".", "limit": 4}, ctx)["rows"]
    every = sorted((r[0] for r in runs["rows"]), reverse=True)
    assert [r[0] for r in top] == every[:4]
    timeline = call("timeline", {"from": ".", "limit": 50}, ctx)["entries"]
    assert [e["t"] for e in timeline] == sorted(e["t"] for e in timeline)
    keys = call("keys", {"from": "."}, ctx)
    alone = call("keys", {"from": "."}, dataclasses.replace(ctx, sources=None))
    assert keys["runs"] > 0 and keys["runs"] == runs["meta"]["matched"]
    assert alone["runs"] < keys["runs"]


def test_aggregates_are_labelled_by_source(box: Path, ctx: Context) -> None:
    """Curves aggregated over a field are computed per source and say which."""
    curves = call("series", {"from": ".", "y": ["val/acc"], "by": ["config.lr"]}, ctx)["curves"]
    sources = {c["by"].get("source") for c in curves}
    assert sources == {".", "@box"}


def test_writes_land_on_the_remote(box: Path, ctx: Context, project: Path) -> None:
    """A note on @box is written by box into its own files, with this machine's author."""
    answer = call("note add", {"group": f"@box/{SWEEP}", "type": "observation",
                               "description": "Seen from the laptop."}, ctx)  # fmt: skip
    assert answer["path"].startswith(f"@box/{SWEEP}/notes/")
    written = box / answer["path"].removeprefix("@box/")
    assert "Seen from the laptop." in written.read_text()
    assert not (project / "beamtime" / answer["path"].removeprefix("@box/")).exists()
    notes = call("notes", {"from": ".", "limit": 5}, ctx)["entries"]
    assert (
        notes[0]["description"] == "Seen from the laptop." and notes[0]["group"] == f"@box/{SWEEP}"
    )


def test_runs_are_found_wherever_they_are(box: Path, ctx: Context) -> None:
    """A run id this machine doesn't know is looked up on the remotes."""
    run = call("runs", {"from": f"@box/{SWEEP}", "limit": 1}, ctx)["rows"][0][0]
    card = call("card", {"run": run}, ctx)
    assert card["run"]["id"] == run and card["run"]["path"].startswith(f"@box/{SWEEP}/")


def test_pages_of_remote_groups(box: Path, ctx: Context) -> None:
    """A remote group's view comes from the remote; its blocks' calls point back there."""
    view = dataclasses.replace(ctx, caller="view")
    page = dispatch(view, "view", {"path": f"@box/{SWEEP}"})
    assert page["path"] == f"@box/{SWEEP}"
    calls = [n["data"]["main"] for n in walk(page["view"]) if n.get("data", {}).get("main")]
    assert calls and all(c["scope"].startswith("@box") for c in calls)
    first = calls[0]
    answer = dispatch(view, first["method"], first["params"])
    assert answer["meta"].get("source", "@box") == "@box"


def test_errors_name_the_source(box: Path, ctx: Context, tmp_path: Path) -> None:
    """Unknown sources, unreachable ones and user commands on remote groups say what to do."""
    with pytest.raises(OpError, match="no source @nowhere"):
        call("runs", {"from": "@nowhere/x"}, ctx)
    with pytest.raises(OpError, match="user command"):
        call("rm", {"target": f"@box/{SWEEP}"}, ctx)
    broken = Spec(name="gone", path=str(tmp_path), command="false", transport="command")
    ctx.sources.clients.update(Sources([broken]).clients)
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
    assert (
        argv[-1]
        == "~/venvs/bt/bin/beamtime serve --stdio --logdir '${SCRATCH}/p b' --cache '/tmp/{user}'"
    )


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
    page = dispatch(dataclasses.replace(ctx, caller="view"), "view", {"path": f"@box/{run}"})
    assert page["path"] == f"@box/copied/{run}"


def test_remote_series_end_up_envelope_only_for_the_cli(box: Path, ctx: Context) -> None:
    """A remote answers with both field sets; the CLI and MCP get the envelope only, from one
    source or merged, and the web UI keeps both."""
    old = {"last", "min", "max", "count", "mean"}
    for target in (f"@box/{SWEEP}", "."):
        query = {"from": target, "y": ["train/loss"], "points": 20}
        for caller in ("cli", "mcp"):
            curves = call("series", query, dataclasses.replace(ctx, caller=caller))["curves"]
            assert curves and all("y" in c and not old & set(c) for c in curves), (target, caller)
        web = dispatch(dataclasses.replace(ctx, caller="view"), "series", query)["curves"]
        assert all({"y", "last"} <= set(c) for c in web if not c.get("raw")), target


def test_logged_files_of_remote_runs(box: Path, ctx: Context) -> None:
    """A remote's logged entries keep their run-relative paths; their files come from that remote."""
    from beamtime.remote.route import remote_file

    keys = call("keys", {"from": f"@box/{SWEEP}"}, ctx)["data"]["rows"]
    key = next(k for k, kind, *_ in keys if kind == "image")
    entries = call("data", {"from": f"@box/{SWEEP}", "key": key}, ctx)["entries"]
    with_file = [e for e in entries if e.get("path")]
    assert with_file and not with_file[0]["path"].startswith("@")
    e = with_file[0]
    content = remote_file(ctx, e["run"], e["path"], "box")
    run_dir = next(box.rglob(e["run"]))
    assert content == (run_dir / e["path"]).read_bytes()


HUNG = """
import json, sys
for line in sys.stdin:
    message = json.loads(line)
    if message["method"] == "hello":
        print(json.dumps({"id": message["id"], "result": {"version": "0"}}), flush=True)
"""


def test_a_hung_remote_is_left_out_of_listings(
    ctx: Context, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A remote that shakes hands but never answers delays a listing by the timeout, no more."""
    from beamtime.remote import route

    (tmp_path / "hung.py").write_text(HUNG)
    hung = Spec(name="hung", path=".", command=f"{sys.executable} {tmp_path / 'hung.py'}",
                transport="command")  # fmt: skip
    ctx.sources.clients.update(Sources([hung]).clients)
    monkeypatch.setattr(route, "LISTING_S", 0.5)
    started = time.monotonic()
    groups = call("groups", {"from": "."}, ctx)
    assert time.monotonic() - started < 10
    states = {s["name"]: s["state"] for s in groups["meta"]["sources"]}
    assert states == {".": "connected", "@box": "connected", "@hung": "unreachable"}
    assert any(r[0].startswith("@box") for r in groups["rows"])


def test_closing_fails_waiting_requests(tmp_path: Path) -> None:
    """A request waiting on a connection that closes fails at once instead of at its timeout."""
    import threading

    from beamtime.remote.client import RemoteClient, Unreachable

    (tmp_path / "hung.py").write_text(HUNG)
    client = RemoteClient(spec=Spec(name="hung", path=".", transport="command",
                                    command=f"{sys.executable} {tmp_path / 'hung.py'}"))  # fmt: skip
    with pytest.raises(Unreachable, match="didn't answer runs within"):
        client.request("runs", {}, timeout=0.3)
    threading.Timer(0.3, client.close).start()
    started = time.monotonic()
    with pytest.raises(Unreachable):
        client.request("runs", {}, timeout=30)
    assert time.monotonic() - started < 10


def test_the_proposal_block_answers_through_a_remote(box: Path, ctx: Context) -> None:
    """Both calls of a remote group's proposal block point at the remote and find the group."""
    from beamtime.ops.views import write_version
    from beamtime.views import model as m

    shown = m.parse({"body": [{"proposal": {}}]}, source="t")
    write_version(Context.make(root=box.parent, caller="cli"), SWEEP, shown, None, None)
    view = dataclasses.replace(ctx, caller="view")
    page = dispatch(view, "view", {"path": f"@box/{SWEEP}"})
    blocks = [n for n in walk(page["view"]) if n["block"] == "proposal"]
    assert blocks
    for call in blocks[0]["data"].values():
        assert call["params"]["group"] == f"@box/{SWEEP}" and call["scope"] == f"@box/{SWEEP}"
        assert dispatch(view, call["method"], call["params"])


def test_aggregated_runs_name_their_source(box: Path, ctx: Context) -> None:
    """runs --by over both sources keeps each source's groups and says where they come from."""
    out = call("runs", {"from": ".", "by": ["config.lr"]}, ctx)
    assert out["columns"][:2] == ["runs", "source"]
    assert {r[1] for r in out["rows"]} == {".", "@box"}
    sources = [r[1] for r in out["rows"]]
    assert sources == sorted(sources, key=lambda s: s != ".")


class OldRemote:
    """A remote of 0.2: its series curves carry the old fields only."""

    def __init__(self) -> None:
        """Remember how a remote is addressed."""
        self.spec = SimpleNamespace(scope=".")

    def request(self, method: str, params: dict, **_: Any) -> dict:
        """Answer every call with the pinned 0.2 series answer.

        :param method: The method.
        :param params: Its parameters.
        :return: The answer, in the old shape."""
        path = Path(__file__).parent / "fixtures" / "series-0.2.json"
        return json.loads(path.read_text())

    def close(self) -> None:
        """Hold no connection."""


@pytest.mark.parametrize("target", ["@box/g", "."])
@pytest.mark.parametrize("caller", ["cli", "mcp"])
def test_an_old_remotes_curves_reach_cli_and_mcp_with_values(
    ctx: Context, target: str, caller: str
) -> None:
    """The envelope is added on arrival, before the strip of the old fields, so a CLI or MCP
    caller gets values from a remote that only knows the old fields, single or federated."""
    old = {"last", "min", "max", "count", "mean"}
    ctx.sources.clients["box"] = OldRemote()
    ctx = dataclasses.replace(ctx, caller=caller)
    query = {"from": target, "y": ["train/loss"], "points": 5}
    curves = call("series", query, ctx)["curves"]
    remote = [c for c in curves if c.get("run") == "r0001aaaa" or c.get("runs")]
    assert len(remote) == 3
    for c in remote:
        assert not old & set(c) and c["y"] and len(c["y"]) == len(c["x"])
    down = next(c for c in remote if c["metric"] == "train/acc")
    assert (down["y"], down["lo"], down["hi"], down["n"]) == (
        [0.15, 0.4], [0.1, 0.3], [0.2, 0.5], [2, 2]
    )  # fmt: skip


class FakeClient:
    """A source that answers one list of group rows, or is down."""

    def __init__(self, rows: list[list[Any]] | None, *, cut: bool = False) -> None:
        """Remember what the source answers.

        :param rows: Its rows, or ``None`` for a source that is down.
        :param cut: Whether it is an old remote that ignores ``whole`` and cuts at its budget."""
        self.rows, self.cut, self.asked, self.whole = rows, cut, [], []
        self.spec = SimpleNamespace(scope=".")

    def request(
        self, method: str, params: dict, *, caller: str = "cli", whole: bool = False, **_: Any
    ) -> dict:
        """Answer like a remote's ``groups``, or fail; a current remote cuts unless asked whole.

        :param method: The method.
        :param params: Its parameters, remembered.
        :param caller: Whose defaults apply.
        :param whole: Whether the request line asks for the whole answer.
        :return: The answer."""
        self.asked.append(params)
        self.whole.append(whole)
        if self.rows is None:
            raise OpError("down", code=1)
        meta: dict[str, Any] = {"matched": len(self.rows)}
        if self.cut:
            meta |= {"cut": True, "next": "3", "hint": "answer cut"}
        answer = {"kind": "groups", "columns": ["path"], "rows": list(self.rows), "meta": meta}
        return answer if self.cut else budget.page(answer, None, caller=caller, whole=whole)


def page_of(rows: list[list[Any]], ctx: Context) -> dict:
    """Answer like this machine's ``groups``, paged for the context.

    :param rows: The local rows.
    :param ctx: The context the call runs in.
    :return: The answer."""
    answer = {"kind": "groups", "columns": ["path"], "rows": list(rows),
              "meta": {"matched": len(rows)}}  # fmt: skip
    return budget.page(answer, None, caller=ctx.caller, whole=ctx.whole)


def paged_groups(
    ctx: Context, local: list[list[Any]], *clients: FakeClient
) -> tuple[list[list[Any]], int]:
    """Follow ``meta.next`` over federated groups until it is absent.

    :param ctx: A context with this machine as a source.
    :param local: The local rows.
    :param clients: The remotes, named ``s0``, ``s1``, ...
    :return: Every row in the order the pages gave them, and the number of pages."""
    from beamtime.remote.route import federate

    sources = SimpleNamespace(clients={f"s{i}": c for i, c in enumerate(clients)})
    ctx = dataclasses.replace(ctx, sources=sources)
    seen: list[list[Any]] = []
    cursor = None

    def local_answer(params: dict, c: Context) -> dict:
        return page_of(local, c)

    for pages in range(1, 50):
        params = {"from": "."} | ({"cursor": cursor} if cursor else {})
        page = federate("groups", params, ctx, local_answer)
        seen += page["rows"]
        if (cursor := page["meta"].get("next")) is None:
            return seen, pages
    raise AssertionError("paging does not end")


@pytest.fixture
def small_pages(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cut every answer at 300 characters.

    :param monkeypatch: Pytest's monkeypatch."""
    monkeypatch.setitem(budget.cut.__kwdefaults__, "max_chars", 300)


def test_federated_pages_give_every_item_once(ctx: Context, small_pages: None) -> None:
    """Following the cursor lists both sources' items once, local first; matched is the sum."""
    local = [[f"local/{i:02d}"] for i in range(30)]
    one = FakeClient([[f"@s0/{i:02d}"] for i in range(30)])
    two = FakeClient([[f"@s1/{i:02d}"] for i in range(30)])
    rows, pages = paged_groups(ctx, local, one, two)
    assert pages > 1 and rows == [*local, *one.rows, *two.rows]
    assert all("cursor" not in p for p in one.asked + two.asked)
    assert all(one.whole + two.whole)


def test_paging_reaches_beyond_a_source_budget(ctx: Context, small_pages: None) -> None:
    """Every answer is larger than the budget, yet one walk of meta.next gives each row once."""
    from beamtime.remote.route import federate

    local = [[f"local/{i:02d}"] for i in range(30)]
    one = FakeClient([[f"@s0/{i:02d}"] for i in range(30)])
    two = FakeClient([[f"@s1/{i:02d}"] for i in range(30)])
    assert all(len(json.dumps(rows)) > 300 for rows in (local, one.rows, two.rows))
    sources = SimpleNamespace(clients={"s0": one, "s1": two})
    ctx = dataclasses.replace(ctx, sources=sources)
    seen, cursor = [], None
    for _ in range(50):
        params = {"from": "."} | ({"cursor": cursor} if cursor else {})
        page = federate("groups", params, ctx, lambda p, c: page_of(local, c))
        assert not any("cut" in s for s in page["meta"]["sources"])
        seen += page["rows"]
        if (cursor := page["meta"].get("next")) is None:
            break
    else:
        raise AssertionError("paging does not end")
    assert seen == [*local, *one.rows, *two.rows]


def test_federated_runs_page_through_local(box: Path, ctx: Context, small_pages: None) -> None:
    """Paging runs over . gives every run of this machine and of @box exactly once."""
    view = dataclasses.replace(ctx, caller="view")
    reference = [
        r[0]
        for answer in (
            call("runs", {"from": ".", "limit": 1000}, dataclasses.replace(view, sources=None)),
            call("runs", {"from": "@box", "limit": 1000}, view),
        )
        for r in answer["rows"]
    ]
    seen, cursor = [], None
    for _ in range(200):
        params = {"from": ".", "limit": 1000} | ({"cursor": cursor} if cursor else {})
        page = call("runs", params, ctx)
        seen += [r[0] for r in page["rows"]]
        if (cursor := page["meta"].get("next")) is None:
            break
    else:
        raise AssertionError("paging does not end")
    assert len(reference) > 40 and sorted(seen) == sorted(reference)
    assert len(set(seen)) == len(seen)


def test_whole_answer_is_capped(ctx: Context, monkeypatch: pytest.MonkeyPatch) -> None:
    """An answer over WHOLE_MAX_CHARS still carries meta.next, and the source is flagged cut."""
    from beamtime.remote.route import federate

    monkeypatch.setattr(budget, "WHOLE_MAX_CHARS", 200)
    big = FakeClient([[f"@s0/{i:02d}"] for i in range(30)])
    ctx = dataclasses.replace(ctx, sources=SimpleNamespace(clients={"s0": big}))
    local = [["a"], ["b"]]
    answer = federate("groups", {"from": "."}, ctx, lambda p, c: page_of(local, c))
    assert "cut" not in answer["meta"]["sources"][0]
    state = answer["meta"]["sources"][1]
    assert state["cut"] is True and state["hint"] == "narrow from or where to see all of @s0"
    assert answer["meta"]["cut"] is True and "next" not in answer["meta"]
    assert answer["meta"]["hint"] == "narrow from or where to see all of @s0"


def test_view_federation_is_whole(
    ctx: Context, small_pages: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The web UI gets every row of every source in one answer, whatever the budgets."""
    from beamtime.remote.route import federate

    monkeypatch.setattr(budget, "WHOLE_MAX_CHARS", 200)
    local = [[f"local/{i:02d}"] for i in range(30)]
    one = FakeClient([[f"@s0/{i:02d}"] for i in range(30)])
    ctx = dataclasses.replace(ctx, caller="view", sources=SimpleNamespace(clients={"s0": one}))
    answer = federate("groups", {"from": "."}, ctx, lambda p, c: page_of(local, c))
    assert answer["rows"] == [*local, *one.rows]
    assert "next" not in answer["meta"] and "cut" not in answer["meta"]


def test_a_source_that_cut_itself_says_so(ctx: Context) -> None:
    """A source's own cut shows in meta.sources with a hint; the merged answer has no stale cursor."""
    from beamtime.remote.route import federate

    cut = FakeClient([["@s0/a"], ["@s0/b"], ["@s0/c"]], cut=True)
    ctx = dataclasses.replace(ctx, sources=SimpleNamespace(clients={"s0": cut}))
    answer = federate("groups", {"from": "."}, ctx, lambda p, c: {
        "kind": "groups", "columns": ["path"], "rows": [["x"]], "meta": {"matched": 1}})  # fmt: skip
    state = answer["meta"]["sources"][1]
    assert state["cut"] is True and state["hint"] == "narrow from or where to see all of @s0"
    assert "cut" not in answer["meta"]["sources"][0]
    assert "next" not in answer["meta"] and answer["meta"]["matched"] == 4
    assert answer["meta"]["cut"] is True
    assert answer["meta"]["hint"] == "narrow from or where to see all of @s0"


def test_a_source_that_cut_itself_shows_in_the_cli_text(ctx: Context) -> None:
    """The text says where the missing items are, not to raise a limit that would not help."""
    from beamtime.cli.format import render
    from beamtime.remote.route import federate

    cut = FakeClient([["@s0/a"], ["@s0/b"]], cut=True)
    ctx = dataclasses.replace(ctx, sources=SimpleNamespace(clients={"s0": cut}))
    answer = federate("groups", {"from": "."}, ctx, lambda p, c: {
        "kind": "groups", "columns": ["path"], "rows": [["x"]], "meta": {"matched": 1}})  # fmt: skip
    last = render(answer).splitlines()[-1]
    assert last.endswith("narrow from or where to see all of @s0")
    assert "--limit" not in last


def test_local_answers_name_this_machine_with_a_dot(ctx: Context) -> None:
    """meta.source and the sources of a status say `.` for this machine, `@name` for a remote."""
    local = dataclasses.replace(ctx, sources=None)
    assert call("groups", {"from": "."}, local)["meta"]["source"] == "."
    assert [s["name"] for s in call("status", {}, ctx)["sources"]] == [".", "@box"]


def test_bad_cursor(ctx: Context) -> None:
    """A cursor Beamtime did not give out is refused with code 2, as for one source."""
    from beamtime.remote.route import federate

    source = FakeClient([["a"]])
    ctx = dataclasses.replace(ctx, sources=SimpleNamespace(clients={"s0": source}))
    with pytest.raises(OpError) as raised:
        federate("groups", {"from": ".", "cursor": "zz"}, ctx, lambda p, c: {
            "kind": "groups", "columns": ["path"], "rows": [], "meta": {}})  # fmt: skip
    assert raised.value.code == 2 and source.whole == [True]


def test_down_source_paging(ctx: Context, small_pages: None) -> None:
    """A source that is down does not shift the others' items between pages."""
    local = [[f"local/{i:02d}"] for i in range(30)]
    down, up = FakeClient(None), FakeClient([[f"@s1/{i:02d}"] for i in range(30)])
    rows, pages = paged_groups(ctx, local, down, up)
    assert pages > 1 and rows == [*local, *up.rows]
    assert all(down.whole + up.whole)
