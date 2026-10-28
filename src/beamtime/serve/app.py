"""The Starlette app: the operations as API, live updates, run files and the frontend."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version
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

from beamtime.format.ids import is_run_id
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL
from beamtime.serve.live import Hub

STATIC = Path(__file__).parent / "static"
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
        try:
            match method:
                case "meta":
                    answer = await run_in_threadpool(meta, ctx)
                case "view":
                    answer = await run_in_threadpool(view, ctx, body.get("path", "."))
                case "watch":
                    hub.watch(str(body.get("client")), dict(body.get("watched") or {}))
                    answer = {"kind": "watch", "watching": len(body.get("watched") or {})}
                case _ if (op := BY_TOOL.get(method)) is not None:
                    answer = await run_in_threadpool(call, op.name, body, ctx)
                case _:
                    return error(f"no API method {method!r}", 4)
        except OpError as e:
            return error(str(e), e.code)
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


def meta(ctx: Context) -> dict[str, Any]:
    """Describe the project for the shell: name, version, theme pair.

    :param ctx: The operation context.
    :return: The answer."""
    from beamtime.views.theme import pair

    return {
        "kind": "meta",
        "project": ctx.root.name,
        "root": str(ctx.root),
        "logdir": str(ctx.logdir),
        "version": version("beamtime"),
        "theme": pair(str(ctx.settings.get("theme") or "beamtime"), ctx.root),
    }


def view(ctx: Context, path: str) -> dict[str, Any]:
    """Answer the view of a group or run: for now the built-in default.

    :param ctx: The operation context.
    :param path: A group path, or a run id or path.
    :return: ``{kind, path, run, view, summary}`` with the run's path resolved; ``summary``
        names the main metric's best run for the header."""
    from beamtime.index.index import Index
    from beamtime.views.defaults import default_view, summary

    path = path.strip("/") or "."
    name = path.rsplit("/", 1)[-1]
    run = name if is_run_id(name) else None
    if run is not None:
        index = Index(logdir=ctx.logdir)
        try:
            if (found := index.run_path(run)) is None:
                index.catch_up(".", budget_s=0)
                found = index.run_path(run)
        finally:
            index.close()
        if found is None:
            raise OpError(f"no run {run!r} below the log dir", code=4)
        path = found.relative_to(ctx.logdir).as_posix()
    elif not (ctx.logdir / path).is_dir() or ".." in path.split("/"):
        raise OpError(f"no group {path!r} below the log dir", code=4)
    return {
        "kind": "view",
        "path": path,
        "run": run,
        "view": default_view(ctx, path),
        "summary": summary(ctx, path),
    }


def locate(ctx: Context, run_id: str, rel: str) -> Path | None:
    """Find a file inside a run directory, refusing paths that leave it.

    :param ctx: The operation context.
    :param run_id: The run id.
    :param rel: The file's path inside the run.
    :return: The file, or ``None``."""
    from beamtime.index.index import Index

    if not is_run_id(run_id):
        return None
    index = Index(logdir=ctx.logdir)
    try:
        run_dir = index.run_path(run_id)
    finally:
        index.close()
    if run_dir is None:
        return None
    path = (run_dir / rel).resolve()
    if not path.is_relative_to(run_dir.resolve()) or not path.is_file():
        return None
    return path
