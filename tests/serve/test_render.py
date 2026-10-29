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
    assert Path(one["shots"][0]["file"]).name == "bar-metric-val-acc-max-light.png"
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
