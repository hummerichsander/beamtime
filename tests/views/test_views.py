from pathlib import Path

import pytest
import yaml

from beamtime.format.schema import SchemaError
from beamtime.guide import EXAMPLES
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.serve.app import view as page_view
from beamtime.views import model as m
from beamtime.views.compile import apply_prefs, compile_view, from_tree
from beamtime.views.defaults import default_view

SWEEP = "scaling/lr-sweep"


def parse(text: str) -> m.View:
    """Parse a view from YAML text.

    :param text: The YAML.
    :return: The view."""
    return m.parse(yaml.safe_load(text), source="test")


def test_parse_normalizes_nodes_and_fills_ids() -> None:
    """One-key nodes and list-form layouts become the union; ids are stable and unique."""
    view = parse("""
body:
  - row:
      - stat: {aggregate: count}
      - stat: {field: metric.val/acc.max, aggregate: best}
  - line: {y: val/acc}
  - line: {y: val/acc}
  - tabs: [{section: {title: Curves, children: [{line: {y: [a, b]}}]}}]
""")
    assert [n.id for n in m.walk(view.body)] == [
        "row-1", "stat-1", "stat-metric-val-acc-max", "line-val-acc", "line-val-acc-1",
        "tabs-1", "section-curves", "line-a",
    ]  # fmt: skip
    again = parse(m.dump(m.to_yaml_form(view)))
    assert m.to_yaml_form(again) == m.to_yaml_form(view)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("body: [{line: {y: 3}}]", "body[0].line.y"),
        ("body: [{grid: [{line: {z: 1}}]}]", "body[0].grid.children[0].line: Object contains unknown field `z`"),
        ("body: [{phase-map: {}}]", "no block 'phase-map'"),
        ("body: [{tabs: [{line: {y: a}}]}]", "each tab is a section"),
        ("body: [line]", "one block name with its props"),
        ("schema: 2", "no reader for view schema 2"),
    ],
)  # fmt: skip
def test_parse_errors_name_the_node(text: str, message: str) -> None:
    """Errors say where in the view they are."""
    with pytest.raises(SchemaError, match=message.replace("[", r"\[").replace("]", r"\]")):
        parse(text)


def test_compile_resolves_scope_filters_and_props() -> None:
    """Blocks become the default tree's nodes with declared calls relative to the page."""
    view = parse("""
filters: {run.status: {ne: failed}}
metrics: {val/loss: {scale: log, higher_is_better: false}}
body:
  - grid:
      children:
        - line: {id: c, y: val/loss, by: config.lr, smooth: 0.6, from: sub, depth: 1}
        - scatter: {x: config.lr, y: metric.val/acc.max, seeds: config.seed, where: {config.wd: 0}}
  - stat: {field: metric.val/loss.min, aggregate: best}
  - output: {}
""")
    tree = compile_view(view, path="g")
    grid, stat, output = tree["children"]
    line, scatter = grid["children"]
    assert grid["props"]["addable"] and "y" not in grid["props"]["template"]["params"]
    assert line["data"]["main"]["params"] == {
        "from": "g/sub", "where": {"run.status": {"ne": "failed"}}, "depth": 1, "y": ["val/loss"],
        "x": "_step", "points": 300, "band": "minmax", "by": ["config.lr"],
    }  # fmt: skip
    assert line["props"]["scale"] == "log" and line["props"]["smooth"] == 0.6
    assert scatter["data"]["main"]["params"]["where"] == {
        "run.status": {"ne": "failed"},
        "config.wd": 0,
    }
    assert stat["props"]["lower"] is True
    # an output block needs a run; on a group page without one it says so.
    assert output["block"] == "note"
    run_tree = compile_view(view, path="g/20261024-101532-k3m9xq2a")
    assert run_tree["children"][2]["data"]["main"]["params"]["run"] == "20261024-101532-k3m9xq2a"


def test_default_view_round_trips_with_prefs(ctx: Context) -> None:
    """The default view written as YAML compiles back to the same charts; prefs fold in."""
    tree = default_view(ctx, SWEEP)
    body = from_tree(tree, path=SWEEP)
    view = m.parse({"body": body}, source="default")
    again = compile_view(view, path=SWEEP)
    lines = lambda t: [n["props"]["y"] for n in walk(t) if n["block"] == "line"]  # noqa: E731
    assert lines(again) == lines(tree)
    prefs = {
        "view": {"smooth": 0.5, "by": None},
        "charts": {"line-val-acc": {"by": "config.lr", "band": "std", "scale": "log"}},
        "added": ["lr", "x/new"],
        "hidden": ["x"],
    }
    folded = apply_prefs(body, prefs)
    props = {p["id"]: p for b, p in yaml_walk(folded) if b == "line"}
    wanted = {"by": ["config.lr"], "band": "std", "scale": "log", "smooth": 0.5}
    assert props["line-val-acc"].items() >= wanted.items()
    # a shown metric isn't added twice; a new one joins the first grid of curves.
    assert [p for p in props if p.startswith("added-")] == ["added-x-new"]
    assert any("added-x-new" in str(k) for k in folded[0]["grid"]["children"])
    assert "seeds" not in props["line-val-acc"]
    assert props["line-train-loss"]["smooth"] == 0.5
    # the view-wide "each run" removes the default's seed averaging.
    assert "seeds" not in props["line-train-loss"]
    assert "hidden" not in str(folded)


