import dataclasses
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from beamtime.ops.context import Context
from beamtime.remote.client import Spec
from beamtime.remote.sources import Sources

COMMAND = f"{sys.executable} -m beamtime.cli"


@pytest.fixture
def box(project: Path, tmp_path: Path, fresh_logdir: Callable[[Path, int], None]) -> Path:
    """A second log dir, the remote ``box``.

    :param project: The local project.
    :param tmp_path: Pytest's temporary directory.
    :param fresh_logdir: Writes a generated log dir.
    :return: The remote's log dir."""
    logdir = tmp_path / "box" / "beamtime"
    fresh_logdir(logdir, 7)
    return logdir


@pytest.fixture
def box_spec(box: Path) -> Spec:
    """How to reach ``box``: over a plain command.

    :param box: The remote's log dir.
    :return: The spec."""
    return Spec(name="box", path=str(box), command=COMMAND, transport="command")


@pytest.fixture
def ctx(project: Path, box_spec: Spec) -> Iterator[Context]:
    """The project's context as a running serve holds it, with ``box`` as a source.

    :param project: The local project.
    :param box_spec: How to reach the remote.
    :return: The context."""
    sources = Sources([box_spec])
    yield dataclasses.replace(Context.make(caller="cli"), sources=sources)
    sources.close()
