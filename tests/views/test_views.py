from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from beamtime.format.schema import SchemaError
from beamtime.guide import EXAMPLES
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.serve.api import view as page_view
from beamtime.views import model as m
from beamtime.views.compile import compile_view
from beamtime.views.defaults import default_view
from beamtime.views.prefs import apply_prefs

SWEEP = "scaling/lr-sweep"
BENCH = "realistic/egnn-bench"


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
        ("body: [{Phase_Map: {}}]", "no block 'Phase_Map'"),
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
    template = tree["props"]["template"]
    assert "y" not in template["params"] and template["method"] == "series"
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


def test_config_block_in_the_default_views(ctx: Context, roles: dict[str, str]) -> None:
    """A group shows its varying config after the curves; a run shows its config, closed."""
    blocks = [m.block_of(b) for b in default_view(ctx, SWEEP).body]
    assert blocks.index("section") < blocks.index("config") < blocks.index("table")
    path = f"scaling/long-context/{roles['running']}"
    run = compile_view(default_view(ctx, path), path=path)
    config = next(c for c in run["children"] if c["block"] == "config")
    assert config["props"]["mode"] == "run" and config["props"]["open"] is False
    assert config["data"]["main"]["method"] == "card" and config["data"]["keys"]["params"] == {"from": "scaling/long-context"}


def test_default_view_round_trips_with_prefs(ctx: Context) -> None:
    """The default view written as YAML compiles back to the same charts; prefs fold in."""
    default = default_view(ctx, SWEEP)
    tree = compile_view(default, path=SWEEP)
    body = m.to_yaml_form(default)["body"]
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
    # a shown metric isn't added twice; a new one goes to a grid of added charts after the curves.
    assert [p for p in props if p.startswith("added-")] == ["added-x-new"]
    added = next(n["grid"] for n in folded if n.get("grid", {}).get("id") == "added")
    assert "added-x-new" in str(added)
    assert "seeds" not in props["line-val-acc"]
    assert props["line-train-loss"]["smooth"] == 0.5
    # the view-wide "each run" removes the default's seed averaging.
    assert "seeds" not in props["line-train-loss"]
    assert "hidden" not in str(folded)


def test_save_as_view_drops_removed_charts_and_keeps_the_order() -> None:
    """Hidden charts leave the view, sections emptied by it too; the rest stays in its order."""
    from beamtime.views.defaults import curves

    metrics = ["val/acc", "val/loss", "train/loss", "train/lr", "lr"]
    body = m.to_yaml_form(m.View(body=curves(metrics, None, False, "val/acc")))["body"]
    removed = ["line-val-acc", "line-train-loss", "line-train-lr", "added-x/new"]
    prefs = {"removed": removed, "added": ["x/new", "y/new"]}
    folded = apply_prefs(body, prefs)
    props = [p["id"] for b, p in yaml_walk(folded) if b in ("section", "grid", "line")]
    assert props == [
        "charts-val", "charts-val-curves", "line-val-loss",
        "charts-unprefixed", "charts-unprefixed-curves", "line-lr", "added", "added-y-new",
    ]  # fmt: skip


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
    from beamtime.views.model import yaml_walk as walk_

    return walk_(body)


def test_header_follows_the_views_lead_metric(ctx: Context) -> None:
    """The facts line's best value uses the view's first metric and its direction."""
    from beamtime.ops.views import save_page
    from beamtime.serve.api import summary_of

    assert summary_of(ctx, SWEEP)["summary"]["metric"] == "val/acc"
    save_page(Context.make(caller="view"), SWEEP, {}, "T", "F")
    folder = ctx.logdir / SWEEP / "view"
    newest = sorted(folder.glob("*.yaml"))[-1]
    data = yaml.safe_load(newest.read_text())
    data["metrics"] = {"train/loss": {"higher_is_better": False, "label": "Training loss"}}
    (folder / "20991231-000000-zzzz.yaml").write_text(yaml.safe_dump(data))
    best = summary_of(ctx, SWEEP)["summary"]
    assert (best["metric"], best["stat"], best["label"]) == ("train/loss", "min", "Training loss")


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


