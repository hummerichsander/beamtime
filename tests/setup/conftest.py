"""Fixtures of the setup tests: a fake home and a small project."""

from pathlib import Path

import pytest


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point HOME and the XDG directories at a folder of the test, so nothing real is touched.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :return: The fake home directory."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))
    return home


@pytest.fixture
def project_tree(tmp_path: Path) -> Path:
    """Build a uv project with a Lightning script, a SLURM script and an environment with Beamtime.

    :param tmp_path: The test's temporary directory.
    :return: The project root."""
    root = tmp_path / "project"
    (root / "jobs").mkdir(parents=True)
    (root / "train.py").write_text("import lightning as L\n")
    (root / "jobs" / "train.sbatch").write_text(
        "#!/bin/bash\n#SBATCH --nodes=1\nrsync -a out/ juwels:results/\n"
    )
    (root / "pyproject.toml").write_text("[project]\nname = 'demo'\n[tool.uv]\n")
    packages = root / ".venv" / "lib" / "python3.11" / "site-packages"
    for dist in ("beamtime-0.2.0", "starlette-0.40.0", "uvicorn-0.30.0"):
        (packages / f"{dist}.dist-info").mkdir(parents=True)
    return root
