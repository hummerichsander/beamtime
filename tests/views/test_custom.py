from pathlib import Path
import re

import pytest
import yaml

from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.views import bundle
from beamtime.serve.api import view as page_view
from beamtime.views import code
from beamtime.views import model as m
from beamtime.views import store
from beamtime.views.compile import compile_view
from beamtime.views.store import code_text
from beamtime.views.validate import static

SWEEP = "scaling/lr-sweep"
GOOD = (
    "export default function render(root) { bt.preact.render(bt.preact.html`<p>hi</p>`, root); }\n"
)


def walk(t: dict) -> list[dict]:
    """List a block tree's nodes.

    :param t: The root.
    :return: The nodes, depth first."""
    return [t, *(n for c in t.get("children", []) for n in walk(c))]


def test_custom_queries_compile_to_calls() -> None:
    """Declared queries become API calls over the page, with filters and placeholders kept."""
    view = m.parse(
        yaml.safe_load("""
filters: {run.status: finished}
body:
  - custom:
      id: c
      code: code/c.js
      libs: [d3]
      where: {config.seed: 0}
      queries:
        runs: {runs: {select: [run.id, config.lr]}}
        detail: {series: {from: $run, y: [val/acc]}}
        sub: {runs: {from: ./sub, where: {config.lr: 0.1}}}
        table: {file: {path: data/t.csv}}
"""),
        source="test",
    )
    tree = compile_view(view, path=SWEEP, draft="d")
    node = next(n for n in walk(tree) if n["id"] == "c")
    assert node["props"]["code"] == {"view": SWEEP, "path": "code/c.js", "draft": "d"}
    assert node["props"]["libs"] == ["d3"]
    data = node["data"]
    where = {"run.status": "finished", "config.seed": 0}
    assert data["runs"] == {"method": "runs", "scope": SWEEP,
                            "params": {"from": SWEEP, "where": where, "select": ["run.id", "config.lr"]}}  # fmt: skip
    assert data["detail"]["params"]["from"] == "$run"
    assert data["sub"]["params"]["from"] == f"{SWEEP}/sub"
    assert data["sub"]["params"]["where"] == where | {"config.lr": 0.1}
    assert data["table"]["params"] == {"view": SWEEP, "path": "data/t.csv", "draft": "d"}


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("function render(root) {}", "no default export"),
        ("import x from 'y';\n" + GOOD, "imports a module"),
        (GOOD + "const r = await import('x');", "imports a module"),
        (GOOD + "fetch('/api/runs');", "uses fetch"),
        (GOOD + "new WebSocket('ws://x');", "uses WebSocket"),
        (GOOD + "const c = '#ff0000';", "color literal"),
        (GOOD + "el.style.fill = 'rgb(1, 2, 3)';", "color literal"),
        (GOOD + "const xs = [" + ", ".join(["1.5"] * 250) + "];", "numbers inline"),
        (GOOD + "// " + "x" * 70_000, "KB"),
    ],
)
def test_code_checks(source: str, message: str) -> None:
    """Each rule of the code checks fires on its own."""
    assert any(message in p for p, _ in code.problems(source)), code.problems(source)


def test_code_checks_ignore_comments_and_strings() -> None:
    """Words in comments and strings are no calls: a caption may say fetch."""
    source = GOOD + "// fetch the data, then import it\nconst s = 'we fetch nothing';\n"
    assert code.problems(source) == []


def test_placeholders_and_fill() -> None:
    """Placeholders are whole strings; fill replaces the known ones."""
    q = {"from": "$run", "y": ["$metric", "val/acc"], "x": "cost $5"}
    assert code.placeholders(q) == {"run", "metric"}
    assert code.fill(q, {"run": "r1"}) == {
        "from": "r1",
        "y": ["$metric", "val/acc"],
        "x": "cost $5",
    }


