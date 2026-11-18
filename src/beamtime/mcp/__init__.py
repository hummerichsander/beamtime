"""The MCP server and its prompts (layer 8); needs ``beamtime[serve]``."""

import sys
from pathlib import Path


def serve(root: str | Path | None = None) -> int:
    """Run the MCP server over stdio.

    :param root: The project root, or ``None`` to find it from the working directory.
    :return: The exit code."""
    try:
        import anyio

        from beamtime.mcp.server import run
    except ImportError:
        print(
            "beamtime: the MCP server needs the serve extra: pip install 'beamtime[serve]'",
            file=sys.stderr,
        )
        return 1
    from beamtime.index.cache import resolve_cache
    from beamtime.index.procs import register
    from beamtime.ops.context import Context

    # outside a project Context.make falls back to the working directory, as every tool call does.
    ctx = Context.make(root=root, caller="mcp")
    cache = resolve_cache(ctx.logdir, ctx.settings)
    registration = None
    try:
        registration = register(
            "mcp",
            root=str(ctx.root),
            logdir=str(ctx.logdir),
            cache=str(cache.path),
            cache_kind=cache.kind,
        )
    except OSError as e:
        print(f"beamtime: not listed in the process registry ({e})", file=sys.stderr)
    try:
        anyio.run(run, root, registration)
    finally:
        if registration is not None:
            registration.close()
    return 0
