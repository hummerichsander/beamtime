"""The operation set shared by the CLI, MCP and the API (layer 8)."""

from typing import Any

import msgspec

from beamtime.ops.registry import BY_NAME


def call(name: str, params: dict[str, Any], context: Any) -> dict[str, Any]:
    """Validate parameters and run an operation.

    :param name: The operation, e.g. ``runs`` or ``mcp install``.
    :param params: The parameters by their encoded names (``from``, not ``from_``).
    :param context: The ``ops.context.Context``.
    :return: The answer."""
    from beamtime import remote
    from beamtime.ops.context import OpError

    op = BY_NAME[name]

    def here(given: dict[str, Any]) -> dict[str, Any]:
        try:
            p = msgspec.convert(given, type=op.params, strict=False)
        except msgspec.ValidationError as e:
            raise OpError(f"{name}: {e}", code=2) from None
        return op.function()(context, p)

    # pull is the one command that reaches a remote itself.
    if op.name == "pull" or (remote.active is None and not remote.targets(params)):
        return here(params)
    if op.user_only and remote.targets(params):
        raise OpError(f"{name} is a user command; run it on the remote itself (ssh)", code=2)
    from beamtime.remote.route import routed

    return routed(op.tool, params, context, here)
