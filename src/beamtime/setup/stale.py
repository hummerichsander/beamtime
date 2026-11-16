"""The update checks: what an older release set up around the data and this release would change."""

import os
import shutil
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from beamtime import __version__
from beamtime.format.constants import RUN
from beamtime.settings import MOVED
from beamtime.setup.agents import SERVER, ConfigError, client_named, config_places, read_json
from beamtime.setup.plan import release

if TYPE_CHECKING:
    from beamtime.setup.scan import AgentFound, Past, PythonEnv

SKIPPED = (".git", ".beamtime", "node_modules", "__pycache__")


@dataclass(frozen=True, kw_only=True)
class Stale:
    """One stale item: what is there, what this release puts there, and whether it is ticked."""

    item: str
    before: str
    after: str
    ticked: bool = True
    path: str | None = None

    @property
    def line(self) -> str:
        """The item as one line, as ``setup --check`` prints it.

        :return: E.g. ``rules: CLAUDE.md has the 0.1.1 rules -> the 0.3.0 rules``."""
        return f"{self.item}: {self.before} -> {self.after}"


def find(
    root: Path,
    *,
    home: Path,
    logdir: Path,
    agents: Iterable["AgentFound"],
    past: Iterable["Past"],
    env: "PythonEnv | None",
    which: Callable[[str], str | None] = shutil.which,
) -> tuple[Stale, ...]:
    """Run every local check of a set-up project; a remote needs a probe and is checked apart.

    :param root: The project root.
    :param home: The home directory.
    :param logdir: The project's log dir.
    :param agents: The agent clients the scan found.
    :param past: The past work the scan found.
    :param env: The project's Python environment, or ``None``.
    :param which: Looks up a program on ``PATH``.
    :return: The stale items in the order of the spec's table."""
    agents = list(agents)
    found = [
        stale_rules(agents),
        stale_mcp(root, home, agents, env, which),
        stale_skills(root),
        stale_settings(root),
        stale_sdk(env),
        *stale_runs(root, logdir, past),
    ]
    return tuple(s for s in found if s is not None)


def stale_rules(agents: Iterable["AgentFound"]) -> Stale | None:
    """Compare each rules block with the text of this release.

    A block that matches no release was edited by hand, and its update is not ticked.

    :param agents: The agent clients the scan found.
    :return: The item, or ``None`` when every block is current or there is none."""
    files = {a.rules_file: a.release for a in agents if a.has_block}
    old = {name: found for name, found in files.items() if found != __version__}
    if not old:
        return None
    before = "; ".join(
        f"{name} has the {found} rules" if found else f"{name} was edited by hand"
        for name, found in old.items()
    )
    return Stale(
        item="rules",
        before=before,
        after=f"the {__version__} rules",
        ticked=all(old.values()),
    )


def stale_mcp(
    root: Path,
    home: Path,
    agents: Iterable["AgentFound"],
    env: "PythonEnv | None",
    which: Callable[[str], str | None],
) -> Stale | None:
    """Check each registered MCP command: it must start and be what this release picks.

    :param root: The project root.
    :param home: The home directory.
    :param agents: The agent clients the scan found.
    :param env: The project's Python environment, or ``None``.
    :param which: Looks up a program on ``PATH``.
    :return: The item, or ``None`` when every command is fine or no command could replace it."""
    from beamtime.setup.agents import check_command, mcp_command

    root = root.resolve()
    shared = unshared = None
    picked = False
    rows = []
    for found in agents:
        if not found.registered:
            continue
        client = client_named(found.client)
        for path, keys in config_places(client, root, home):
            if (command := read_command(path, keys)) is None or command[-1:] != ["mcp"]:
                continue
            if not picked:
                shared = mcp_command(env, root, shared=True, which=which)
                unshared = mcp_command(env, root, shared=False, which=which)
                picked = True
            options = [c for c in (shared if client.shared else None, unshared) if c]
            if not options:
                continue
            starts = check_command(command, root)[0] is not None
            if not starts:
                why = "does not start"
            elif command not in options:
                why = "is not what this release picks"
            else:
                continue
            rows.append((f"{client.label}: {' '.join(command)} {why}", " ".join(options[0])))
    if not rows:
        return None
    return Stale(item="mcp", before="; ".join(r[0] for r in rows), after=rows[0][1])


