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
    settings = page.locator(".chart-settings:popover-open")
    settings.get_by_role("combobox", name="x axis").click()
    settings.get_by_role("option", name="wall time").click()
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

    # the type menu supersedes too, keeping the body and evidence; only the type line changes.
    # (nth=0 is the group's verdict note, whose type is fixed; nth=1 is a plain observation.)
    old_path = next(p for p in notes_dir.iterdir() if "type: observation" in p.read_text())
    old_text = old_path.read_text()
    before = set(notes_dir.iterdir())
    page.click(".notes .note >> nth=1 >> button[aria-label=\"Change the note's type\"]")
    page.click(".menu-list button:has-text('theory')")
    page.wait_for_timeout(500)
    added = set(notes_dir.iterdir()) - before
    assert len(added) == 1
    new_text = added.pop().read_text()
    assert "type: theory" in new_text
    # the body and the description are byte-identical; the evidence still names the same run
    # (its YAML shorthand may be rewritten, since this goes through the op layer, not the raw file).
    assert old_text.rsplit("---", 1)[-1].strip() == new_text.rsplit("---", 1)[-1].strip()
    old_description = next(l for l in old_text.splitlines() if l.startswith("description:"))
    assert old_description in new_text
    run_id = re.search(r"\d{8}-\d{6}-\w+", old_text.split("evidence:")[1]).group()
    assert run_id in new_text

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


def wait_until(condition, timeout: float = 15.0) -> None:
    """Poll a condition until it holds; the page's own CSP forbids ``wait_for_function``.

    :param condition: A function returning a truthy value when done.
    :param timeout: Seconds to wait at most."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return
        time.sleep(0.1)
    raise AssertionError("condition not met in time")


def test_the_title_and_favicon_show_a_running_run(live_page) -> None:
    """A group with a running run gets a (1) count in its title and a dot on its favicon."""
    page = live_page.page
    live_page.goto("/f/local/live")
    page.wait_for_selector(".chart canvas")
    wait_until(lambda: page.title().startswith("(1) live"))
    assert page.title().endswith("· Beamtime")
    href = page.eval_on_selector("link[rel=icon]", "el => el.href")
    assert href.startswith("data:image/png")
    live_page.stop_writer()
    wait_until(lambda: page.title() == "live · Beamtime", timeout=30)
    href = page.eval_on_selector("link[rel=icon]", "el => el.href")
    assert href.endswith("/static/favicon.svg")


LAST_STEP = """
const { html } = bt.preact;

function Last() {
  const d = bt.useData("loss");
  const x = d.curves[0]?.x ?? [];
  return html`<p id="last-step">${x.length ? x[x.length - 1] : "none"}</p>`;
}

