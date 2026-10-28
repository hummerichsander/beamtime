import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.ops.context import Context
from beamtime.synth import Manifest, generate

# the index cache of every test lives in a temporary directory, never in ~/.cache.
os.environ["BEAMTIME_CACHE"] = tempfile.mkdtemp(prefix="beamtime-cache-")

GOLDEN = Path(__file__).parent / "golden" / "schema1" / "beamtime"
NOW = datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def golden() -> Path:
    """The checked-in schema-1 log dir.

    :return: Its path; tests must not write into it."""
    return GOLDEN


@pytest.fixture(scope="session")
def synth(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Manifest]:
    """A synthetic log dir at scale s with seed 0, shared by the session.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The log dir and its manifest."""
    logdir = tmp_path_factory.mktemp("synth") / "beamtime"
    return logdir, generate(logdir, seed=0, now=NOW)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A git project with a generated log dir, as the working directory.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: The project root."""
    root = tmp_path / "proj"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    generate(root / "beamtime", seed=0, now=datetime.now(timezone.utc))
    monkeypatch.chdir(root)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    return root


@pytest.fixture
def ctx(project: Path) -> Context:
    """The operation context of the project.

    :param project: The project root.
    :return: The context."""
    return Context.make(caller="cli")


@pytest.fixture
def roles(project: Path) -> dict[str, str]:
    """The generator's runs by role.

    :param project: The project root.
    :return: Role to run id."""
    return json.loads((project / "beamtime" / "_synth.json").read_text())["roles"]