def test_axis_titles_compile_and_yield_to_the_viewer() -> None:
    """Authored axis titles reach every chart kind; a viewer's other x or metric drops its title."""
    body = [
        {"line": {"id": "c", "y": "val/loss", "xlabel": "tokens", "ylabel": "loss"}},
        {"scatter": {"id": "s", "x": "config.lr", "y": "val/loss", "ylabel": "best loss"}},
        {"bar": {"id": "b", "x": "config.arm", "y": "val/loss", "xlabel": "arm"}},
        {"histogram": {"id": "h", "key": "grads", "ylabel": "layers"}},
    ]
    tree = compile_view(m.parse({"body": body}, source="t"), path="g")
    line, scatter, bar, hist = (k["props"] for k in tree["children"])
    assert (line["xlabel"], line["ylabel"]) == ("tokens", "loss")
    assert (scatter["xlabel"], scatter["ylabel"]) == (None, "best loss")
    assert bar["xlabel"] == "arm" and hist["ylabel"] == "layers"
    folded = apply_prefs(deepcopy(body), {"charts": {"c": {"x": "_elapsed"}}})
    assert folded[0]["line"] == {"id": "c", "y": "val/loss", "ylabel": "loss", "x": "_elapsed"}
    folded = apply_prefs(deepcopy(body), {"charts": {"c": {"y": ["val/acc", "val/f1"]}}})
    assert folded[0]["line"]["xlabel"] == "tokens" and "ylabel" not in folded[0]["line"]


def test_a_metric_as_x_and_a_page_wide_x_fold_into_the_view() -> None:
    """Any logged metric is an x axis; a page-wide x reaches every line, a chart's own wins."""
    body = [
        {"line": {"id": "a", "y": "val/loss", "xlabel": "tokens"}},
        {"line": {"id": "b", "y": "val/loss"}},
    ]
    prefs = {"view": {"x": "sys/gpu_mem"}, "charts": {"b": {"x": "epoch"}}}
    folded = apply_prefs(deepcopy(body), prefs)
    assert folded[0]["line"] == {"id": "a", "y": "val/loss", "x": "sys/gpu_mem"}
    assert folded[1]["line"]["x"] == "epoch"
    tree = compile_view(m.parse({"body": folded}, source="t"), path="g")
    assert [k["data"]["main"]["params"]["x"] for k in tree["children"]] == ["sys/gpu_mem", "epoch"]


def test_a_charts_colormap_and_color_fold_into_its_block() -> None:
    """A colormap and a color field reach the chart they were chosen for; the page-wide one the others."""
    from beamtime.views.validate import structure

    body = [
        {"line": {"id": "a", "y": "val/loss", "color": "config.lr"}},
        {"line": {"id": "b", "y": "val/loss"}},
        {"scatter": {"id": "s", "x": "config.lr", "y": "val/loss"}},
        {"bar": {"id": "r", "x": "config.arm", "y": "val/loss", "colormap": "magma"}},
    ]
    prefs = {"view": {"colormap": "RdBu"}, "charts": {"a": {"color": None}, "b": {"colormap": None}}}
    folded = apply_prefs(deepcopy(body), prefs)
    assert "color" not in folded[0]["line"] and folded[0]["line"]["colormap"] == "RdBu"
    assert "colormap" not in folded[1]["line"]
    assert folded[2]["scatter"]["colormap"] == "RdBu" and folded[3]["bar"]["colormap"] == "RdBu"
    tree = compile_view(m.parse({"body": folded}, source="t"), path="g")
    assert [k["props"].get("colormap") for k in tree["children"]] == ["RdBu", None, "RdBu", "RdBu"]
    bad = m.parse({"body": [{"line": {"id": "c", "y": "val/loss", "colormap": "nope"}}]}, source="t")
    assert any("no colormap 'nope'" in f.message for f in structure(bad, None))


def test_text_panels_from_the_ui(ctx: Context) -> None:
    """A text panel is added at the top, edited, and removed, each a new version."""
    from beamtime.ops.views import edit_text

    ui = Context.make(caller="view")
    edit_text(ui, SWEEP, None, "First *thoughts*.")
    first = page_view(ctx, SWEEP)["view"]["children"][0]
    assert (first["block"], first["props"]["text"]) == ("markdown", "First *thoughts*.")
    edit_text(ui, SWEEP, first["id"], "Better $x^2$.")
    assert page_view(ctx, SWEEP)["view"]["children"][0]["props"]["text"] == "Better $x^2$."
    edit_text(ui, SWEEP, first["id"], "")
    assert page_view(ctx, SWEEP)["view"]["children"][0]["block"] != "markdown"
    messages = [e["message"] for e in call("view history", {"group": SWEEP}, ctx)["entries"]]
    assert messages[0] == "removed a text panel in the web UI"
    with pytest.raises(OpError, match="no text panel"):
        edit_text(ui, SWEEP, "nope", "x")


