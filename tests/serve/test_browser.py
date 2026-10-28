import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from beamtime.format.io import json_line
from beamtime.serve.app import STATIC

sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture
def server(project: Path):
    """``beamtime serve`` on a free port for the generated project.

    :param project: The project root.
    :return: The URL with the token."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    script = Path(sys.executable).parent / "beamtime"
    proc = subprocess.Popen(
        [script, "serve", "--port", "0"], cwd=project, stderr=subprocess.PIPE, text=True
    )
    url = None
    deadline = time.time() + 30
    while time.time() < deadline and url is None:
        line = proc.stderr.readline()
        if m := re.search(r"(http://localhost:\d+)/f/local\?token=(\S+)", line):
            url = m.group(0)
    if url is None:
        proc.kill()
        pytest.fail("serve printed no URL")
    yield url
    proc.terminate()
    proc.wait(10)


@pytest.fixture
def page():
    """A headless Chromium page; skipped where no Chromium can run.

    :return: The page."""
    with sync_api.sync_playwright() as p:
        browser = None
        for kw in ({}, {"channel": "chrome"}):
            try:
                browser = p.chromium.launch(**kw)
                break
            except Exception:
                continue
        if browser is None:
            pytest.skip("no Chromium available (playwright install chromium)")
        yield browser.new_page(viewport={"width": 1280, "height": 900})
        browser.close()


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
    assert page.locator(".preds .pred .sym.tone-good").count() >= 2
    # a view transition that hangs reports itself only after its timeout.
    page.wait_for_timeout(4500)
    assert errors == []

    asked: list[dict] = []
    page.on("request", lambda r: r.url.endswith("/api/series") and asked.append(json.loads(r.post_data)))
    over = page.locator(".chart .u-over").first.bounding_box()
    page.mouse.move(over["x"] + over["width"] * 0.2, over["y"] + 40)
    page.mouse.down()
    page.mouse.move(over["x"] + over["width"] * 0.5, over["y"] + 50, steps=6)
    page.mouse.up()
    page.wait_for_timeout(1000)
    assert any(q.get("steps") for q in asked), "drag-zoom refetches the window"
    asked.clear()
    page.select_option(".view-bar select >> nth=1", "")
    page.wait_for_timeout(1000)
    assert asked and all("seeds" not in q for q in asked), "aggregation applies to every chart"
    page.click("table.runs tbody tr:nth-child(1) .swatch")
    assert page.locator("table.runs tbody tr.hidden-run").count() == 1
    page.click(".notes .note >> nth=0 >> .note-toggle")
    page.wait_for_selector(".notes .note.open .md p")

    # text edits in place: a note's title saves as one new note that supersedes the old one.
    notes_dir = project / "beamtime" / "scaling" / "lr-sweep" / "notes"
    before = set(notes_dir.iterdir())
    page.click(".notes .note >> nth=0 >> .note-title")
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type("Edited in the browser.")
    page.keyboard.press("Enter")
    page.wait_for_selector(".notes .note-title:has-text('Edited in the browser.')")
    page.wait_for_timeout(500)
    added = set(notes_dir.iterdir()) - before
    assert len(added) == 1 and "supersedes:" in added.pop().read_text()

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
