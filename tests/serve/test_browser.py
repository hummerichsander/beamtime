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
    page.on(
        "request", lambda r: r.url.endswith("/api/series") and asked.append(json.loads(r.post_data))
    )
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
    page.click('.notes .note >> nth=1 >> button[aria-label="Change the note\'s type"]')
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
    data["body"].append(
        {"table": {"id": "runs", "columns": ["run.name", "config.lr", "config.seed"]}}
    )
    file.write_text(yaml.safe_dump(data, sort_keys=False))
    call("view save", {"draft": "pm"}, ctx)
    script = Path(sys.executable).parent / "beamtime"
    proc = subprocess.Popen(
        [script, "serve", "--port", "0"], cwd=project, stderr=subprocess.PIPE, text=True
    )
    try:
        url = None
        while url is None:
            if m := re.search(
                r"(http://localhost:\d+)/f/local\?token=(\S+)", proc.stderr.readline()
            ):
                url = m
        page.goto(f"{url[1]}/f/local/{sweep}?token={url[2]}")
        frame = page.frame_locator(".custom-frame iframe")
        frame.locator("rect").first.wait_for(timeout=30_000)
        # the frame is sandboxed (an opaque origin): its fonts are CORS requests.
        inner = next(f for f in page.frames if "kit/frame" in f.url)
        assert inner.evaluate(
            "document.fonts.load('12.5px \"IBM Plex Sans\"').then((f) => f.length > 0)"
        )
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
        page.frame_locator("dialog.chart-dialog[open] iframe").locator("rect").first.wait_for(
            timeout=30_000
        )
    finally:
        proc.terminate()
        proc.wait(10)


def test_live_page_fixture_follows_a_running_writer(live_page) -> None:
    """The fixture's writer appears in the app and its metrics keep arriving."""
    live_page.goto("/f/local/live")
    live_page.page.wait_for_selector(".chart canvas")
    metrics = next((live_page.project / "beamtime" / "live").glob("*/_metrics.jsonl"))
    before = len(metrics.read_text().splitlines())
    deadline = time.time() + 10
    while len(metrics.read_text().splitlines()) <= before:
        assert time.time() < deadline, "no metrics arrived after the page opened"
        live_page.page.wait_for_timeout(200)
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
    page.on(
        "request",
        lambda r: (
            r.url.rsplit("/", 1)[-1] in ("code", "series")
            and asked.append(r.url.rsplit("/", 1)[-1])
        ),
    )
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
        lambda r: (
            r.url.rsplit("/", 1)[-1] in ("series", "view", "notes", "memory_show")
            and asked.append(r.url.rsplit("/", 1)[-1])
        ),
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
    columns = [
        "run.name",
        "config.hydrantic",
        "config.hydrantic.trainer.max_epochs",
        "config.hparams.egnn.vector_channels",
    ]
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
    cells = (
        page.locator("table.runs").last.locator("tbody tr").first.locator("td").all_inner_texts()
    )
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

    run = (
        page.locator("table.runs")
        .last.locator("tbody tr")
        .first.locator("a")
        .first.get_attribute("href")
    )
    page.goto(f"{base}{run}?token={token}")
    section = page.locator(
        "section.collapsible:has(.config-tree), .section:has(.section-label:text-is('config')) section.collapsible"
    ).first
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
            {
                "table": {
                    "id": "once-table",
                    "columns": ["run.name"],
                    "sparkline": "validation/first_eval",
                    "where": one,
                }
            },
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


