from pathlib import Path

import pytest
import yaml

from beamtime.format.schema import SchemaError
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.serve.app import view as page_view
from beamtime.views import model as m
from beamtime.views.library import BlockDef, Library, Param, problems, queries_for
from beamtime.views.store import code_text

SWEEP = "scaling/lr-sweep"
GENERAL = """schema: 1
name: phase-map
description: Heatmap of a value over two config fields. Use for two-way sweeps; not for runs.
params:
  x: {kind: field}
  y: {kind: field}
  value: {kind: field}
  curves: {kind: metrics, default: [val/acc]}
examples:
  - {x: config.lr, y: config.seed, value: metric.val/acc.max}
  - {x: config.lr, y: config.seed, value: metric.train/loss.min, curves: [train/loss]}
queries:
  runs: {runs: {select: [run.id, $x, $y, $value]}}
  detail: {series: {from: $run, y: $curves}}
code: code/phase-map.js
libs: [d3]
"""


def walk(t: dict) -> list[dict]:
    """List a block tree's nodes.

    :param t: The root.
    :return: The nodes, depth first."""
    return [t, *(n for c in t.get("children", []) for n in walk(c))]


def draft_view(ctx: Context, project: Path, group: str, name: str, nodes: list[dict]) -> None:
    """Start a view draft of a group and put nodes first in it.

    :param ctx: The operation context.
    :param project: The project root.
    :param group: The group.
    :param name: The draft's name.
    :param nodes: Nodes in YAML form."""
    call("view new", {"group": group, "name": name}, ctx)
    file = project / ".beamtime" / "drafts" / name / "view.yaml"
    data = yaml.safe_load(file.read_text())
    data["finding"] = "x"
    data["body"] = nodes + data["body"]
    file.write_text(yaml.safe_dump(data))


def library_block(ctx: Context, project: Path) -> Path:
    """Promote the custom example's block, generalize it and save it at the root.

    :param ctx: The operation context.
    :param project: The project root.
    :return: The block draft's folder."""
    call("view new", {"group": SWEEP, "from": "custom", "name": "pm"}, ctx)
    file = project / ".beamtime" / "drafts" / "pm" / "view.yaml"
    file.write_text(file.read_text().replace("TODO: the result in one sentence.", "x"))
    call("view save", {"draft": "pm"}, ctx)
    call("block promote", {"group": SWEEP, "block_id": "phase-map", "name": "phase-map"}, ctx)
    folder = project / ".beamtime" / "drafts" / "blocks" / "phase-map"
    (folder / "block.yaml").write_text(GENERAL)
    call("block save", {"draft": "phase-map"}, ctx)
    return folder


def test_unknown_names_parse_as_library_uses() -> None:
    """A one-key node with an unknown name is a library block; params and common props split."""
    view = m.parse(yaml.safe_load("body: [{phase-map: {x: config.lr, caption: c, span: 2}}]"))
    (use,) = view.body
    assert isinstance(use, m.Use) and use.name == "phase-map" and use.id == "phase-map"
    assert (use.params, use.caption, use.span) == ({"x": "config.lr"}, "c", 2)
    assert m.to_yaml_form(view)["body"] == [
        {"phase-map": {"id": "phase-map", "caption": "c", "span": 2, "x": "config.lr"}}
    ]
    with pytest.raises(SchemaError, match="no block 'Phase Map'"):
        m.parse({"body": [{"Phase Map": {}}]})


def test_params_are_checked_and_filled() -> None:
    """Unknown, missing and mistyped params are named; list params splice into lists."""
    block = BlockDef(
        name="b",
        code="code/b.js",
        params={"x": Param(kind="field"), "ys": Param(kind="metrics", default=["a"])},
        queries={"q": {"runs": {"select": ["run.id", "$x", "$ys"], "from": "$run"}}},
    )
    assert problems(block, {"x": "config.lr"}) == []
    assert problems(block, {}) == ["b needs x (field)"]
    assert problems(block, {"x": 3, "z": 1}) == ["b has no param 'z'", "b.x is a field, not 3"]
    filled = queries_for(block, {"x": "config.lr", "ys": ["m1", "m2"]})
    assert filled["q"]["runs"] == {"select": ["run.id", "config.lr", "m1", "m2"], "from": "$run"}


def test_nearer_blocks_win(ctx: Context, project: Path) -> None:
    """A block in a group overrides one of the same name at the root; built-in names don't count."""
    logdir = project / "beamtime"
    for where, desc in ((logdir, "root"), (logdir / "scaling", "group")):
        (where / "blocks" / "pm").mkdir(parents=True)
        (where / "blocks" / "pm" / "20261030-000000-aaaa.yaml").write_text(
            f"name: pm\ndescription: {desc}\ncode: code/pm.js\n"
        )
    (logdir / "blocks" / "line").mkdir()
    (logdir / "blocks" / "line" / "20261030-000000-aaaa.yaml").write_text("name: line\ncode: x\n")
    assert Library(ctx=ctx, path=SWEEP).get("pm").block.description == "group"
    assert Library(ctx=ctx, path=".").get("pm").block.description == "root"
    assert Library(ctx=ctx, path=SWEEP).names == ["pm"]
    with pytest.raises(SchemaError, match="no block 'pn'.*Did you mean 'pm'"):
        Library(ctx=ctx, path=SWEEP).get("pn")


