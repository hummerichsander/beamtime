"""Remote sources (layer 4): other machines' log dirs, reached over ssh and named ``@<name>/...``.

This module stays tiny, since every CLI and MCP call loads it: ``targets`` tells whether parameters
name a source, and ``answer`` routes the call. A running ``serve`` holds its sources on its
operation context (``Context.sources``)."""

from typing import Any

# parameters that name a place: a group, a run, a page.
TARGETS = ("group", "from", "run", "path", "view", "source", "to", "target", "dest", "targets")


def places(params: dict[str, Any]) -> list[str]:
    """List the places a call names, also the items of a list of targets.

    :param params: An operation's parameters.
    :return: The text values of the target parameters, in order."""
    out = []
    for key in TARGETS:
        match params.get(key):
            case str() as v:
                out.append(v)
            case list() as vs:
                out += [v for v in vs if isinstance(v, str)]
    return out


def targets(params: dict[str, Any]) -> bool:
    """Tell whether a call names a remote source as its target.

    :param params: An operation's parameters.
    :return: Whether a target (or a query's ``from``) starts with ``@``."""
    if any(v.startswith("@") for v in places(params)):
        return True
    if isinstance(query := params.get("query"), dict):
        return any(
            isinstance(q, dict) and str(q.get("from", "")).startswith("@") for q in query.values()
        )
    return False


def answer(name: str, params: dict[str, Any], ctx: Any) -> dict[str, Any]:
    """Answer an operation for the CLI or MCP: through the running serve when remotes are
    involved (it holds the connections and merges), else in this process.

    :param name: The operation.
    :param params: Its parameters.
    :param ctx: The operation context.
    :return: The answer."""
    from beamtime.ops import call
    from beamtime.ops.context import OpError
    from beamtime.ops.registry import BY_NAME

    op = BY_NAME[name]
    if op.local or ctx.sources is None and not targets(params) and not ctx.settings.get("remotes"):
        return call(name, params, ctx)
    if op.user_only:
        if targets(params):
            raise OpError(f"{name} is a user command; run it on the remote itself (ssh)", code=2)
        return call(name, params, ctx)
    from beamtime.remote import via_serve
    from beamtime.remote.route import routed

    if via_serve.involves_remotes(ctx, op.tool, params):
        if (found := via_serve.call(ctx, op.tool, params)) is not None:
            return found
    return routed(op.tool, params, ctx, lambda given: call(name, given, ctx))
