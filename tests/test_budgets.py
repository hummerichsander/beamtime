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


def test_one_shot_runs_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``beamtime runs`` answers a sorted run table within 150 ms (best of 5)."""
    from beamtime.query import run
    from beamtime.synth import generate

    root = tmp_path / "proj"
    (root / ".git").mkdir(parents=True)
    generate(root / "beamtime", seed=0)
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    run({"runs": {}}, logdir=root / "beamtime", budget_s=60)
    script = Path(sys.executable).parent / ("beamtime.exe" if sys.platform == "win32" else "beamtime")
    args = [script, "runs", "--sort", "-metric.val/acc.last", "--limit", "5"]
    best = float("inf")
    for _ in range(5):
        t = time.perf_counter()
        subprocess.run(args, cwd=root, env=dict(os.environ), check=True, capture_output=True)
        best = min(best, time.perf_counter() - t)
    assert best < 0.150, f"beamtime runs took {best * 1000:.0f} ms"


STATIC = Path(__file__).parents[1] / "src" / "beamtime" / "serve" / "static"
SHELL_BUDGET = 120_000
KIT_BUDGET = 45_000


def imports(entry: str) -> tuple[set[str], set[str]]:
    """Follow a bundle's static imports through the chunks it shares with other entries.

    :param entry: The entry file, e.g. ``app.js``.
    :return: The files loaded with it (itself included), and the chunks it loads lazily."""
    import re

    static, lazy, todo = {entry}, set(), [entry]
    while todo:
        text = (STATIC / todo.pop()).read_text()
        for f in re.findall(r'(?:from|import)\s*"\./(?:\.\./)?((?:chunks/)?[\w.-]+\.js)"', text):
            f = f if f.startswith("chunks/") else f"chunks/{f}"
            if f not in static:
                static.add(f)
                todo.append(f)
        lazy |= {f if f.startswith("chunks/") else f"chunks/{f}"
                 for f in re.findall(r'import\("\./(?:\.\./)?((?:chunks/)?[\w.-]+\.js)"\)', text)}
    return static, lazy - static


def gzipped(files: set[str]) -> int:
    """Measure files compressed.

    :param files: Paths below the static folder.
    :return: The total size in bytes."""
    import gzip

    return sum(len(gzip.compress((STATIC / f).read_bytes(), 9)) for f in files)


def test_shell_bundle_budget() -> None:
    """The shell (entry, its static imports, CSS) stays within 120 KB compressed; charts,
    Markdown and KaTeX load lazily."""
    import re

    static, lazy = imports("app.js")
    size = gzipped(static | {"app.css"})
    assert size <= SHELL_BUDGET, f"shell is {size / 1000:.1f} KB compressed"
    for lib in ("uplot", "md"):
        assert any(lib in f for f in lazy) and not any(lib in f for f in static), lib
    md = next(f for f in lazy if "md" in f)
    assert re.search(r'import\("\./katex-[\w-]+\.js"\)', (STATIC / md).read_text())


def test_kit_bundle_budget() -> None:
    """A custom block's frame loads the kit within 45 KB compressed; D3 and uPlot only on use."""
    static, lazy = imports("kit.js")
    size = gzipped(static)
    assert size <= KIT_BUDGET, f"the kit is {size / 1000:.1f} KB compressed"
    for lib in ("d3", "uplot"):
        assert any(lib in f for f in lazy) and not any(lib in f for f in static), lib
