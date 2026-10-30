"""The Starlette app: the operations as API, live updates, run files and the frontend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

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
            return reply({"kind": "watch", "watching": len(body.get("watched") or {})})
        try:
            answer = await run_in_threadpool(dispatch, ctx, method, body)
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
        path = await run_in_threadpool(locate, ctx, run_id, rel)
        if path is None:
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