def test_view_ops_and_the_page(ctx: Context, project: Path) -> None:
    """A draft from an example validates, saves as a version, and the page shows it."""
    answer = call("view new", {"group": SWEEP, "from": "sweep"}, ctx)
    draft = Path(answer["file"])
    assert draft == project / ".beamtime" / "drafts" / "lr-sweep" / "view.yaml"
    assert (project / ".beamtime" / ".gitignore").read_text().strip().endswith("*")
    with pytest.raises(OpError, match="exists"):
        call("view new", {"group": SWEEP, "from": "sweep"}, ctx)
    text = draft.read_text()
    assert "metric.val/acc.max" in text and "config.lr" in text

    result = call("view validate", {"draft": "lr-sweep", "render": False}, ctx)
    assert result["ok"], result["findings"]
    assert {f["message"] for f in result["findings"]} == {"no finding"}

    draft.write_text(text.replace("metric.val/acc.max", "metric.val/accc.max", 1))
    result = call("view validate", {"draft": "lr-sweep", "render": False}, ctx)
    assert not result["ok"]
    assert any("did you mean" in f["message"].lower() for f in result["findings"])
    with pytest.raises(OpError, match="errors"):
        call("view save", {"draft": "lr-sweep"}, ctx)

    draft.write_text(text.replace("TODO: the result", "lr 3e-4 is best"))
    assert page_view(ctx, SWEEP)["source"] == "default"
    saved = call("view save", {"draft": "lr-sweep", "message": "first"}, ctx)
    shown = page_view(ctx, SWEEP)
    assert shown["source"] == "view" and shown["version"] == saved["version"]
    assert shown["finding"].startswith("lr 3e-4 is best")
    assert shown["author"] == shown["user"]

    # no inheritance: the parent group and the sweep's runs keep the default.
    assert page_view(ctx, "scaling")["source"] == "default"
    run = shown["view"]["children"][-1]["data"]["main"]["params"]["from"]
    rows = call("runs", {"from": run, "limit": 1}, ctx)["rows"]
    assert page_view(ctx, rows[0][0])["source"] == "default"

    history = call("view history", {"group": SWEEP}, ctx)["entries"]
    assert [e["message"] for e in history] == ["first"]
    assert call("view show", {"group": SWEEP}, ctx)["yaml"].startswith("schema: 1")
    assert page_view(ctx, SWEEP, version=saved["version"])["version"] == saved["version"]
    with pytest.raises(OpError, match="no view version"):
        page_view(ctx, SWEEP, version="20990101-000000-aaaa")


def test_broken_version_falls_back(ctx: Context, project: Path) -> None:
    """An invalid view version shows the default with a notice instead of breaking the page."""
    folder = project / "beamtime" / SWEEP / "view"
    folder.mkdir()
    (folder / "20261027-100000-abcd.yaml").write_text("schema: 1\nbody: [{nope: {}}]\n")
    shown = page_view(ctx, SWEEP)
    assert shown["source"] == "default" and "no block 'nope'" in shown["invalid"]
    assert shown["view"]["children"][0]["id"] == "invalid-view"


def test_data_files_are_hashed_on_save(ctx: Context, project: Path) -> None:
    """A draft's data file is stored under its content hash and read through the file query."""
    call("view new", {"group": SWEEP, "from": "sweep", "name": "fit"}, ctx)
    folder = project / ".beamtime" / "drafts" / "fit"
    (folder / "data" / "fit.csv").write_text("lr,acc\n0.001,0.9\n0.01,0.8\n")
    data = yaml.safe_load((folder / "view.yaml").read_text())
    data["finding"] = "x"
    data["body"].append({"data_table": {"id": "fit", "file": "data/fit.csv"}})
    (folder / "view.yaml").write_text(yaml.safe_dump(data))
    answer = call("file", {"view": SWEEP, "path": "data/fit.csv", "draft": "fit"}, ctx)
    assert answer["rows"] == [[0.001, 0.9], [0.01, 0.8]]
    call("view save", {"draft": "fit"}, ctx)
    shown = page_view(ctx, SWEEP)
    table = next(n for n in walk(shown["view"]) if n["id"] == "fit")
    ref = table["data"]["main"]["params"]["path"]
    assert ref.startswith("data/") and ref.endswith("-fit.csv") and len(ref) == len("data/12345678-fit.csv")
    assert call("file", {"view": SWEEP, "path": ref}, ctx)["rows"][1] == [0.01, 0.8]
    # a new draft from the saved view brings its data files along.
    call("view new", {"group": SWEEP, "name": "fit2"}, ctx)
    assert (project / ".beamtime" / "drafts" / "fit2" / ref).is_file()


