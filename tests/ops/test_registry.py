from beamtime.mcp.server import INSTRUCTIONS
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
    assert len(user_only) == 18
    assert f"({', '.join(user_only)})" in INSTRUCTIONS
    assert not {op.tool for op in OPS if op.user_only} & set(BY_TOOL)


def test_one_source_params_exist() -> None:
    """The parameters an operation limits to one source are fields of its struct."""
    named = {op.name: op.one_source for op in OPS if op.one_source}
    assert named == {"compare": ("targets",), "cp": ("source", "dest")}
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
