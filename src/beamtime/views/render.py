"""The headless renderer: a draft rendered in an installed browser, screenshots and layout checks.

The renderer is a client of ``serve``: it serves the project on a free local port for the call
and opens the draft with ``?render=1``, the view without the shell. It never downloads a
browser; without one the render is skipped and validation stays static."""

import dataclasses
import secrets
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.resources import files
from typing import Any
from urllib.parse import quote

from beamtime.ops.context import Context
from beamtime.views.store import Draft

TIME_LIMIT_S = 15
INSTALL = "uv run playwright install chromium"
SETTLED = """() => typeof window.__btBusy === "function" && window.__btBusy() === 0
  && !document.querySelector(".skeleton") && !!document.querySelector(".view .node")"""


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
            path = "/".join(quote(part) for part in d.group.split("/")) if d.group != "." else ""
            url = f"{base}/f/local/{path}?draft={quote(d.name)}&render=1&theme={theme}"
            page.goto(f"{base}/f/local?token={token}&render=1")
            started = time.monotonic()
            page.goto(url)
            if not settle(page):
                findings.append(error(f"the page didn't finish rendering within {TIME_LIMIT_S} s"))
            out["seconds"] = round(time.monotonic() - started, 2)
            out["rendered"] = True
            findings += page.evaluate(files(__package__).joinpath("checks.js").read_text())
            if shots:
                out["shots"] = screenshots(ctx, page, d, block, theme)
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


def screenshots(ctx: Context, page: Any, d: Draft, block: str | None, theme: str) -> list[dict]:
    """Write the page's (or one block's) screenshot into ``.beamtime/renders/<draft>/``.

    :param ctx: The operation context.
    :param page: The settled page.
    :param d: The draft.
    :param block: One block's id, or ``None`` for the page.
    :param theme: The theme, part of the file name.
    :return: ``{file, block}`` per screenshot."""
    folder = d.dir.parent.parent / "renders" / d.name
    folder.mkdir(parents=True, exist_ok=True)
    if block is not None:
        target = page.locator(f'[data-block-id="{block}"]')
        if not target.count():
            return [{"file": None, "block": block, "error": f"no block {block!r} in the draft"}]
        file = folder / f"{block}-{theme}.png"
        target.first.screenshot(path=str(file))
        return [{"file": str(file), "block": block}]
    file = folder / f"page-{theme}.png"
    page.screenshot(path=str(file), full_page=True)
    return [{"file": str(file), "block": None}]


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

    from beamtime.serve.app import build
    from beamtime.serve.auth import TokenGuard
    from beamtime.serve.live import Hub
    from beamtime.serve.server import bind

    sock = bind(0)
    port = sock.getsockname()[1]
    token = secrets.token_urlsafe(24)
    app = build(ctx=dataclasses.replace(ctx, caller="view"), hub=Hub())
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
