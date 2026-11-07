from pathlib import Path

import msgspec
import pytest

from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import OPS, ServeParams
from beamtime.serve.app import subscribe_remotes
from beamtime.serve.live import Client, Hub
from beamtime.serve.server import forward_remote_change, serve
from tests.serve.conftest import PORT, TOKEN


def test_static_files_are_public_everything_else_needs_the_token(client) -> None:
    """Static files load without a token; pages and the API refuse without one."""
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/f/local").status_code == 401
    assert client.post("/api/runs", json={}).status_code == 401
    wrong = client.post("/api/runs", json={}, headers={"authorization": "Bearer nope"})
    assert wrong.status_code == 401 and wrong.json()["error"] == "missing or wrong token"
    assert client.get("/f/local?token=nope").status_code == 401


def test_token_in_the_url_sets_a_cookie(client) -> None:
    """Opening the printed URL signs the browser in and drops the token from the URL."""
    r = client.get("/f/local/scaling?token=test-token&sel=a", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/f/local/scaling?sel=a"
    cookie = r.headers["set-cookie"]
    assert f"beamtime-{PORT}={TOKEN}" in cookie and "HttpOnly" in cookie
    assert "samesite=strict" in cookie.lower()
    page = client.get("/f/local/scaling")
    assert page.status_code == 200 and "Beamtime" in page.text
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert client.post("/api/meta", json={}).status_code == 200


def test_api_answers_equal_the_operations(api, project: Path) -> None:
    """Each API method returns what its operation returns for the web UI."""
    ctx = Context.make(caller="view")
    for method, params in [
        ("runs", {"from": "scaling/lr-sweep", "select": ["run.name", "config.lr"]}),
        ("groups", {"from": "."}),
        ("check", {"group": "scaling/lr-sweep"}),
        ("series", {"from": "scaling/lr-sweep", "y": ["val/acc"], "points": 20}),
    ]:
        got = api(method, **params)
        assert got.status_code == 200, got.text
        want = call(method, params, ctx)
        want = msgspec.json.decode(msgspec.json.encode(want, enc_hook=str))
        strip = lambda a: {k: v for k, v in a.items() if k != "meta"}  # noqa: E731
        assert strip(got.json()) == strip(want), method


def test_view_answers_are_not_cut(api) -> None:
    """The web UI gets whole answers, not the 8k-token pages agents get."""
    r = api("series", **{"from": ".", "y": ["train/loss"], "points": 1000})
    assert r.status_code == 200
    assert "next" not in r.json()["meta"]
    assert len(r.content) > 32_000


def test_errors_and_user_only_operations(api) -> None:
    """Operation errors keep their code; user-only operations are not in the API, except those
    the web UI offers its user (deleting a note, its settings)."""
    r = api("runs", **{"from": "nowhere"})
    assert r.status_code == 404 and "no group" in r.json()["error"]
    r = api("runs", bogus=1)
    assert r.status_code == 400
    user_only = [op.tool for op in OPS if op.user_only]
    assert {"serve", "demo", "rm", "gc", "mv"} <= set(user_only)
    for method in set(user_only) - {"note_rm", "set"}:
        assert api(method).status_code == 404, method
    assert api("note_rm").status_code == 400 and api("set").status_code == 400


def test_view_of_groups_and_runs(api, roles: dict[str, str]) -> None:
    """The default view fits the group: proposal, curves, table; subgroups at the top."""
    sweep = api("view", path="scaling/lr-sweep").json()
    blocks = [c["block"] for c in sweep["view"]["children"]]
    assert blocks[0] == "section" and {"table", "notes"} <= set(blocks) and "proposal" not in blocks
    walk = lambda n: [n["block"], *[b for c in n.get("children", []) for b in walk(c)]]  # noqa: E731
    assert "stat" not in walk(sweep["view"])
    # the proposal's predicted metric is pinned: an open Main section, the rest in one.
    main, other = (c for c in sweep["view"]["children"] if c["block"] == "section")
    assert main["props"]["title"] == "Main (1)" and main["props"]["open"] is True
    curves = [g for s in (main, other) for g in s["children"]]
    assert all(c["data"]["main"]["method"] == "series" for g in curves for c in g["children"])
    assert [c["props"]["y"] for g in curves for c in g["children"]] == ["val/acc", "train/loss", "lr"]
    table = next(c for c in sweep["view"]["children"] if c["block"] == "table")
    assert table["props"]["sparkline"] == "val/acc" and "spark" in table["data"]
    best = api("summary", path="scaling/lr-sweep").json()["summary"]
    assert best["metric"] == "val/acc" and best["config"]["lr"] == 3e-4
    assert sweep["pins"] == [{"y": "val/acc", "higher": True}]
    unpinned = api("view", path="scaling/lr-sweep", metrics=[]).json()
    assert unpinned["pins"] == [] and unpinned["view"]["children"][0]["block"] == "grid"
    assert api("summary", path="scaling/lr-sweep", metrics=[]).json()["summary"] is None

    top = api("view", path="").json()
    assert top["path"] == "." and top["view"]["children"][0]["block"] == "groups"
    assert api("summary", path=".").json()["summary"] is None
    recent = next(c for c in top["view"]["children"] if c["block"] == "table")
    assert recent["props"]["columns"] == ["run.name", "run.status", "run.group", "run.created_at"]

    failed = roles["diverging"]
    run = api("view", path=failed).json()
    assert run["run"] == failed and run["path"].endswith(failed)
    output = next(c for c in run["view"]["children"] if c["block"] == "output")
    assert output["props"]["open"] is True

    assert api("view", path="nowhere").status_code == 404
    assert api("view", path="scaling/lr-sweep/proposal").status_code == 404
    assert api("view", path="../etc").status_code == 404


def test_run_files_stay_inside_the_run(client, api, project: Path) -> None:
    """Logged images are served by run id; paths leaving the run are refused."""
    entries = []
    for folder in ("scaling/lr-sweep", "tokenizer/bpe-vs-unigram"):
        r = api("data", **{"from": folder, "key": "samples", "step": "last"})
        if r.status_code == 200:
            entries += [e for e in r.json()["entries"] if e.get("kind") == "image"]
    assert entries
    e = entries[0]
    auth = {"authorization": f"Bearer {TOKEN}"}
    img = client.get(f"/api/file/{e['run']}/{e['path']}", headers=auth)
    assert img.status_code == 200 and img.content.startswith(b"\x89PNG")
    bad = client.get(f"/api/file/{e['run']}/..%2F..%2F_synth.json", headers=auth)
    assert bad.status_code == 404
    assert client.get("/api/file/not-a-run/x.png", headers=auth).status_code == 404


def test_meta_has_the_theme_pair(api) -> None:
    """The shell gets the project name and both theme variants."""
    meta = api("meta").json()
    assert meta["project"] == "proj"
    assert meta["theme"]["light"]["type"] == "light"
    assert meta["theme"]["dark"]["colors"]["surface"] == "#252523"
    assert "theory" in meta["note_types"] and "verdict" in meta["note_types"]


def test_a_set_setting_reaches_the_next_meta_with_remotes(project: Path) -> None:
    """With remotes each UI call runs on a copy of the context; a new setting must still show.

    :param project: The project root."""
    import dataclasses
    from types import SimpleNamespace

    from beamtime.serve.api import dispatch

    ctx = Context.make(root=project, caller="view")
    ctx = dataclasses.replace(ctx, sources=SimpleNamespace(clients={}))
    dispatch(ctx, "set", {"key": "theme_mode", "value": "dark"})
    assert dispatch(ctx, "meta", {})["settings"]["theme_mode"] == "dark"
    dispatch(ctx, "set", {"key": "theme_mode", "value": "system"})
    assert dispatch(ctx, "meta", {})["settings"]["theme_mode"] == "system"


def test_serve_refuses_a_second_daemon(project: Path) -> None:
    """A second serve for the same root points at the running one."""
    from beamtime.index.daemon import Daemon

    ctx = Context.make(caller="cli")
    daemon = Daemon(logdir=ctx.logdir, port=8123)
    assert daemon.start()
    try:
        with pytest.raises(OpError, match="already runs .*localhost:8123"):
            serve(ctx, ServeParams(port=0))
    finally:
        daemon.stop()


def test_save_view_from_the_ui(api, project: Path) -> None:
    """Save as view writes a version with the viewer's settings; the page then shows it."""
    prefs = {"view": {"by": None}, "charts": {"line-val-acc": {"smooth": 0.4}}, "added": []}
    r = api("save_view", path="scaling/lr-sweep", prefs=prefs, title="Sweep", finding="lr 3e-4.")
    assert r.status_code == 200, r.text
    shown = api("view", path="scaling/lr-sweep").json()
    assert (shown["source"], shown["title"], shown["finding"]) == ("view", "Sweep", "lr 3e-4.")
    history = api("view_history", group="scaling/lr-sweep").json()["entries"]
    assert history[0]["message"] == "saved from the web UI"
    assert api("save_view", path="nope", prefs={}).status_code == 404


@pytest.mark.parametrize(
    "figure",
    [
        {"kind": "line", "xlabel": "step", "ylabel": "loss", "yscale": "log", "series": [
            {"label": "a", "color": "#2a78d6", "x": [0, 1, 2], "y": [1.0, 0.5, None], "lo": [0.9, 0.4, None], "hi": [1.1, 0.6, None]},
            {"label": "b", "color": "#eb6834", "x": [0, 1, 2], "y": [0.8, 0.3, 0.2]}]},
        {"kind": "scatter", "xscale": "log", "yscale": "symlog", "series": [
            {"color": "#2a78d6", "x": [0.001, 0.01], "y": [0.9, -0.2], "err": [0.01, None]}],
         "fit": {"x": [0.001, 0.01], "y": [0.9, 0.8]}},
        {"kind": "bar", "categories": ["sgd", "adam"], "groups": [
            {"label": None, "colors": ["#2a78d6", "#eb6834"], "value": [0.5, 0.7], "lo": [0.4, 0.6], "hi": [0.6, 0.8]}]},
        {"kind": "histogram", "series": [{"label": "r", "color": "#2a78d6", "start": [0, 1], "end": [1, 2], "count": [3, 4]}]},
    ],
)  # fmt: skip
def test_figures_are_pdfs(api, figure: dict) -> None:
    """Every chart kind is drawn as a vector PDF."""
    pytest.importorskip("scienceplots")
    r = api("figure", **figure)  # drawn in the project's figure_style, [science, nature]
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf" and r.content.startswith(b"%PDF")
    assert api("figure", kind="pie").status_code == 400


def test_meta_lists_settings_and_styles(api) -> None:
    """The settings page gets the project's settings, themes and figure styles."""
    pytest.importorskip("scienceplots")
    m = api("meta").json()
    assert m["settings"]["figure_style"] == ["science", "nature"]
    assert "beamtime" in m["themes"] and "science" in m["figure_styles"]
    assert api("set", key="figure_style", value=["science", "ieee"]).status_code == 200
    assert api("meta").json()["settings"]["figure_style"] == ["science", "ieee"]
    assert api("figure", kind="line", series=[{"x": [0, 1], "y": [1, 2]}]).status_code == 200


def test_the_custom_block_frame_has_its_own_policy(client, static: Path) -> None:
    """The frame may run blob code and be framed by the page; static files allow CORS."""
    (static / "kit").mkdir()
    (static / "kit" / "frame.html").write_text("<!doctype html>")
    frame = client.get("/static/kit/frame.html")
    csp = frame.headers["content-security-policy"]
    assert "script-src 'self' blob:" in csp and "connect-src 'none'" in csp
    assert "frame-ancestors 'self'" in csp
    assert frame.headers["access-control-allow-origin"] == "*"
    page = client.get("/static/app.js")
    assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
    assert "access-control-allow-origin" not in client.post("/api/runs", json={}).headers


def test_code_is_read_with_the_token(api, client) -> None:
    """Custom-block code comes through the API, never as a public file."""
    from beamtime.ops import call

    call("view new", {"group": "scaling/lr-sweep", "from": "custom", "name": "pm"}, Context.make())
    ref = {"view": "scaling/lr-sweep", "path": "code/phase-map.js", "draft": "pm"}
    assert "export default" in api("code", **ref).json()["code"]
    assert client.post("/api/code", json=ref).status_code == 401
    assert api("code", **(ref | {"path": "view.yaml"})).status_code == 404


def test_project_style_files(api, project: Path) -> None:
    """A project's .mplstyle file is offered, can be set, and draws the PDF; a missing one can't."""
    pytest.importorskip("scienceplots")
    (project / "styles").mkdir()
    (project / "styles" / "paper.mplstyle").write_text("lines.linewidth: 3\n")
    assert "styles/paper.mplstyle" in api("meta").json()["figure_styles"]
    ok = api("set", key="figure_style", value=["science", "styles/paper.mplstyle"])
    assert ok.status_code == 200, ok.json()
    pdf = api("figure", kind="line", series=[{"x": [0, 1], "y": [1, 2]}])
    assert pdf.status_code == 200, pdf.text
    assert pdf.content.startswith(b"%PDF")
    missing = api("set", key="figure_style", value=["styles/none.mplstyle"])
    assert missing.status_code == 400 and "no style file" in missing.json()["error"]


def test_forward_remote_change_prefixes_paths_and_kinds() -> None:
    """A remote's changed event becomes @name-prefixed paths with their kinds, for the hub."""
    seen = []
    hub = type("FakeHub", (), {"changed": lambda self, d: seen.append(d)})()
    forward_remote_change(hub, "box", {"changed": {".": ["authored"], "g/r": ["metrics"]}})
    assert seen == [{"@box": {"authored"}, "@box/g/r": {"metrics"}}]


def test_subscribe_remotes_reads_the_scope_out_of_the_scope_kinds_pair() -> None:
    """Pages watching a remote's scope (with its kinds) tell that source to subscribe to it."""
    hub = Hub()
    hub.clients["p"] = Client(watched={"q": ("@box/g", {"metrics"}), "r": (".", {"authored"})})

    class FakeSpec:
        scope = "."

    class FakeClient:
        state = "connected"
        spec = FakeSpec()

        def __init__(self) -> None:
            self.subscribed: list[str] | None = None

        def subscribe(self, paths: list[str]) -> None:
            self.subscribed = paths

    sources = type("FakeSources", (), {"clients": {"box": FakeClient()}})()
    subscribe_remotes(hub, sources)
    assert sources.clients["box"].subscribed == [".", "g"]
