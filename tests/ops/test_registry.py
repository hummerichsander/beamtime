from importlib import import_module

import pytest

from beamtime.cli.format import render, renderers
from beamtime.mcp.server import INSTRUCTIONS
from beamtime.ops import call
from beamtime.ops.answers import ANSWERS, Answer
from beamtime.ops.context import Context
from beamtime.ops.registry import BY_API, BY_NAME, BY_TOOL, METHODS, OPS


def test_names_and_tools_are_unique() -> None:
    """No two operations share a CLI path or an MCP tool name."""
    assert len({m.name for m in METHODS}) == len(METHODS)
    assert len({m.tool for m in METHODS}) == len(METHODS)
    assert set(BY_NAME) == {op.name for op in OPS}


def test_every_impl_imports() -> None:
    """Each operation's ``impl`` names a callable that exists."""
    for m in METHODS:
        assert callable(m.function()), m.name


def test_instructions_name_every_user_only_op() -> None:
    """The MCP instructions list the user-only operations from the registry, and no tool is one."""
    user_only = sorted(op.name for op in OPS if op.user_only)
    assert len(user_only) == 20
    assert f"({', '.join(user_only)})" in INSTRUCTIONS
    assert not {op.tool for op in OPS if op.user_only} & set(BY_TOOL)


def test_one_source_params_exist() -> None:
    """The parameters an operation limits to one source are fields of its struct."""
    named = {op.name: op.one_source for op in OPS if op.one_source}
    assert named == {"compare": ("targets",), "cp": ("source", "dest"), "run promote": ("runs",)}
    for op in OPS:
        assert set(op.one_source) <= set(op.params.__struct_fields__)


PAGE_METHODS = {
    "hello", "files", "meta", "view", "summary", "save_view", "view_text", "figure", "code",
    "run_diff", "view_check", "view_put", "view_compile", "view_files", "block_check", "block_put",
}  # fmt: skip


def test_page_methods_are_registered() -> None:
    """The page methods are methods without parameters, so they are no CLI command or MCP tool."""
    pages = {m.name for m in METHODS if m.params is None}
    assert pages == PAGE_METHODS
    assert not pages & (set(BY_NAME) | set(BY_TOOL))
    assert pages <= set(BY_API)
    assert all(m.params is not None for m in OPS)
    assert {"note_rm", "set"} <= set(BY_API) and "rm" not in BY_API


def test_method_facts_agree() -> None:
    """A draft method has a parameter to say so, an operation has a summary, and a page method
    has no CLI facet."""
    for m in METHODS:
        if m.params is None:
            assert not m.positional and m.stdin is None and not m.user_only, m.name
            continue
        assert m.summary, m.name
        if m.drafts:
            assert {"group", "draft"} & set(m.params.__struct_fields__), m.name
    for m in METHODS:
        assert set(m.draft_params) <= {"draft", "block_draft"}, m.name
        if m.params is not None:
            assert set(m.draft_params) <= set(m.params.__struct_fields__), m.name


def test_derived_routing_sets() -> None:
    """What the API routes, and what snapshots refuse, come from the declarations."""
    from beamtime.remote.route import WRITES
    from beamtime.serve.api import ROUTED

    assert {"view", "summary", "save_view", "view_text", "code", "run_diff"} <= ROUTED
    assert (
        not {"hello", "files", "meta", "figure", "view_put", "block_put", "note_rm", "set"} & ROUTED
    )
    assert {"view_text", "save_view"} <= WRITES


def test_kinds_and_renderers_agree() -> None:
    """Every kind is an answer kind, a listing's kind merges, kinds share a renderer, writes name one."""
    for m in METHODS:
        assert m.kind is None or m.kind in ANSWERS, m.name
        assert m.render is None or m.kind is not None, m.name
        assert not m.writes or m.kind is not None, m.name
        if m.listing:
            assert type(ANSWERS[m.kind]).merged is not Answer.merged, m.name
        if m.render:
            module, name = m.render.split(":")
            assert callable(getattr(import_module(module), name)), m.name
    by_kind: dict[str, set[str | None]] = {}
    for m in METHODS:
        by_kind.setdefault(m.kind, set()).add(m.render)
    assert all(len(renders) == 1 for renders in by_kind.values())