def test_a_colormap_belongs_to_its_chart(server: str, page, project: Path) -> None:
    """Choosing a colormap recolors that chart's groups only, and the choice survives a reload;
    with one curve per run the row is disabled."""
    url = (
        f"{server.split('/f/local')[0]}/f/local/scaling/lr-sweep?token={server.split('token=')[1]}"
    )
    page.goto(url)
    page.wait_for_selector(".chart canvas")
    first = page.locator(".chart-frame").first
    first.hover()
    first.locator("button[aria-label='Chart settings']").click()
    settings = page.locator(".chart-settings:popover-open")
    runs = settings.locator("select").filter(has_text="each run")
    runs.select_option(label="each run")
    page.wait_for_timeout(300)
    assert settings.get_by_role("combobox", name="Colormap").is_disabled()
    runs.select_option(label="mean by lr")
    page.wait_for_timeout(500)
    settings.get_by_role("combobox", name="Colormap").click()
    settings.get_by_role("option", name="magma").click()
    page.keyboard.press("Escape")
    page.evaluate("scrollTo(0, 0)")
    page.wait_for_timeout(500)

    def marks(frame) -> list[str]:
        """The inline colors of a chart's legend swatches."""
        return frame.locator(".legend-item .swatch").evaluate_all(
            "els => els.map(e => e.getAttribute('style') || '')"
        )

    magma = {"color: rgb(0, 0, 4);", "color: rgb(252, 253, 191);"}
    assert magma <= set(marks(page.locator(".chart-frame").first))
    assert not magma & set(marks(page.locator(".chart-frame").nth(1)))
    page.reload()
    page.wait_for_selector(".chart canvas")
    assert magma <= set(marks(page.locator(".chart-frame").first))


def test_epochs_are_a_fact_and_a_column_not_a_chart(
    server: str, page, project: Path, roles: dict
) -> None:
    """A run's header says how far it is through its epochs; the group's table has the column, and
    neither page draws the epoch stair."""
    base = server.split("/f/local")[0]
    token = server.split("token=")[1]
    page.goto(f"{base}/r/{roles['realistic_killed']}?token={token}")
    page.wait_for_selector(".facts")
    page.wait_for_function("document.querySelector('.facts').innerText.includes('epoch')")
    assert "epoch 2 of 5 · 38 % through" in page.locator(".facts").inner_text()
    assert page.locator(".chart .chart-title:text-is('epoch')").count() == 0

    page.goto(f"{base}/f/local/realistic/egnn-bench?token={token}")
    page.wait_for_selector("table.runs th:has-text('progress')")
    cells = page.locator("table.runs td.progress").all_inner_texts()
    assert {c.strip() for c in cells} == {"80 %", "20 %"}, cells


def test_the_default_view_groups_charts_by_prefix_and_a_hidden_chart_comes_back(
    server: str, page, project: Path
) -> None:
    """Sections by prefix with the first two open; a hidden chart can be shown again, the choice
    survives a reload, "Save as view" keeps it, and a section remembers being closed."""
    base = server.split("/f/local")[0]
    token = server.split("token=")[1]
    page.goto(f"{base}/f/local/realistic/egnn-bench?token={token}")
    page.wait_for_selector(".chart canvas")
    toggles = "button.view-section-title"
    names = lambda: page.locator(toggles).evaluate_all(  # noqa: E731
        "els => els.map(e => e.getAttribute('aria-label') || e.innerText)"
    )
    assert names() == [
        "Close validation (4)", "Close energy (3)", "Open Other (2)", "Open System (2)",
    ]  # fmt: skip
    assert page.locator(".chart-title:text-is('validation/loss')").count() == 1
    assert page.locator(".chart-title:text-is('sys/gpu_mem')").count() == 0

    frames = page.locator(".chart-frame")
    before = frames.count()
    frame = frames.first
    frame.hover()
    frame.locator("button[aria-label='Hide this chart']").click()
    page.wait_for_selector("button:has-text('1 hidden · show')")
    assert frames.count() == before - 1
    page.reload()
    page.wait_for_selector("button:has-text('1 hidden · show')")
    page.locator("button:has-text('1 hidden · show')").click()
    page.wait_for_function(f"() => document.querySelectorAll('.chart-frame').length == {before}")
    assert page.locator("button:has-text('hidden · show')").count() == 0

    frame = frames.first
    gone = frame.locator(".chart-title").inner_text()
    frame.hover()
    frame.locator("button[aria-label='Hide this chart']").click()
    page.locator(".save-view").click()
    page.locator(".save-actions button[type=submit]").click()
    # the form closes once the save has landed; the chart count holds before it already.
    page.wait_for_selector(".save-actions", state="detached")
    page.wait_for_function(
        f"() => document.querySelectorAll('.chart-frame').length == {before - 1}"
    )
    page.reload()
    page.wait_for_selector(".chart canvas")
    assert (
        frames.count() == before - 1
        and page.locator("button:has-text('hidden · show')").count() == 0
    )
    assert page.locator(f".chart-title:text-is('{gone}')").count() == 0

    page.locator(toggles).nth(1).click()
    page.reload()
    page.wait_for_selector(".chart canvas")
    assert names()[1] == "Open energy (3)"