def test_custom_example_saves_code_under_its_hash(ctx: Context, project: Path) -> None:
    """The custom example validates; saving stores its code by content hash; the page reads it."""
    call("view new", {"group": SWEEP, "from": "custom", "name": "pm"}, ctx)
    folder = project / ".beamtime" / "drafts" / "pm"
    assert (folder / "code" / "phase-map.js").is_file()
    result = call("view validate", {"draft": "pm", "render": False}, ctx)
    assert result["ok"], result["findings"]
    call("view save", {"draft": "pm"}, ctx)
    node = next(n for n in walk(page_view(ctx, SWEEP)["view"]) if n["id"] == "phase-map")
    ref = node["props"]["code"]
    assert ref["path"].startswith("code/") and ref["path"].endswith("-phase-map.js")
    assert "export default" in code_text(ctx, ref)["code"]
    # a new draft from the saved view brings the code along.
    call("view new", {"group": SWEEP, "name": "pm2"}, ctx)
    assert (project / ".beamtime" / "drafts" / "pm2" / ref["path"]).is_file()


def test_validation_reports_bad_custom_blocks(ctx: Context, project: Path) -> None:
    """A missing code file, an unknown library or kind, and broken code are errors."""
    call("view new", {"group": SWEEP, "name": "bad"}, ctx)
    folder = project / ".beamtime" / "drafts" / "bad"
    (folder / "code").mkdir()
    (folder / "code" / "net.js").write_text(GOOD + "fetch('x');")
    (folder / "view.yaml").write_text("""schema: 1
finding: x
body:
  - custom: {id: missing, code: code/none.js}
  - custom: {id: lib, code: code/net.js, libs: [plotly], queries: {q: {plots: {}}}}
""")
    findings = call("view validate", {"draft": "bad", "render": False}, ctx)["findings"]
    messages = {(f["id"], f["message"].split(" (")[0]) for f in findings if f["level"] == "error"}
    assert ("missing", "no code file 'code/none.js'") in messages
    assert ("lib", "no library 'plotly'") in messages
    assert ("lib", "query 'q' must name one kind") in messages
    assert ("lib", "code/net.js: uses fetch") in messages


def test_code_stays_in_code_folders(ctx: Context, project: Path) -> None:
    """Only .js files in a view's or draft's code/ folder are served."""
    call("view new", {"group": SWEEP, "from": "custom", "name": "pm"}, ctx)
    ok = code_text(ctx, {"view": SWEEP, "path": "code/phase-map.js", "draft": "pm"})
    assert ok["path"] == "code/phase-map.js"
    for path in ("view.yaml", "code/../view.yaml", "../../beamtime.yaml", "code/none.js"):
        with pytest.raises(OpError):
            code_text(ctx, {"view": SWEEP, "path": path, "draft": "pm"})


FILE_VIEW = """schema: 1
finding: x
body:
  - data_table: {id: dt, file: data/fit.csv}
  - custom:
      id: c
      code: code/c.js
      queries:
        t: {file: {path: data/fit.csv}}
        u: {file: {path: $name}}
"""


def draft_with_file(ctx: Context, project: Path, name: str, text: str = FILE_VIEW) -> Path:
    """Make a draft with a custom block, a data file and the given view.

    :param ctx: The operation context.
    :param project: The project root.
    :param name: The draft's name.
    :param text: The view's YAML.
    :return: The draft's folder."""
    call("view new", {"group": SWEEP, "name": name}, ctx)
    folder = project / ".beamtime" / "drafts" / name
    (folder / "code").mkdir()
    (folder / "code" / "c.js").write_text(GOOD)
    (folder / "data" / "fit.csv").write_text("lr,acc\n0.1,0.5\n")
    (folder / "view.yaml").write_text(text)
    return folder


def test_custom_file_query_survives_save(ctx: Context, project: Path) -> None:
    """A custom block's file query is copied on save, so the saved page and a new draft have it."""
    draft_with_file(
        ctx, project, "fit", FILE_VIEW.replace("  - data_table: {id: dt, file: data/fit.csv}\n", "")
    )
    assert call("view validate", {"draft": "fit", "render": False}, ctx)["ok"]
    call("view save", {"draft": "fit"}, ctx)
    node = next(n for n in walk(page_view(ctx, SWEEP)["view"]) if n["id"] == "c")
    ref = node["data"]["t"]["params"]["path"]
    assert ref.startswith("data/") and ref.endswith("-fit.csv")
    assert (ctx.logdir / SWEEP / "view" / ref).is_file()
    saved = list((ctx.logdir / SWEEP / "view").glob("*.yaml"))
    assert ref in max(saved).read_text()
    data = yaml.safe_load(max(saved).read_text())
    _, findings = static(ctx, SWEEP, data, source="saved")
    assert not [f for f in findings if f.level == "error"], findings
    call("view new", {"group": SWEEP, "name": "fit2"}, ctx)
    assert (project / ".beamtime" / "drafts" / "fit2" / ref).is_file()