@pytest.mark.parametrize("name", EXAMPLES)
def test_examples_validate_on_synth(ctx: Context, name: str) -> None:
    """Every example, filled with a fitting group's keys, has no errors."""
    group = {"direction": "scaling", "run": None}.get(name, SWEEP)
    if group is None:
        group = call("runs", {"from": SWEEP, "limit": 1}, ctx)["rows"][0][0]
    call("view new", {"group": group, "from": name, "name": f"ex-{name}"}, ctx)
    result = call("view validate", {"draft": f"ex-{name}", "render": False}, ctx)
    assert result["ok"], result["findings"]


def test_save_page_from_the_ui(ctx: Context) -> None:
    """Save as view writes the default with the viewer's settings, title and finding."""
    from beamtime.ops.views import save_page

    ui = Context.make(caller="view")
    save_page(ui, SWEEP, {"charts": {"line-val-acc": {"smooth": 0.3}}, "added": ["lr"]}, "T", "F")
    shown = page_view(ctx, SWEEP)
    assert (shown["title"], shown["finding"]) == ("T", "F")
    line = next(n for n in walk(shown["view"]) if n["id"] == "line-val-acc")
    assert line["props"]["smooth"] == 0.3


def test_guide_parts(ctx: Context) -> None:
    """The guide answers every part; blocks list the union; a group adds its keys."""
    assert "view_new" in call("guide", {}, ctx)["text"]
    assert "**scatter**" in call("guide", {"part": "blocks"}, ctx)["text"]
    assert "- x: text (required" in call("guide", {"part": "blocks", "name": "scatter"}, ctx)["text"]
    assert "This group" in call("guide", {"group": SWEEP}, ctx)["text"]
    for part in ("queries", "checklist", "anti-patterns", "kit", "examples"):
        assert call("guide", {"part": part}, ctx)["text"]


def walk(t: dict) -> list[dict]:
    """List a block tree's nodes.

    :param t: The root.
    :return: Every node."""
    return [t, *(x for k in t.get("children", []) for x in walk(k))]


def yaml_walk(body: list) -> list:
    """List YAML-form nodes.

    :param body: The nodes.
    :return: ``(block, props)`` pairs."""
    from beamtime.views.compile import yaml_walk as walk_

    return walk_(body)


def test_header_follows_the_views_lead_metric(ctx: Context) -> None:
    """The facts line's best value uses the view's first metric and its direction."""
    from beamtime.ops.views import save_page
    from beamtime.serve.app import summary_of

    assert summary_of(ctx, SWEEP)["summary"]["metric"] == "val/acc"
    save_page(Context.make(caller="view"), SWEEP, {}, "T", "F")
    folder = ctx.logdir / SWEEP / "view"
    newest = sorted(folder.glob("*.yaml"))[-1]
    data = yaml.safe_load(newest.read_text())
    data["metrics"] = {"train/loss": {"higher_is_better": False}}
    (folder / "20991231-000000-zzzz.yaml").write_text(yaml.safe_dump(data))
    best = summary_of(ctx, SWEEP)["summary"]
    assert (best["metric"], best["stat"]) == ("train/loss", "min")


def test_new_chart_settings_save_and_compile() -> None:
    """Symlog, y limits, a step range, legend and raw-curve settings fold in and compile."""
    body = [{"grid": {"id": "g", "children": [{"line": {"id": "c", "y": "val/loss"}}]}}]
    prefs = {"charts": {"c": {"scale": "symlog", "ymin": 0.1, "ymax": None, "steps": [100, None],
                              "legend": False, "raw": False}}}  # fmt: skip
    folded = apply_prefs(body, prefs)
    props = folded[0]["grid"]["children"][0]["line"]
    assert props == {"id": "c", "y": "val/loss", "scale": "symlog", "ymin": 0.1, "steps": [100, None],
                     "legend": False, "raw": False}  # fmt: skip
    tree = compile_view(m.parse({"body": folded}, source="t"), path="g")
    line = tree["children"][0]["children"][0]
    assert line["props"]["scale"] == "symlog" and line["props"]["legend"] is False
    assert line["data"]["main"]["params"]["steps"] == [100, None]
