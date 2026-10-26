import os
import subprocess
import sys
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from beamtime.format.tree import iter_runs

Script = Callable[..., subprocess.CompletedProcess]


@pytest.fixture
def logdir(tmp_path: Path) -> Path:
    """The log dir scripts write to through ``BEAMTIME_LOGDIR``.

    :param tmp_path: Pytest's temporary directory.
    :return: The log dir."""
    return tmp_path / "logs"


@pytest.fixture
def script(tmp_path: Path, logdir: Path) -> Script:
    """Run a training script in a subprocess, so hooks and fd capture stay out of pytest.

    :param tmp_path: Pytest's temporary directory.
    :param logdir: The log dir.
    :return: A function taking the script's code and returning the finished process."""

    def run(
        code: str,
        *,
        env: dict[str, str] | None = None,
        timeout: float = 60,
        name: str = "train.py",
    ) -> subprocess.CompletedProcess:
        path = tmp_path / name
        path.write_text(textwrap.dedent(code))
        environ = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith(("BEAMTIME_", "SLURM_", "RANK", "LOCAL_RANK", "NODE_RANK"))
        }
        environ |= {"BEAMTIME_LOGDIR": str(logdir), "PYTHONUNBUFFERED": "1"} | (env or {})
        return subprocess.run(
            [sys.executable, str(path)],
            cwd=tmp_path,
            env=environ,
            capture_output=True,
            timeout=timeout,
        )

    return run


def only_run(logdir: Path) -> Path:
    """Find the single run below a log dir.

    :param logdir: The log dir.
    :return: The run directory."""
    runs = list(iter_runs(logdir))
    assert len(runs) == 1, runs
    return runs[0]
