"""The ``script`` operation: run an agent's Python in a child interpreter with ``bt`` loaded."""

import os
import signal
import subprocess
import sys
import time
from typing import Any

from beamtime.ops.context import Context

# -I keeps the root off sys.path, so `bt` comes from the installed package, not from the root.
BOOTSTRAP = (
    "import sys\n"
    "from beamtime import bt\n"
    "exec(compile(sys.stdin.read(), '<script>', 'exec'), {'__name__': '__main__', 'bt': bt})\n"
)
STDOUT_MAX = 20_000
STDERR_MAX = 4_000


def script(ctx: Context, p: Any) -> dict[str, Any]:
    """Run Python with ``bt`` preloaded in a child of this interpreter, in the project root.

    :param ctx: The operation context.
    :param p: The ``ScriptParams``.
    :return: ``{kind, stdout, stderr, exit, seconds, cut}``; a timeout gives ``exit: None``."""
    env = {**os.environ, **({"BEAMTIME_AUTHOR": p.author} if p.author else {})}
    started = time.monotonic()
    child = subprocess.Popen(
        [sys.executable, "-I", "-u", "-c", BOOTSTRAP],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=ctx.root,
        env=env,
        start_new_session=os.name == "posix",
    )
    timed_out = False
    try:
        out, err = child.communicate(p.code, timeout=p.timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill(child)
        out, err = child.communicate()
    cut = {}
    if len(out) > STDOUT_MAX:
        cut["stdout"] = len(out) - STDOUT_MAX
        out = out[:STDOUT_MAX]
    if len(err) > STDERR_MAX:
        cut["stderr"] = len(err) - STDERR_MAX
        err = err[-STDERR_MAX:]
    if timed_out:
        err += f"\nscript killed after {p.timeout:g} s; pass a larger `timeout` (at most 600).\n"
    return {
        "kind": "script",
        "stdout": out,
        "stderr": err,
        "exit": None if timed_out else child.returncode,
        "seconds": round(time.monotonic() - started, 3),
        "cut": cut,
    }


def kill(child: subprocess.Popen) -> None:
    """Kill a child and, where the platform has process groups, everything it started.

    :param child: The running script."""
    if os.name == "posix":
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        child.kill()