def test_promote_validate_save_and_reuse(ctx: Context, project: Path) -> None:
    """A custom block becomes a library block that another group's view uses, pinned."""
    folder = library_block(ctx, project)
    listing = call("block list", {"group": "scaling"}, ctx)
    assert listing["rows"][0][:4] == ["phase-map", listing["rows"][0][1], ".",
                                      "x: field, y: field, value: field, curves: metrics"]  # fmt: skip
    version = listing["rows"][0][1]
    assert "export default" in call("block show", {"name": "phase-map"}, ctx)["code"]

    use = {"phase-map": {"x": "config.lr", "y": "config.seed", "value": "metric.val/acc.max",
                         "caption": "c"}}  # fmt: skip
    draft_view(ctx, project, "scaling", "sc", [use])
    result = call("view validate", {"draft": "sc", "render": False}, ctx)
    assert result["ok"], result["findings"]
    call("view save", {"draft": "sc"}, ctx)
    shown = page_view(ctx, "scaling")
    node = next(n for n in walk(shown["view"]) if n["id"] == "phase-map")
    assert node["block"] == "custom" and node["props"]["library"] == {"name": "phase-map",
                                                                        "version": version}  # fmt: skip
    assert node["props"]["params"]["curves"] == ["val/acc"]
    assert node["data"]["runs"]["params"]["select"][1:] == ["config.lr", "config.seed",
                                                            "metric.val/acc.max"]  # fmt: skip
    assert "export default" in code_text(ctx, node["props"]["code"])["code"]
    saved = sorted((project / "beamtime" / "scaling" / "view").glob("*.yaml"))[-1]
    assert yaml.safe_load(saved.read_text())["uses"] == {"phase-map": version}

    # a newer version: the view keeps its pin until it is upgraded.
    code = folder / "code" / "phase-map.js"
    code.write_text(code.read_text().replace("Stronger color", "A stronger color"))
    call("block save", {"draft": "phase-map"}, ctx)
    rows = call("view outdated", {}, ctx)["rows"]
    assert [r[:3] for r in rows] == [["scaling", "phase-map", version]]
    assert page_view(ctx, "scaling")["outdated"][0]["pinned"] == version
    call("view upgrade", {"group": "scaling"}, ctx)
    assert call("view outdated", {}, ctx)["rows"] == []
    assert page_view(ctx, "scaling")["outdated"] == []


def test_block_checks(ctx: Context, project: Path) -> None:
    """Promoted drafts need a description and examples; hard-coded keys and copies are named."""
    call("view new", {"group": SWEEP, "from": "custom", "name": "pm"}, ctx)
    file = project / ".beamtime" / "drafts" / "pm" / "view.yaml"
    file.write_text(file.read_text().replace("TODO: the result in one sentence.", "x"))
    call("view save", {"draft": "pm"}, ctx)
    with pytest.raises(OpError, match="no custom block 'nope'.*phase-map"):
        call("block promote", {"group": SWEEP, "block_id": "nope", "name": "pm"}, ctx)
    call("block promote", {"group": SWEEP, "block_id": "phase-map", "name": "pm"}, ctx)
    findings = call("block validate", {"draft": "pm", "render": False}, ctx)["findings"]
    errors = {f["message"] for f in findings if f["level"] == "error"}
    assert "the description says what it shows, when to use it and when not" in errors
    assert "0 example(s); give at least 2" in errors
    warned = {f["message"] for f in findings if f["level"] == "warning"}
    assert "'config.lr' is fixed in the queries" in warned

    folder = project / ".beamtime" / "drafts" / "blocks" / "pm"
    (folder / "block.yaml").write_text(GENERAL.replace("name: phase-map", "name: pm")
                                       .replace("code/phase-map.js", "code/pm.js"))  # fmt: skip
    code = folder / "code" / "pm.js"
    code.write_text(code.read_text() + "\nconst fixed = 'val/acc';\n")
    findings = call("block validate", {"draft": "pm", "render": False}, ctx)["findings"]
    assert {"level": "error", "block": "pm", "message": "'val/acc' is hard-coded in the code",
            "fix": "make it a param, or read it from the query's columns"} in findings  # fmt: skip
    with pytest.raises(OpError, match="has errors"):
        call("block save", {"draft": "pm"}, ctx)
    code.write_text(code.read_text().replace("const fixed = 'val/acc';", ""))
    call("block save", {"draft": "pm"}, ctx)
    call("block fork", {"name": "pm", "new_name": "pm2"}, ctx)
    forked = yaml.safe_load((folder.parent / "pm2" / "block.yaml").read_text())
    assert forked["derived_from"].startswith("pm@") and forked["name"] == "pm2"
    findings = call("block validate", {"draft": "pm2", "render": False}, ctx)["findings"]
    assert any(f["message"] == "pm declares the same queries" for f in findings)
    with pytest.raises(OpError, match="built-in"):
        call("block fork", {"name": "pm", "new_name": "line"}, ctx)


def test_a_missing_block_shows_the_default(ctx: Context, project: Path) -> None:
    """A view naming a block the page can't find falls back to the default, saying why."""
    folder = project / "beamtime" / SWEEP / "view"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "20261030-100000-abcd.yaml").write_text("schema: 1\nbody: [{phase-mapp: {}}]\n")
    shown = page_view(ctx, SWEEP)
    assert shown["source"] == "default" and "no block 'phase-mapp'" in shown["invalid"]
