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
    page.goto(f"{base}/f/local/scaling/lr-sweep")
    page.wait_for_selector("text=Predictions")
    page.wait_for_selector(".chart canvas")
    assert page.locator(".preds .pred .sym.tone-good").count() >= 2

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