def test_layout_prefs_fold_into_the_view() -> None:
    """The viewer's order of a grid's blocks and their widths are saved with the view."""
    body = [{"grid": {"id": "g", "children": [{"line": {"id": "a", "y": "x"}}, {"line": {"id": "b", "y": "y"}},
                                              {"stat": {"id": "c"}}]}}]  # fmt: skip
    folded = apply_prefs(body, {"order": {"g": ["c", "a"]}, "spans": {"a": "full", "b": 1}})
    kids = folded[0]["grid"]["children"]
    assert [next(iter(k.values()))["id"] for k in kids] == ["c", "a", "b"]
    assert kids[1]["line"]["span"] == "full" and "span" not in kids[2]["line"]


def test_authored_views_keep_notes_and_memory(ctx: Context) -> None:
    """A view without notes or memory blocks still shows them, after its own blocks."""
    from beamtime.ops.views import write_version

    write_version(ctx, SWEEP, m.parse({"body": [{"line": {"y": "val/acc"}}]}, source="t"), None, None)
    blocks = [n["block"] for n in page_view(ctx, SWEEP)["view"]["children"]]
    assert blocks == ["line", "memory", "notes"]
    placed = {"body": [{"notes": {"id": "mine", "limit": 9}}, {"line": {"y": "val/acc"}}]}
    write_version(ctx, SWEEP, m.parse(placed, source="t"), None, None)
    blocks = [n["block"] for n in page_view(ctx, SWEEP)["view"]["children"]]
    assert blocks == ["notes", "line", "memory"]


def test_curves_sit_in_sections_by_prefix() -> None:
    """Every metric has one chart, in the section of its prefix; sys/* is last and closed."""
    from beamtime.views.defaults import curves

    metrics = ["val/acc", "val/loss", "train/loss", "train/lr", "lr", "sys/cpu", "energy/a", "energy/b"]
    out = curves(metrics, None, False, [])
    assert [(s.title, s.open) for s in out] == [
        ("val (2)", True), ("train (2)", True), ("energy (2)", False),
        ("Other (1)", False), ("System (1)", False),
    ]  # fmt: skip
    charts = [c.y for s in out for c in s.children[0].children]
    assert sorted(charts) == sorted(metrics) and out[0].children[0].children[0].id == "line-val-acc"


def test_pins_make_the_main_section_and_one_prefix_is_a_plain_grid() -> None:
    """Pinned metrics sit in an open Main section and stay in their own section; prefixes of one
    metric go to Other."""
    from beamtime.views.defaults import curves

    metrics = ["val/acc", "train/loss", "train/lr", "energy/e", "energy/m", "x/one"]
    out = curves(metrics, None, False, ["energy/e", "val/acc"])
    assert [(s.title, s.open) for s in out] == [
        ("Main (2)", True), ("train (2)", True), ("energy (2)", True), ("Other (2)", False),
    ]  # fmt: skip
    assert [c.y for c in out[0].children[0].children] == ["energy/e", "val/acc"]
    assert out[0].children[0].children[0].id == "pin-energy-e"
    assert out[2].children[0].children[0].id == "line-energy-e"
    (grid,) = curves(["loss", "acc", "epoch"], None, False, [])
    assert isinstance(grid, m.Grid) and [c.y for c in grid.children] == ["loss", "acc"]


def test_ui_changes_on_a_broken_view_say_how_to_repair(ctx: Context, project: Path) -> None:
    """Save as view and text panels refuse a broken saved version with a clear message."""
    from beamtime.ops.views import edit_text, save_page

    folder = project / "beamtime" / SWEEP / "view"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "20261031-100000-abcd.yaml").write_text("body: [unclosed\n")
    ui = Context.make(caller="view")
    with pytest.raises(OpError, match="is broken"):
        save_page(ui, SWEEP, {}, "T", "F")
    with pytest.raises(OpError, match="view new"):
        edit_text(ui, SWEEP, None, "x")


