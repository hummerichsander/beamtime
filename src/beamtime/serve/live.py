"""Live updates: pages watch API calls by scope; the daemon's changes name the stale ones."""

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

MIN_INTERVAL_S = 1.0
KEEPALIVE_S = 15.0


def affects(changed: str, scope: str) -> bool:
    """Tell whether a change of one path makes an answer about a scope stale.

    A run's change affects its group and every group above; a group's change (notes,
    proposals) affects the groups and runs below it too, whose answers cite them.

    :param changed: The changed run or group path, relative to the log dir.
    :param scope: The group or run path an answer is about.
    :return: Whether the answer is stale."""
    if scope in (".", "") or changed == scope:
        return True
    return changed.startswith(f"{scope}/") or scope.startswith(f"{changed}/") or changed == "."


@dataclass(kw_only=True)
class Client:
    """One open page: the calls it watches and the ids waiting to be sent."""

    # call id to (scope, the kinds of change it cares about).
    watched: dict[str, tuple[str, set[str]]] = field(default_factory=dict)
    pending: set[str] = field(default_factory=set)
    wake: asyncio.Event = field(default_factory=asyncio.Event)


class Hub:
    """Routes the daemon's changes to the pages that show affected answers."""

    def __init__(self) -> None:
        """Create an empty hub; ``bind`` must be called from the event loop."""
        self.clients: dict[str, Client] = {}
        self.loop: asyncio.AbstractEventLoop | None = None
        self.closed = False

    def bind(self) -> None:
        """Remember the running event loop, so other threads can hand over changes."""
        self.loop = asyncio.get_running_loop()

    def close(self) -> None:
        """End every stream, so the server can stop without waiting for pages."""
        self.closed = True
        for client in self.clients.values():
            client.wake.set()

    def watch(self, client: str, watched: dict[str, tuple[str, list[str]]]) -> None:
        """Replace the calls a page watches.

        :param client: The page's id.
        :param watched: Call id to ``[scope, kinds]``, the kinds of change it cares about."""
        self.clients.setdefault(client, Client()).watched = {
            qid: (scope, set(kinds)) for qid, (scope, kinds) in watched.items()
        }

    def changed(self, changed: dict[str, set[str]]) -> None:
        """Hand over changed paths and their kinds from the indexing thread.

        :param changed: Run and group paths relative to the log dir, to the kinds that changed."""
        if self.loop is not None:
            self.loop.call_soon_threadsafe(self.dispatch, dict(changed))

    def dispatch(self, changed: dict[str, set[str]]) -> None:
        """Queue the ids of affected calls for every page.

        :param changed: Run and group paths relative to the log dir, to the kinds that changed."""
        for client in self.clients.values():
            stale = {
                qid
                for qid, (scope, kinds) in client.watched.items()
                if any(affects(p, scope) and not ks.isdisjoint(kinds) for p, ks in changed.items())
            }
            if stale:
                client.pending |= stale
                client.wake.set()

    async def stream(self, client_id: str) -> AsyncIterator[str]:
        """Stream server-sent events to one page: ``stale`` events with call ids.

        At most one event per second goes out, so a page refetches a call at most once
        a second however often its runs write.

        :param client_id: The page's id.
        :return: The event stream."""
        client = self.clients.setdefault(client_id, Client())
        yield f"event: hello\ndata: {json.dumps({'client': client_id})}\n\n"
        last = 0.0
        try:
            while not self.closed:
                try:
                    await asyncio.wait_for(client.wake.wait(), KEEPALIVE_S)
                except TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if self.closed:
                    return
                if (wait := last + MIN_INTERVAL_S - time.monotonic()) > 0:
                    await asyncio.sleep(wait)
                client.wake.clear()
                ids, client.pending = sorted(client.pending), set()
                last = time.monotonic()
                if ids:
                    yield f"event: stale\ndata: {json.dumps(ids)}\n\n"
        finally:
            self.clients.pop(client_id, None)
