from beamtime.mcp.server import INSTRUCTIONS
from beamtime.ops.registry import BY_NAME, BY_TOOL, OPS


def test_names_and_tools_are_unique() -> None:
    """No two operations share a CLI path or an MCP tool name."""
    assert len({op.name for op in OPS}) == len(OPS)
    assert len({op.tool for op in OPS}) == len(OPS)
    assert set(BY_NAME) == {op.name for op in OPS}


def test_every_impl_imports() -> None:
    """Each operation's ``impl`` names a callable that exists."""
    for op in OPS:
        assert callable(op.function()), op.name


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
