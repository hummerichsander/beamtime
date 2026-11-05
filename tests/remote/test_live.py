import asyncio
import json
import time
from pathlib import Path

from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.remote.client import RemoteClient, Spec
from beamtime.serve.live import Hub
from beamtime.serve.server import forward_remote_change

SWEEP = "scaling/lr-sweep"


def test_an_authored_change_on_a_remote_wakes_only_the_pages_watching_authored_calls(
    box: Path, box_spec: Spec
) -> None:
    """A note written by the CLI on the remote marks a watching notes call stale, not a chart's,
    through the same stdio transport the ssh sources use (here a plain command, for the test)."""

    async def scenario() -> set[str]:
        hub = Hub()
        hub.bind()
        hub.watch(
            "p",
            {
                "notes": [f"@box/{SWEEP}", ["authored"]],
                "chart": [f"@box/{SWEEP}", ["metrics"]],
            },
        )
        stream = hub.stream("p")
        await anext(stream)
        client = RemoteClient(spec=box_spec, on_event=lambda e: forward_remote_change(hub, "box", e))
        client.connect()
        client.subscribe(["."])
        try:
            # the remote's first catch-up only builds its index, over the whole log dir; let
            # that one-off noise (and its "stale" event) pass before writing the note to notice.
            await asyncio.wait_for(anext(stream), 5)
            box_ctx = Context.make(root=box.parent, caller="cli")
            call(
                "note add",
                {"group": SWEEP, "type": "observation", "description": "seen from the laptop"},
                box_ctx,
            )
            event = await asyncio.wait_for(anext(stream), 10)
            return set(json.loads(event.split("data: ")[1]))
        finally:
            client.close()
            await stream.aclose()

    assert asyncio.run(scenario()) == {"notes"}
