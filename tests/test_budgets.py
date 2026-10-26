import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

HEAVY = {"numpy", "pandas", "starlette", "uvicorn", "mcp", "playwright", "pyarrow"}


@pytest.mark.parametrize(
    "module", ["beamtime", "beamtime.cli", "beamtime.format.run", "beamtime.query"]
)
def test_no_heavy_imports(module: str) -> None:
    """Importing the package, the CLI or the readers pulls in no heavy dependency."""
    code = f"import sys, json, {module}; print(json.dumps(sorted(sys.modules)))"
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    loaded = {m.split(".")[0] for m in json.loads(out.stdout)}
    assert not loaded & HEAVY


@pytest.mark.skipif(sys.version_info < (3, 11), reason="the CLI needs Python 3.11")
def test_cli_startup_budget() -> None:
    """The installed ``beamtime`` command answers within 150 ms (best of 5)."""
    script = Path(sys.executable).parent / ("beamtime.exe" if sys.platform == "win32" else "beamtime")
    best = float("inf")
    for _ in range(5):
        t = time.perf_counter()
        subprocess.run([script, "--help"], capture_output=True, check=True)
        best = min(best, time.perf_counter() - t)
    assert best < 0.150, f"beamtime --help took {best * 1000:.0f} ms"


def test_one_shot_query_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A fresh process imports the query layer and answers a run table within 150 ms."""
    from beamtime.query import run
    from beamtime.synth import generate

    logdir = tmp_path / "beamtime"
    generate(logdir, seed=0)
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    env = dict(os.environ)
    run({"runs": {}}, logdir=logdir, budget_s=60)
    code = (
        "from pathlib import Path; from beamtime.query import run; "
        f"run({{'runs': {{'sort': ['-metric.val/acc.last'], 'limit': 5}}}}, logdir=Path({str(logdir)!r}))"
    )
    best = float("inf")
    for _ in range(5):
        t = time.perf_counter()
        subprocess.run([sys.executable, "-c", code], env=env, check=True)
        best = min(best, time.perf_counter() - t)
    assert best < 0.150, f"one-shot query took {best * 1000:.0f} ms"
