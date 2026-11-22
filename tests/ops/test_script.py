import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from beamtime.cli.format import render
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.serve.api import dispatch_here


def run(ctx: Context, code: str, **params: object) -> dict:
    """Run code through the ``script`` operation.

    :param ctx: The operation context.
    :param code: The Python to run.
    :param params: More parameters.
    :return: The answer."""
    return call("script", {"code": code, **params}, ctx)


def alive(pid: int) -> bool:
    """Tell whether a process still runs.

    :param pid: Its id.
    :return: Whether it exists."""
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def test_script_preloads_bt(ctx: Context) -> None:
    """``bt`` needs no import line and answers a plain dict."""
    answer = run(ctx, "print(bt.status()['kind'])")
    assert answer["kind"] == "script"
    assert answer["stdout"] == "status\n" and answer["stderr"] == ""
    assert answer["exit"] == 0 and answer["cut"] == {}
    assert render(answer) == "status"


def test_script_runs_in_the_root(ctx: Context) -> None:
    """The working directory is the project root."""
    assert run(ctx, "import os; print(os.getcwd())")["stdout"].strip() == str(ctx.root.resolve())


def test_script_author_reaches_the_child(ctx: Context) -> None:
    """``author`` is the default author of writes made through ``bt``."""
    code = "import os; print(os.environ.get('BEAMTIME_AUTHOR'))"
    assert run(ctx, code, author="claude-x")["stdout"] == "claude-x\n"


def test_script_traceback(ctx: Context) -> None:
    """An error is an answer: a nonzero exit and the tail of stderr naming the script's line."""
    answer = run(ctx, "x = 1\nraise ValueError('boom')")
    assert answer["exit"] == 1 and "<script>" in answer["stderr"] and "boom" in answer["stderr"]
    assert answer["stderr"].endswith("ValueError: boom\n")
    assert render(answer).splitlines()[-1].startswith("script: exit 1")


def test_script_timeout_kills(ctx: Context) -> None:
    """A loop past the timeout is killed with what it started, and the answer says so."""
    if os.name != "posix":
        pytest.skip("process groups are POSIX")
    code = (
        "import subprocess, sys\n"
        "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "print(p.pid)\n"
        "while True:\n    pass\n"
    )
    answer = run(ctx, code, timeout=1)
    grandchild = int(answer["stdout"].split()[0])
    try:
        assert answer["exit"] is None and 1 <= answer["seconds"] < 10
        assert "killed after 1 s" in answer["stderr"] and "timeout" in answer["stderr"]
        deadline = time.monotonic() + 5
        while alive(grandchild) and time.monotonic() < deadline:
            time.sleep(0.05)
        assert not alive(grandchild)
        assert "timed out" in render(answer)
    finally:
        if alive(grandchild):
            os.kill(grandchild, 9)


def test_script_cuts_output(ctx: Context) -> None:
    """Stdout keeps its head, stderr its tail, and the answer says how much went."""
    code = "import sys\nprint('a' * 20_100, end='')\nprint('b' * 3_000 + 'c' * 1_500, file=sys.stderr, end='')"
    answer = run(ctx, code)
    assert answer["stdout"] == "a" * 20_000 and answer["cut"]["stdout"] == 100
    assert answer["stderr"] == "b" * 2_500 + "c" * 1_500 and answer["cut"]["stderr"] == 500
    assert "stdout cut by 100 characters" in render(answer)


def test_script_ignores_root_modules(ctx: Context) -> None:
    """``-I`` keeps the root off ``sys.path``: a ``json.py`` there is not imported."""
    (ctx.root / "json.py").write_text("raise RuntimeError('planted')", encoding="utf-8")
    answer = run(ctx, "import json; print(json.dumps([1]))")
    assert answer["stdout"] == "[1]\n" and answer["exit"] == 0


def test_script_timeout_limit(ctx: Context) -> None:
    """A timeout above 600 seconds is refused."""
    with pytest.raises(OpError):
        run(ctx, "pass", timeout=601)


def test_script_not_an_api_method(ctx: Context) -> None:
    """Neither the web UI, a view's blocks nor a remote can run code through serve's API."""
    with pytest.raises(OpError, match="no API method 'script'"):
        dispatch_here(ctx, "script", {"code": "print(1)"})


def test_script_reads_stdin_on_the_cli(project: Path) -> None:
    """``echo code | beamtime script`` prints the script's output."""
    done = subprocess.run(
        [sys.executable, "-m", "beamtime.cli", "script"],
        input='print(bt.status()["kind"])',
        cwd=project,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert done.returncode == 0 and done.stdout == "status\n", done.stderr
