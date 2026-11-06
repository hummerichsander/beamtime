"""The headless renderer: a draft rendered in an installed browser, screenshots and layout checks.

The renderer is a client of ``serve``: it serves the project on a free local port for the call
and opens the draft with ``?render=1``, the view without the shell. It never downloads a
browser; without one the render is skipped and validation stays static."""

import dataclasses
import secrets
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import quote

from beamtime.ops.context import Context
from beamtime.views.store import Draft

TIME_LIMIT_S = 15
INSTALL = "uv run playwright install chromium"
SETTLED = """() => typeof window.__btBusy === "function" && window.__btBusy() === 0
  && !document.querySelector(".skeleton") && !!document.querySelector(".view .node")"""
# 46 x 90 px patches at the default width: 4,140 visual tokens, inside Claude's newer limits.
SHOT_HEIGHT = 2520
JPEG_QUALITY = 75


def page_url(group: str) -> str:
    """The ``/f/...`` path of a group or run, local or on another source, without a query.

    :param group: ``.`` or a bare path for local, ``@source/...`` for another source.
    :return: The URL path."""
    if group.startswith("@"):
        source, _, rest = group.partition("/")
        tail = "/".join(quote(part) for part in rest.split("/")) if rest else ""
        return f"/f/{source}" + (f"/{tail}" if tail else "")
    tail = "/".join(quote(part) for part in group.split("/")) if group != "." else ""
    return "/f/local" + (f"/{tail}" if tail else "")


def render_draft(
    ctx: Context,
    d: Draft,
    *,
    shots: bool,
    block: str | None = None,
    theme: str = "light",
    width: int = 1280,
) -> dict[str, Any]:
    """Render a draft once: findings from the page, and screenshots if asked.

    :param ctx: The operation context.
    :param d: The draft.
    :param shots: Whether to write screenshots.
    :param block: One block's id to screenshot instead of the page.
    :param theme: ``light`` or ``dark``.
    :param width: The page width in CSS pixels.
    :return: ``{rendered, findings, shots}``, or ``{rendered: False, reason, command}``."""
    url = f"{page_url(d.group)}?draft={quote(d.name)}&render=1&theme={theme}"
    shoot = (lambda page: screenshots(ctx, page, d, block, theme)) if shots else None
    return rendered(ctx, url, theme=theme, width=width, shoot=shoot)


def render_page(
    ctx: Context, path: str, file: Path, *, theme: str = "light", width: int = 1280
) -> dict[str, Any]:
    """Render a page's saved view once and screenshot it, full height, uncapped.

    Unlike ``render_draft``, this never cuts the shot: its only caller is the view-task
    harness's judge, which must see every block to score the page fairly.

    :param ctx: The operation context.
    :param path: The group or run path.
    :param file: Where the screenshot goes.
    :param theme: ``light`` or ``dark``.
    :param width: The page width in CSS pixels.
    :return: ``{rendered, findings, shots}``, or ``{rendered: False, reason, command}``."""
    rel = "/".join(quote(part) for part in path.split("/")) if path != "." else ""

    def shoot(page: Any) -> tuple[list[dict[str, Any]], None]:
        file.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(file), full_page=True)
        return [{"file": str(file), "block": None}], None

    url = f"/f/local/{rel}?render=1&theme={theme}"
    return rendered(ctx, url, theme=theme, width=width, shoot=shoot)


def rendered(
    ctx: Context,
    url: str,
    *,
    theme: str,
    width: int,
    shoot: Callable[[Any], tuple[list[dict[str, Any]], dict[str, Any] | None]] | None,
) -> dict[str, Any]:
    """Open a page in an installed browser: its findings, and its screenshots if asked.

    :param ctx: The operation context.
    :param url: The page's URL path with its query.
    :param theme: ``light`` or ``dark``.
    :param width: The page width in CSS pixels.
    :param shoot: Takes the settled page to its screenshots and what a page shot cut, if any.
    :return: ``{rendered, findings, shots}``, plus ``cut`` if a page shot was capped, or
        ``{rendered: False, reason, command}``."""
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        return skipped("Playwright is not installed; it comes with beamtime's serve extra")
    findings: list[dict[str, Any]] = []
    out: dict[str, Any] = {"rendered": False, "findings": findings, "shots": []}
    with serving(ctx) as (base, token), sync_playwright() as p:
        if (browser := launch(p)) is None:
            return skipped("no installed Chromium, Chrome or Edge was found")
        try:
            page = browser.new_page(
                viewport={"width": width, "height": 900}, color_scheme=theme, device_scale_factor=1
            )
            page.on("pageerror", lambda e: findings.append(error(f"page error: {e}")))
            page.on(
                "console",
                lambda m: m.type == "error" and findings.append(error(f"console: {m.text}")),
            )
            page.goto(f"{base}/f/local?token={token}&render=1")
            started = time.monotonic()
            page.goto(f"{base}{url}")
            if not settle(page):
                findings.append(error(f"the page didn't finish rendering within {TIME_LIMIT_S} s"))
            out["seconds"] = round(time.monotonic() - started, 2)
            out["rendered"] = True
            findings += page.evaluate(files(__package__).joinpath("checks.js").read_text())
            if shoot is not None:
                out["shots"], cut = shoot(page)
                if cut is not None:
                    out["cut"] = cut
        except Error as e:
            findings.append(error(f"the render failed: {e}"))
        finally:
            browser.close()
    return out


