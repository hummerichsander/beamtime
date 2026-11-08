"""The API both transports answer, HTTP for browsers and stdio for ssh: the operations under their
MCP names, the page methods the web UI needs, and ``hello`` and ``files`` for remotes.

Nothing here needs Starlette, so a remote answers over stdio with the base install."""

import base64
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from beamtime.format.constants import ENV_DIR
from beamtime.format.ids import is_run_id
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL
from beamtime.query.models import closest
from beamtime.sdk.paths import find_run

STATIC = Path(__file__).parent / "static"
STARTED = time.time()
PROTOCOL = 1
READ_LIMIT = 4 << 20
# page methods with a target; with the operations, what the API routes to remote sources.
PAGES = ("view", "summary", "save_view", "view_text", "code", "run_diff")
ROUTED = (*PAGES, *(op.tool for op in BY_TOOL.values() if not op.local))


def dispatch(ctx: Context, method: str, body: dict[str, Any]) -> dict[str, Any] | bytes:
    """Answer one API call.

    :param ctx: The operation context.
    :param method: The method: an operation's MCP name, or a page or remote method.
    :param body: Its parameters.
    :return: The answer; a figure is a PDF."""
    import dataclasses

    from beamtime import remote

    here = ctx
    if ctx.sources is not None and (ctx.caller == "view" or "everywhere" in body):
        # the web UI's page of this machine is this machine; the group tree asks for everywhere.
        body = dict(body)
        here = dataclasses.replace(ctx, merge=bool(body.pop("everywhere", False)))
    elif "everywhere" in body:
        body = {k: v for k, v in body.items() if k != "everywhere"}
    # a draft is always local; its own view/code/file dispatch fetches from another source itself.
    draft_local = method in ("view", "code", "file") and (
        body.get("draft") is not None or body.get("block_draft") is not None
    )
    if method in ROUTED and not draft_local and (ctx.sources is not None or remote.targets(body)):
        from beamtime.remote.route import routed

        return routed(method, body, here, lambda given: dispatch_here(here, method, given))
    out = dispatch_here(here, method, body)
    # `set` reloads the settings on the copy; the next call starts from ctx.
    ctx.settings = here.settings
    return out


def dispatch_here(ctx: Context, method: str, body: dict[str, Any]) -> dict[str, Any] | bytes:
    """Answer one API call on this machine.

    :param ctx: The operation context.
    :param method: The method.
    :param body: Its parameters.
    :return: The answer."""
    match method:
        case "hello":
            return hello(ctx, body)
        case "files":
            return files(ctx, body)
        case "meta":
            return meta(ctx)
        case "view":
            return view(
                ctx,
                body.get("path", "."),
                body.get("version"),
                body.get("draft"),
                body.get("metrics"),
            )
        case "save_view":
            return save_view(
                ctx,
                str(body.get("path", ".")),
                body.get("prefs") or {},
                body.get("title"),
                body.get("finding"),
            )
        case "note_rm" | "set":
            # user commands the UI offers its user (deleting a note, its settings page);
            # agents never use this API.
            return call(method.replace("_", " "), body, ctx)
        case "view_text":
            from beamtime.ops.views import edit_text

            page = page_of(ctx, str(body.get("path", ".")))[0]
            return edit_text(ctx, page, body.get("id"), str(body.get("text") or ""))
        case "figure":
            from beamtime.views.export import figure_pdf

            return figure_pdf(ctx, body)
        case "code":
            from beamtime.views.store import code_text

            return code_text(ctx, body)
        case "view_check" | "view_put" | "view_compile" | "view_files":
            from beamtime.ops import views

            return getattr(views, method)(ctx, body)
        case "block_check" | "block_put":
            from beamtime.ops import blocks

            return getattr(blocks, method)(ctx, body)
        case "run_diff":
            return run_diff(ctx, str(body.get("run", "")))
        case "summary":
            return summary_of(ctx, body.get("path", "."), body.get("metrics"))
        case _ if (op := BY_TOOL.get(method)) is not None:
            return call(op.name, body, ctx)
        case _:
            raise OpError(f"no API method {method!r}", code=4)


def hello(ctx: Context, body: dict[str, Any]) -> dict[str, Any]:
    """Shake hands: the same protocol major version on both sides, or a clear refusal.

    :param ctx: The operation context.
    :param body: ``{protocol, version}`` of the caller.
    :return: This side's protocol, version and log dir."""
    mine = version("beamtime")
    if (theirs := body.get("protocol", PROTOCOL)) != PROTOCOL:
        raise OpError(
            f"protocol {theirs} (beamtime {body.get('version', '?')}) can't talk to protocol "
            f"{PROTOCOL} (beamtime {mine}); install the same beamtime on both sides, e.g. "
            "`uv tool install --upgrade beamtime`",
            code=2,
        )
    return {
        "kind": "hello",
        "protocol": PROTOCOL,
        "version": mine,
        "logdir": str(ctx.logdir),
        "logdir_exists": ctx.logdir.is_dir(),
        "cache": cache_info(),
    }