def test_block_example_drafts_keep_their_names(ctx: Context) -> None:
    """A view draft can't take a name the block examples render under."""
    with pytest.raises(OpError, match="kept for block examples"):
        call("view new", {"group": SWEEP, "name": "block-curve"}, ctx)


def test_the_default_view_is_a_view(ctx: Context) -> None:
    """The default view compiles like an authored one and starts a draft as written."""
    from beamtime.ops.views import current_yaml

    view = default_view(ctx, SWEEP)
    assert [m.block_of(n) for n in view.body][-2:] == ["memory", "notes"]
    text, origin = current_yaml(ctx, SWEEP)
    assert origin == "the built-in default view"
    assert m.parse(yaml.safe_load(text), source="t").body == view.body


def test_main_metrics_are_pinned_never_guessed(ctx: Context) -> None:
    """The proposal's predicted metric is the default pin; a group without one has none."""
    from beamtime.views.defaults import pins_of

    assert pins_of(ctx, SWEEP) == [{"y": "val/acc", "higher": True}]
    assert pins_of(ctx, SWEEP, []) == []
    given = [{"y": "nope", "higher": True}, {"y": "train/loss", "higher": False}]
    assert pins_of(ctx, SWEEP, given) == [{"y": "train/loss", "higher": False}]
    assert pins_of(ctx, BENCH) == []


def test_the_default_view_takes_the_pins(ctx: Context) -> None:
    """Pins make an open Main section, the table's metric columns and its sparkline."""
    from beamtime.views.defaults import pins_of

    titles = lambda v: [b.title for b in v.body if isinstance(b, m.Section)]  # noqa: E731
    table = lambda v: next(b for b in v.body if isinstance(b, m.Table))  # noqa: E731
    bench = default_view(ctx, BENCH)
    assert not any(t.startswith("Main") for t in titles(bench))
    assert table(bench).sparkline is None
    assert not any(c.startswith("metric.") for c in table(bench).columns)

    pins = [{"y": "train/loss", "higher": False}, {"y": "val/acc", "higher": True}]
    view = default_view(ctx, SWEEP, pins)
    main = next(b for b in view.body if isinstance(b, m.Section))
    assert (main.title, main.open) == ("Main (2)", True)
    assert [c.id for c in main.children[0].children] == ["pin-train-loss", "pin-val-acc"]
    # a pinned metric is charted in Main and again in its own section, under different ids.
    charts = [c for b in view.body if isinstance(b, m.Section) for c in b.children[0].children]
    assert [c.y for c in charts].count("train/loss") == 2
    assert len({c.id for c in charts}) == len(charts)
    assert table(view).sparkline == "train/loss"
    assert table(view).columns[-2:] == ["metric.train/loss.last", "metric.val/acc.last"]

    default = default_view(ctx, SWEEP)
    assert next(b for b in default.body if isinstance(b, m.Section)).title == "Main (1)"
    none = default_view(ctx, SWEEP, pins_of(ctx, SWEEP, []))
    assert not any(t.startswith("Main") for t in titles(none))


def test_a_prefix_named_main_does_not_collide_with_the_main_section() -> None:
    """Main and a ``main/*`` prefix are two sections with their own ids."""
    from beamtime.views.defaults import curves

    sections = curves(["main/a", "main/b", "val/x", "val/y"], None, False, ["val/x"])
    ids = [s.id for s in sections]
    assert {"main", "charts-main"} <= set(ids) and len(set(ids)) == len(ids)


def test_the_page_answers_with_its_pins(ctx: Context) -> None:
    """The view answer says which metrics are pinned; the viewer's pins reach the default view."""
    from beamtime.serve.api import view

    assert view(ctx, SWEEP)["pins"] == [{"y": "val/acc", "higher": True}]
    assert view(ctx, SWEEP, metrics=[])["pins"] == []
    assert view(ctx, BENCH)["pins"] == []
    mine = [{"y": "train/loss", "higher": False}]
    answer = view(ctx, SWEEP, metrics=mine)
    assert answer["pins"] == mine
    assert answer["view"]["children"][0]["props"]["title"] == "Main (1)"


