"""The Starlette app: the operations as API, live updates, run files and the frontend."""

import dataclasses
import mimetypes
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import msgspec
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import (
    FileResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from beamtime.ops.context import Context, OpError
from beamtime.serve.api import STATIC, dispatch, locate
from beamtime.serve.live import Hub

if TYPE_CHECKING:
    from beamtime.remote.sources import Sources

STATUS = {1: 400, 2: 400, 3: 422, 4: 404}


def build(*, ctx: Context, hub: Hub, static: Path = STATIC) -> Starlette:
    """Build the app for one project.

    :param ctx: The operation context, with caller ``view``.
    :param hub: The live-update hub the daemon reports to.
    :param static: The bundled frontend.
    :return: The app, without the token guard."""

    async def api(request: Request) -> Response:
        method = request.path_params["method"]
        try:
            body = await request.json() if await request.body() else {}
        except ValueError:
            return error("the body is not JSON", 2)
        if not isinstance(body, dict):
            return error("the body is a JSON object of parameters", 2)
        if method == "watch":
            hub.watch(str(body.get("client")), dict(body.get("watched") or {}))
            await run_in_threadpool(subscribe_remotes, hub, ctx.sources)
            return reply({"kind": "watch", "watching": len(body.get("watched") or {})})
        # the CLI and MCP send their calls about remotes here, with their own answer sizes.
        caller = request.headers.get("x-beamtime-caller")
        here = dataclasses.replace(ctx, caller=caller) if caller in ("cli", "mcp") else ctx
        try:
            answer = await run_in_threadpool(dispatch, here, method, body)
        except OpError as e:
            return error(str(e), e.code)
        if isinstance(answer, bytes):
            return Response(answer, media_type="application/pdf")
        return reply(answer)

    async def subscribe(request: Request) -> Response:
        hub.bind()
        client = request.query_params.get("client") or "anonymous"
        return StreamingResponse(
            hub.stream(client),
            media_type="text/event-stream",
            headers={"cache-control": "no-store", "x-accel-buffering": "no"},
        )

    async def run_file(request: Request) -> Response:
        run_id, rel = request.path_params["run"], request.path_params["path"]
        # a run on a remote: /api/file/@box/<id>/<path>, never this machine's copy of it.
        source = None
        if run_id.startswith("@") and "/" in rel:
            source, (run_id, rel) = run_id[1:], rel.split("/", 1)
        path = None if source else await run_in_threadpool(locate, ctx, run_id, rel)
        if path is None:
            from beamtime.remote.route import remote_file

            content = await run_in_threadpool(remote_file, ctx, run_id, rel, source)
            if content is not None:
                kind = mimetypes.guess_type(rel)[0] or "application/octet-stream"
                return Response(
                    content, media_type=kind, headers={"cache-control": "private, max-age=3600"}
                )
            return error(f"no file {rel!r} in run {run_id!r}", 4)
        return FileResponse(path, headers={"cache-control": "private, max-age=3600"})

    async def page(request: Request) -> Response:
        index = static / "index.html"
        if not index.is_file():
            return Response(
                "The frontend is not built: run `npm run build` in web/.", status_code=500
            )
        return FileResponse(index, headers={"cache-control": "no-cache"})

    async def home(request: Request) -> Response:
        return RedirectResponse("/f/local", 307)

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        hub.bind()
        yield

    return Starlette(
        routes=[
            Route("/", home),
            Route("/api/subscribe", subscribe),
            Route("/api/file/{run}/{path:path}", run_file),
            Route("/api/{method}", api, methods=["POST"]),
            Mount("/static", StaticFiles(directory=static, check_dir=False), name="static"),
            Route("/f", page),
            Route("/f/{path:path}", page),
            Route("/r/{path:path}", page),
            Route("/timeline", page),
            Route("/settings", page),
            Route("/settings/{path:path}", page),
        ],
        lifespan=lifespan,
    )


def reply(answer: Any, status: int = 200) -> Response:
    """Encode an answer as JSON; non-finite numbers become ``null``.

    :param answer: The answer.
    :param status: The HTTP status.
    :return: The response."""
    return Response(
        msgspec.json.encode(answer, enc_hook=str),
        status_code=status,
        media_type="application/json",
        headers={"cache-control": "no-store"},
    )


def error(message: str, code: int) -> Response:
    """Answer an operation error.

    :param message: What went wrong and what to do.
    :param code: The operation's exit code.
    :return: The JSON error."""
    return reply({"error": message, "code": code}, STATUS.get(code, 400))


def subscribe_remotes(hub: Hub, sources: "Sources | None") -> None:
    """Tell each connected remote which of its scopes open pages watch.

    :param hub: The live-update hub with every page's watched scopes.
    :param sources: The serve's remotes."""
    if sources is None:
        return
    # copies: pages come and go on the event loop while this runs in a worker thread.
    watched = [list(client.watched.values()) for client in list(hub.clients.values())]
    scopes = {scope for each in watched for scope in each}
    for name, client in sources.clients.items():
        if client.state != "connected":
            continue
        own = [s for s in scopes if s == f"@{name}" or s.startswith(f"@{name}/")]
        mine = {s[len(name) + 2 :] or "." for s in own}
        if "." in scopes:
            mine.add(client.spec.scope)
        client.subscribe(sorted(mine))
