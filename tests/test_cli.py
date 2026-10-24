import subprocess
import sys

from beamtime import __version__


def test_version() -> None:
    """The CLI reports the installed package version."""
    out = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert __version__ in out.stdout