def test_page_kinds_use_the_generic_walk() -> None:
    """The page methods' kinds have an entry, and it is the generic walk."""
    pages = {m.kind for m in METHODS if m.params is None and m.kind not in ANSWERS.keys() - {None}}
    assert not pages - {None}
    for kind in ("hello", "files", "meta", "view", "summary", "code", "diff"):
        assert (
            ANSWERS[kind].placed({"kind": kind, "path": "g"}, lambda v: f"@a/{v}")["path"] == "@a/g"
        )


READS = {
    "status": {}, "keys": {}, "groups": {}, "runs": {"limit": 3},
    "series": {"from": "tokenizer", "y": ["val/ppl"]},
    "data": {"from": "scaling/lr-sweep", "key": "samples"},
    "file": {"view": "scaling", "path": "data/3f9a21c0-fit.csv"},
    "logs": {}, "wait": {"timeout": 0}, "diagnose": {}, "timeline": {"limit": 3}, "notes": {},
    "proposal show": {"group": "scaling/lr-sweep"}, "check": {"group": "scaling/lr-sweep"},
    "digest": {"group": "scaling/lr-sweep"}, "plan missing": {"group": "scaling/lr-sweep"},
    "memory show": {"group": "scaling/lr-sweep"}, "query": {"query": {"groups": {"from": "."}}},
    "guide": {}, "view show": {"group": "scaling/lr-sweep"},
    "view history": {"group": "scaling/lr-sweep"}, "view outdated": {}, "block list": {},
    "settings": {}, "doctor": {}, "source list": {},
}  # fmt: skip


def test_every_read_renders(ctx: Context, roles: dict[str, str]) -> None:
    """Each read operation answers with its kind, and its text is never the raw dict."""
    data = ctx.logdir / "scaling" / "view" / "data"
    data.mkdir(parents=True)
    (data / "3f9a21c0-fit.csv").write_text("lr,acc\n0.001,0.9\n0.003,0.85\n", encoding="utf-8")
    calls = READS | {
        "card": {"run": roles["diverging"]},
        "output": {"run": roles["diverging"]},
        "resume": {"run": roles["killed"]},
        "compare": {"targets": ["scaling/lr-sweep", "tokenizer"]},
    }
    named = {op.name for op in OPS if not op.user_only and not op.writes and not op.drafts}
    # a library block and a browser are what these two need; their answers are checked below.
    assert named - {"block show", "export"} <= set(calls), named - set(calls)
    for name, params in calls.items():
        answer = call(name, params, ctx)
        op = BY_NAME[name]
        assert op.kind is None or answer["kind"] == op.kind, name
        text = render(answer)
        assert text and text != str(answer), name
        if answer["kind"] not in renderers():
            assert answer.get("lines"), name


def test_export_renders_both_answers() -> None:
    """The page export answers with lines, the file export of a table with its size."""
    page = {"kind": "export", "lines": ["wrote x/index.html: 3 answers"], "dir": "x", "meta": {}}
    assert render(page) == "wrote x/index.html: 3 answers"
    file = {
        "kind": "export",
        "path": "x.csv",
        "format": "csv",
        "rows": 4,
        "bytes": 90,
        "columns": ["run", "step"],
        "first_row": ["a1", None],
        "meta": {},
    }
    assert render(file) == "wrote 4 rows to x.csv (90 bytes)\ncolumns: run, step\nfirst row: a1, "


def test_stale_kinds_are_declared() -> None:
    """Every method names the changes that stale it, within the three kinds."""
    kinds = {"metrics", "status", "authored"}
    assert all(m.stale_on and set(m.stale_on) <= kinds for m in METHODS)
    by_tool = {m.tool: m for m in METHODS}
    assert by_tool["series"].stale_on == ("metrics", "status")
    assert by_tool["notes"].stale_on == ("authored",)
    assert by_tool["view"].stale_on == ("status", "authored")
    assert by_tool["status"].stale_on == ("metrics", "status", "authored")
