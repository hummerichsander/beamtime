import os
import re
import subprocess
import sys
import textwrap
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("starlette")
pytest.importorskip("httpx")

from starlette.testclient import TestClient

from beamtime.ops.context import Context
from beamtime.serve.app import STATIC, build
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


@pytest.fixture
def server(project: Path) -> Iterator[str]:
    """``beamtime serve`` on a free port for the generated project.

    :param project: The project root.
    :return: The URL with the token."""
    if not (STATIC / "app.js").is_file():
        pytest.skip("the frontend is not built")
    script = Path(sys.executable).parent / "beamtime"
    proc = subprocess.Popen(
        [script, "serve", "--port", "0"], cwd=project, stderr=subprocess.PIPE, text=True
    )
    url = None
    deadline = time.time() + 30
    while time.time() < deadline and url is None:
        line = proc.stderr.readline()
        if m := re.search(r"(http://localhost:\d+)/f/local\?token=(\S+)", line):
            url = m.group(0)
    if url is None:
        proc.kill()
        pytest.fail("serve printed no URL")
    yield url
    proc.terminate()
    proc.wait(10)


@pytest.fixture
def page() -> Iterator[Any]:
    """A headless browser page; skipped where no browser can run.

    :return: The Playwright page."""
    sync_api = pytest.importorskip("playwright.sync_api")
    from beamtime.views.render import launch

    with sync_api.sync_playwright() as p:
        if (browser := launch(p)) is None:
            pytest.skip("no Chromium available (playwright install chromium)")
        yield browser.new_page(viewport={"width": 1280, "height": 900})
        browser.close()


WRITER = """
import sys
import time
from pathlib import Path

import beamtime

stop = Path(sys.argv[1])
run = beamtime.init(dir="live", name="live", system_metrics=False)
step = 0
while not stop.exists():
    run.log({"live/loss": 1 / (1 + step), "live/step_time": 0.2}, step=step)
    step += 1
    time.sleep(0.2)
run.finish()
"""


@dataclass
class Live:
    """A running experiment, ``serve`` and a browser page on the same project."""

    page: Any
    base: str
    token: str
    project: Path
    writer: subprocess.Popen
    stop_file: Path

    def goto(self, path: str) -> None:
        """Open a page of the app.

        :param path: The path, e.g. ``/f/local/live``."""
        self.page.goto(f"{self.base}{path}?token={self.token}")

    def stop_writer(self) -> None:
        """Let the experiment finish and wait for it."""
        self.stop_file.touch()
        self.writer.wait(30)


@pytest.fixture
def live_page(project: Path, tmp_path: Path, server: str, page: Any) -> Iterator[Live]:
    """A page on a project where a script logs a step every 0.2 s through the SDK.

    Wait with ``page.wait_for_timeout``, never ``time.sleep``: that blocks Playwright's events.

    :param project: The project root.
    :param tmp_path: Pytest's temporary directory.
    :param server: The URL of ``serve`` for the project.
    :param page: The browser page.
    :return: The handle; the writer is stopped at teardown."""
    script, stop = tmp_path / "writer.py", tmp_path / "stop"
    script.write_text(textwrap.dedent(WRITER))
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BEAMTIME_", "SLURM_"))}
    env |= {"BEAMTIME_LOGDIR": str(project / "beamtime"), "PYTHONUNBUFFERED": "1"}
    writer = subprocess.Popen([sys.executable, script, stop], cwd=project, env=env)
    live = Live(
        page=page,
        base=server.split("/f/local")[0],
        token=server.split("token=")[1],
        project=project,
        writer=writer,
        stop_file=stop,
    )
    deadline = time.time() + 30
    while not any((project / "beamtime" / "live").glob("*/_metrics.jsonl")):
        assert time.time() < deadline and writer.poll() is None, "the writer logged nothing"
        time.sleep(0.1)
    yield live
    stop.touch()
    try:
        writer.wait(30)
    except subprocess.TimeoutExpired:
        writer.kill()