def test_main_metrics_are_pinned_in_the_ui(server: str, page, project: Path) -> None:
    """Without a proposal nothing is main; pinning a chart opens Main, sets the best and the
    sparkline, survives a reload and "Save as view"; a proposal's metric starts pinned and can go."""
    base = server.split("/f/local")[0]
    token = server.split("token=")[1]
    page.goto(f"{base}/f/local/realistic/egnn-bench?token={token}")
    page.wait_for_selector(".chart canvas")
    titles = lambda: page.locator("button.view-section-title").evaluate_all(  # noqa: E731
        "els => els.map(e => e.getAttribute('aria-label') || e.innerText)"
    )
    page.wait_for_function("() => document.querySelector('.facts')?.innerText.includes('runs')")
    assert not any("Main" in t for t in titles())
    assert "best" not in page.locator(".facts").inner_text()
    assert page.locator("table.runs td.spark").count() == 0

    page.set_viewport_size({"width": 1200, "height": 500})
    page.locator("button.view-section-title[aria-label='Open Other (2)']").click()
    frame = page.locator(".chart-frame", has=page.locator(".chart-title:text-is('training/loss')"))
    scroller = page.locator(".main")
    scroller.evaluate("e => { e.scrollTop = e.scrollHeight; }")
    frame.locator("button[aria-label='Chart settings']").click()
    pin = frame.locator("button:has-text('Pin as main metric')")
    pin.hover()
    own = frame.element_handle()
    top, scrolled = own.bounding_box()["y"], scroller.evaluate("e => e.scrollTop")
    assert scrolled > 0
    pin.click()
    page.wait_for_function(
        "() => document.querySelector('button.view-section-title')?.getAttribute('aria-label') == 'Close Main (1)'"
    )
    page.wait_for_function("() => document.querySelector('.facts').innerText.includes('best')")
    page.wait_for_selector("table.runs td.spark")
    # the chart stays in its own section as well, and where the viewer was looking.
    assert page.locator(".chart-title:text-is('training/loss')").count() == 2
    assert page.locator("button.view-section-title[aria-label='Close Other (2)']").count() == 1
    assert abs(own.bounding_box()["y"] - top) < 3
    assert scroller.evaluate("e => e.scrollTop") > scrolled
    assert page.locator(".chart-frame button[aria-label='Lower is better']").count() == 2

    page.reload()
    page.wait_for_selector(".chart canvas")
    page.wait_for_function("() => document.querySelector('.facts').innerText.includes('best')")
    assert "Main (1)" in titles()[0]

    page.locator(".chart-frame button[aria-label='Lower is better']").first.click()
    page.wait_for_selector(".chart-frame button[aria-label='Higher is better']")
    page.locator(".chart-frame button[aria-label='Higher is better']").first.click()
    page.locator(".save-view").click()
    page.locator(".save-actions button[type=submit]").click()
    page.wait_for_selector(".save-actions", state="detached")
    page.reload()
    page.wait_for_selector(".chart canvas")
    assert "Main (1)" in titles()[0]
    assert page.locator(".save-view").count() == 0
    saved = sorted((project / "beamtime" / "realistic" / "egnn-bench" / "view").glob("*.yaml"))[-1]
    assert "main_metrics: [training/loss]" in saved.read_text().split("body:")[0]

    page.goto(f"{base}/f/local/scaling/lr-sweep?token={token}")
    page.wait_for_selector(".chart canvas")
    assert "Main (1)" in titles()[0]
    frame = page.locator(".chart-frame", has=page.locator(".chart-title:text-is('val/acc')")).first
    frame.locator("button[aria-label='Chart settings']").click()
    frame.locator("button:has-text('Unpin')").click()
    page.wait_for_function(
        "() => !document.querySelector('button.view-section-title')?.getAttribute('aria-label')?.includes('Main')"
    )
    page.wait_for_function("() => !document.querySelector('.facts').innerText.includes('best')")