def cache_info() -> dict[str, str | None]:
    """Describe the cache a stdio session indexes into.

    :return: Its path, whether it is temporary, and why a configured one was refused."""
    import sys

    stdio = sys.modules.get("beamtime.serve.stdio")
    return dict(stdio.CACHE) if stdio is not None else {}


def files(ctx: Context, body: dict[str, Any]) -> dict[str, Any]:
    """List the files below a folder of the log dir, or read one from an offset.

    :param ctx: The operation context.
    :param body: ``{list: <folder>}`` or ``{read: <file>, offset, limit}``, relative to the log dir.
    :return: ``{entries: [{path, size, mtime}]}``, or ``{data (base64), size, eof}``."""
    root = ctx.logdir.resolve()

    def inside(rel: str) -> Path:
        path = (root / rel).resolve()
        if path != root and root not in path.parents:
            raise OpError(f"{rel!r} is outside the log dir", code=2)
        return path

    if (rel := body.get("list")) is not None:
        folder = inside(str(rel))
        if not folder.is_dir():
            return {"kind": "files", "entries": []}
        entries = []
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                st = f.stat()
                rel_path = f.relative_to(root).as_posix()
                entries.append({"path": rel_path, "size": st.st_size, "mtime": st.st_mtime})
        return {"kind": "files", "entries": entries}
    if (rel := body.get("read")) is not None:
        path = inside(str(rel))
        if not path.is_file():
            raise OpError(f"no file {rel!r}", code=4)
        offset = int(body.get("offset") or 0)
        limit = min(int(body.get("limit") or READ_LIMIT), READ_LIMIT)
        with path.open("rb") as f:
            f.seek(offset)
            data = f.read(limit)
        size = path.stat().st_size
        return {
            "kind": "files",
            "data": base64.b64encode(data).decode(),
            "size": size,
            "eof": offset + len(data) >= size,
        }
    raise OpError("files takes {list: <folder>} or {read: <file>, offset, limit}", code=2)


def bundle() -> str | None:
    """Name the frontend build the server has.

    :return: The entry file's modification time, or ``None`` without a build."""
    entry = STATIC / "app.js"
    return str(entry.stat().st_mtime_ns) if entry.is_file() else None


def meta(ctx: Context) -> dict[str, Any]:
    """Describe the project for the shell: name, version, theme pair.

    :param ctx: The operation context.
    :return: The answer."""
    from beamtime.format.authored import NOTE_TYPES
    from beamtime.ops.admin import figure_styles, project_styles
    from beamtime.ops.reading import sources
    from beamtime.views.theme import colormaps, names, pair

    return {
        "kind": "meta",
        "note_types": list(NOTE_TYPES),
        "project": ctx.root.name,
        "root": str(ctx.root),
        "logdir": str(ctx.logdir),
        "version": version("beamtime"),
        "theme": pair(str(ctx.settings.get("theme") or "beamtime"), ctx.root),
        # a frontend rebuilt after the server started (an editable install) may call
        # methods this server doesn't know yet; the shell then asks for a restart.
        "outdated": (STATIC / "app.js").is_file() and (STATIC / "app.js").stat().st_mtime > STARTED,
        # which frontend the server has; a page that reconnects to another one reloads.
        "bundle": bundle(),
        "settings": {
            "theme": ctx.settings.get("theme"),
            "theme_mode": ctx.settings.get("theme_mode"),
            "figure_style": ctx.settings.get("figure_style"),
            "file": str(ctx.root / "beamtime.yaml"),
        },
        "themes": names(ctx.root),
        "colormaps": colormaps(),
        "figure_styles": figure_styles() + project_styles(ctx.root),
        "sources": sources(ctx),
    }


