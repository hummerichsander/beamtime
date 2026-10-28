from pathlib import Path

import msgspec
import pytest

from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import OPS, ServeParams
from beamtime.serve.server import serve
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
        ("folders", {"from": "."}),
        ("check", {"folder": "scaling/lr-sweep"}),
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
    """Operation errors keep their code; user-only operations are not in the API."""
    r = api("runs", **{"from": "nowhere"})
    assert r.status_code == 404 and "no folder" in r.json()["error"]
    r = api("runs", bogus=1)
    assert r.status_code == 400
    user_only = [op.tool for op in OPS if op.user_only]
    assert {"serve", "demo", "rm", "gc", "mv"} <= set(user_only)
    for method in user_only:
        assert api(method).status_code == 404, method


def test_view_of_folders_and_runs(api, roles: dict[str, str]) -> None:
    """The default view fits the folder: proposal, curves, table; subfolders at the top."""
    sweep = api("view", path="scaling/lr-sweep").json()
    blocks = [c["block"] for c in sweep["view"]["children"]]
    assert blocks[0] == "proposal" and {"row", "grid", "table"} <= set(blocks)
    curves = next(c for c in sweep["view"]["children"] if c["block"] == "grid")
    assert all(c["data"]["main"]["method"] == "series" for c in curves["children"])
    assert curves["children"][0]["props"]["y"] == "val/acc"

    top = api("view", path="").json()
    assert top["path"] == "." and top["view"]["children"][0]["block"] == "folders"

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
    assert meta["theme"]["dark"]["colors"]["sidebar.bg"] == "#151b23"


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
