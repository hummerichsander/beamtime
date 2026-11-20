import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

ROOT = Path(__file__).parents[1]
GALLERY = ROOT / "design" / "gallery.html"
COMPONENTS = (
    "Section", "Header", "Proposal", "Mark", "Table", "Chart", "Images", "Note", "Stat",
    "Sym", "Tag", "Button", "IconButton", "Field", "Notice", "Config",
)  # fmt: skip


def script(name: str, *args: object) -> subprocess.CompletedProcess:
    """Run one of the design scripts.

    :param name: The script's name in ``scripts/``.
    :param args: Its arguments.
    :return: The finished process."""
    command = [sys.executable, ROOT / "scripts" / name, *args]
    return subprocess.run(command, capture_output=True, text=True)


def test_tokens_css_is_current() -> None:
    """The committed stylesheet is what the tokens generate."""
    assert script("build-tokens", "--check").returncode == 0


def test_favicons_follow_the_system_theme_and_are_bundled() -> None:
    """The mark's rest and live icons recolor in dark mode, the live one loops and stops under reduced motion, and both ship."""
    tokens = (ROOT / "design" / "tokens.css").read_text()
    light, dark = re.findall(r"--accent: (#\w+)", tokens)[:2]
    static = ROOT / "src" / "beamtime" / "serve" / "static"
    for name in ("favicon.svg", "favicon-live.svg"):
        svg = (ROOT / "design" / name).read_text()
        assert "@media (prefers-color-scheme: dark)" in svg
        assert f"stroke: {light};" in svg and f"stroke: {dark};" in svg
        assert (static / name).read_bytes() == (ROOT / "design" / name).read_bytes()
    live = (ROOT / "design" / "favicon-live.svg").read_text()
    assert "2.8s" in live and "infinite" in live
    assert re.search(r"prefers-reduced-motion: reduce\)\s*{[^}]*animation: none", live)
    assert "animation" not in (ROOT / "design" / "favicon.svg").read_text()
    assert script("build-tokens", "--check").returncode == 0
    index = (static / "index.html").read_text()
    assert '<link rel="icon" href="/static/favicon.svg"' in index


def test_app_css_has_no_raw_values() -> None:
    """The app's and the docs site's stylesheets take colors and type from tokens."""
    done = script("check-design")
    assert done.returncode == 0, done.stderr


def test_the_check_finds_raw_values(tmp_path: Path) -> None:
    """Raw colors and pixel font sizes fail; tokens and relative sizes don't."""
    css = tmp_path / "x.css"
    css.write_text("a { color: #fff; font-size: 12.5px; }\nb { font: 700 13px serif; }\n")
    done = script("check-design", css)
    assert done.returncode == 1
    assert all(w in done.stderr for w in ("#fff", "12.5px", "13px"))
    css.write_text("a { color: var(--ink); font-size: 0.8em; font: var(--text-small); inline-size: 12px; }\n")
    assert script("check-design", css).returncode == 0


def test_every_component_has_its_page_and_gallery_entry() -> None:
    """The gallery shows every component, and each has its rules and markup."""
    text = GALLERY.read_text()
    for name in COMPONENTS:
        assert f'id="{name}"' in text
        page = (ROOT / "design" / "components" / f"{name}.md").read_text()
        assert "```html" in page, name


@pytest.fixture(scope="module")
def browser():
    """A headless Chromium; skipped where none can run.

    :return: The browser."""
    sync_api = pytest.importorskip("playwright.sync_api")
    from beamtime.views.render import launch

    with sync_api.sync_playwright() as p:
        if (browser := launch(p)) is None:
            pytest.skip("no Chromium available (playwright install chromium)")
        yield browser
        browser.close()


def render(browser, theme: str, width: int, shots: Path) -> dict:
    """Open the gallery in a theme and take its screenshot.

    :param browser: The browser.
    :param theme: ``light`` or ``dark``.
    :param width: The viewport's width.
    :param shots: Where the screenshot goes.
    :return: What the page reports."""
    page = browser.new_page(viewport={"width": width, "height": 900})
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.on("requestfailed", lambda r: errors.append(f"failed {r.url}"))
    page.goto(GALLERY.as_uri())
    while page.evaluate("document.documentElement.dataset.theme") != theme:
        page.click("#toggle")
    # fonts.ready resolves at once when the page has not requested its fonts yet.
    page.wait_for_function(
        """() => ['XCharter', 'IBM Plex Sans', 'IBM Plex Mono'].every(
          (name) => [...document.fonts].some((f) => f.family === name && f.status === 'loaded')
        )"""
    )
    page.screenshot(path=shots / f"gallery-{theme}-{width}.png", full_page=True)
    state = page.evaluate(
        """() => ({
          background: getComputedStyle(document.documentElement).backgroundColor,
          ink: getComputedStyle(document.body).color,
          fonts: [...document.fonts].filter((f) => f.status === 'loaded').map((f) => f.family),
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        })"""
    )
    page.close()
    return state | {"errors": errors}


def test_the_gallery_renders_in_both_themes(browser, tmp_path: Path) -> None:
    """Light and dark render without errors, with their fonts, at desktop and phone width."""
    shots = Path(os.environ.get("DESIGN_SHOTS", tmp_path))
    shots.mkdir(parents=True, exist_ok=True)
    seen = {}
    for theme in ("light", "dark"):
        for width in (1280, 390):
            state = render(browser, theme, width, shots)
            assert state["errors"] == [], (theme, width)
            assert state["overflow"] <= 0, (theme, width)
            assert {"XCharter", "IBM Plex Sans", "IBM Plex Mono"} <= set(state["fonts"]), (theme, width)
            seen[theme] = state
    assert seen["light"]["background"] != seen["dark"]["background"]
    assert seen["light"]["ink"] != seen["dark"]["ink"]
    tokens = (ROOT / "design" / "tokens.css").read_text()
    # the same values the tokens give; rgb() here, hex there.
    paper = re.search(r"--paper: #(\w{2})(\w{2})(\w{2})", tokens).groups()
    assert seen["light"]["background"] == "rgb({}, {}, {})".format(*(int(c, 16) for c in paper))


def test_the_mark_gathers_left_on_hover(browser) -> None:
    """The middle and right stroke move 2 and 4 units left on hover, with or without reduced motion (which only drops the movement)."""
    reads = {}
    for motion in ("no-preference", "reduce"):
        page = browser.new_page(viewport={"width": 1280, "height": 900}, reduced_motion=motion)
        page.goto(GALLERY.as_uri())
        mark = page.locator("#Mark svg.mark").first
        mark.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        rest = page.evaluate("[...document.querySelectorAll('#Mark svg.mark')[0].querySelectorAll('path')].map((p) => getComputedStyle(p).transform)")
        mark.hover()
        page.wait_for_timeout(600)
        hover = page.evaluate("[...document.querySelectorAll('#Mark svg.mark')[0].querySelectorAll('path')].map((p) => getComputedStyle(p).transform)")
        reads[motion] = (rest, hover)
        page.close()
    for rest, hover in reads.values():
        assert rest == ["none", "none", "none"]
        assert hover[0] == "none"
        assert hover[1] == "matrix(1, 0, 0, 1, -2, 0)"
        assert hover[2] == "matrix(1, 0, 0, 1, -4, 0)"
