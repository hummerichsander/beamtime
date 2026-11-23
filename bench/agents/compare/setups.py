"""The setups of the benchmark: a project per session with data, rules, tools and PATH."""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

import yaml

from beamtime.guide.rules import END, START, render
from beamtime.ops.registry import OPS
from beamtime.settings import resolve_agent

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LIBRARIES = ["numpy", "pandas", "scipy", "matplotlib", "tensorboard", "pyyaml"]
TOOLS = "Bash,Read,Write,Edit,Glob,Grep"

PREAMBLE = """# Project

This project holds the results of numerical experiments. Answer the questions you are given from the
data in this project. Work on your own and do not ask back. Python with numpy, pandas, scipy and
matplotlib is on the PATH.
"""

FILES = """The runs are plain files in `runs/<group>/<run id>/`; groups nest as folders.
- `config.json`: the run's config as logged, nested.
- `metrics.csv`: `step`, `time`, then one column per metric, sorted; a cell is empty where the
  metric was not logged at that step.
- `output.log`: the run's captured output; its last line tells how the run ended. There is no
  status file.
"""

TENSORBOARD = """The runs are TensorBoard logs in `tb/<group>/<run id>/`; groups nest as folders.
- `events.out.tfevents.*`: one scalar per metric and step with its wall time; read it with
  `tensorboard.backend.event_processing.event_accumulator.EventAccumulator(folder,
  size_guidance={"scalars": 0})`. The hparams plugin summary holds the config.
- `hparams.yaml`: the run's config as logged, nested.
- `output.log`: the run's captured output; its last line tells how the run ended. There is no
  status file.
"""

# only data sets with a record get this line, so the `s` sessions keep the text of L72.
RECORD_LINE = """- `record/<group>/`, next to `{top}/`: the researchers' proposals (with predictions), notes and
  memory, where there are any.
"""


@dataclass(kw_only=True)
class Setup:
    """How one setup gives an agent the data."""

    name: str
    data: Literal["beamtime", "files", "tensorboard"]
    mcp: bool
    env: Literal["base", "beamtime"]
    section: str
    check: bool = False


@dataclass(kw_only=True)
class Envs:
    """The two Python environments of a batch."""

    base: Path
    beamtime: Path

    def bin(self, env: str) -> Path:
        """Give the executables folder of an environment.

        :param env: ``base`` or ``beamtime``.
        :return: The folder."""
        match env:
            case "base":
                return self.base / "bin"
            case "beamtime":
                return self.beamtime / "bin"
            case _:
                raise ValueError(f"unknown environment {env!r}")


@dataclass(kw_only=True)
class Project:
    """A prepared session: the folder the agent works in and how to start it."""

    setup: str
    root: Path
    claude_md: Path
    tools: str
    allowed: str
    mcp_config: Path | None
    env: dict[str, str]

    @property
    def flags(self) -> list[str]:
        """The ``claude`` flags that make the session this setup and nothing else.

        :return: The flags; the caller adds the prompt, the model and the output format."""
        flags = ["--tools", self.tools, "--allowedTools", self.allowed, "--strict-mcp-config"]
        if self.mcp_config is not None:
            flags += ["--mcp-config", str(self.mcp_config)]
        return (
            flags
            + ["--setting-sources", "project", "--disable-slash-commands"]
            + ["--no-session-persistence"]
        )


def rules_block() -> str:
    """Render Beamtime's agent rules for default agent settings, as shipped.

    :return: The block with its markers."""
    user_only = sorted(o.name for o in OPS if o.user_only)
    return f"{START}\n{render(resolve_agent({}), user_only)}\n{END}\n"


SETUPS = {
    "mcp": Setup(name="mcp", data="beamtime", mcp=True, env="base", section=rules_block()),
    # a regression check, not a target: it runs on the first seed only (mcp is the measured setup).
    "cli": Setup(
        name="cli", data="beamtime", mcp=False, env="beamtime", section=rules_block(), check=True
    ),
    "files": Setup(name="files", data="files", mcp=False, env="base", section=FILES),
    "tensorboard": Setup(
        name="tensorboard", data="tensorboard", mcp=False, env="base", section=TENSORBOARD
    ),
}


def make_envs(root: Path) -> Envs:
    """Build the two environments with uv, reusing those whose install finished.

    ``base`` has the analysis libraries; ``beamtime`` adds this checkout's ``beamtime[serve]``.

    :param root: The folder that will hold ``base/`` and ``beamtime/``.
    :return: The environments."""
    envs = Envs(base=root / "base", beamtime=root / "beamtime")
    for path, extra in ((envs.base, []), (envs.beamtime, [f"{REPO}[serve]"])):
        # written last, so a venv whose install failed is built again instead of reused.
        if (done := path / ".installed").exists():
            continue
        subprocess.run(["uv", "venv", "--clear", "--python", "3.11", str(path)], check=True)
        python = str(path / "bin" / "python")
        subprocess.run(["uv", "pip", "install", "--python", python, *LIBRARIES, *extra], check=True)
        done.touch()
    return envs


