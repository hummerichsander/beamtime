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
    anyio.run(run, root)
    return 0
