"""The remote layer end to end over real ssh: a Docker container with sshd and Beamtime installed.

Opt-in (building the image needs the network and a minute): ``BEAMTIME_DOCKER=1 pytest
tests/remote/test_docker.py``."""

import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.ops.context import Context, OpError
from beamtime.remote import answer as call
from beamtime.remote.client import Spec
from beamtime.synth import generate

SWEEP = "scaling/lr-sweep"
IMAGE = "beamtime-e2e"
ROOT = Path(__file__).parents[2]

if not os.environ.get("BEAMTIME_DOCKER"):
    pytest.skip("opt-in: BEAMTIME_DOCKER=1", allow_module_level=True)
if shutil.which("docker") is None or subprocess.run(["docker", "info"], capture_output=True).returncode:
    pytest.skip("no Docker daemon", allow_module_level=True)


def run(*args: str, **kw) -> subprocess.CompletedProcess:
    """Run a command, failing the test on errors.

    :param args: The command.
    :param kw: More subprocess arguments.
    :return: The finished process."""
    return subprocess.run(args, check=True, capture_output=True, text=True, **kw)


def free_port() -> int:
    """Find a free local port.

    :return: The port."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def container(tmp_path_factory: pytest.TempPathFactory):
    """A container serving a synthetic log dir over ssh, reachable as the host alias ``box``.

    An ``ssh`` wrapper on PATH adds the test's ssh config, so Beamtime runs plain ``ssh box``.

    :param tmp_path_factory: Pytest's temporary directories.
    :return: ``(name, logdir on this machine, environment for subprocesses)``."""
    tmp = tmp_path_factory.mktemp("docker")
    build = tmp / "build"
    build.mkdir()
    run("uv", "build", "--wheel", "-o", str(build), cwd=ROOT)
    shutil.copy(Path(__file__).parent / "docker" / "Dockerfile", build)
    run("docker", "build", "-q", "-t", IMAGE, str(build))
    logdir = tmp / "data" / "beamtime"
    generate(logdir, seed=11, now=datetime.now(timezone.utc))
    key = tmp / "key"
    run("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key))
    port = free_port()
    name = f"beamtime-e2e-{os.getpid()}"
    run("docker", "run", "-d", "--name", name, "-p", f"127.0.0.1:{port}:22",
        "-v", f"{tmp / 'data'}:/data", "-e", f"KEY={(tmp / 'key.pub').read_text().strip()}", IMAGE)  # fmt: skip
    config = tmp / "ssh_config"
    config.write_text(
        f"Host box\n  HostName 127.0.0.1\n  Port {port}\n  User root\n  IdentityFile {key}\n"
        "  StrictHostKeyChecking no\n  UserKnownHostsFile /dev/null\n  LogLevel ERROR\n"
    )
    bin_dir = tmp / "bin"
    bin_dir.mkdir()
    wrapper = bin_dir / "ssh"
    wrapper.write_text(f'#!/bin/sh\nexec {shutil.which("ssh")} -F {config} "$@"\n')
    wrapper.chmod(0o755)
    env = os.environ | {"PATH": f"{bin_dir}:{os.environ['PATH']}"}
    old_path, os.environ["PATH"] = os.environ["PATH"], env["PATH"]
    deadline = time.monotonic() + 30
    while subprocess.run(["ssh", "-o", "BatchMode=yes", "box", "true"], capture_output=True).returncode:
        assert time.monotonic() < deadline, "sshd in the container didn't come up"
        time.sleep(0.5)
    yield name, logdir, env
    os.environ["PATH"] = old_path
    subprocess.run(["docker", "rm", "-f", name], capture_output=True)


@pytest.fixture
def box(container, project: Path) -> Path:
    """The container's log dir as seen from here.

    :param container: The container.
    :param project: The local project.
    :return: The log dir."""
    return container[1]


@pytest.fixture
def box_spec(container) -> Spec:
    """The container as the source ``@box``, over ssh.

    :param container: The container.
    :return: The spec."""
    return Spec(name="box", host="box", path="/data/beamtime")


def test_over_ssh_reads_merge_and_a_verdict_lands_there(box: Path, ctx: Context) -> None:
    """Over real ssh: reads, merged listings, and a verdict written here stored on the remote."""
    runs = call("runs", {"from": f"@box/{SWEEP}", "select": ["run.group"]}, ctx)
    assert runs["rows"] and {r[1] for r in runs["rows"]} == {f"@box/{SWEEP}"}
    groups = [r[0] for r in call("groups", {"from": "."}, ctx)["rows"]]
    assert "scaling" in groups and f"@box/{SWEEP}" in groups
    shown = call("proposal show", {"group": f"@box/{SWEEP}"}, ctx)
    version = shown["version"]
    verdicts = {p["name"]: "confirmed" for p in shown["proposal"]["predictions"]}
    note = call("note add", {"group": f"@box/{SWEEP}", "type": "verdict", "proposal": version,
                             "verdict": verdicts, "overall": "confirmed",
                             "description": "Judged on the laptop."}, ctx)  # fmt: skip
    stored = box / note["path"].removeprefix("@box/")
    assert stored.is_file() and "Judged on the laptop." in stored.read_text()
    notes = call("notes", {"from": f"@box/{SWEEP}", "limit": 1}, ctx)["entries"]
    assert notes[0]["type"] == "verdict"


def test_a_view_drafted_here_is_checked_and_saved_there(box: Path, ctx: Context) -> None:
    """Over real ssh: a draft for a remote group stays here; validating and saving it run there,
    and its data file lands on the remote under its hash."""
    import yaml

    new = call("view new", {"group": f"@box/{SWEEP}", "name": "over-ssh"}, ctx)
    draft = Path(new["file"]).parent
    view = {"schema": 1, "title": "over ssh", "finding": "x",
            "body": [{"data_table": {"id": "fit", "file": "data/fit.csv"}}]}  # fmt: skip
    (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
    (draft / "data" / "fit.csv").write_text("x,y\n1,2\n")
    assert call("view validate", {"draft": "over-ssh", "render": False}, ctx)["ok"]
    saved = call("view save", {"draft": "over-ssh"}, ctx)
    assert (box / saved["path"].removeprefix("@box/")).is_file()
    assert list((box / SWEEP / "view" / "data").glob("*-fit.csv"))


def test_pull_survives_the_remote_going_away(container, box: Path, ctx: Context) -> None:
    """A pulled snapshot answers while the container is stopped; the connection comes back."""
    name = container[0]
    call("pull", {"target": f"box:{SWEEP}"}, ctx)
    run("docker", "stop", "-t", "1", name)
    try:
        answer = call("runs", {"from": f"@box/{SWEEP}"}, ctx)
        assert answer["meta"]["snapshot"]
        with pytest.raises(OpError, match="read-only"):
            call("note add", {"group": f"@box/{SWEEP}", "type": "idea", "description": "x"}, ctx)
    finally:
        run("docker", "start", name)
    deadline = time.monotonic() + 90
    while True:
        answer = call("runs", {"from": f"@box/{SWEEP}"}, ctx)
        if "snapshot" not in answer["meta"]:
            break
        assert time.monotonic() < deadline, "the connection didn't come back"
        time.sleep(2)


def test_serve_shows_both_sources(container, project: Path) -> None:
    """beamtime serve with the remote configured shows both trees and the remote's page."""
    pw = pytest.importorskip("playwright.sync_api")
    from beamtime.views import render

    _, _, env = container
    (project / "beamtime.yaml").write_text(
        "remotes:\n  box: {host: box, path: /data/beamtime}\n"
    )
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "beamtime.cli", "serve", "--port", str(port)],
        cwd=project, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )  # fmt: skip
    try:
        url = ""
        while "token=" not in url:
            url = server.stdout.readline()
            assert url or server.poll() is None, "serve ended"
        url = url.strip()
        base = url.split("/f/")[0]
        with pw.sync_playwright() as p:
            browser = render.launch(p)
            if browser is None:
                pytest.skip("no browser")
            page = browser.new_page()
            page.goto(url)
            # every source is a root row, local included (D1); the remote's answers come later.
            page.locator(".tree-item.source-root").nth(1).wait_for(timeout=60_000)
            roots = page.locator(".tree-item.source-root .tree-name").all_inner_texts()
            assert roots == ["local", "@box"]
            page.goto(f"{base}/f/@box/{SWEEP}")
            page.locator(".page h1", has_text="lr-sweep").wait_for(timeout=60_000)
            assert page.locator(".crumbs").inner_text().startswith("@box")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=30)


