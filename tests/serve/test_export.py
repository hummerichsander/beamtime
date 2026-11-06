import json
from pathlib import Path

import pytest
import yaml

from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.query import run as run_query
from beamtime.views.export import folder_for, run_ids, with_points

SWEEP = "scaling/lr-sweep"


def test_points_are_asked_for_charts_only() -> None:
    """Chart curves get the export's points; sparklines and other calls stay as the page asked."""
    assert with_points("series", {"y": ["a"], "points": 300}, 1000)["points"] == 1000
    assert with_points("series", {"y": ["a"], "points": 300}, "all")["points"] == "all"
    assert with_points("series", {"y": ["a"], "points": 48}, 1000)["points"] == 48
    assert with_points("series", {"y": ["a"]}, 1000)["points"] == 1000
    assert with_points("runs", {"limit": 300}, 1000) == {"limit": 300}


def test_all_points_returns_raw_curves(project: Path) -> None:
    """points: all answers every logged point, past the chart budget."""
    q = {"series": {"from": SWEEP, "y": ["val/acc"], "points": "all"}}
    answer = run_query(q, logdir=project / "beamtime", caller="view")
    assert answer["curves"] and all(c["raw"] for c in answer["curves"])
    assert answer["meta"]["points"] == "all"


def test_export_folders_are_new_or_earlier_exports(tmp_path: Path) -> None:
    """An export never writes into a folder holding something else."""
    folder_for(tmp_path / "new")
    (tmp_path / "used").mkdir()
    (tmp_path / "used" / "notes.txt").write_text("mine")
    with pytest.raises(OpError, match="isn't empty"):
        folder_for(tmp_path / "used")
    (tmp_path / "old").mkdir()
    (tmp_path / "old" / "_export.json").write_text("{}")
    folder_for(tmp_path / "old")


def test_placeholder_runs_come_from_the_page() -> None:
    """Run ids for placeholder queries are those of the page's run tables, in order."""
    calls = [
        {"method": "runs", "params": {}, "answer": {"columns": ["run.id", "x"], "rows": [["a", 1], ["b", 2]]}},
        {"method": "series", "params": {}, "answer": {"curves": []}},
        {"method": "runs", "params": {}, "answer": {"columns": ["run.name"], "rows": [["n"]]}},
    ]  # fmt: skip
    assert run_ids(calls) == ["a", "b"]


def test_export_needs_one_target(ctx: Context) -> None:
    """--html or --figures, not both and not neither."""
    with pytest.raises(OpError, match="--html"):
        call("export", {"group": SWEEP}, ctx)


@pytest.fixture
def chromium():
    """Skip where no Chromium can run.

    :return: The Playwright module."""
    sync_api = pytest.importorskip("playwright.sync_api")
    from beamtime.views.render import launch

    with sync_api.sync_playwright() as p:
        browser = launch(p)
        if browser is None:
            pytest.skip("no Chromium available (playwright install chromium)")
        browser.close()
    return sync_api


def custom_view(ctx: Context, project: Path) -> None:
    """Save the custom example (a phase map with a placeholder query) as the sweep's view.

    :param ctx: The operation context.
    :param project: The project root."""
    call("view new", {"group": SWEEP, "from": "custom", "name": "pm"}, ctx)
    file = project / ".beamtime" / "drafts" / "pm" / "view.yaml"
    data = yaml.safe_load(file.read_text())
    data["finding"] = "lr 3e-4 is best."
    file.write_text(yaml.safe_dump(data, sort_keys=False))
    call("view save", {"draft": "pm"}, ctx)


def test_an_export_opens_from_disk(chromium, ctx: Context, project: Path, tmp_path: Path) -> None:
    """The exported page renders from file:// without any network, custom block and placeholder
    query included; a run page's images are copied next to it."""
    custom_view(ctx, project)
    out = tmp_path / "out"
    answer = call("export", {"group": SWEEP, "html": str(out)}, ctx)
    assert answer["answers"] > 5 and (out / "index.html").is_file()
    assert "preact" in (out / "static" / "THIRD_PARTY_LICENSES.txt").read_text()
    # inlined: a file opened from disk has no server to ask for /static/favicon.svg.
    assert 'data:image/svg+xml;base64,' in (out / "index.html").read_text()
    run = call("data", {"from": SWEEP, "key": "samples"}, ctx)["entries"][0]["run"]
    images = tmp_path / "run"
    call("export", {"group": run, "html": str(images)}, ctx)
    assert any((images / "files").rglob("*.png"))
    with chromium.sync_playwright() as p:
        from beamtime.views.render import launch

        browser = launch(p)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        errors, network = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and errors.append(m.text))
        page.route("http*://**", lambda r: (network.append(r.request.url), r.abort()))
        page.goto((out / "index.html").as_uri())
        page.wait_for_selector(".view-source:has-text('a snapshot of')", timeout=15_000)
        frame = page.frame_locator(".custom-frame iframe")
        frame.locator("svg g").first.wait_for(timeout=15_000)
        frame.locator("svg g").first.click()
        frame.locator("canvas").first.wait_for(timeout=15_000)
        assert not page.locator(".custom-error").count()
        assert "not part of this snapshot" not in frame.locator("body").inner_text()
        page.goto((images / "index.html").as_uri())
        page.wait_for_selector(".images img", timeout=15_000)
        page.wait_for_function("[...document.querySelectorAll('.images img')].every(i => i.naturalWidth > 0)")
        browser.close()
    assert not errors and not network


def test_figures_at_paper_size(chromium, ctx: Context, tmp_path: Path) -> None:
    """Each chart becomes a PNG at the column width (four device pixels per CSS pixel) with its
    data as CSV."""
    out = tmp_path / "figs"
    answer = call("export", {"group": SWEEP, "figures": str(out)}, ctx)
    assert answer["figures"]
    png = out / "line-val-acc.png"
    assert png.is_file()
    width = int.from_bytes(png.read_bytes()[16:20], "big")
    assert width == round(3.3 * 96) * 4
    assert (out / "line-val-acc.csv").read_text().startswith("x,")
    pytest.importorskip("matplotlib")
    pytest.importorskip("scienceplots")
    assert (out / "line-val-acc.pdf").read_bytes().startswith(b"%PDF")
    assert json.loads(json.dumps(answer["lines"]))
