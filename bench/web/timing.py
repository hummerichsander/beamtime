"""Measure the UI's timing budgets on a scale-M log dir: python bench/web/timing.py [dir].

First view (warm cache): from navigation to a complete header and visible blocks, charts excluded.
Group to group: from a click in the tree to the new group's header and blocks.
Hover on a chart: the longest pointer event (Event Timing API) while sweeping across a chart.
"""

import re
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from beamtime.synth import generate

READY = """() => {
  const v = document.querySelector('.view');
  return !!v && !v.querySelector('.skeleton') && !!document.querySelector('.header .facts');
}"""
# the longest pointer handling while the pointer sweeps over a chart, from the Event Timing API.
WATCH = """() => { window.__events = []; new PerformanceObserver((l) => window.__events.push(
  ...l.getEntries().map((e) => e.duration))).observe({ type: "event", durationThreshold: 16, buffered: false }); }"""


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp()) / "proj"
    if not (root / "beamtime").is_dir():
        (root / ".git").mkdir(parents=True, exist_ok=True)
        generate(root / "beamtime", seed=0, scale="m")
    script = Path(sys.executable).parent / "beamtime"
    subprocess.run([script, "--root", root, "reindex"], check=True, capture_output=True)
    proc = subprocess.Popen([script, "--root", root, "serve", "--port", "0"],
                            stderr=subprocess.PIPE, text=True)
    url = None
    while url is None:
        if m := re.search(r"http://localhost:\d+/f/local\?token=\S+", proc.stderr.readline()):
            url = m.group(0)
    base = url.split("/f/local")[0]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(url)
            page.wait_for_function(READY)
            # the tree loads after the page; the measures need its groups.
            page.wait_for_function("() => document.querySelectorAll('a.tree-item').length > 2")
            folders = [a.get_attribute("href") for a in page.query_selector_all("a.tree-item")][1:6]
            first, nav = [], []
            for href in folders * 3:
                t = time.perf_counter()
                page.goto(base + href)
                page.wait_for_function(READY)
                first.append(time.perf_counter() - t)
            for href in folders * 3:
                page.goto(base + "/f/local")
                page.wait_for_function(READY)
                page.hover(f"a.tree-item[href='{href}']")
                page.wait_for_timeout(150)
                t = time.perf_counter()
                page.click(f"a.tree-item[href='{href}']")
                page.wait_for_function(f"() => location.pathname === '{href}' && ({READY})()")
                nav.append(time.perf_counter() - t)
            hover = []
            token = url.split("token=")[1]
            groups = page.request.post(f"{base}/api/groups", data={}, headers={"authorization": f"Bearer {token}"}).json()
            rows = [dict(zip(groups["columns"], r)) for r in groups["rows"]]
            # the groups with the most runs of their own: the charts with the most curves.
            busy = sorted((r for r in rows if r["direct"]), key=lambda r: -r["direct"])[:3]
            print("hover on:", [(r["path"], r["direct"]) for r in busy])
            for row in busy:
                page.goto(f"{base}/f/local/{row['path']}")
                page.wait_for_function(READY)
                page.wait_for_selector(".chart canvas", timeout=10_000)
                page.evaluate(WATCH)
                box = page.locator(".chart .u-over").first.bounding_box()
                for i in range(40):
                    page.mouse.move(box["x"] + box["width"] * (i + 1) / 41, box["y"] + box["height"] / 2)
                    page.wait_for_timeout(16)
                page.wait_for_timeout(300)
                hover.append(max(page.evaluate("window.__events") or [0]) / 1000)
            browser.close()
    finally:
        proc.terminate()
        proc.wait(10)
    measures = [("first view", first, 0.3), ("group to group", nav, 0.1), ("hover on a chart", hover, 0.05)]
    for name, xs, budget in measures:
        print(f"{name}: median {statistics.median(xs) * 1000:.0f} ms, "
              f"max {max(xs) * 1000:.0f} ms (budget {budget * 1000:.0f} ms)")


if __name__ == "__main__":
    main()
