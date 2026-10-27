import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.ops.context import Context
from beamtime.synth import generate


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


def env_for(project: Path) -> dict[str, str]:
    """The environment a CLI subprocess needs for the project.

    :param project: The project root.
    :return: The environment."""
    return dict(os.environ)