def test_custom_block_follows_live_data_over_ssh(container, project: Path) -> None:
    """A custom block on a running remote experiment keeps up, and fetches its code once."""
    pw = pytest.importorskip("playwright.sync_api")
    import yaml

    from beamtime.ops import call as local
    from beamtime.views import render
    from tests.serve.test_browser import LAST_STEP, last_step

    _, logdir, env = container
    root = logdir.parent
    writer = root / "writer.py"
    writer.write_text(
        "import time\nimport beamtime\n"
        "run = beamtime.init(dir='live', name='live', system_metrics=False)\n"
        "for step in range(400):\n"
        "    run.log({'live/loss': 1 / (1 + step)}, step=step)\n"
        "    time.sleep(0.2)\nrun.finish()\n"
    )
    clean = {k: v for k, v in env.items() if not k.startswith(("BEAMTIME_", "SLURM_"))}
    proc = subprocess.Popen([sys.executable, writer], cwd=root, env=clean | {"BEAMTIME_LOGDIR": str(logdir)})
    try:
        remote_ctx = Context.make(root=root, caller="cli")
        deadline = time.monotonic() + 30
        while not any((logdir / "live").glob("*/_metrics.jsonl")):
            assert time.monotonic() < deadline and proc.poll() is None, "the writer logged nothing"
            time.sleep(0.1)
        local("view new", {"group": "live", "name": "last"}, remote_ctx)
        draft = root / ".beamtime" / "drafts" / "last"
        view = {"schema": 1, "title": "live", "finding": "x", "body": [{"custom": {
            "id": "last", "code": "code/last.js",
            "queries": {"loss": {"series": {"y": ["live/loss"], "points": 50}}},
        }}]}  # fmt: skip
        (draft / "view.yaml").write_text(yaml.safe_dump(view, sort_keys=False))
        (draft / "code").mkdir()
        (draft / "code" / "last.js").write_text(LAST_STEP)
        local("view save", {"draft": "last"}, remote_ctx)

        (project / "beamtime.yaml").write_text("remotes:\n  box: {host: box, path: /data/beamtime}\n")
        port = free_port()
        server = subprocess.Popen(
            [sys.executable, "-m", "beamtime.cli", "serve", "--port", str(port)],
            cwd=project, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )  # fmt: skip
        try:
            url = ""
            while "token=" not in url:
                url = server.stdout.readline()
                assert url or server.poll() is None, "serve ended"
            base, token = url.strip().split("/f/")[0], url.strip().split("token=")[1]
            with pw.sync_playwright() as p:
                browser = render.launch(p)
                if browser is None:
                    pytest.skip("no browser")
                page = browser.new_page()
                asked: list[str] = []
                page.on("request", lambda r: r.url.endswith("/api/code") and asked.append(r.url))
                page.goto(f"{base}/f/@box/live?token={token}")
                page.wait_for_selector(".custom-frame iframe", timeout=60_000)
                deadline = time.monotonic() + 60
                while last_step(page) < 0:
                    assert time.monotonic() < deadline, "the block never showed a step"
                    page.wait_for_timeout(200)
                first = last_step(page)
                page.wait_for_timeout(15_000)
                assert last_step(page) > first + 10, "the block shows the step it started with"
                assert len(asked) == 1
                assert page.locator(".custom-error").count() == 0
                browser.close()
        finally:
            server.terminate()
            server.wait(timeout=30)
    finally:
        proc.kill()
