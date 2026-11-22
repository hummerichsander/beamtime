"""The setups of the benchmark: a project per session with data, rules, tools and PATH."""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import yaml

from beamtime.guide.rules import END, START, render
from beamtime.ops.registry import OPS
from beamtime.settings import resolve_agent

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LIBRARIES = ["numpy", "pandas", "scipy", "matplotlib", "tensorboard", "pyyaml"]
TOOLS = "Bash,Read,Write,Edit,Glob,Grep"
REFUSAL = "there is no beamtime command here: import bt in Python, see CLAUDE.md"

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

SCRIPT = """The runs are a Beamtime log dir in `beamtime/`, read through `bt.py` next to this file:
it gives Beamtime's operations as Python functions, named as the tools below but called in Python:
`bt.runs(...)`, `bt.series(...)`, `bt.check(...)`. There is no `beamtime` command here.

```python
import bt
bt.ops()                                             # every operation with its summary
bt.params("runs")                                    # one operation's parameters, as a schema
bt.runs({"from": ".", "limit": 200})                 # call it; bt.call("runs", from_=...) too
```

An answer is a plain dict and arrives whole, so keep it in a variable and filter, join and
aggregate it in Python; print only what you need to see. A read you have already made is answered
from disk, so calling it again in a later script costs nothing and needs no re-plan.

The operations above already compute the statistics, intervals and per-run summaries, and every
reader of this record shares the numbers they return. Python here is for joining, filtering and
formatting those answers, not for arriving at them: before computing a number yourself, look for
the operation or field that returns it. Pulling raw points, or writing a statistic by hand, means
you have probably missed one.
- from and group: a group below the log dir or a run id; depth: levels below it, default all.
  hidden: True includes hidden runs.
- where: field -> value or {op: value}; ops eq ne lt le gt ge in nin has exists glob; also
  any: [...], not: {...}.
- field expressions, for select, sort, by and where (not a parameter of their own):
  run.status, config.lr, metric.val/acc.max, metric.train/loss.mean[0:1000],
  value.test/acc, metric.a.nonfinite_step, metric.a.rise_step:3, metric.a[b.min_step].
- `bt.guide(part=...)` reads Beamtime's own guide (`bt.guide()` lists the parts). User-only
  commands are not exposed.
- An error may suggest a command like `beamtime keys <group>`; here that is
  `bt.keys({"from": "<group>"})`.

Every operation and the parameters it takes, which are the only names it accepts; `bt.params(name)`
adds the types and defaults in full.

```
{reference}
```
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
    # the operations as Python functions (``script/bt.py``), with no ``beamtime`` command.
    api: bool = False


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


def api_reference() -> str:
    """List every operation an agent may call with the parameters it takes.

    The MCP setup has its tool schemas in the prompt from the first turn; this is the same
    information for the script setup, which otherwise spends turns guessing parameter names.

    :return: One line per operation."""
    from beamtime.mcp.server import schema

    def kind(node: dict[str, Any]) -> str:
        match node.get("type") or ("array" if "items" in node else None):
            case "array":
                return "list"
            case "integer":
                return "int"
            case "boolean":
                return "bool"
            case "object":
                return "dict"
            case "string":
                return "str"
            case _:
                return "enum" if node.get("enum") else "any"

    lines = []
    for op in OPS:
        if op.user_only:
            continue
        props = schema(op).get("properties", {}) if op.params is not None else {}
        lines.append(f"{op.tool}({', '.join(f'{k}:{kind(v)}' for k, v in props.items())})")
    return "\n".join(lines)


def script_section() -> str:
    """Render the script setup's data section with the operation list filled in.

    :return: The section."""
    return SCRIPT.replace("{reference}", api_reference())


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
    # the same operations as mcp, called from code: their answers land in variables, not in
    # the context window. Measured like mcp, so it runs on every seed.
    "script": Setup(
        name="script",
        data="beamtime",
        mcp=False,
        env="beamtime",
        section=f"{rules_block()}\n{script_section()}",
        api=True,
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
    if spec.api:
        shutil.copy(HERE / "script" / "bt.py", root / "bt.py")
        env["PATH"] = os.pathsep.join([str(shadow(session_dir)), env["PATH"]])
    if spec.data == "beamtime":
        warm(envs, root, env)
    return replace(project, env=env)


def shadow(session_dir: Path) -> Path:
    """Make a folder whose ``beamtime`` refuses, so the script setup reads through the Python API
    and not through the CLI.

    :param session_dir: The session's own folder.
    :return: The folder, which goes first on the PATH."""
    folder = session_dir / "bin"
    folder.mkdir(parents=True, exist_ok=True)
    stub = folder / "beamtime"
    stub.write_text(f"#!/bin/sh\necho '{REFUSAL}' >&2\nexit 2\n")
    stub.chmod(0o755)
    return folder


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