export default function render(root) {
  bt.preact.render(html`<${Last} />`, root);
}
"""


def last_step(page) -> int:
    """Read the step a custom block shows, or -1 before it shows one.

    :param page: The Playwright page.
    :return: The step."""
    text = page.frame_locator(".custom-frame iframe").locator("#last-step").inner_text(timeout=5000)
    return int(text) if text.isdigit() else -1


def test_custom_blocks_follow_live_data(live_page) -> None:
    """A custom block on ``bt.useData`` keeps up with a running experiment, asks for its code
    once, and does not turn into an error after the experiment stops."""
    import yaml

    from beamtime.ops import call
    from beamtime.ops.context import Context

    project, page = live_page.project, live_page.page
    ctx = Context.make()
    call("view new", {"group": "live", "name": "last"}, ctx)
    draft = project / ".beamtime" / "drafts" / "last"
    view = {
        "schema": 1,
        "title": "live",
        "finding": "x",
        "body": [
            {
                "custom": {
                    "id": "last",
                    "code": "code/last.js",
                    "queries": {"loss": {"series": {"y": ["live/loss"], "points": 50}}},
                }
            }
        ],
    }
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    (draft / "code").mkdir()
    (draft / "code" / "last.js").write_text(LAST_STEP)
    call("view save", {"draft": "last"}, ctx)

    asked: list[str] = []
    page.on("request", lambda r: r.url.rsplit("/", 1)[-1] in ("code", "series") and asked.append(r.url.rsplit("/", 1)[-1]))
    live_page.goto("/f/local/live")
    page.wait_for_selector(".custom-frame iframe")
    deadline = time.time() + 30
    while last_step(page) < 0:
        assert time.time() < deadline, "the block never showed a step"
        page.wait_for_timeout(200)
    first = last_step(page)
    page.wait_for_timeout(10_000)
    assert last_step(page) > first + 10, "the block shows the step it started with"
    assert asked.count("code") == 1, "the code is immutable, so it is fetched once"

    live_page.stop_writer()
    page.wait_for_timeout(20_000)
    assert page.locator(".custom-error").count() == 0


def test_live_ticks_refetch_only_what_changed(live_page) -> None:
    """A metric tick refetches series, not the authored calls view, notes and memory_show."""
    page = live_page.page
    asked: list[str] = []
    page.on(
        "request",
        lambda r: r.url.rsplit("/", 1)[-1] in ("series", "view", "notes", "memory_show")
        and asked.append(r.url.rsplit("/", 1)[-1]),
    )
    live_page.goto("/f/local/live")
    page.wait_for_selector(".chart canvas")
    asked.clear()
    page.wait_for_timeout(5000)
    assert "series" in asked
    assert not {"view", "notes", "memory_show"} & set(asked)


def test_nested_configs_read_well_everywhere(server: str, page, project: Path) -> None:
    """A real, nested config shows as a tree in the drawer and on the run page, as the varying keys on
    the group page, and as short labels and summaries in tables: never as [object Object]."""
    import yaml

    from beamtime.ops import call
    from beamtime.ops.context import Context

    base = server.split("/f/local")[0]
    token = server.split("token=")[1]
    group = "realistic/egnn-bench"
    ctx = Context.make()
    call("view new", {"group": group, "name": "nested"}, ctx)
    draft = project / ".beamtime" / "drafts" / "nested"
    view = yaml.safe_load((draft / "view.yaml").read_text())
    columns = ["run.name", "config.hydrantic", "config.hydrantic.trainer.max_epochs", "config.hparams.egnn.vector_channels"]
    view["body"].append({"table": {"id": "nested", "title": "Nested", "columns": columns}})
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    call("view save", {"draft": "nested"}, ctx)

    page.goto(f"{base}/f/local/{group}?token={token}")
    page.wait_for_selector("table.kv")
    hyper = page.locator("section.collapsible:has(h3:has-text('Hyperparameters'))")
    assert "arm" in hyper.inner_text() and "large, medium, small" in hyper.inner_text()
    page.wait_for_selector("table.runs th:has-text('max_epochs')")
    headers = page.locator("table.runs").last.locator("th").all_inner_texts()
    assert "max_epochs" in " ".join(headers) and "vector_channels" in " ".join(headers), headers
    cells = page.locator("table.runs").last.locator("tbody tr").first.locator("td").all_inner_texts()
    assert any(c.startswith("{") and c.endswith("keys}") for c in cells), cells
    assert "[object" not in page.inner_text("body")

    page.locator("table.runs").last.locator("tbody tr").first.click()
    page.wait_for_selector(".drawer .config-tree .config-leaf")
    drawer = page.locator(".drawer .config-tree")
    all_leaves = drawer.locator(".config-leaf").count()
    assert drawer.locator(".config-key:text-is('hparams.egnn.vector_channels')").count() == 1
    drawer.locator("input[type=checkbox]").check()
    assert 0 < drawer.locator(".config-leaf").count() < all_leaves
    assert drawer.locator(".config-varies").count() > 0
    assert "[object" not in page.inner_text(".drawer")

    run = page.locator("table.runs").last.locator("tbody tr").first.locator("a").first.get_attribute("href")
    page.goto(f"{base}{run}?token={token}")
    section = page.locator("section.collapsible:has(.config-tree), .section:has(.section-label:text-is('config')) section.collapsible").first
    section.wait_for()
    assert section.locator(".config-tree").count() == 0, "the config starts closed on a run's page"
    section.locator("button.collapse-toggle").click()
    section.locator(".config-leaf").first.wait_for()
    section.locator("input[type=search]").fill("max_epochs")
    assert section.locator(".config-leaf").count() == 1
    assert "[object" not in page.inner_text("body")


DATA_PIXELS = """() => {
  const canvas = document.querySelector('.chart canvas');
  const c = canvas.getBoundingClientRect();
  const o = document.querySelector('.chart .u-over').getBoundingClientRect();
  const k = canvas.width / c.width;
  const [x0, y0, w, h] = [Math.floor((o.left - c.left) * k), Math.floor((o.top - c.top) * k), Math.floor(o.width * k), Math.floor(o.height * k)];
  const data = canvas.getContext('2d').getImageData(x0, y0, w, h).data;
  const probe = document.createElement('canvas').getContext('2d');
  const colors = [1, 2, 3, 4, 5, 6].map((i) => {
    probe.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(`--data-${i}`).trim();
    probe.fillRect(0, 0, 1, 1);
    return probe.getImageData(0, 0, 1, 1).data;
  });
  let n = 0;
  for (let i = 0; i < data.length; i += 4)
    if (data[i + 3] > 200 && colors.some((c) => Math.abs(c[0] - data[i]) + Math.abs(c[1] - data[i + 1]) + Math.abs(c[2] - data[i + 2]) < 24)) n++;
  return n;
}"""


def test_a_single_point_is_drawn(server: str, page, project: Path) -> None:
    """A metric with one point shows it, on a chart and in a sparkline: the plot holds pixels in a
    run's color, which only a marker can draw."""
    import yaml

    from beamtime.ops import call
    from beamtime.ops.context import Context

    group = "realistic/egnn-bench"
    ctx = Context.make()
    call("view new", {"group": group, "name": "single"}, ctx)
    draft = project / ".beamtime" / "drafts" / "single"
    one = {"config.arm": "small", "config.seed": 0}
    view = {
        "schema": 1,
        "title": "one point",
        "finding": "x",
        "body": [
            {"line": {"id": "once", "y": "validation/first_eval", "where": one}},
            {"table": {"id": "once-table", "columns": ["run.name"], "sparkline": "validation/first_eval", "where": one}},
        ],
    }
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    call("view save", {"draft": "single"}, ctx)

    page.goto(f"{server.split('/f/local')[0]}/f/local/{group}?token={server.split('token=')[1]}")
    page.wait_for_selector(".chart canvas")
    box_of(page, ".chart .u-over")
    page.wait_for_timeout(500)
    assert page.evaluate(DATA_PIXELS) >= 6, "the single point is not drawn"
    page.wait_for_selector("td.spark svg")
    assert page.locator("td.spark circle").count() == 1
    assert page.locator("td.spark polyline").count() == 0


