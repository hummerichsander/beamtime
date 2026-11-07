import pytest
import yaml

from beamtime.ops import call
from beamtime.ops.context import Context

pytest.importorskip("playwright.sync_api")

BENCH = "realistic/egnn-bench"

# the pixels of a chart's canvas in its left and bottom strips, where the axis titles are drawn.
TITLE_PIXELS = """(el) => {
  const canvas = el.querySelector('canvas');
  const k = canvas.getContext('2d');
  const strip = 20 * (canvas.width / canvas.getBoundingClientRect().width);
  const seen = (x, y, w, h) => k.getImageData(x, y, w, h).data.some((v, i) => i % 4 === 3 && v > 40);
  return [seen(0, 0, strip, canvas.height), seen(0, canvas.height - strip, canvas.width, strip)];
}"""

HOVER_ROWS = "() => document.querySelectorAll('.bt-tip:not([hidden]) .bt-tip-row').length"


def show(project, server: str, page, group: str, body: list[dict]) -> None:
    """Save a view with the given blocks for a group and open the group's page.

    :param project: The project root.
    :param server: The server's URL with the token.
    :param page: The Playwright page.
    :param group: The group.
    :param body: The view's blocks."""
    ctx = Context.make()
    call("view new", {"group": group, "name": "axes"}, ctx)
    view = {"schema": 1, "title": "axes", "finding": "x", "body": body}
    (project / ".beamtime" / "drafts" / "axes" / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    call("view save", {"draft": "axes"}, ctx)
    base, token = server.split("/f/local")[0], server.split("token=")[1]
    page.goto(f"{base}/f/local/{group}?token={token}")
    page.wait_for_selector(".chart-plot canvas")
    page.wait_for_timeout(800)


def titles(page) -> dict[str, tuple[str, str]]:
    """Read the axis titles of every chart on the page and check they are drawn.

    :param page: The Playwright page.
    :return: Each chart's id mapped to its x and y title."""
    out = {}
    for frame in page.locator(".chart-frame").all():
        # a chart is drawn once it is on screen.
        frame.scroll_into_view_if_needed()
        root = frame.locator(".uplot")
        root.wait_for()
        page.wait_for_timeout(300)
        x, y = root.get_attribute("data-xlabel"), root.get_attribute("data-ylabel")
        left, bottom = root.evaluate(TITLE_PIXELS)
        title = frame.locator(".chart-title").inner_text()
        assert (left or not y) and (bottom or not x), f"{title}: titles {x!r}, {y!r} not drawn"
        out[title] = (x, y)
    return out


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_every_chart_kind_has_both_axis_titles(server: str, page, project, scheme: str) -> None:
    """Lines (each clock, a metric as x), scatter, bar and histogram name their axes, in either theme."""
    page.emulate_media(color_scheme=scheme)
    body = [
        {"line": {"id": "step", "title": "step", "y": "validation/loss"}},
        {"line": {"id": "epoch", "title": "epoch", "y": "validation/loss", "x": "epoch"}},
        {"line": {"id": "time", "title": "time", "y": "validation/loss", "x": "_t"}},
        {"line": {"id": "elapsed", "title": "elapsed", "y": ["validation/loss", "training/loss"], "x": "_elapsed"}},
        {"line": {"id": "path", "title": "path", "y": "validation/loss", "x": "sys/gpu_mem"}},
        {"line": {"id": "own", "title": "own", "y": "training/loss", "xlabel": "iterations", "ylabel": "nats"}},
        {"scatter": {"id": "sc", "title": "sc", "x": "config.seed", "y": "metric.validation/loss.min"}},
        {"bar": {"id": "bar", "title": "bar", "x": "config.arm", "y": "metric.validation/loss.min"}},
    ]
    show(project, server, page, BENCH, body)
    loss = "validation/loss"
    assert titles(page) == {
        "step": ("step", loss),
        "epoch": ("epoch", loss),
        "time": ("wall time", loss),
        "elapsed": ("elapsed", ""),
        "path": ("sys/gpu_mem", loss),
        "own": ("iterations", "nats"),
        "sc": ("seed", f"{loss} min"),
        "bar": ("arm", f"{loss} min"),
    }


def test_histograms_name_their_axes(server: str, page, project) -> None:
    """A histogram's x is its key, its y the count."""
    show(project, server, page, "scaling/lr-sweep", [{"histogram": {"id": "h", "title": "h", "key": "grads/layer3"}}])
    assert titles(page) == {"h": ("grads/layer3", "count")}


def test_hover_over_elapsed_lists_every_run(server: str, page, project) -> None:
    """Runs logged at different times share no x; each still answers with its own nearest point."""
    body = [{"line": {"id": "t", "y": "validation/loss", "x": "_elapsed", "legend": False}}]
    show(project, server, page, BENCH, body)
    over = page.locator(".chart .u-over").first.bounding_box()
    page.mouse.move(over["x"] + over["width"] * 0.25, over["y"] + over["height"] / 2)
    page.wait_for_timeout(300)
    # the nine runs of the group and the x row on top.
    assert page.evaluate(HOVER_ROWS) == 10
