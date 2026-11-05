import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from beamtime.format.io import json_line

pytest.importorskip("playwright.sync_api")


def box_of(page, selector: str) -> dict:
    """Wait until a chart's overlay is laid out, and measure it.

    A chart is drawn, and redrawn when more of its data arrives, a moment after its canvas
    appears; meanwhile its overlay has no box.

    :param page: The Playwright page.
    :param selector: The overlay, e.g. ``.chart .u-over`` (the first match counts).
    :return: Its bounding box."""
    deadline = time.time() + 10
    while (box := page.locator(selector).first.bounding_box()) is None or not box["width"]:
        assert time.time() < deadline, f"{selector} never got a size"
        page.wait_for_timeout(100)
    return box


def test_folder_run_and_live_curve(server: str, page, project: Path, roles: dict) -> None:
    """The shell loads without errors, navigates without reloads, and curves grow live."""
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    base = server.split("/f/local")[0]
    page.goto(server)
    page.wait_for_selector(".tree-item")
    page.click("a.tree-item:has-text('scaling')")
    page.wait_for_url(f"{base}/f/local/scaling")
    page.wait_for_selector(".page h1:has-text('scaling')", timeout=2000)
    page.click("a.group-row:has-text('lr-sweep')")
    page.wait_for_selector(".page h1:has-text('lr-sweep')", timeout=2000)
    page.wait_for_selector(".chart canvas")
    assert page.locator(".checks .check.tone-good").count() >= 2
    # a view transition that hangs reports itself only after its timeout.
    page.wait_for_timeout(4500)
    assert errors == []

    asked: list[dict] = []
    page.on("request", lambda r: r.url.endswith("/api/series") and asked.append(json.loads(r.post_data)))
    over = box_of(page, ".chart .u-over")
    page.mouse.move(over["x"] + over["width"] * 0.2, over["y"] + 40)
    page.mouse.down()
    page.mouse.move(over["x"] + over["width"] * 0.5, over["y"] + 50, steps=6)
    page.mouse.up()
    page.wait_for_timeout(1000)
    assert any(q.get("steps") for q in asked), "drag-zoom refetches the window"
    asked.clear()
    first = page.locator(".chart-frame").first
    first.hover()
    first.locator("button[aria-label='Chart settings']").click()
    page.locator(".chart-settings:popover-open select").first.select_option("_t")
    page.wait_for_timeout(1000)
    assert asked and all(q["x"] == "_t" for q in asked), "a chart's own settings refetch only it"
    page.keyboard.press("Escape")
    page.click("table.runs tbody tr:nth-child(1) .swatch")
    assert page.locator("table.runs tbody tr.hidden-run").count() == 1
    page.click(".notes .note >> nth=0 >> .note-toggle")
    page.wait_for_selector(".notes .note.open .md p")

    # text edits in place: a note's title saves as one new note that supersedes the old one.
    notes_dir = project / "beamtime" / "scaling" / "lr-sweep" / "notes"
    before = set(notes_dir.iterdir())
    page.click(".notes .note >> nth=0 >> .note-title")
    page.wait_for_selector(".notes textarea:focus")
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type("Edited in the browser.")
    page.keyboard.press("Enter")
    page.wait_for_selector(".notes .note-title:has-text('Edited in the browser.')")
    page.wait_for_timeout(500)
    added = set(notes_dir.iterdir()) - before
    assert len(added) == 1 and "supersedes:" in added.pop().read_text()

    # a new note: choosing its type keeps the form open; title and body are saved together.
    before = set(notes_dir.iterdir())
    page.click(".notes-block .block-action button, .collapsible:has(.notes) .block-action button")
    page.select_option(".new-note select", "idea")
    page.fill(".new-note .new-note-title", "Try a warmup.")
    page.fill(".new-note textarea", "Maybe **500** steps.")
    page.click(".new-note button[type=submit]")
    page.wait_for_selector(".notes .note-title:has-text('Try a warmup.')")
    added = set(notes_dir.iterdir()) - before
    text = added.pop().read_text()
    assert "type: idea" in text and "Maybe **500** steps." in text

    # deleting asks once, then moves the note to the trash.
    row = page.locator(".notes .note:has(.note-title:has-text('Try a warmup.'))")
    row.hover()
    row.locator("button[aria-label^='Delete this note']").click()
    row.locator(".note-confirm button:has-text('Delete')").click()
    page.wait_for_selector(".notes .note-title:has-text('Try a warmup.')", state="detached")
    assert list((project / "beamtime" / "_trash").rglob("*.md"))

    # "add text" puts a text panel at the top, open for typing; saving writes a view version.
    page.goto(f"{base}/f/local/scaling/lr-sweep")
    page.click(".view-source button:has-text('add text')")
    page.wait_for_selector(".markdown-block textarea:focus")
    page.keyboard.type("A *first* look.")
    page.keyboard.press("ControlOrMeta+Enter")
    page.wait_for_selector(".markdown-block em:has-text('first')")
    assert list((project / "beamtime" / "scaling" / "lr-sweep" / "view").glob("*.yaml"))

    # the timeline draws runs and notes, and zooms with the wheel.
    page.goto(f"{base}/timeline?from=scaling")
    page.wait_for_selector(".timeline-chart canvas")
    box = box_of(page, ".timeline-chart .u-over")
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.wheel(0, -400)
    page.wait_for_timeout(300)
    assert page.locator(".timeline-chart button[aria-checked='true']").count() == 0, "zoomed in"

    running = roles["running"]
    page.goto(f"{base}/r/{running}")
    page.wait_for_url(re.compile(rf".*/f/local/.+/{running}$"))
    page.wait_for_selector(".chart canvas")
    page.evaluate("window.__marker = 1")
    series: list[str] = []
    page.on("request", lambda r: r.url.endswith("/api/series") and series.append(r.url))
    run_dir = next(project.glob(f"beamtime/**/{running}"))
    lines = (run_dir / "_metrics.jsonl").read_text().splitlines()
    step = json.loads(lines[-1])["_step"]
    with (run_dir / "_metrics.jsonl").open("ab") as f:
        for i in range(1, 50):
            f.write(json_line({"_step": step + i, "_t": time.time(), "train/loss": 0.1}))
    (run_dir / "_run.json").touch()
    deadline = time.time() + 15
    while not series and time.time() < deadline:
        page.wait_for_timeout(200)
    assert series, "no refetch after new metric lines"
    assert page.evaluate("window.__marker") == 1
    assert errors == []


