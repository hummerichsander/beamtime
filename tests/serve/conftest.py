from pathlib import Path

import pytest

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from starlette.testclient import TestClient

from beamtime.ops.context import Context
from beamtime.serve.app import build
from beamtime.serve.auth import TokenGuard
from beamtime.serve.live import Hub

TOKEN = "test-token"
PORT = 9999


@pytest.fixture
def static(tmp_path: Path) -> Path:
    """A stand-in for the built frontend.

    :param tmp_path: Pytest's temporary directory.
    :return: The static directory."""
    d = tmp_path / "static"
    d.mkdir()
    (d / "index.html").write_text("<!doctype html><title>Beamtime</title>")
    (d / "app.js").write_text("console.log(1)")
    return d


@pytest.fixture
def hub() -> Hub:
    """A live-update hub.

    :return: The hub."""
    return Hub()


@pytest.fixture
def client(project: Path, static: Path, hub: Hub):
    """A test client of the guarded app for the generated project.

    :param project: The project root.
    :param static: The stand-in frontend.
    :param hub: The hub.
    :return: The client, not yet signed in."""
    ctx = Context.make(caller="view")
    app = TokenGuard(build(ctx=ctx, hub=hub, static=static), token=TOKEN, port=PORT)
    with TestClient(app, base_url="http://localhost") as c:
        yield c


@pytest.fixture
def api(client):
    """A function posting to the API with the token.

    :param client: The test client.
    :return: ``api(method, **params) -> response``."""

    def post(method: str, **params):
        return client.post(
            f"/api/{method}", json=params, headers={"authorization": f"Bearer {TOKEN}"}
        )

    return post
