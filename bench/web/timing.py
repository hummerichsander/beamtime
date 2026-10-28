"""Measure the UI's timing budgets on a scale-M log dir: python bench/web/timing.py [dir].

First view (warm cache): from navigation to a complete frame and visible blocks, charts excluded.
Folder to folder: from a click in the tree to the new folder's frame and blocks.
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
  return !!v && !v.querySelector('.skeleton') && !document.querySelector('.stat-value.pending')
    && !!document.querySelector('.frame .counts');
}"""


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
            browser.close()
    finally:
        proc.terminate()
        proc.wait(10)
    for name, xs, budget in [("first view", first, 0.3), ("folder to folder", nav, 0.1)]:
        print(f"{name}: median {statistics.median(xs) * 1000:.0f} ms, "
              f"max {max(xs) * 1000:.0f} ms (budget {budget * 1000:.0f} ms)")


if __name__ == "__main__":
    main()