BAND_AT_BOTTOM = """() => {
  const canvas = document.querySelector('.chart canvas');
  const c = canvas.getBoundingClientRect();
  const o = document.querySelector('.chart .u-over').getBoundingClientRect();
  const k = canvas.width / c.width;
  const [x0, y0, w, h] = [Math.floor((o.left - c.left) * k), Math.floor((o.top - c.top) * k), Math.floor(o.width * k), Math.floor(o.height * k)];
  const rows = 6;
  const data = canvas.getContext('2d').getImageData(x0, y0 + h - rows * k - 2, w, rows * k).data;
  const probe = document.createElement('canvas').getContext('2d');
  probe.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--data-1').trim();
  probe.fillRect(0, 0, 1, 1);
  const color = probe.getImageData(0, 0, 1, 1).data;
  let n = 0;
  for (let i = 0; i < data.length; i += 4)
    if (data[i + 3] > 8 && data[i + 3] < 200 && Math.abs(color[0] - data[i]) + Math.abs(color[1] - data[i + 1]) + Math.abs(color[2] - data[i + 2]) < 60) n++;
  return n;
}"""


def test_a_band_on_a_log_axis_reaches_the_bottom(server: str, page, project: Path) -> None:
    """mean − std of a metric that crosses zero is not positive: the band is clipped at the floor, so
    it is filled down to the bottom of the plot instead of ending in holes."""
    import yaml

    from beamtime.ops import call
    from beamtime.ops.context import Context

    group = "realistic/egnn-bench"
    ctx = Context.make()
    call("view new", {"group": group, "name": "band"}, ctx)
    draft = project / ".beamtime" / "drafts" / "band"
    line = {
        "id": "signed",
        "y": "validation/signed",
        "by": "config.arm",
        "band": "std",
        "scale": "log",
        "where": {"config.arm": "small"},
    }
    view = {"schema": 1, "title": "band", "finding": "x", "body": [{"line": line}]}
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    call("view save", {"draft": "band"}, ctx)

    page.goto(f"{server.split('/f/local')[0]}/f/local/{group}?token={server.split('token=')[1]}")
    page.wait_for_selector(".chart canvas")
    box_of(page, ".chart .u-over")
    page.wait_for_timeout(500)
    assert page.evaluate(BAND_AT_BOTTOM) > 10, "the band does not reach the bottom of the plot"