def test_the_header_follows_the_pins(ctx: Context) -> None:
    """No pin, no best; the viewer's first pin leads, else the view's, else the proposal's."""
    from beamtime.serve.api import summary_of

    assert summary_of(ctx, BENCH)["summary"] is None
    assert summary_of(ctx, SWEEP, [])["summary"] is None
    mine = [{"y": "train/loss", "higher": False}, {"y": "val/acc", "higher": True}]
    best = summary_of(ctx, SWEEP, mine)["summary"]
    assert (best["metric"], best["stat"]) == ("train/loss", "min")
    best = summary_of(ctx, BENCH, [{"y": "training/loss", "higher": True}])["summary"]
    assert (best["metric"], best["stat"]) == ("training/loss", "max")


def test_save_as_view_writes_the_pins(ctx: Context) -> None:
    """Pins become ``main_metrics`` in order, the direction only where it differs; null leaves it."""
    from beamtime.ops.views import save_page

    def newest() -> dict:
        return yaml.safe_load(sorted((ctx.logdir / SWEEP / "view").glob("*.yaml"))[-1].read_text())

    ui = Context.make(caller="view")
    pins = [{"y": "train/loss", "higher": False}, {"y": "val/acc", "higher": False}]
    save_page(ui, SWEEP, {"main": pins}, "T", "F")
    saved = newest()
    assert saved["main_metrics"] == ["train/loss", "val/acc"]
    assert saved["metrics"] == {"val/acc": {"higher_is_better": False}}
    main = next(n["section"] for n in saved["body"] if n["section"]["id"] == "main")
    assert main["title"] == "Main (2)"

    save_page(ui, SWEEP, {"main": None}, "T", "F")
    assert newest()["main_metrics"] == saved["main_metrics"]


def test_unpinning_everything_keeps_the_labels(ctx: Context, project: Path) -> None:
    """``metrics:`` only says how a metric is shown, so no main metric loses no label."""
    from beamtime.ops.views import save_page

    shown = {"val/acc": {"label": "Accuracy", "unit": "%"}, "train/loss": {"scale": "log"}}
    call("view new", {"group": SWEEP, "from": "sweep", "name": "mine"}, ctx)
    file = project / ".beamtime" / "drafts" / "mine" / "view.yaml"
    data = yaml.safe_load(file.read_text()) | {"finding": "x", "metrics": shown}
    file.write_text(yaml.safe_dump(data | {"main_metrics": ["val/acc"]}))
    call("view save", {"draft": "mine"}, ctx)

    save_page(Context.make(caller="view"), SWEEP, {"main": []}, "T", "F")
    saved = yaml.safe_load(sorted((ctx.logdir / SWEEP / "view").glob("*.yaml"))[-1].read_text())
    assert saved["main_metrics"] == [] and saved["metrics"] == shown


def test_a_saved_view_declares_its_main_metrics(ctx: Context) -> None:
    """``main_metrics`` are the pins and the header's lead; ``[]`` is none; a view from before
    it leads with its first ``metrics:`` entry; without either the proposal's metrics apply."""
    from beamtime.views.store import declared_of

    view = lambda **kw: m.View(**kw)  # noqa: E731
    shown = {"val/acc": m.MetricInfo(label="Accuracy"), "train/loss": m.MetricInfo(unit="nats")}
    assert declared_of(view()) is None
    assert declared_of(view(main_metrics=[])) == []
    assert declared_of(view(metrics=shown, main_metrics=["train/loss"])) == [
        {"y": "train/loss", "higher": False, "label": None}
    ]
    assert declared_of(view(metrics=shown)) == [{"y": "val/acc", "higher": True, "label": "Accuracy"}]
    flipped = {"x": m.MetricInfo(higher_is_better=False)}
    assert declared_of(view(metrics=flipped))[0]["higher"] is False


def test_constant_means_one_value_everywhere(ctx: Context) -> None:
    """A flat zero is constant; a one-point metric that differs between runs is not."""
    keys = call("keys", {"from": "realistic/egnn-bench"}, ctx)
    constant = {r[0]: r[3] for r in keys["metrics"]["rows"]}
    assert constant["energy/Aconst_w1"] and not constant["validation/first_eval"]


def test_system_charts_are_not_averaged_over_seeds() -> None:
    """System metrics are per machine; seed averaging applies to the others only."""
    from beamtime.views.defaults import curves

    out = curves(["val/acc", "val/loss", "sys/cpu"], "config.seed", False, [])
    seeds = {c.y: c.seeds for s in out for c in s.children[0].children}
    assert seeds == {"val/acc": "config.seed", "val/loss": "config.seed", "sys/cpu": None}
