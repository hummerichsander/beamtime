from pathlib import Path

import pytest

from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.serve.app import STATIC
from beamtime.views import render

pytest.importorskip("playwright.sync_api")

SWEEP = "scaling/lr-sweep"
WIDGETS = """schema: 1
title: All widgets
finding: lr 3e-4 is best.
body:
  - row:
      - stat: {title: Best, field: metric.val/acc.max, aggregate: best}
  - grid:
      columns: 2
      children:
        - scatter: {x: config.lr, y: metric.val/acc.max, x_scale: log, seeds: config.seed, fit: log, caption: a}
        - bar: {x: config.lr, y: metric.val/acc.max, caption: b}
        - line: {y: val/acc, by: [config.lr], caption: c}
        - histogram: {key: grads/layer3, caption: d}
  - tabs:
      - section: {title: Tables, children: [{data_table: {key: val/per_class}}]}
      - section: {title: Events, children: [{timeline: {limit: 5}}]}
"""


@pytest.fixture
def browser_ok() -> None:
    """Skip where the frontend isn't built or no browser can run."""
    from playwright.sync_api import sync_playwright

    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    with sync_playwright() as p:
        browser = render.launch(p)
        if browser is None:
            pytest.skip("no installed Chromium, Chrome or Edge")
        browser.close()


def draft(ctx: Context, project: Path, name: str, text: str) -> None:
    """Write a draft for the sweep.

    :param ctx: The operation context.
    :param project: The project root.
    :param name: The draft's name.
    :param text: Its YAML."""
    call("view new", {"group": SWEEP, "name": name}, ctx)
    (project / ".beamtime" / "drafts" / name / "view.yaml").write_text(text)


def test_every_widget_renders_cleanly(browser_ok, ctx: Context, project: Path) -> None:
    """A draft with every new widget renders without errors, blank blocks or overflow."""
    draft(ctx, project, "all", WIDGETS)
    answer = call("view render", {"draft": "all"}, ctx)
    assert answer["rendered"], answer
    assert answer["findings"] == [], answer["findings"]
    shot = Path(answer["shots"][0]["file"])
    assert shot.is_file() and shot.stat().st_size > 20_000
    one = call("view render", {"draft": "all", "block": "bar-metric-val-acc-max"}, ctx)
    assert Path(one["shots"][0]["file"]).name == "bar-metric-val-acc-max-light.jpg"
    assert call("view validate", {"draft": "all"}, ctx)["render"]["rendered"]


def test_render_reports_blank_blocks_and_errors(browser_ok, ctx: Context, project: Path) -> None:
    """A blank block and a block without data are reported by the render."""
    text = "schema: 1\nfinding: x\nbody:\n  - note: {id: empty, text: ' '}\n  - images: {key: nope}\n"
    draft(ctx, project, "broken", text)
    findings = call("view render", {"draft": "broken"}, ctx)["findings"]
    assert {"level": "error", "id": "empty", "block": "note", "message": "the block is blank"} in findings
    assert any(f.get("id") == "images-nope" for f in findings)


