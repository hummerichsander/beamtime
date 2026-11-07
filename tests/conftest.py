import ctypes
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.format.constants import RUN
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


def clone(src: Path, dest: Path) -> None:
    """Copy a directory tree, on macOS as one copy-on-write clone.

    :param src: The tree to copy.
    :param dest: Where the copy goes; must not exist."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    # parallel workers contend on file creation; one clonefile call creates no files.
    if sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.clonefile(os.fsencode(src), os.fsencode(dest), 0) == 0:
            return
    shutil.copytree(src, dest)


@pytest.fixture(scope="session")
def fresh_logdir(tmp_path_factory: pytest.TempPathFactory) -> Callable[[Path, int], None]:
    """Generated log dirs judged against the current time, cloned from one generation per seed.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: ``fresh_logdir(dest, seed)`` writes the log dir of ``seed`` to ``dest``."""
    made: dict[int, tuple[float, Path]] = {}

    def copy(dest: Path, seed: int) -> None:
        if seed not in made:
            src = tmp_path_factory.mktemp(f"seed{seed}") / "beamtime"
            now = datetime.now(timezone.utc)
            generate(src, seed=seed, now=now)
            made[seed] = (now.timestamp(), src)
        stamp, src = made[seed]
        clone(src, dest)
        # heartbeats are _run.json mtimes; shift them so the copy reads as generated now.
        shift = time.time() - stamp
        for run in dest.rglob(RUN):
            st = run.stat()
            os.utime(run, (st.st_atime + shift, st.st_mtime + shift))

    return copy


@pytest.fixture
def project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fresh_logdir: Callable[[Path, int], None]
) -> Path:
    """A git project with a generated log dir, as the working directory.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :param fresh_logdir: Writes a generated log dir.
    :return: The project root."""
    root = tmp_path / "proj"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    fresh_logdir(root / "beamtime", 0)
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
