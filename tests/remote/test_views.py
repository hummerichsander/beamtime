"""Views and block drafts on a remote group (D2): the draft stays with the agent; the check and
the write happen on the source."""

import json
from pathlib import Path

import pytest
import yaml

from beamtime.ops.context import Context, OpError
from beamtime.remote import answer as call

SWEEP = "scaling/lr-sweep"
CUSTOM_CODE = (
    "export default function render(root) {\n"
    "  bt.preact.render(bt.preact.html`<p>hi</p>`, root);\n"
    "}\n"
)


def test_new_validate_render_save_cycle_for_a_remote_group(box: Path, ctx: Context) -> None:
    """The whole cycle on @box/scaling/lr-sweep: new, edit (a custom block and a data file),
    validate, render, save. The files land on box under their hash; findings come from box."""
    new = call("view new", {"group": f"@box/{SWEEP}", "name": "remote-view"}, ctx)
    assert new["group"] == f"@box/{SWEEP}"
    draft = Path(new["file"]).parent
    meta = json.loads((draft / "_draft.json").read_text())
    assert meta["group"] == f"@box/{SWEEP}"

    view = {
        "schema": 1,
        "title": "remote",
        "finding": "x",
        "body": [
            {"data_table": {"id": "fit", "file": "data/fit.csv"}},
            {
                "custom": {
                    "id": "c",
                    "code": "code/c.js",
                    "queries": {"main": {"runs": {"from": ".", "limit": 1}}},
                }
            },
        ],
    }
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    (draft / "data" / "fit.csv").write_text("x,y\n1,2\n")
    (draft / "code").mkdir(exist_ok=True)
    (draft / "code" / "c.js").write_text(CUSTOM_CODE)

    checked = call("view validate", {"draft": "remote-view"}, ctx)
    assert checked["ok"], checked["findings"]

    render = call("view render", {"draft": "remote-view"}, ctx)
    if not render.get("rendered"):
        pytest.skip(f"no browser: {render.get('reason')}")
    assert not any(f["level"] == "error" for f in render.get("findings", []))
    assert render["shots"] and Path(render["shots"][0]["file"]).is_file()

    saved = call("view save", {"draft": "remote-view"}, ctx)
    assert saved["path"].startswith(f"@box/{SWEEP}/view/")
    written = box / saved["path"].removeprefix("@box/")
    assert written.is_file() and "remote" in written.read_text()
    assert list((box / SWEEP / "view" / "data").glob("*-fit.csv"))
    assert list((box / SWEEP / "view" / "code").glob("*-c.js"))

    shown = call("view show", {"group": f"@box/{SWEEP}"}, ctx)
    assert shown["current"] and "remote" in shown["yaml"]


def test_save_refuses_a_draft_with_errors(box: Path, ctx: Context) -> None:
    """A remote draft with an error is refused without writing anything on the source."""
    new = call("view new", {"group": f"@box/{SWEEP}", "name": "broken"}, ctx)
    draft = Path(new["file"]).parent
    (draft / "view.yaml").write_text(
        yaml.safe_dump({"schema": 1, "body": [{"data_table": {"id": "x"}}]})
    )
    with pytest.raises(OpError, match="has errors"):
        call("view save", {"draft": "broken"}, ctx)
    checked = call("view validate", {"draft": "broken"}, ctx)
    assert not checked["ok"]


def test_promote_a_custom_block_from_a_remote_view(box: Path, ctx: Context) -> None:
    """A block draft starts from a remote group's saved custom block, code included."""
    new = call("view new", {"group": f"@box/{SWEEP}", "name": "to-save"}, ctx)
    draft = Path(new["file"]).parent
    view = {
        "schema": 1,
        "title": "t",
        "finding": "x",
        "body": [
            {
                "custom": {
                    "id": "mine",
                    "code": "code/mine.js",
                    "queries": {"main": {"runs": {"from": ".", "limit": 1}}},
                }
            }
        ],
    }
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    (draft / "code").mkdir(exist_ok=True)
    (draft / "code" / "mine.js").write_text(CUSTOM_CODE)
    call("view save", {"draft": "to-save"}, ctx)

    promoted = call(
        "block promote",
        {"group": f"@box/{SWEEP}", "block_id": "mine", "name": "promoted-block"},
        ctx,
    )
    folder = Path(promoted["file"]).parent
    assert (folder / "code" / "promoted-block.js").read_text() == CUSTOM_CODE
    meta = json.loads((folder / "_draft.json").read_text())
    assert meta["group"] == f"@box/{SWEEP}"