def view(
    ctx: Context,
    path: str,
    version: str | None = None,
    draft: str | None = None,
    metrics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Answer the view of a group or run: its own, else the built-in default.

    :param ctx: The operation context.
    :param path: A group path, or a run id or path.
    :param version: A saved version to show instead of the newest.
    :param draft: A draft to show instead, for the renderer.
    :param metrics: The viewer's pins ``{y, higher}`` for the default view; ``[]`` is none.
    :return: ``{kind, path, run, view, source, version, ...}`` with the run's path resolved."""
    from beamtime.views.store import shown

    if draft is not None and path.startswith("@"):
        from beamtime.ops.views import draft_view

        return {"kind": "view", "path": path, "run": None} | draft_view(ctx, path, draft)
    path, run = page_of(ctx, path)
    return {"kind": "view", "path": path, "run": run} | shown(
        ctx, path, version=version, draft_name=draft, metrics=metrics
    )


def page_of(ctx: Context, path: str) -> tuple[str, str | None]:
    """Resolve a page: a group path, or a run by id or path.

    :param ctx: The operation context.
    :param path: The page as the URL names it.
    :return: The path below the log dir, and the run id for a run."""
    from beamtime.index.index import Index

    path = path.strip("/") or "."
    name = path.rsplit("/", 1)[-1]
    run = name if is_run_id(name) else None
    if run is not None:
        if not ctx.logdir.is_dir():
            raise OpError(f"no run {run!r}; no local log dir", code=4)
        with Index(logdir=ctx.logdir) as index:
            if (found := index.run_path(run)) is None:
                index.catch_up(".", budget_s=0)
                found = index.run_path(run)
        # a run created after the daemon's last walk is not indexed yet.
        if found is None and (found := find_run(ctx.logdir, run)) is None:
            raise OpError(f"no run {run!r} below the log dir", code=4)
        path = found.relative_to(ctx.logdir).as_posix()
    elif ".." in path.split("/"):
        raise OpError(f"no group {path!r} below the log dir", code=4)
    elif not (ctx.logdir / path).is_dir():
        from beamtime.format.moves import current

        # an old link to a moved group shows the group where it is now.
        if not (ctx.logdir / (moved := current(ctx.logdir, path))).is_dir():
            parent = (ctx.logdir / path).parent
            options = [p.name for p in parent.iterdir() if p.is_dir()] if parent.is_dir() else []
            raise OpError(f"no group {path!r} below the log dir.{closest(name, options)}", code=4)
        path = moved
    return path, run


def save_view(
    ctx: Context, path: str, prefs: dict[str, Any], title: str | None, finding: str | None
) -> dict[str, Any]:
    """Save what a page shows with the viewer's chart settings as a new view version.

    :param ctx: The operation context, with caller ``view``: the local account is the author.
    :param path: A group path, or a run's path.
    :param prefs: The viewer's ``{view, charts, added}`` for the page.
    :param title: The view's title.
    :param finding: The view's finding.
    :return: The new version."""
    from beamtime.ops.views import save_page

    return save_page(ctx, page_of(ctx, path)[0], prefs, title, finding)


def summary_of(
    ctx: Context, path: str, metrics: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Answer the lead metric's best run for the header, apart from the view so it loads in
    parallel.

    :param ctx: The operation context.
    :param path: A group or run path.
    :param metrics: The viewer's pins ``{y, higher}``; ``[]`` is none. Without them the view's
        first main metric leads, else the proposal's first predicted metric.
    :return: ``{kind, path, summary}``; ``summary`` is ``None`` without a lead."""
    from beamtime.views.defaults import pins_of, summary
    from beamtime.views.store import declared

    path = path.strip("/") or "."
    if metrics is None and (ctx.logdir / path).is_dir():
        metrics = declared(ctx, path)
    if metrics is None:
        metrics = pins_of(ctx, path)
    found = (
        (metrics[0]["y"], not metrics[0]["higher"], metrics[0].get("label")) if metrics else None
    )
    return {"kind": "summary", "path": path, "summary": summary(ctx, path, found)}


def run_diff(ctx: Context, run_id: str) -> dict[str, Any]:
    """Read the uncommitted changes a run recorded, for the run page's code viewer.

    :param ctx: The operation context.
    :param run_id: The run id.
    :return: ``{kind, run, text}``.
    :raises OpError: If the run recorded no diff."""
    from beamtime.ops.reading import find_run

    path = find_run(ctx, run_id) / ENV_DIR / "git.diff"
    if not path.is_file():
        raise OpError(f"run {run_id!r} recorded no git diff", code=4)
    return {"kind": "diff", "run": run_id, "text": path.read_text(errors="replace")}


def locate(ctx: Context, run_id: str, rel: str) -> Path | None:
    """Find a file inside a run directory, refusing paths that leave it.

    :param ctx: The operation context.
    :param run_id: The run id.
    :param rel: The file's path inside the run.
    :return: The file, or ``None``."""
    from beamtime.index.index import Index

    if not is_run_id(run_id):
        return None
    with Index(logdir=ctx.logdir) as index:
        run_dir = index.run_path(run_id)
    if run_dir is None:
        return None
    path = (run_dir / rel).resolve()
    if not path.is_relative_to(run_dir.resolve()) or not path.is_file():
        return None
    return path
