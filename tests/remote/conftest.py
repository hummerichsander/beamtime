import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime import remote
from beamtime.remote.client import Spec
from beamtime.remote.sources import Sources
from beamtime.synth import generate

COMMAND = f"{sys.executable} -m beamtime.cli"


@pytest.fixture
def box(project: Path, tmp_path: Path):
    """A second log dir served as the remote ``box`` over a plain command, as a running serve
    would hold it.

    :param project: The local project.
    :param tmp_path: Pytest's temporary directory.
    :return: The remote's log dir."""
    logdir = tmp_path / "box" / "beamtime"
    generate(logdir, seed=7, now=datetime.now(timezone.utc))
    spec = Spec(name="box", path=str(logdir), command=COMMAND, transport="command")
    remote.active = Sources([spec])
    yield logdir
    remote.active.close()
    remote.active = None
