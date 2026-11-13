import subprocess
import sys

import pytest

from beamtime import __version__


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_version() -> None:
    """The CLI reports the installed package version."""
    out = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert __version__ in out.stdout


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_version_without_serve_extra() -> None:
    """The version gains a note when the serve extra's ``mcp`` package is missing."""
    code = (
        "import sys; sys.modules['mcp'] = None; sys.argv = ['beamtime', '--version'];"
        "from beamtime.cli import main; main()"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert f"beamtime {__version__} (no serve extra)" in out.stdout


@pytest.mark.skipif(sys.version_info >= (3, 11), reason="only on Python 3.10")
def test_cli_refuses_python_310() -> None:
    """On Python 3.10 the CLI explains that it needs 3.11 and the SDK still works."""
    out = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert out.returncode == 1 and "needs Python 3.11" in out.stderr