def prepare(setup: str, session_dir: Path, data_dir: Path, envs: Envs) -> Project:
    """Set up a session's project: its data, CLAUDE.md, MCP config, PATH and a warm index.

    :param setup: A key of ``SETUPS``.
    :param session_dir: The session's own folder; the project, cache and config live inside.
    :param data_dir: The folder ``data.make_logdir`` filled; read, never changed.
    :param envs: The environments from ``make_envs``.
    :return: The project."""
    spec = SETUPS[setup]
    project = planned(setup, session_dir)
    root = project.root
    root.mkdir(parents=True)
    logdir = data_dir / "beamtime"
    cache = session_dir / "cache"

    match spec.data:
        case "beamtime":
            shutil.copytree(logdir, root / "beamtime")
            (root / "beamtime.yaml").write_text(yaml.safe_dump({"logdir": "beamtime"}))
        case "files":
            export(envs, "export_files", logdir, root)
        case "tensorboard":
            export(envs, "export_tensorboard", logdir, root)
        case _:
            raise ValueError(f"unknown data {spec.data!r}")
    section = spec.section
    if (root / "record").is_dir():
        section += RECORD_LINE.format(top="runs" if spec.data == "files" else "tb")
    project.claude_md.write_text(f"{PREAMBLE}\n## Data\n\n{section}")

    # a host BEAMTIME_LOGDIR and the like would redirect the CLI and MCP setups.
    env = {k: v for k, v in os.environ.items() if not k.startswith("BEAMTIME_")}
    env.pop("PYTHONPATH", None)
    env.update(
        PATH=path_of(envs.bin(spec.env)),
        VIRTUAL_ENV=str(envs.base if spec.env == "base" else envs.beamtime),
        BEAMTIME_CACHE=str(cache),
        XDG_CONFIG_HOME=str(session_dir / "config"),
        CLAUDE_CODE_DISABLE_AUTO_MEMORY="1",
    )

    if spec.mcp:
        server = {
            "command": str(envs.bin("beamtime") / "beamtime"),
            "args": ["--root", str(root), "mcp"],
            "env": {"BEAMTIME_CACHE": str(cache), "XDG_CONFIG_HOME": env["XDG_CONFIG_HOME"]},
        }
        project.mcp_config.write_text(json.dumps({"mcpServers": {"beamtime": server}}))
    if spec.data == "beamtime":
        warm(envs, root, env)
    return replace(project, env=env)


def planned(setup: str, session_dir: Path) -> Project:
    """Name a session's project and flags without touching the disk or the environment.

    :param setup: A key of ``SETUPS``.
    :param session_dir: The session's own folder.
    :return: The project with an empty ``env``."""
    spec = SETUPS[setup]
    return Project(
        setup=setup,
        root=session_dir / "proj",
        claude_md=session_dir / "proj" / "CLAUDE.md",
        tools=TOOLS,
        allowed=f"mcp__beamtime__*,{TOOLS}" if spec.mcp else TOOLS,
        mcp_config=session_dir / "mcp.json" if spec.mcp else None,
        env={},
    )


def export(envs: Envs, function: str, logdir: Path, dest: Path) -> None:
    """Run an exporter of ``formats.py`` in the ``beamtime`` environment, which has tensorboard.

    :param envs: The environments.
    :param function: ``export_files`` or ``export_tensorboard``.
    :param logdir: The log dir.
    :param dest: The folder that will hold the export."""
    code = (
        f"import sys; from pathlib import Path; sys.path.insert(0, {str(HERE)!r}); import formats; "
        f"formats.{function}(Path({str(logdir)!r}), Path({str(dest)!r}))"
    )
    python = envs.bin("beamtime") / "python"
    subprocess.run([str(python), "-c", code], check=True, stdout=subprocess.DEVNULL)


def warm(envs: Envs, root: Path, env: dict[str, str]) -> None:
    """Index the whole project before the session, as a running daemon would keep it.

    ``reindex`` is a user-only operation; the harness plays the user.

    :param envs: The environments.
    :param root: The project.
    :param env: The session's environment, with its own cache."""
    beamtime = str(envs.bin("beamtime") / "beamtime")
    subprocess.run(
        [beamtime, "--root", str(root), "reindex"], env=env, check=True, stdout=subprocess.DEVNULL
    )


def path_of(first: Path) -> str:
    """Build a PATH that starts with an environment and holds no other ``beamtime``.

    :param first: The environment's executables folder.
    :return: The PATH."""
    keep = [d for d in os.environ.get("PATH", "").split(os.pathsep) if d and not has_beamtime(d)]
    return os.pathsep.join([str(first), *keep])


def has_beamtime(folder: str) -> bool:
    """Say whether a folder holds a ``beamtime`` executable.

    :param folder: The folder.
    :return: Whether it does."""
    return shutil.which("beamtime", path=folder) is not None