def test_without_a_browser_the_render_is_skipped(
    ctx: Context, project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No browser: validation stays static and names the user's install command."""
    monkeypatch.setattr(render, "launch", lambda p: None)
    draft(ctx, project, "plain", WIDGETS)
    result = call("view validate", {"draft": "plain"}, ctx)
    assert result["ok"] and not result["render"]["rendered"]
    assert result["render"]["command"] == "uv run playwright install chromium"
    assert any("render skipped" in line for line in result["lines"])


def test_custom_blocks_render_in_their_frame(browser_ok, ctx: Context, project: Path) -> None:
    """The custom example draws in its frame; errors and blank frames are reported."""
    call("view new", {"group": SWEEP, "from": "custom", "name": "pm"}, ctx)
    answer = call("view render", {"draft": "pm"}, ctx)
    assert answer["rendered"], answer
    assert answer["findings"] == [], answer["findings"]
    folder = project / ".beamtime" / "drafts" / "pm"
    (folder / "code" / "throws.js").write_text("export default function render(root) { throw new Error('boom'); }\n")
    (folder / "code" / "empty.js").write_text("export default function render(root) {}\n")
    (folder / "view.yaml").write_text("""schema: 1
finding: x
body:
  - custom: {id: throws, code: code/throws.js}
  - custom: {id: empty, code: code/empty.js}
  - stat: {title: Runs, aggregate: count}
""")
    findings = call("view render", {"draft": "pm"}, ctx)["findings"]
    assert any(f.get("message", "").startswith("console: [block throws] Error: boom") for f in findings), findings
    assert {"level": "error", "id": "empty", "block": "custom", "message": "the custom block draws nothing"} in findings


def test_block_examples_render(browser_ok, ctx: Context, project: Path) -> None:
    """block validate renders a block draft's examples as uses in a view of its group."""
    from tests.views.test_library import GENERAL

    call("view new", {"group": SWEEP, "from": "custom", "name": "pm"}, ctx)
    file = project / ".beamtime" / "drafts" / "pm" / "view.yaml"
    file.write_text(file.read_text().replace("TODO: the result in one sentence.", "x"))
    call("view save", {"draft": "pm"}, ctx)
    call("block promote", {"group": SWEEP, "block_id": "phase-map", "name": "phase-map"}, ctx)
    (project / ".beamtime" / "drafts" / "blocks" / "phase-map" / "block.yaml").write_text(GENERAL)
    answer = call("block validate", {"draft": "phase-map"}, ctx)
    assert answer["render"]["rendered"] and answer["ok"], answer["findings"]


def jpeg_size(path: Path) -> tuple[int, int]:
    """Read a JPEG's pixel size from its SOF marker, without an imaging library.

    :param path: The JPEG file.
    :return: ``(width, height)``."""
    data = path.read_bytes()
    i = 2
    while i < len(data):
        marker = data[i + 1]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height = int.from_bytes(data[i + 5 : i + 7], "big")
            width = int.from_bytes(data[i + 7 : i + 9], "big")
            return width, height
        i += 2 + int.from_bytes(data[i + 2 : i + 4], "big")
    raise ValueError(f"{path}: no JPEG SOF marker found")


def test_a_tall_page_is_capped_and_names_what_fell_below(browser_ok, ctx: Context, project: Path) -> None:
    """A page taller than the cap is clipped to exactly 1280 x SHOT_HEIGHT; cut names the rest."""
    body = "\n".join(f"  - line: {{id: c{i}, y: val/acc}}" for i in range(40))
    draft(ctx, project, "long", f"schema: 1\nfinding: x\nbody:\n{body}\n")
    answer = call("view render", {"draft": "long"}, ctx)
    assert answer["rendered"], answer
    file = Path(answer["shots"][0]["file"])
    assert file.suffix == ".jpg"
    assert jpeg_size(file) == (1280, render.SHOT_HEIGHT)
    cut = answer["cut"]
    assert cut["shown_height"] == render.SHOT_HEIGHT and cut["page_height"] > render.SHOT_HEIGHT
    assert cut["blocks_below"], cut
    assert any("the page is" in line and "below it" in line for line in answer["lines"])

    one = cut["blocks_below"][0]
    below = call("view render", {"draft": "long", "block": one}, ctx)
    assert below["shots"][0]["block"] == one and Path(below["shots"][0]["file"]).is_file()
    assert "cut" not in below


def test_a_short_page_has_no_cut(browser_ok, ctx: Context, project: Path) -> None:
    """A page within the cap gets its full height, with no cut key at all."""
    draft(ctx, project, "short", "schema: 1\nfinding: x\nbody:\n  - line: {y: val/acc}\n")
    answer = call("view render", {"draft": "short"}, ctx)
    assert answer["rendered"] and "cut" not in answer
    width, height = jpeg_size(Path(answer["shots"][0]["file"]))
    assert width == 1280 and height < render.SHOT_HEIGHT


def test_render_page_stays_full_height_and_uncapped(browser_ok, ctx: Context, tmp_path: Path) -> None:
    """The view-task harness's judge keeps a full-page PNG: it must see every block to score it."""
    shot = tmp_path / "page.png"
    answer = render.render_page(ctx, SWEEP, shot)
    assert answer["rendered"] and "cut" not in answer
    assert shot.is_file() and shot.read_bytes().startswith(b"\x89PNG")
