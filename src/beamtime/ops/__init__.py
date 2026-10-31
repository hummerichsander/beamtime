"""The operation set shared by the CLI, MCP and the API (layer 8)."""

from typing import Any

import msgspec

from beamtime.ops.registry import BY_NAME


def call(name: str, params: dict[str, Any], context: Any) -> dict[str, Any]:
    """Validate parameters and run an operation on this machine.

    Calls that may concern remote sources go through ``beamtime.remote.answer`` (CLI and MCP) or
    the API's dispatch, which route them and come back here for this machine's part.

    :param name: The operation, e.g. ``runs`` or ``mcp install``.
    :param params: The parameters by their encoded names (``from``, not ``from_``).
    :param context: The ``ops.context.Context``.
    :return: The answer."""
    from beamtime.ops.context import OpError

    op = BY_NAME[name]
    try:
        p = msgspec.convert(params, type=op.params, strict=False)
    except msgspec.ValidationError as e:
        raise OpError(f"{name}: {e}", code=2) from None
    return op.function()(context, p)