def test_custom_blocks_share_hover_downloads_and_expand(project: Path, page) -> None:
    """A custom block's frame shares the hovered run with the page, downloads through the page, and
    expands into the page's dialog, like the built-in charts."""
    import yaml

    from beamtime.ops import call
    from beamtime.ops.context import Context

    ctx = Context.make()
    sweep = "scaling/lr-sweep"
    call("view new", {"group": sweep, "from": "custom", "name": "pm"}, ctx)
    file = project / ".beamtime" / "drafts" / "pm" / "view.yaml"
    data = yaml.safe_load(file.read_text())
    data["finding"] = "x"
    data["body"].append({"table": {"id": "runs", "columns": ["run.name", "config.lr", "config.seed"]}})
    file.write_text(yaml.safe_dump(data, sort_keys=False))
    call("view save", {"draft": "pm"}, ctx)
    script = Path(sys.executable).parent / "beamtime"
    proc = subprocess.Popen([script, "serve", "--port", "0"], cwd=project, stderr=subprocess.PIPE, text=True)
    try:
        url = None
        while url is None:
            if m := re.search(r"(http://localhost:\d+)/f/local\?token=(\S+)", proc.stderr.readline()):
                url = m
        page.goto(f"{url[1]}/f/local/{sweep}?token={url[2]}")
        frame = page.frame_locator(".custom-frame iframe")
        frame.locator("rect").first.wait_for(timeout=30_000)
        # the frame is sandboxed (an opaque origin): its fonts are CORS requests.
        inner = next(f for f in page.frames if "kit/frame" in f.url)
        assert inner.evaluate("document.fonts.load('12.5px \"IBM Plex Sans\"').then((f) => f.length > 0)")
        muted = "getComputedStyle(document.documentElement).getPropertyValue('--muted')"
        light = inner.evaluate(muted)
        toggle = page.locator(".topbar-actions [aria-label^='Theme']")
        while "(switch to system)" not in toggle.get_attribute("aria-label"):
            toggle.click()
            page.wait_for_timeout(300)
        page.wait_for_timeout(300)
        assert inner.evaluate(muted) != light, "the frame's tokens follow the page's mode"
        frame.locator("rect").nth(1).hover()
        page.wait_for_selector("table.runs tr.hovered", timeout=5_000)
        with page.expect_download() as download:
            page.locator(".custom-block .chart-tools [aria-label^='Download']").click()
        assert download.value.suggested_filename == "phase-map.svg"
        page.locator(".custom-block .chart-tools [aria-label='Expand']").click()
        page.frame_locator("dialog.chart-dialog[open] iframe").locator("rect").first.wait_for(timeout=30_000)
    finally:
        proc.terminate()
        proc.wait(10)


def test_live_page_fixture_follows_a_running_writer(live_page) -> None:
    """The fixture's writer appears in the app and its metrics keep arriving."""
    live_page.goto("/f/local/live")
    live_page.page.wait_for_selector(".chart canvas")
    metrics = next((live_page.project / "beamtime" / "live").glob("*/_metrics.jsonl"))
    before = len(metrics.read_text().splitlines())
    live_page.page.wait_for_timeout(1000)
    assert len(metrics.read_text().splitlines()) > before
    live_page.stop_writer()
    assert live_page.writer.returncode == 0