def test_an_old_remote_gets_an_upgrade_message(
    ctx: Context, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A remote whose beamtime doesn't know a bundle method answers a clear upgrade message,
    naming its version, instead of a raw 'no API method' error."""
    from beamtime.remote import sources as remote_sources
    from beamtime.remote.client import RemoteError
    from beamtime.remote.route import on_source

    class FakeClient:
        name = "box"
        info = {"version": "0.1.0"}

        def request(self, method: str, params: dict, caller: str = "cli") -> None:
            raise RemoteError("box", f"no API method {method!r}", code=4)

    monkeypatch.setattr(remote_sources, "client_for", lambda ctx, name: FakeClient())
    with pytest.raises(OpError, match=r"@box runs beamtime 0\.1\.0.*needs a newer version"):
        on_source("view_check", f"@box/{SWEEP}", ctx, {"yaml": "schema: 1\n", "files": {}})


def test_a_bundle_cannot_leave_the_sources_log_dir(box: Path, ctx: Context, tmp_path: Path) -> None:
    """The source resolves a bundle's group in its own index and refuses file references outside
    the bundle, so nothing is written or read beyond its log dir."""
    import dataclasses

    from beamtime.serve.api import dispatch

    here = dataclasses.replace(ctx, logdir=box, sources=None)
    outside = tmp_path / "outside.js"
    outside.write_text(CUSTOM_CODE)
    empty_view = "schema: 1\ntitle: t\nfinding: f\nbody: []\n"
    with pytest.raises(OpError, match="leaves the log dir"):
        dispatch(here, "view_put", {"group": "../../evil", "draft": "d", "yaml": empty_view})
    assert not (box.parent.parent / "evil").exists()
    custom = {"id": "c", "code": str(outside), "queries": {"main": {"runs": {"from": "."}}}}
    text = yaml.safe_dump({"schema": 1, "title": "t", "finding": "f", "body": [{"custom": custom}]})
    with pytest.raises(OpError, match="leaves the draft"):
        dispatch(here, "view_put", {"group": SWEEP, "draft": "d", "yaml": text})
    assert not (box / SWEEP / "view").exists() or not list((box / SWEEP / "view").rglob("*outside*"))
    with pytest.raises(OpError, match="leaves the log dir"):
        dispatch(here, "view_files", {"group": "../..", "ref": "data/x"})


def test_a_block_promoted_from_a_remote_view_is_checked_and_saved_there(
    box: Path, ctx: Context
) -> None:
    """A block draft from a remote group stays here; validating it (its examples rendered with
    the draft's own code) and saving it run on the source, where the block lands."""
    new = call("view new", {"group": f"@box/{SWEEP}", "name": "with-block"}, ctx)
    draft = Path(new["file"]).parent
    custom = {"id": "mine", "code": "code/mine.js", "queries": {"main": {"runs": {"from": "."}}}}
    view = {"schema": 1, "title": "t", "finding": "x", "body": [{"custom": custom}]}
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    (draft / "code").mkdir(exist_ok=True)
    (draft / "code" / "mine.js").write_text(CUSTOM_CODE)
    call("view save", {"draft": "with-block"}, ctx)

    promoted = call(
        "block promote", {"group": f"@box/{SWEEP}", "block_id": "mine", "name": "greeting"}, ctx
    )
    file = Path(promoted["file"])
    block = yaml.safe_load(file.read_text())
    block["description"] = "Says hi. Use to test blocks on a remote; not for results."
    block["params"] = {"n": {"kind": "number", "default": 1}}
    block["examples"] = [{"n": 1}, {"n": 2}]
    file.write_text(yaml.safe_dump(block, sort_keys=False))

    checked = call("block validate", {"draft": "greeting"}, ctx)
    assert checked["ok"], checked["findings"]
    if checked.get("render", {}).get("rendered"):
        assert not any(f["level"] == "error" for f in checked["findings"])

    saved = call("block save", {"draft": "greeting", "group": SWEEP}, ctx)
    assert saved["path"].startswith(f"@box/{SWEEP}/blocks/greeting/")
    assert (box / saved["path"].removeprefix("@box/")).is_file()
    assert list((box / SWEEP / "blocks" / "greeting" / "code").glob("*-greeting.js"))
    assert not list((box.parent / ".beamtime" / "bundles").glob("*"))

    with pytest.raises(OpError, match="saves on @box"):
        call("block save", {"draft": "greeting", "group": "@elsewhere/x"}, ctx)

    # a view on the remote pins the block; a newer version is picked up by view upgrade.
    new = call("view new", {"group": f"@box/{SWEEP}", "name": "uses-block"}, ctx)
    uses = {"schema": 1, "title": "t", "finding": "x", "body": [{"greeting": {"id": "g", "n": 1}}]}
    Path(new["file"]).write_text(yaml.safe_dump(uses, sort_keys=False))
    call("view save", {"draft": "uses-block"}, ctx)
    pinned = yaml.safe_load(newest_view(box).read_text())["uses"]["greeting"]
    code = file.parent / "code" / "greeting.js"
    code.write_text(code.read_text().replace("hi", "hello"))
    call("block save", {"draft": "greeting", "group": SWEEP}, ctx)
    assert call("view outdated", {"group": f"@box/{SWEEP}"}, ctx)["rows"]
    call("view upgrade", {"group": f"@box/{SWEEP}"}, ctx)
    assert yaml.safe_load(newest_view(box).read_text())["uses"]["greeting"] != pinned

    # a fork of the remote's library block starts here and saves there under its new name.
    forked = call(
        "block fork", {"name": "greeting", "new_name": "wave", "group": f"@box/{SWEEP}"}, ctx
    )
    assert "hello" in (Path(forked["file"]).parent / "code" / "wave.js").read_text()
    call("block save", {"draft": "wave", "group": SWEEP}, ctx)
    assert list((box / SWEEP / "blocks" / "wave").glob("*.yaml"))


def newest_view(box: Path) -> Path:
    """Find the newest view version of the sweep on the remote.

    :param box: The remote's log dir.
    :return: Its file."""
    return sorted((box / SWEEP / "view").glob("*.yaml"))[-1]


def test_page_writes_on_a_remote_group(box: Path, ctx: Context) -> None:
    """The web UI's own writes, a text panel and saving a page's settings, land on the source."""
    import dataclasses

    from beamtime.serve.api import dispatch

    here = dataclasses.replace(ctx, caller="view")
    added = dispatch(here, "view_text", {"path": f"@box/{SWEEP}", "text": "From the laptop."})
    assert added["path"].startswith(f"@box/{SWEEP}/view/")
    assert "From the laptop." in newest_view(box).read_text()
    body = {"path": f"@box/{SWEEP}", "prefs": {}, "title": "Remote", "finding": "Saved here."}
    saved = dispatch(here, "save_view", body)
    assert saved["path"].startswith(f"@box/{SWEEP}/view/")
    assert yaml.safe_load(newest_view(box).read_text())["title"] == "Remote"
