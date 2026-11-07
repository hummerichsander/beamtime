import pytest

from tests.serve.test_axes import BENCH, show

pytest.importorskip("playwright.sync_api")

LOSS = {"y": "validation/loss"}
OPEN = ".chart-settings:popover-open"

# a rectangle's edges, for the panel and for the chart frame it must not cover.
RECTS = """(frame) => {
  const f = frame.getBoundingClientRect();
  const p = document.querySelector('.chart-settings:popover-open').getBoundingClientRect();
  return { f: [f.left, f.top, f.right, f.bottom], p: [p.left, p.top, p.right, p.bottom], w: innerWidth, h: innerHeight };
}"""

# whether anything in the panel reaches past its right edge.
OVERFLOW = """() => {
  const panel = document.querySelector('.chart-settings:popover-open');
  const edge = panel.getBoundingClientRect().right;
  const wide = [...panel.querySelectorAll('*')].filter((e) => e.getBoundingClientRect().right > edge + 0.5).map((e) => e.className || e.tagName);
  return { scroll: panel.scrollWidth - panel.clientWidth, wide };
}"""


def grid_of_three(project, server: str, page) -> None:
    """Open a wide page with three charts in one row.

    :param project: The project root.
    :param server: The server's URL with the token.
    :param page: The Playwright page."""
    page.set_viewport_size({"width": 1800, "height": 1400})
    charts = [{"line": {"id": f"c{i}", "title": f"chart {i}", **LOSS}} for i in range(3)]
    show(project, server, page, BENCH, [{"grid": {"id": "g", "columns": 3, "children": charts}}])


def x_titles(page) -> list[str]:
    """Wait for all three charts to be drawn and read their x axis titles.

    :param page: The Playwright page.
    :return: The titles, in page order."""
    page.wait_for_function("document.querySelectorAll('.chart-frame .uplot').length === 3")
    page.wait_for_timeout(500)
    return page.locator(".chart-frame .uplot").evaluate_all("(els) => els.map((e) => e.dataset.xlabel)")


def open_settings(page, n: int) -> None:
    """Open the settings of the n-th chart.

    :param page: The Playwright page.
    :param n: The chart's position."""
    frame = page.locator(".chart-frame").nth(n)
    frame.scroll_into_view_if_needed()
    frame.hover(position={"x": frame.bounding_box()["width"] - 10, "y": 10})
    frame.locator("button[aria-label='Chart settings']").click()
    page.wait_for_selector(OPEN)
    page.wait_for_timeout(500)


def test_the_panel_sits_beside_its_chart(server: str, page, project) -> None:
    """In the first column the panel opens to the right of the chart, in the last to its left; neither covers it."""
    grid_of_three(project, server, page)
    open_settings(page, 0)
    r = page.locator(".chart-frame").nth(0).evaluate(RECTS)
    assert r["p"][0] >= r["f"][2], r
    page.keyboard.press("Escape")
    open_settings(page, 2)
    r = page.locator(".chart-frame").nth(2).evaluate(RECTS)
    assert r["p"][2] <= r["f"][0] and r["p"][0] >= 0, r


def test_the_panel_docks_to_the_edge_on_a_narrow_screen(server: str, page, project) -> None:
    """At 600 px neither side has room: the panel sits against the right edge, on screen, and follows a resize."""
    grid_of_three(project, server, page)
    page.set_viewport_size({"width": 600, "height": 900})
    page.wait_for_timeout(500)
    open_settings(page, 0)
    r = page.locator(".chart-frame").nth(0).evaluate(RECTS)
    assert r["p"][2] == pytest.approx(r["w"] - 8, abs=1) and r["p"][0] >= 0, r
    assert 0 <= r["p"][1] and r["p"][3] <= r["h"], r
    page.set_viewport_size({"width": 520, "height": 900})
    page.wait_for_timeout(300)
    r = page.locator(".chart-frame").nth(0).evaluate(RECTS)
    assert r["p"][2] == pytest.approx(r["w"] - 8, abs=1), r


def test_the_panel_follows_scrolling(server: str, page, project) -> None:
    """Scrolling moves the panel with its chart until the edge of the screen holds it."""
    grid_of_three(project, server, page)
    open_settings(page, 0)
    frame = page.locator(".chart-frame").first
    assert page.locator(OPEN).bounding_box()["y"] == pytest.approx(frame.bounding_box()["y"], abs=1)
    page.mouse.wheel(0, 100)
    page.wait_for_timeout(300)
    assert page.locator(OPEN).bounding_box()["y"] == pytest.approx(frame.bounding_box()["y"], abs=1)
    page.mouse.wheel(0, 2000)
    page.wait_for_timeout(300)
    box = page.locator(OPEN).bounding_box()
    assert 0 <= box["y"] and box["y"] + box["height"] <= 1400


def test_the_longest_metric_name_does_not_scroll_the_panel(server: str, page, project) -> None:
    """A chip, a select and the step range stay inside the panel, with the longest logged metric chosen."""
    metrics = ["validation/loss", "sys/gpu_mem"]
    long = "validation/" + "per_layer_gradient_norm_of_the_encoder_" * 3 + "mean"
    show(project, server, page, BENCH, [{"line": {"id": "c", "title": "c", "y": metrics}}])
    open_settings(page, 0)
    panel = page.locator(OPEN)
    panel.get_by_role("combobox", name="Metrics").click()
    assert panel.evaluate(OVERFLOW)["scroll"] <= 0
    # a chip made as long as the longest real name must wrap, not push the panel wider.
    page.evaluate(
        """(name) => { const chip = document.querySelector('.chart-settings:popover-open .ms-chip');
        chip.firstChild.textContent = name; }""",
        long,
    )
    result = panel.evaluate(OVERFLOW)
    assert result["scroll"] <= 0 and not result["wide"], result


def test_any_metric_is_an_x_axis_and_applies_to_all_charts(server: str, page, project) -> None:
    """The x axis picks from Progress and Metrics; one button sets it on every chart of the page."""
    grid_of_three(project, server, page)
    for frame in page.locator(".chart-frame").all():
        frame.scroll_into_view_if_needed()
    page.wait_for_timeout(500)
    open_settings(page, 0)
    panel = page.locator(OPEN)
    panel.get_by_role("combobox", name="x axis").click()
    assert panel.locator(".ms-group").all_inner_texts() == ["Progress", "Metrics"]
    assert panel.get_by_role("option", name="elapsed").count() == 1
    panel.get_by_role("combobox", name="x axis").fill("gpu")
    panel.get_by_role("option", name="sys/gpu_mem").click()
    page.wait_for_timeout(800)
    assert x_titles(page) == ["sys/gpu_mem", "step", "step"]
    panel.get_by_text("Use this x axis on all charts on this page").click()
    page.wait_for_timeout(1000)
    assert x_titles(page) == ["sys/gpu_mem"] * 3


def test_a_non_monotone_x_with_aggregation_says_so(server: str, page, project) -> None:
    """Averaging over a metric that goes back on itself is refused by the server and shown as a notice."""
    show(project, server, page, BENCH, [{"line": {"id": "c", "title": "c", "by": ["config.arm"], **LOSS}}])
    open_settings(page, 0)
    panel = page.locator(OPEN)
    panel.get_by_role("combobox", name="x axis").fill("gpu")
    panel.get_by_role("option", name="sys/gpu_mem").click()
    page.wait_for_selector(".chart-frame .notice.error")
    assert "goes back on itself" in page.locator(".chart-frame .notice.error").inner_text()
    assert page.locator(".chart-frame .chart-plot").count() == 0
