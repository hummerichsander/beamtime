"""One-shot CLI and MCP calls that involve remotes go through the running ``serve``, which holds the
connections and merges; without one they connect themselves."""

import json
import urllib.error
import urllib.request
from typing import Any

from beamtime.ops.context import Context, OpError

LISTINGS = ("groups", "runs", "series", "data", "timeline", "notes", "keys")


def involves_remotes(ctx: Context, tool: str, params: dict[str, Any]) -> bool:
    """Tell whether a call needs the remotes: it names one, or lists everything while remotes are
    configured.

    :param ctx: The operation context.
    :param tool: The operation's MCP name.
    :param params: Its parameters.
    :return: Whether to ask the running serve."""
    from beamtime import remote

    if remote.targets(params):
        return True
    everything = params.get("from", ".") in (".", "", None)
    return bool(ctx.settings.get("remotes")) and tool in LISTINGS and everything


def call(ctx: Context, tool: str, params: dict[str, Any]) -> dict[str, Any] | None:
    """Answer a call through the root's running serve.

    :param ctx: The operation context.
    :param tool: The operation's MCP name.
    :param params: Its parameters.
    :return: The answer, or ``None`` if no serve runs (the caller then answers it itself)."""
    from beamtime.index.cache import cache_dir, daemon_status
    from beamtime.serve.auth import TOKEN_FILE

    cache = cache_dir(ctx.logdir)
    status = daemon_status(cache) or {}
    if not status.get("port"):
        return None
    try:
        token = (cache / TOKEN_FILE).read_text().strip()
    except OSError:
        return None
    request = urllib.request.Request(
        f"http://127.0.0.1:{status['port']}/api/{tool}",
        data=json.dumps(params).encode(),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "x-beamtime-caller": ctx.caller,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read() or b"{}")
        raise OpError(body.get("error", f"HTTP {e.code}"), code=int(body.get("code", 1))) from None
    except (urllib.error.URLError, OSError):
        # the serve went away between the check and the call: answer here.
        return None