def test_shared_data_file_is_stored_once(ctx: Context, project: Path) -> None:
    """The same file in data_table and a custom query is stored once; both refs point at it."""
    draft_with_file(ctx, project, "twice")
    call("view save", {"draft": "twice"}, ctx)
    stored = list((ctx.logdir / SWEEP / "view" / "data").iterdir())
    assert len(stored) == 1
    text = max((ctx.logdir / SWEEP / "view").glob("*.yaml")).read_text()
    assert text.count(f"data/{stored[0].name}") == 2


def test_file_placeholder_is_not_copied(ctx: Context, project: Path) -> None:
    """A $placeholder as a file path is not a file: nothing is copied for it and it stays."""
    text = FILE_VIEW.replace("  - data_table: {id: dt, file: data/fit.csv}\n", "")
    text = text.replace("t: {file: {path: data/fit.csv}}\n", "")
    folder = draft_with_file(ctx, project, "ph", text)
    (folder / "data" / "fit.csv").unlink()
    call("view save", {"draft": "ph"}, ctx)
    assert not (ctx.logdir / SWEEP / "view" / "data").exists()
    assert "path: $name" in max((ctx.logdir / SWEEP / "view").glob("*.yaml")).read_text()


def test_file_refs_skip_library_blocks_and_placeholders() -> None:
    """Only data tables, custom code and custom file queries name files, in document order."""
    body = yaml.safe_load(FILE_VIEW)["body"] + [
        {"section": {"children": [{"my-block": {"file": "data/x.csv"}}]}}
    ]
    assert m.file_refs(body) == ["data/fit.csv", "code/c.js"]


def test_bundle_carries_custom_file_query(ctx: Context, project: Path) -> None:
    """A draft's bundle for a remote holds the files its custom blocks query."""
    draft_with_file(ctx, project, "bun")
    files = bundle(ctx, store.draft(ctx, "bun"))["files"]
    assert {"data/fit.csv", "code/c.js"} <= set(files)


@pytest.mark.parametrize("outside", ["../secret.csv", "ABSOLUTE"])
def test_file_query_outside_the_draft_is_not_bundled_or_saved(
    ctx: Context, project: Path, tmp_path: Path, outside: str
) -> None:
    """A custom file query that leaves the draft is neither packed for a remote nor saved."""
    secret = tmp_path / "secret.csv"
    secret.write_text("k,v\n1,2\n")
    ref = str(secret) if outside == "ABSOLUTE" else outside
    text = FILE_VIEW.replace("  - data_table: {id: dt, file: data/fit.csv}\n", "")
    folder = draft_with_file(ctx, project, "esc", text.replace("path: data/fit.csv", f"path: {ref}"))
    (folder.parent / "secret.csv").write_text("k,v\n1,2\n")
    assert set(bundle(ctx, store.draft(ctx, "esc"))["files"]) == {"code/c.js"}
    with pytest.raises(OpError):
        call("view save", {"draft": "esc"}, ctx)
    assert not (ctx.logdir / SWEEP / "view" / "data").exists()


def test_view_new_writes_no_file_outside_the_draft(ctx: Context, project: Path) -> None:
    """A saved view whose file query leaves its folder starts a draft without that file."""
    draft_with_file(ctx, project, "fit")
    call("view save", {"draft": "fit"}, ctx)
    saved = max((ctx.logdir / SWEEP / "view").glob("*.yaml"))
    (ctx.logdir / SWEEP / "secret.csv").write_text("k,v\n1,2\n")
    text = re.sub(r"path: data/[^}]*", "path: ../secret.csv", saved.read_text())
    saved.chmod(0o644)
    saved.write_text(text)
    call("view new", {"group": SWEEP, "name": "fit2"}, ctx)
    assert not (project / ".beamtime" / "drafts" / "secret.csv").exists()
