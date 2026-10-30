"""Remote sources (layer 4): other machines' log dirs, reached over ssh and named ``@<name>/...``.

This module stays tiny, since every operation call checks it: the running ``serve`` registers its
sources here, and ``targets`` tells whether parameters name one."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from beamtime.remote.sources import Sources

# the sources a running `beamtime serve` holds; a one-shot CLI call has none.
active: "Sources | None" = None


def targets(params: dict[str, Any]) -> bool:
    """Tell whether parameters name a remote source anywhere a target can be.

    :param params: An operation's parameters.
    :return: Whether a string value (or a query's ``from``) starts with ``@``."""
    for v in params.values():
        if isinstance(v, str) and v.startswith("@"):
            return True
        if isinstance(v, dict):
            for inner in v.values():
                if isinstance(inner, dict) and str(inner.get("from", "")).startswith("@"):
                    return True
    return False


def answer(name: str, params: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Answer an operation for the CLI or MCP: through the running serve when remotes are
    involved (it holds the connections and merges), else in this process.

    :param name: The operation.
    :param params: Its parameters.
    :param ctx: The operation context.
    :return: The answer."""
    from beamtime.ops import call
    from beamtime.ops.registry import BY_NAME

    op = BY_NAME[name]
    if not op.user_only and (targets(params) or ctx.settings.get("remotes")):
        from beamtime.remote import via_serve

        if via_serve.involves_remotes(ctx, op.tool, params):
            if (found := via_serve.call(ctx, op.tool, params)) is not None:
                return found
    return call(name, params, ctx)
