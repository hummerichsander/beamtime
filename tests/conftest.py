from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.synth import Manifest, generate

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