def test_hiding_works_outside_grids_and_add_a_chart_follows_the_charts(
    server: str, page, project: Path
) -> None:
    """The × hides a chart that sits directly in the body or a section, not only in a grid, and
    "Add a chart" comes after the page's last chart, before the run table."""
    import yaml

    from beamtime.ops import call
    from beamtime.ops.context import Context

    group = "realistic/egnn-bench"
    ctx = Context.make()
    call("view new", {"group": group, "name": "loose"}, ctx)
    draft = project / ".beamtime" / "drafts" / "loose"
    view = {
        "schema": 1,
        "title": "loose charts",
        "finding": "x",
        "body": [
            {"line": {"id": "alone", "y": "validation/loss"}},
            {
                "section": {
                    "id": "more",
                    "title": "More",
                    "children": [{"line": {"id": "inner", "y": "training/loss"}}],
                }
            },
            {"table": {"id": "runs", "columns": ["run.name"]}},
        ],
    }
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    call("view save", {"draft": "loose"}, ctx)

    page.goto(f"{server.split('/f/local')[0]}/f/local/{group}?token={server.split('token=')[1]}")
    page.wait_for_selector(".chart canvas")
    page.wait_for_selector(".add-chart")
    before_table = page.evaluate(
        "() => !!(document.querySelector('.add-chart').compareDocumentPosition("
        "document.querySelector('table.runs')) & Node.DOCUMENT_POSITION_FOLLOWING)"
    )
    assert before_table, "Add a chart sits after the run table"
    for title in ("validation/loss", "training/loss"):
        frame = page.locator(f".chart-frame:has(.chart-title:text-is('{title}'))")
        frame.hover()
        frame.locator("button[aria-label='Hide this chart']").click()
        page.wait_for_function(
            f"![...document.querySelectorAll('.chart-title')].some(e => e.innerText === '{title}')"
        )
    page.locator("button:has-text('1 hidden · show')").first.click()
    page.wait_for_selector(".chart-title:text-is('validation/loss')")


CURVES = """
const { html } = bt.preact;
const d3 = bt.lib.d3;
const M = { top: 8, right: 8, bottom: 34, left: 48 };

// a d3 line chart in the frame's chart: what the remote's curves.js draws by hand.
const yOf = (c) => c.y ?? c.last ?? c.mean;

function drawer(curves, tag) {
  return (el, { width, height, prefs, hovered, hidden, xlabel, ylabel }) => {
    el.dataset.draws = String(Number(el.dataset.draws ?? 0) + 1);
    el.dataset.tone = bt.theme.tone("good");
    const shown = curves.filter((c) => !hidden.has(c.run));
    const xs = shown.flatMap((c) => c.x);
    const ys = shown.flatMap(yOf).filter((v) => v !== null && v > 0);
    const x = d3.scaleLinear(d3.extent(xs), [M.left, width - M.right]);
    const y = (prefs.scale === "log" ? d3.scaleLog() : d3.scaleLinear()).domain(d3.extent(ys)).range([height - M.bottom, M.top]);
    const ramp = bt.theme.scale("sequential", prefs.colormap);
    const svg = d3.select(el).selectAll("svg").data([0]).join("svg").attr("width", width).attr("height", height).attr("data-scale", prefs.scale);
    svg.selectAll("path.curve")
      .data(shown, (c) => c.run)
      .join("path")
      .attr("class", "curve")
      .attr("data-run", (c) => c.run)
      .attr("data-hot", (c) => (c.run === hovered ? "1" : null))
      .attr("fill", "none")
      .attr("stroke", (c, i) => ramp(i / Math.max(1, shown.length - 1)))
      .attr("stroke-width", (c) => (c.run === hovered ? 3 : 1.5))
      .attr("d", (c) => d3.line().defined((_, i) => yOf(c)[i] !== null && yOf(c)[i] > 0).x((_, i) => x(c.x[i])).y((_, i) => y(yOf(c)[i]))(c.x))
      .on("pointerenter", (e, c) => bt.hover(c.run))
      .on("pointerleave", () => bt.hover(null));
    svg.selectAll("text.axis")
      .data([[width / 2, height - 6, xlabel], [12, height / 2, ylabel]])
      .join("text")
      .attr("class", "axis")
      .attr("x", (d) => d[0])
      .attr("y", (d) => d[1])
      .attr("fill", "var(--muted)")
      .text((d) => `${tag} ${d[2]}`);
  };
}

function Curves() {
  const curves = bt.useData("curves");
  const list = curves.curves;
  const series = list.map((c) => ({ key: c.run, label: bt.name(c.run), color: bt.theme.runColor(c.run) }));
  const rows = [["step", ...list.map((c) => c.run)], ...(list[0]?.x ?? []).map((s, i) => [s, ...list.map((c) => yOf(c)[i])])];
  return html`
    <${bt.chart.Figure} id="a" title="Train loss" xlabel="step" ylabel="train/loss" series=${series}
      settings=${["scale", "smooth", "colormap"]} csv=${rows} draw=${drawer(list, "a")} />
    <${bt.chart.Figure} id="b" title="Second" xlabel="step" ylabel="train/loss" settings=${["scale"]} draw=${drawer(list, "b")} />
    <p id="vocab">
      <${bt.ui.Sym} kind="run" value="finished" word />
      <${bt.ui.Sym} kind="run" value="no-such-state" />
      <${bt.ui.Sym} kind="no-such-kind" value="x" />
      <${bt.ui.Tag} tone="good">tag<//> <${bt.ui.Icon} name="check" />
      <${bt.ui.Predictions} />
    </p>`;
}

export default function render(root) {
  bt.preact.render(html`<${Curves} />`, root);
}
"""