def settle(page: Any) -> bool:
    """Wait until no call or chart build is pending, twice, a moment apart.

    :param page: The Playwright page.
    :return: Whether it settled within the time limit."""
    from playwright.sync_api import TimeoutError

    deadline = time.monotonic() + TIME_LIMIT_S
    try:
        for _ in range(2):
            left = max(0.1, deadline - time.monotonic())
            page.wait_for_function(SETTLED, timeout=left * 1000)
            page.wait_for_timeout(300)
    except TimeoutError:
        return False
    return True


def screenshots(
    ctx: Context, page: Any, d: Draft, block: str | None, theme: str
) -> tuple[list[dict], dict[str, Any] | None]:
    """Write the page's (or one block's) screenshot into ``.beamtime/renders/<draft>/``.

    A page shot is capped at ``SHOT_HEIGHT``: height is what costs visual tokens, and a tall page
    makes an agent judge blocks it never saw. A block shot is never cut; it is already one block.

    :param ctx: The operation context.
    :param page: The settled page.
    :param d: The draft.
    :param block: One block's id, or ``None`` for the page.
    :param theme: The theme, part of the file name.
    :return: ``{file, block}`` per screenshot, and what the page shot cut, if anything."""
    folder = d.dir.parent.parent / "renders" / d.name
    folder.mkdir(parents=True, exist_ok=True)
    if block is not None:
        target = page.locator(f'[data-block-id="{block}"]')
        if not target.count():
            shot = {"file": None, "block": block, "error": f"no block {block!r} in the draft"}
            return [shot], None
        file = folder / f"{block}-{theme}.jpg"
        target.first.screenshot(path=str(file), type="jpeg", quality=JPEG_QUALITY)
        return [{"file": str(file), "block": block}], None
    file = folder / f"page-{theme}.jpg"
    full = page.evaluate("document.documentElement.scrollHeight")
    shown = min(full, SHOT_HEIGHT)
    cut = None
    if shown < full:
        cut = {"page_height": full, "shown_height": shown, "blocks_below": below(page, shown)}
    clip = {"x": 0, "y": 0, "width": page.viewport_size["width"], "height": shown}
    page.screenshot(path=str(file), full_page=True, clip=clip, type="jpeg", quality=JPEG_QUALITY)
    return [{"file": str(file), "block": None}], cut


def below(page: Any, shown: int) -> list[str]:
    """List the ids of blocks lying, even partly, below a screenshot's cut height.

    :param page: The settled page.
    :param shown: How many pixels of the page the screenshot shows.
    :return: Block ids, in the page's top-to-bottom order."""
    return page.evaluate(
        """(shown) => [...document.querySelectorAll("[data-block-id]")]
          .filter((el) => el.getBoundingClientRect().bottom + window.scrollY > shown)
          .map((el) => el.dataset.blockId)""",
        shown,
    )


def launch(p: Any) -> Any:
    """Launch an installed browser: Playwright's Chromium, else Chrome, else Edge.

    :param p: The Playwright instance.
    :return: The browser, or ``None``."""
    from playwright.sync_api import Error

    for channel in (None, "chrome", "msedge"):
        try:
            return p.chromium.launch(**({"channel": channel} if channel else {}))
        except Error:
            continue
    return None


@contextmanager
def serving(ctx: Context) -> Iterator[tuple[str, str]]:
    """Serve the project on a free local port with a fresh token, for one render.

    :param ctx: The operation context.
    :return: The base URL and the token, while serving."""
    import uvicorn

    from beamtime.remote.sources import Sources, spec_of
    from beamtime.serve.app import build
    from beamtime.serve.auth import TokenGuard
    from beamtime.serve.live import Hub
    from beamtime.serve.server import bind

    sock = bind(0)
    port = sock.getsockname()[1]
    token = secrets.token_urlsafe(24)
    # a draft on another source needs its queries, and a remote-drafted group, routed; a call
    # already holding connections (a running serve) lends them rather than opening new ones.
    owned = ctx.sources is None
    configured = ctx.settings.get("remotes") or {}
    sources = ctx.sources
    if sources is None and configured:
        sources = Sources([spec_of(n, c) for n, c in configured.items()])
    app = build(ctx=dataclasses.replace(ctx, caller="view", sources=sources), hub=Hub())
    config = uvicorn.Config(
        TokenGuard(app, token=token, port=port), log_level="warning", lifespan="on"
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.02)
    try:
        yield f"http://127.0.0.1:{port}", token
    finally:
        server.should_exit = True
        thread.join(5)
        sock.close()
        if sources is not None and owned:
            sources.close()


def skipped(reason: str) -> dict[str, Any]:
    """Say that the render was skipped and how the user gets a browser.

    :param reason: Why.
    :return: The result."""
    return {"rendered": False, "reason": reason, "command": INSTALL, "findings": [], "shots": []}


def error(message: str) -> dict[str, Any]:
    """Make an error finding of the page.

    :param message: What went wrong.
    :return: The finding."""
    return {"level": "error", "message": message}