def read_command(path: Path, keys: list[str]) -> list[str] | None:
    """Read the command of the beamtime entry in a client's config, without ``--root``.

    :param path: The config file.
    :param keys: The nested keys of its servers table.
    :return: The command with its arguments, or ``None`` when there is no entry."""
    try:
        if path.suffix == ".toml":
            import tomllib

            data: Any = tomllib.loads(path.read_text())
        else:
            data = read_json(path)
    except (OSError, ValueError, ConfigError):
        return None
    for key in (*keys, SERVER):
        if not isinstance(data, dict) or (data := data.get(key)) is None:
            return None
    if not isinstance(data, dict):
        return None
    command = data.get("command")
    match command:
        case str():
            words = [command, *map(str, data.get("args") or [])]
        case list():
            words = [str(w) for w in command]
        case _:
            return None
    out = []
    skip = False
    for word in words:
        if skip:
            skip = False
        elif word == "--root":
            skip = True
        else:
            out.append(word)
    return out


def stale_skills(root: Path) -> Stale | None:
    """Compare the project's Beamtime skills with this release's.

    :param root: The project root.
    :return: The item, or ``None`` when the project has no Beamtime skill or all are current."""
    from beamtime.guide.skills import SKILLS, skill_text

    folder = root / ".claude" / "skills"
    if not any(folder.glob("beamtime-*/SKILL.md")):
        return None
    current = [
        n
        for n in SKILLS
        if (file := folder / n / "SKILL.md").is_file() and file.read_text() == skill_text(n)
    ]
    if len(current) == len(SKILLS):
        return None
    return Stale(
        item="skills",
        before=f"{len(current)} of {len(SKILLS)} skills current in .claude/skills/",
        after=f"{len(SKILLS)} skills",
    )


def stale_settings(root: Path) -> Stale | None:
    """Look for settings in ``beamtime.yaml`` that this release no longer reads.

    :param root: The project root.
    :return: The item, or ``None`` when the file has none."""
    if not (keys := moved_keys(root)):
        return None
    return Stale(item="settings", before=f"beamtime.yaml sets {', '.join(keys)}", after="removed")


def moved_keys(root: Path) -> list[str]:
    """List the settings of ``beamtime.yaml`` that this release no longer reads.

    :param root: The project root.
    :return: The keys, in the order of ``MOVED``."""
    import yaml

    file = root / "beamtime.yaml"
    if not file.is_file():
        return []
    try:
        data = yaml.safe_load(file.read_text())
    except yaml.YAMLError:
        return []
    return [k for k in MOVED if k in data] if isinstance(data, dict) else []


def stale_sdk(env: "PythonEnv | None") -> Stale | None:
    """Compare the Beamtime in the project's environment with this one.

    :param env: The project's Python environment, or ``None``.
    :return: The item, or ``None`` when it is current, missing or can't take this release."""
    from beamtime.setup.sdk import sdk_blocker

    if env is None or env.beamtime_version is None or sdk_blocker(env) is not None:
        return None
    if release(env.beamtime_version) >= release(__version__):
        return None
    return Stale(
        item="sdk",
        before=f"beamtime {env.beamtime_version} in the {env.tool} environment",
        after=f"beamtime {__version__}",
    )


def stale_runs(root: Path, logdir: Path, past: Iterable["Past"]) -> list[Stale]:
    """Find Beamtime runs in the project, outside the log dir, that it has not imported.

    :param root: The project root.
    :param logdir: The project's log dir.
    :param past: The past work the scan found.
    :return: One item per folder, its ``path`` the import's ``--import`` value."""
    out = []
    have: set[str] | None = None
    for item in past:
        if item.other or item.found.kind != "beamtime":
            continue
        have = run_names(logdir) if have is None else have
        if not (missing := run_names(item.found.path) - have):
            continue
        path = os.path.relpath(item.found.path, root).replace(os.sep, "/") + "/"
        out.append(
            Stale(
                item="runs",
                before=f"{len(missing)} Beamtime runs in {path}, outside the log dir",
                after="copied into the log dir",
                path=path,
            )
        )
    return out


def run_names(top: Path) -> set[str]:
    """List the names of the run folders below a folder.

    :param top: A log dir or a folder of runs.
    :return: The names."""
    names = set()
    for folder, dirs, files in os.walk(top):
        if RUN in files:
            names.add(Path(folder).name)
            dirs.clear()
        dirs[:] = [d for d in dirs if d not in SKIPPED]
    return names


def stale_remote(name: str, version: str | None) -> Stale | None:
    """Compare the Beamtime on a remote, as a probe found it, with this one.

    :param name: The remote's name.
    :param version: The version the probe read, or ``None`` when there is none.
    :return: The item, or ``None`` when the remote is current or has none."""
    if version is None or release(version) >= release(__version__):
        return None
    return Stale(
        item=f"remote:{name}",
        before=f"beamtime {version} on {name}",
        after=f"beamtime {__version__}",
    )