def figure_view(project: Path, group: str, code: str, queries: dict, table: bool) -> None:
    """Save a view of one custom block on ``bt.chart.Figure``, with a run table beside it if asked.

    :param project: The project root.
    :param group: The group the view belongs to.
    :param code: The block's code.
    :param queries: The block's declared queries.
    :param table: Whether to add a run table block, for the hovered row."""
    import yaml

    from beamtime.ops import call
    from beamtime.ops.context import Context

    ctx = Context.make()
    call("view new", {"group": group, "name": "fig"}, ctx)
    draft = project / ".beamtime" / "drafts" / "fig"
    body = [
        {
            "custom": {
                "id": "curves",
                "title": "Curves",
                "code": "code/curves.js",
                "libs": ["d3"],
                "queries": queries,
            }
        }
    ]
    if table:
        body.append({"table": {"id": "runs", "columns": ["run.name", "config.lr"]}})
    view = {"schema": 1, "title": "fig", "finding": "x", "body": body}
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    (draft / "code").mkdir(exist_ok=True)
    (draft / "code" / "curves.js").write_text(code)
    call("view save", {"draft": "fig"}, ctx)


def test_figure_gets_the_chart_frame(project: Path, server: str, page) -> None:
    """A ``Figure`` with a d3 line has one head (the frame's), settings that redraw only that figure,
    a legend, hover to the table and back, downloads and the theme, and hover or a resize do not refetch."""
    figure_view(
        project,
        "scaling/lr-sweep",
        CURVES,
        {"curves": {"series": {"y": ["train/loss"], "points": 60}}},
        table=True,
    )
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    series: list[str] = []
    page.on("request", lambda r: r.url.endswith("/api/series") and series.append(r.url))
    base, token = server.split("/f/local")[0], server.split("token=")[1]
    page.goto(f"{base}/f/local/scaling/lr-sweep?token={token}")
    frame = page.frame_locator(".custom-frame iframe")
    frame.locator("path.curve").first.wait_for(timeout=30_000)
    assert page.locator(".custom-block > .chart-head").count() == 0, "the page leaves its head out"
    assert frame.locator(".chart-head").count() == 2, "one head per figure"
    assert "a step" in frame.locator(".chart-plot svg").first.locator("text.axis").first.text_content()
    assert frame.locator("#vocab > .sym.tone-good").count() == 1
    assert frame.locator("#vocab > .sym.tone-muted").count() == 2, (
        "unknown values and kinds get the neutral symbol"
    )
    assert frame.locator("#vocab .tag.tone-good").count() == 1
    frame.locator("#vocab .prediction").first.wait_for(timeout=10_000)
    inner = next(f for f in page.frames if "kit/frame" in f.url)

    series_before = len(series)
    first = frame.locator("path.curve").nth(1)
    first.dispatch_event("pointerenter")
    page.wait_for_selector("table.runs tr.hovered", timeout=5_000)
    first.dispatch_event("pointerleave")
    page.wait_for_function(
        "document.querySelector('table.runs tr.hovered') === null", timeout=5_000
    )
    page.locator("table.runs tbody tr").nth(2).hover()
    frame.locator("path.curve[data-hot='1']").first.wait_for(timeout=5_000)
    page.mouse.move(5, 5)
    page.set_viewport_size({"width": 1000, "height": 900})
    page.wait_for_timeout(800)
    assert len(series) == series_before, "hover and a resize redraw without asking for data again"

    draws = lambda fig: int(
        inner.evaluate(f"document.querySelectorAll('.chart-plot')[{fig}].dataset.draws")
    )  # noqa: E731
    stroke = lambda fig: inner.evaluate(
        f"document.querySelectorAll('.chart-plot')[{fig}].querySelector('path.curve').getAttribute('stroke')"
    )  # noqa: E731
    a, b, color = draws(0), draws(1), stroke(0)
    frame.locator(".chart-frame").first.hover()
    frame.locator(".chart-frame").first.locator("[aria-label='Chart settings']").click()
    page.wait_for_timeout(300)
    frame.locator("input[aria-label='Colormap']").click()
    frame.locator("li[role='option']").nth(3).click()
    page.wait_for_timeout(500)
    assert draws(0) > a and stroke(0) != color, "a new colormap redraws its figure"
    assert draws(1) == b, "and only that figure"
    frame.locator("button[role='radio']:has-text('log')").first.click()
    page.wait_for_timeout(300)
    assert frame.locator(".chart-plot svg").first.get_attribute("data-scale") == "log"
    assert frame.locator(".chart-plot svg").nth(1).get_attribute("data-scale") == "linear"
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    with page.expect_download() as download:
        frame.locator(".chart-frame").first.locator("button[aria-label='Download']").click()
        frame.locator(".chart-frame").first.locator("button:has-text('SVG')").dispatch_event("click")
    assert download.value.suggested_filename == "Train_loss.svg"
    page.wait_for_timeout(1100)
    with page.expect_download() as download:
        frame.locator(".chart-frame").first.locator("button[aria-label='Download']").click()
        frame.locator(".chart-frame").first.locator("button:has-text('PNG, white')").dispatch_event("click")
    assert download.value.suggested_filename == "Train_loss.png"
    page.wait_for_timeout(1100)
    with page.expect_download() as download:
        frame.locator(".chart-frame").first.locator("button[aria-label='Download']").click()
        frame.locator(".chart-frame").first.locator("button:has-text('CSV')").dispatch_event("click")
    assert download.value.suggested_filename == "Train_loss.csv"

    legend = frame.locator(".legend-item")
    count = frame.locator("path.curve").count()
    legend.first.click()
    page.wait_for_timeout(300)
    assert frame.locator("path.curve").count() < count, "the legend hides a series"

    tone, a = inner.evaluate("document.querySelector('.chart-plot').dataset.tone"), draws(0)
    toggle = page.locator(".topbar-actions [aria-label^='Theme']")
    while "(switch to system)" not in toggle.get_attribute("aria-label"):
        toggle.click()
        page.wait_for_timeout(300)
    page.wait_for_timeout(500)
    assert draws(0) > a, "a theme change redraws"
    assert inner.evaluate("document.querySelector('.chart-plot').dataset.tone") != tone
    assert errors == []


def test_figure_follows_live_data(live_page) -> None:
    """A ``Figure`` redraws when its query answers with more steps."""
    code = """
const { html } = bt.preact;
function Live() {
  const d = bt.useData("loss");
  const draw = (el) => { el.textContent = ""; const n = d.curves[0]?.x.length ?? 0; el.innerHTML = `<b id="n">${n}</b>`; };
  return html`<${bt.chart.Figure} id="live" title="Live" xlabel="step" ylabel="loss" draw=${draw} />`;
}
export default function render(root) { bt.preact.render(html`<${Live} />`, root); }
"""
    figure_view(
        live_page.project,
        "live",
        code,
        {"loss": {"series": {"y": ["live/loss"], "points": 50}}},
        table=False,
    )
    live_page.goto("/f/local/live")
    page = live_page.page
    text = lambda: (
        page.frame_locator(".custom-frame iframe").locator("#n").inner_text(timeout=30_000)
    )  # noqa: E731
    first = int(text())
    page.wait_for_timeout(8_000)
    assert int(text()) > first
