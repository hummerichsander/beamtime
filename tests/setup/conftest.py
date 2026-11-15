"""Fixtures of the setup tests: a fake home and a small project."""

from pathlib import Path

import pytest

from beamtime import __version__


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point HOME, the XDG directories and the index cache at a folder of the test, so nothing real is touched.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :return: The fake home directory."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(home / ".cache"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(home / ".cache" / "beamtime"))
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
    for dist in (f"beamtime-{__version__}", "starlette-0.40.0", "uvicorn-0.30.0"):
        (packages / f"{dist}.dist-info").mkdir(parents=True)
    return root


@pytest.fixture
def tools(tmp_path: Path):
    """Make a folder of fake programs and give back a function that makes a ``PATH`` from it.

    :param tmp_path: The test's temporary directory.
    :return: A function taking program names and returning the ``PATH`` that finds exactly those."""

    def make(*names: str) -> str:
        """Create the programs.

        :param names: The program names.
        :return: The ``PATH`` value."""
        folder = tmp_path / "bin"
        folder.mkdir(exist_ok=True)
        for name in names:
            (folder / name).write_text("#!/bin/sh\n")
            (folder / name).chmod(0o755)
        return str(folder)

    return make
