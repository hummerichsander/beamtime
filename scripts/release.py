"""Check a release and build it: python scripts/release.py.

Checks a clean tree, the full checks, a fresh web bundle and docs reference, builds the wheel and
the sdist, checks what the wheel holds, installs it into a fresh environment and tries it there.
It publishes nothing; it prints the command that does. The release workflow runs the same wheel
check and smoke test (--wheel-only, --smoke-only)."""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import NoReturn

import tomllib

ROOT = Path(__file__).parents[1]
# files a wheel must hold: the frontend (and its export bundle), the agent guide, the themes and
# the renderer's layout checks.
REQUIRED = (
    "beamtime/serve/static/index.html",
    "beamtime/serve/static/app.js",
    "beamtime/serve/static/kit.js",
    "beamtime/serve/static/katex.css",
    "beamtime/serve/static/export/main.js",
    "beamtime/serve/static/export/kit.js",
    "beamtime/guide/parts/instructions.md",
    "beamtime/views/themes/beamtime-light.json",
    "beamtime/views/themes/beamtime-dark.json",
    "beamtime/views/checks.js",
)
SMOKE = """
import beamtime
run = beamtime.init(dir="smoke", config={"lr": 3e-4}, proposal="The loss goes down.")
for step in range(20):
    run.log({"train/loss": 1.0 / (step + 1)})
run.finish()
"""


def main() -> None:
    """Run the checks in order; stop at the first that fails."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--wheel-only", type=Path, help="only check this wheel's contents")
    parser.add_argument("--smoke-only", type=Path, help="only install this wheel and try it")
    parser.add_argument("--notes", action="store_true", help="print this version's changelog")
    args = parser.parse_args()
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    if args.notes:
        print(notes(version))
        return
    if args.wheel_only:
        check_wheel(args.wheel_only, version)
        return
    if args.smoke_only:
        smoke(args.smoke_only, version)
        return
    step("a clean tree")
    if dirty := run("git", "status", "--porcelain", "--untracked-files=no", capture=True).strip():
        fail(f"uncommitted changes:\n{dirty}")
    step("the changelog")
    notes(version)
    step("ruff and the tests")
    run("uv", "run", "ruff", "check", ".")
    run("uv", "run", "ruff", "format", "--check", ".")
    run("uv", "run", "pytest", "-q")
    step("a fresh web bundle")
    run("npm", "ci", cwd=ROOT / "web")
    run("npm", "test", cwd=ROOT / "web")
    run("npm", "run", "build", cwd=ROOT / "web")
    run("npm", "run", "docs", cwd=ROOT / "web")
    if stale := run(
        "git", "status", "--porcelain", "--", "src/beamtime/serve/static", capture=True
    ):
        fail(f"the committed bundle is stale; commit the rebuilt one:\n{stale}")
    step("build")
    shutil.rmtree(ROOT / "dist", ignore_errors=True)
    run("uv", "build")
    wheel = next((ROOT / "dist").glob(f"beamtime-{version}-*.whl"))
    check_wheel(wheel, version)
    smoke(wheel, version)
    print(f"\nbeamtime {version} is ready. To publish (after the license check), run:\n")
    print("  uv publish dist/*")
    print(
        f"  git tag v{version} && git push --tags   # or push the tag to run the release workflow"
    )


def check_wheel(wheel: Path, version: str) -> None:
    """Check that a wheel holds the frontend, the guide, the themes and the version.

    :param wheel: The wheel.
    :param version: The expected version."""
    step(f"the wheel's contents ({wheel.name})")
    names = set(zipfile.ZipFile(wheel).namelist())
    if missing := [f for f in REQUIRED if f not in names]:
        fail(f"the wheel lacks {', '.join(missing)}")
    if f"beamtime-{version}.dist-info/METADATA" not in names:
        fail(f"the wheel isn't version {version}")
    print(f"  {len(names)} files, all required ones present")


def smoke(wheel: Path, version: str) -> None:
    """Install a wheel into a fresh environment and use it: log a run, list it, check the setup.

    :param wheel: The wheel.
    :param version: The expected version."""
    step("a fresh install")
    with tempfile.TemporaryDirectory() as tmp:
        venv, project = Path(tmp) / "venv", Path(tmp) / "project"
        run("uv", "venv", "--python", "3.11", str(venv))
        python = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        beamtime = python.parent / "beamtime"
        run(
            "uv",
            "pip",
            "install",
            "--python",
            str(python),
            f"beamtime[serve] @ {wheel.resolve().as_uri()}",
        )
        if version not in run(str(beamtime), "--version", capture=True):
            fail(f"the installed beamtime isn't {version}")
        project.mkdir()
        run(str(beamtime), "--root", str(project), "init")
        run(str(python), "-c", SMOKE, cwd=project)
        runs = run(str(beamtime), "--root", str(project), "runs", "smoke", "--json", capture=True)
        if '"finished"' not in runs:
            fail(f"the smoke run wasn't recorded as finished:\n{runs}")
        run(str(beamtime), "--root", str(project), "groups", ".")
        print("  installed, logged a run and listed it")


def notes(version: str) -> str:
    """Read this version's section of the changelog.

    :param version: The version.
    :return: The section's text."""
    text = (ROOT / "CHANGELOG.md").read_text()
    if (m := re.search(rf"^## {re.escape(version)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)) is None:
        fail(f"CHANGELOG.md has no section for {version}")
    return m.group(1).strip()


def run(*args: str, cwd: Path = ROOT, capture: bool = False) -> str:
    """Run a command, stopping the release when it fails.

    :param args: The command.
    :param cwd: Where to run it.
    :param capture: Whether to return its output instead of showing it.
    :return: Its output, when captured."""
    done = subprocess.run(args, cwd=cwd, capture_output=capture, text=True)
    if done.returncode != 0:
        fail(f"`{' '.join(args)}` failed" + (f":\n{done.stdout}{done.stderr}" if capture else ""))
    return done.stdout if capture else ""


def step(name: str) -> None:
    """Announce a step.

    :param name: What is checked."""
    print(f"\n== {name}", flush=True)


def fail(message: str) -> NoReturn:
    """Stop the release.

    :param message: Why."""
    print(f"\nrelease stopped: {message}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
