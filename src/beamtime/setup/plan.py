"""What ``beamtime setup`` changes: the answers, the changes and the command."""

import dataclasses
import os
import re
import shlex
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import msgspec

from beamtime.settings import expand_path
from beamtime.setup.remotes import remote_name_problem

if TYPE_CHECKING:
    from beamtime.ops.registry import SetupParams
    from beamtime.settings import AgentSettings
    from beamtime.setup.importers import Found
    from beamtime.setup.scan import Scan

PATH_START = ("/", "~", "$")
UPDATE_ITEMS = ("rules", "mcp", "skills", "settings", "sdk")
BLOCK_END = "# end beamtime"
BLOCK_HEADS = {
    "record": "# beamtime: run data stays out; proposals, notes, memory and views are committed",
    "none": "# beamtime: the log dir stays out of git",
}
REMOTE_COMMAND = "~/.local/bin/beamtime"


@dataclass(frozen=True, kw_only=True)
class Change:
    """One thing the setup writes: where it lands, how it reads in the review, and how to do it."""

    where: Literal["project", "machine", "remote", "import"]
    label: str
    before: str | None
    after: str
    run: Callable[[], str | None]


class Remote(msgspec.Struct, frozen=True):
    """A remote as ``--remote`` names it: its source, its host and its log dir there."""

    name: str
    host: str | None = None
    path: str | None = None

    @classmethod
    def parse(cls, text: str) -> "Remote":
        """Read ``NAME[=HOST][:PATH]``; a path starts with ``/``, ``~`` or ``$``.

        :param text: The flag value.
        :return: The remote."""
        cut = min((i for i in (text.find("="), text.find(":")) if i >= 0), default=len(text))
        name, rest = text[:cut], text[cut:]
        host = path = None
        if rest.startswith("="):
            host, sep, path = rest[1:].partition(":")
            path = path if sep else None
            if not host:
                raise ValueError(f"--remote {text!r}: no host after '='")
        elif rest:
            path = rest[1:]
        if problem := remote_name_problem(name):
            raise ValueError(f"--remote {text!r}: {problem}")
        if path is not None and not path.startswith(PATH_START):
            raise ValueError(f"--remote {text!r}: a path starts with /, ~ or $")
        return cls(name, host, path)

    def __str__(self) -> str:
        """Write the remote as the flag takes it.

        :return: ``NAME[=HOST][:PATH]``."""
        host = f"={self.host}" if self.host else ""
        path = f":{self.path}" if self.path is not None else ""
        return f"{self.name}{host}{path}"


class Answers(msgspec.Struct, kw_only=True):
    """Every answer of the setup, as the prompts or the flags give it."""

    runs: Literal["here", "remote", "both"] = "here"
    logdir: str
    link_logdir: str | None = None
    remotes: list[Remote] = []
    skip_remotes: list[str] = []
    install_remotes: list[str] = []
    ssh_share: list[str] = []
    cache: str | None = None
    agents: list[str] = []
    agent_style: Literal["careful", "hands-on", "analysis"] = "careful"
    agent_set: dict[str, str] = {}
    rules: bool = True
    imports: list[str] = []
    import_notes: list[str] = []
    import_memory: list[str] = []
    git: Literal["record", "none"] = "record"
    sdk: bool = False
    role: Literal["record", "full"] = "record"
    update: list[str] = []
    migrate_with: str | None = None

    @classmethod
    def defaults(cls, scan: "Scan") -> "Answers":
        """The conservative answers of a scan: nothing outside the project unless a flag names it.

        The agent style and its overrides are the project's own, from its ``beamtime.yaml``.

        :param scan: The facts of the project and the machine.
        :return: The answers without any flag."""
        from beamtime.settings import PRESETS, check_agent

        logdir = scan.project.logdir
        inside = logdir.is_relative_to(scan.root.resolve())
        file = scan.root / "beamtime.yaml"
        agent = check_agent(file, Planner.read(file).get("agent") or {}, []) or {}
        style = agent.get("style", "careful")
        style = "careful" if style == "custom" else style
        knobs = {k: str(v) for k, v in agent.items() if k in PRESETS["careful"]}
        return cls(
            logdir=logdir.relative_to(scan.root.resolve()).as_posix() if inside else str(logdir),
            agent_style=style,
            agent_set=preset_overrides(style, knobs),
            imports=[s.path for s in scan.stale if s.item == "runs" and s.ticked and s.path],
            update=[s.item for s in scan.stale if s.ticked and s.item in UPDATE_ITEMS],
        )

    @classmethod
    def saved(cls, scan: "Scan") -> "Answers":
        """The answers a set-up project and machine stand for: what the files already say.

        Planning them changes nothing, except a rules block that no longer matches the project's
        ``agent`` settings.

        :param scan: The facts of the project and the machine.
        :return: The answers."""
        from beamtime.settings import user_settings_path

        base = cls.defaults(scan)
        named = Planner.read(scan.root / "beamtime.yaml").get("remotes") or {}
        mine = Planner.read(user_settings_path()).get("remotes") or {}
        enabled = [n for n in named if (mine.get(n) or {}).get("enabled") is not False]
        registered = [a for a in scan.agents if a.registered]
        ignore = scan.root / ".gitignore"
        return msgspec.structs.replace(
            base,
            runs="both" if named else "here",
            remotes=[
                Remote(n, (mine.get(n) or {}).get("host"), (named[n] or {}).get("path"))
                for n in enabled
            ],
            skip_remotes=[n for n in named if n not in enabled],
            agents=[a.client for a in registered],
            rules=any(a.has_block for a in registered) if registered else True,
            git="none"
            if ignore.is_file() and BLOCK_HEADS["none"] in ignore.read_text()
            else "record",
        )

    @classmethod
    def from_params(
        cls, p: "SetupParams", scan: "Scan", base: "Answers | None" = None
    ) -> "Answers":
        """Fill the answers from the flags, and what a flag leaves open from the scan.

        :param p: The parameters of ``setup``.
        :param scan: The facts of the project and the machine.
        :param base: The answers a flag leaves open; default the scan's ``defaults``.
        :return: The answers.
        :raises ValueError: A flag value is malformed, or two flags contradict each other."""
        from beamtime.settings import AGENT_KEYS
        from beamtime.setup.agents import CLIENTS

        if base is None:
            base = cls.defaults(scan)
        names = [c.name for c in CLIENTS]
        if p.agents and p.no_agents:
            raise ValueError("--agents and --no-agents contradict each other")
        if p.sdk and p.no_sdk:
            raise ValueError("--sdk and --no-sdk contradict each other")
        for agent in (*p.agents, *([p.migrate_with] if p.migrate_with else [])):
            if agent not in names:
                raise ValueError(f"unknown agent {agent!r}; choose from {', '.join(names)}")
        agent_set = {}
        for item in (pair for text in p.agent_set for pair in split_agent_set(text)):
            key, sep, value = item.partition("=")
            if not sep or key not in AGENT_KEYS:
                raise ValueError(
                    f"--agent-set {item!r}: write KEY=VALUE with a key of {', '.join(AGENT_KEYS)}"
                )
            agent_set[key] = value
        style = p.agent_style or base.agent_style
        if style == base.agent_style:
            agent_set = {**base.agent_set, **agent_set}
        update = None if p.update is None else [u for u in p.update if u]
        for item in update or []:
            remote = item.startswith("remote:") and len(item) > len("remote:")
            if item not in UPDATE_ITEMS and not remote:
                raise ValueError(
                    f"--update {item!r}: choose from {', '.join(UPDATE_ITEMS)} or remote:NAME"
                )
        added = [Remote.parse(t) for t in p.remote]
        taken = {r.name for r in added} | set(p.skip_remote)
        return cls(
            runs=p.runs or base.runs,
            logdir=p.logdir or base.logdir,
            link_logdir=p.link_logdir,
            remotes=[*(r for r in base.remotes if r.name not in taken), *added],
            skip_remotes=[
                *(n for n in base.skip_remotes if n not in taken),
                *p.skip_remote,
            ],
            install_remotes=list(p.install_remote),
            ssh_share=list(p.ssh_share),
            cache=p.cache,
            agents=[a for a in p.agents if a] if p.agents or p.no_agents else base.agents,
            agent_style=style,
            agent_set=preset_overrides(style, agent_set),
            rules=base.rules and not p.no_rules or p.instructions,
            imports=[i for i in p.import_ if i] if p.import_ else base.imports,
            import_notes=list(p.import_notes),
            import_memory=list(p.import_memory),
            git=p.git or base.git,
            sdk=p.sdk or base.sdk and not p.no_sdk,
            role=p.role or base.role,
            update=base.update if update is None else update,
            migrate_with=p.migrate_with,
        )


def preset_overrides(style: str, agent_set: dict[str, str]) -> dict[str, str]:
    """Drop the single keys that only repeat a style's preset; conventions always stay.

    :param style: The agent style.
    :param agent_set: The single keys as ``--agent-set`` text.
    :return: The keys that differ from the preset.
    :raises ValueError: A value is not valid for its key."""
    from beamtime.settings import PRESETS

    preset = PRESETS[style]
    return {k: v for k, v in agent_set.items() if k not in preset or agent_value(k, v) != preset[k]}


def same_agent(a: "AgentSettings", b: "AgentSettings") -> bool:
    """Say whether two agent settings mean the same knobs, wherever their values come from.

    :param a: The one settings.
    :param b: The other.
    :return: ``True`` when every knob and convention is equal; ``custom`` means careful's values."""
    return dataclasses.replace(a, style="", source={}) == dataclasses.replace(
        b, style="", source={}
    )


def split_agent_set(text: str) -> list[str]:
    """Split ``k=v,k=v`` into pairs, only at a comma before a key, so values keep their commas.

    :param text: One ``--agent-set`` value.
    :return: The ``KEY=VALUE`` pairs."""
    from beamtime.settings import AGENT_KEYS

    return [pair for pair in re.split(rf",(?=(?:{'|'.join(AGENT_KEYS)})=)", text) if pair]


def flags(answers: Answers, scan: "Scan") -> list[str]:
    """List the flags that turn the scan's defaults into the answers, in flag table order.

    :param answers: The answers.
    :param scan: The facts the defaults come from.
    :return: One string per flag, its value quoted for a shell."""
    from beamtime.settings import PRESETS

    base = Answers.defaults(scan)
    out = []
    for f in msgspec.structs.fields(Answers):
        value, default = getattr(answers, f.name), getattr(base, f.name)
        if f.name == "agent_set" and answers.agent_style != base.agent_style:
            # another style drops the project's overrides, as from_params does.
            default = {}
        if value == default:
            continue
        match f.name:
            case "runs" | "logdir" | "link_logdir" | "cache" | "role" | "git" | "migrate_with":
                out.append(f"--{f.name.replace('_', '-')} {shlex.quote(value)}")
            case "agent_style":
                out.append(f"--agent-style {value}")
            case "remotes":
                out += [f"--remote {shlex.quote(str(r))}" for r in value]
            case "skip_remotes" | "install_remotes":
                flag = f.name.removesuffix("s").replace("_", "-")
                out += [f"--{flag} {shlex.quote(v)}" for v in value]
            case "ssh_share":
                out += [f"--ssh-share {shlex.quote(v)}" for v in value]
            case "agents":
                out.append(f"--agents {shlex.quote(','.join(value))}" if value else "--no-agents")
            case "agent_set":
                # a key the project overrides and the answers drop goes back to the preset.
                preset = PRESETS[answers.agent_style]
                value = {**{k: str(preset[k]) for k in default if k not in value}, **value}
                out += [f"--agent-set {shlex.quote(f'{k}={v}')}" for k, v in value.items()]
            case "rules":
                out.append("--no-rules")
            case "imports":
                out += [f"--import {shlex.quote(v)}" for v in value] or ["--import ''"]
            case "import_notes" | "import_memory":
                out += [f"--{f.name.replace('_', '-')} {shlex.quote(v)}" for v in value]
            case "sdk":
                out.append("--sdk" if value else "--no-sdk")
            case "update":
                out.append(f"--update {shlex.quote(','.join(value))}")
            case _:
                raise ValueError(f"no flag for the answer {f.name}")
    return out


def command(answers: Answers, scan: "Scan") -> str:
    """Write the ``beamtime setup --yes`` command that makes the same plan, one flag to a line.

    :param answers: The answers.
    :param scan: The facts the defaults come from.
    :return: The command as a shell line with ``\\`` continuations."""
    words = ["beamtime setup --yes", *flags(answers, scan)]
    return " \\\n  ".join(words)


def plan(
    scan: "Scan", answers: Answers, *, which: Callable[[str], str | None] = shutil.which
) -> list[Change]:
    """Decide everything the setup writes; nothing is written until ``apply`` runs the changes.

    :param scan: The facts of the project and the machine.
    :param answers: The answers.
    :param which: Looks up a program on ``PATH``.
    :return: The changes in the order they are applied: project, machine, agents, imports.
    :raises ValueError: An answer can't be carried out; the message says why."""
    return Planner(scan=scan, answers=answers, which=which).changes()


class Planner:
    """Turns the answers into changes, one group at a time."""

    def __init__(
        self, *, scan: "Scan", answers: Answers, which: Callable[[str], str | None]
    ) -> None:
        """Read the project's settings and normalise the log dir answers.

        :param scan: The facts of the project and the machine.
        :param answers: The answers.
        :param which: Looks up a program on ``PATH``."""
        from beamtime.settings import DEFAULTS, user_settings_path

        self.scan = scan
        self.answers = answers
        self.which = which
        self.root = scan.root.resolve()
        self.project_file = self.root / "beamtime.yaml"
        self.user_file = user_settings_path()
        self.given = self.read(self.project_file)
        self.user = self.read(self.user_file)

        self.logdir, self.link = answers.logdir, answers.link_logdir
        outside = not (self.root / expand_path(self.logdir)).resolve().is_relative_to(self.root)
        if (
            outside
            and self.link is None
            and (
                (self.root / expand_path(self.logdir)).resolve() != scan.project.logdir
                or not scan.project.settings
            )
        ):
            self.link, self.logdir = self.logdir, DEFAULTS["logdir"]
        elif outside and self.link is not None:
            # through an existing link the scan sees the target; the project keeps the link's name.
            self.logdir = str(self.given.get("logdir") or DEFAULTS["logdir"])
        self.linked = self.link is not None
        self.inside = self.linked or not outside

    def changes(self) -> list[Change]:
        """List every change, in apply order.

        :return: The changes; empty when the setup is as the answers want it."""
        found = [
            self.beamtime_yaml(),
            self.logdir_link(),
            self.gitignore(),
            self.sdk(),
            self.user_settings(),
            *self.agents(),
            *self.updates(),
            *self.imports(),
            self.notes(),
            *self.remote_changes(),
        ]
        seen: set[tuple[str, str, str]] = set()
        out = []
        for change in found:
            if (
                change is not None
                and (key := (change.where, change.label, change.after)) not in seen
            ):
                seen.add(key)
                out.append(change)
        return out

    def beamtime_yaml(self) -> Change | None:
        """Plan the project's ``beamtime.yaml``: log dir, agent settings and remote paths.

        :return: The change, or ``None`` when the file says it already."""
        from beamtime.settings import DEFAULTS, write_agent, write_key, write_remote

        a = self.answers
        rows: dict[str, tuple[Any, Any]] = {}
        old = self.given.get("logdir")
        # a file without the key already means the default; only a missing file gets it written.
        means = (
            old if old is not None else DEFAULTS["logdir"] if self.project_file.is_file() else None
        )
        if (
            means is None
            or (self.root / expand_path(str(means))).resolve()
            != (self.root / expand_path(self.logdir)).resolve()
        ):
            rows["logdir"] = (old, self.logdir)
        if (agent := self.agent_given()) != (self.given.get("agent") or {}) and agent:
            rows["agent"] = (self.given.get("agent"), agent)
        remotes = self.given.get("remotes") or {}
        for r in a.remotes:
            if r.path is not None and (remotes.get(r.name) or {}).get("path") != r.path:
                conf = {**(remotes.get(r.name) or {}), "path": r.path}
                rows[f"remotes.{r.name}"] = ((remotes.get(r.name) or {}).get("path"), conf)
        if not rows:
            return None

        def run() -> str:
            for key, (_, value) in rows.items():
                if key == "logdir":
                    write_key(self.project_file, key, value)
                elif key == "agent":
                    write_agent(self.project_file, value)
                else:
                    write_remote(self.project_file, key.removeprefix("remotes."), value)
            return "written"

        return Change(
            where="project",
            label="beamtime.yaml",
            before=show_rows({k: v[0] for k, v in rows.items() if v[0] is not None}) or None,
            after=show_rows({k: v[1] for k, v in rows.items()}),
            run=run,
        )

    def agent_given(self) -> dict[str, Any]:
        """The ``agent`` setting the project gets: the chosen style, the keys that differ from its
        preset, and the conventions the file has.

        :return: The mapping to write; empty when nothing is to be written.
        :raises ValueError: A value of ``--agent-set`` is not valid for its key."""
        from beamtime.settings import PRESETS, check_agent, resolve_agent

        a = self.answers
        file = self.given.get("agent")
        file = file if isinstance(file, dict) else {}
        valid = check_agent(self.project_file, file, []) or {}
        given = {k: v for k, v in valid.items() if k != "style" and k not in PRESETS["careful"]}
        # a teammate or a cluster doesn't choose the team's style, so choosing agents writes none.
        chose = bool(a.agents) and self.scan.flow not in ("teammate", "cluster")
        if a.agent_style != "careful" or file or chose or a.agent_set:
            given = {"style": a.agent_style, **given}
        for key, text in preset_overrides(a.agent_style, a.agent_set).items():
            given[key] = agent_value(key, text)
        # a file that already means these values stays as written.
        if file and same_agent(resolve_agent(given), resolve_agent(valid)):
            return file
        return given

    def logdir_link(self) -> Change | None:
        """Plan the link that makes the project's log dir point elsewhere, and its git exclude.

        :return: The change, or ``None`` without a link or when it exists.
        :raises ValueError: The log dir is there already and is not an empty folder."""
        if not self.linked:
            return None
        target = Path(expand_path(str(self.link)))
        if not target.is_absolute():
            target = self.root / target
        target = target.resolve()
        path = self.root / expand_path(self.logdir)
        if path.is_symlink() and path.resolve() != target:
            raise ValueError(f"{path} is a link to {path.resolve()}; remove it first")
        if not path.is_symlink() and path.exists() and (not path.is_dir() or any(path.iterdir())):
            raise ValueError(f"{path} exists and holds files; move it away or use another --logdir")
        exclude = self.exclude_file()
        line = f"/{path.relative_to(self.git_root())}" if exclude else None
        linked = path.is_symlink()
        excluded = (
            exclude is not None and exclude.is_file() and line in exclude.read_text().splitlines()
        )
        if linked and (exclude is None or excluded):
            return None

        def run() -> str:
            target.mkdir(parents=True, exist_ok=True)
            if not path.is_symlink():
                if path.is_dir():
                    path.rmdir()
                path.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(target, path, target_is_directory=True)
            if exclude is not None and not excluded:
                exclude.parent.mkdir(parents=True, exist_ok=True)
                text = exclude.read_text() if exclude.is_file() else ""
                sep = "" if not text or text.endswith("\n") else "\n"
                exclude.write_text(f"{text}{sep}{line}\n")
            return "linked"

        after = f"{self.logdir} -> {target}"
        if exclude:
            after += "\nexcluded in .git/info/exclude; this checkout doesn't commit the record"
        return Change(where="project", label="log dir link", before=None, after=after, run=run)

    def exclude_file(self) -> Path | None:
        """Find this checkout's ``.git/info/exclude``.

        :return: The file's path, or ``None`` outside a git checkout."""
        git = self.git_root()
        return git / ".git" / "info" / "exclude" if (git / ".git").is_dir() else None

    def git_root(self) -> Path:
        """Take the checkout's root, or the project's without one.

        :return: The folder."""
        return self.scan.git.root.resolve() if self.scan.git.root else self.root

    def gitignore(self) -> Change | None:
        """Plan the marked block that keeps run data (or the whole log dir) out of git.

        :return: The change, or ``None`` when the file has the block already."""
        if not self.inside:
            return None
        path = self.root / ".gitignore"
        old = path.read_text() if path.is_file() else ""
        text = gitignore_text(old, self.logdir, self.answers.git)
        if text == old:
            return None
        had = find_block(old.splitlines()) is not None or any(
            line.strip() in plain_entries(self.logdir) for line in old.splitlines()
        )
        after = (
            "run data out; proposals, notes, memory, views in"
            if self.answers.git == "record"
            else "the log dir out"
        )

        def run() -> str:
            path.write_text(text)
            return "written"

        return Change(
            where="project",
            label=".gitignore",
            before="the log dir ignored as a whole" if had else None,
            after=after,
            run=run,
        )

    def sdk(self) -> Change | None:
        """Plan adding the SDK to the project's environment.

        :return: The change, or ``None`` when not asked for or Beamtime is installed already.
        :raises ValueError: There is no environment, or its Python is too old."""
        from beamtime import __version__
        from beamtime.setup.sdk import sdk_blocker, sdk_change

        env = self.scan.env
        if not self.answers.sdk:
            return None
        if env is None:
            raise ValueError(
                "--sdk: the project has no Python environment (uv, poetry, conda or a virtualenv)"
            )
        if (reason := sdk_blocker(env)) is not None:
            raise ValueError(f"--sdk: {reason}")
        from_env = self.mcp_from_env()
        have = env.beamtime_version
        if (
            have is not None
            and release(have) >= release(__version__)
            and (env.has_serve or not from_env)
        ):
            return None
        return sdk_change(env, __version__, from_env, root=self.root)

    def mcp_from_env(self) -> bool:
        """Say whether the agents' MCP command will run from the project's environment.

        :return: ``True`` for a uv or conda environment when agents are registered."""
        env = self.scan.env
        return bool(self.answers.agents) and env is not None and env.tool in ("uv", "conda")

    def user_settings(self) -> Change | None:
        """Plan this machine's settings: the cache, and the remotes it reaches or skips.

        :return: The change, or ``None`` when the file says it already.
        :raises ValueError: A remote is both added and skipped."""
        from beamtime.settings import write_key, write_remote

        a = self.answers
        both = {r.name for r in a.remotes} & set(a.skip_remotes)
        if both:
            raise ValueError(f"{', '.join(sorted(both))}: named by --remote and --skip-remote")
        rows: dict[str, tuple[Any, Any]] = {}
        if a.cache is not None and self.user.get("cache") != a.cache:
            rows["cache"] = (self.user.get("cache"), a.cache)
        remotes = self.user.get("remotes") or {}
        for r in a.remotes:
            old = remotes.get(r.name) or {}
            conf = {k: v for k, v in old.items() if k != "enabled" or v is not False}
            conf["host"] = r.host or old.get("host") or r.name
            if r.name in a.install_remotes:
                conf.setdefault("command", REMOTE_COMMAND)
            if conf != old:
                rows[f"remotes.{r.name}"] = (old or None, conf)
        for name in a.skip_remotes:
            old = remotes.get(name) or {}
            if old.get("enabled") is not False:
                rows[f"remotes.{name}"] = (old or None, {**old, "enabled": False})
        if not rows:
            return None

        def run() -> str:
            for key, (_, value) in rows.items():
                if key == "cache":
                    write_key(self.user_file, key, value)
                else:
                    write_remote(self.user_file, key.removeprefix("remotes."), value)
            return "written"

        return Change(
            where="machine",
            label=display_path(self.user_file, self.scan.home),
            before=show_rows({k: v[0] for k, v in rows.items() if v[0] is not None}) or None,
            after=show_rows({k: v[1] for k, v in rows.items()}),
            run=run,
        )

    def remote_changes(self) -> list[Change]:
        """Plan the shared ssh logins, then the installs, both only for the hosts asked for.

        :return: The changes, last in the plan so an install can use the shared login.
        :raises ValueError: A name is no remote or host this machine knows, or no alias."""
        from beamtime import __version__
        from beamtime.setup.remotes import install_change, ssh_share_changes

        a = self.answers
        config = self.scan.home / ".ssh" / "config"
        out: list[Change] = []
        hosts: dict[str, None] = {}
        for name in a.ssh_share:
            host = self.host_of(name, "--ssh-share")
            if "@" in host:
                raise ValueError(f"--ssh-share {name}: name an alias of ~/.ssh/config, not {host}")
            hosts[host] = None
        for host in hosts:
            out += ssh_share_changes(host, config, display_path(config, self.scan.home))
        for name in dict.fromkeys(a.install_remotes):
            out.append(install_change(self.host_of(name, "--install-remote"), name, __version__))
        for item in a.update:
            if item.startswith("remote:") and (name := item.removeprefix("remote:")) not in (
                a.install_remotes
            ):
                out.append(install_change(self.host_of(name, "--update"), name, __version__))
        return out

    def host_of(self, name: str, flag: str) -> str:
        """Find the ssh host a remote name stands for.

        :param name: A remote of the answers or settings; for ``--ssh-share`` also an ssh host.
        :param flag: The flag the name came with, for the message.
        :return: The host.
        :raises ValueError: The name is none of those."""
        for r in self.answers.remotes:
            if r.name == name:
                return r.host or r.name
        mine = self.user.get("remotes") or {}
        if name in {**(self.given.get("remotes") or {}), **mine}:
            return (mine.get(name) or {}).get("host") or name
        if flag == "--ssh-share" and any(h.name == name for h in self.scan.ssh_hosts):
            return name
        raise ValueError(f"{flag} {name}: no remote of that name; add it with --remote {name}")

    def agents(self) -> list[Change]:
        """Plan the MCP registration, the skills and the rules block of every chosen client.

        :return: The changes.
        :raises ValueError: A client can't be registered."""
        from beamtime.guide.rules import read_block, render
        from beamtime.guide.skills import SKILLS, skill_text
        from beamtime.ops.registry import OPS
        from beamtime.settings import resolve_agent
        from beamtime.setup.agents import CLIENTS, ConfigError, register, rules_change

        a = self.answers
        clients = [c for name in a.agents for c in CLIENTS if c.name == name]
        updating = self.scan.flow == "update"
        has_block = {f.client for f in self.scan.agents if f.has_block}
        env = self.scan.env
        if env is not None and a.sdk and self.mcp_from_env():
            env = dataclasses.replace(env, has_serve=True)
        out = []
        for client in clients:
            try:
                change = register(client, self.root, env, home=self.scan.home, which=self.which)
            except ConfigError as e:
                raise ValueError(f"{client.label}: {e}") from e
            if change.before is None or "mcp" in a.update or client.name == "other":
                out.append(change)
            # an update changes skills and existing rules blocks only where --update says so.
            if (
                client.skills
                and (not updating or "skills" in a.update)
                and any(
                    not (self.root / ".claude" / "skills" / n / "SKILL.md").is_file()
                    or (self.root / ".claude" / "skills" / n / "SKILL.md").read_text()
                    != skill_text(n)
                    for n in SKILLS
                )
            ):
                out.append(skills_change(self.root))
        if not a.rules:
            return out
        agent = resolve_agent(self.agent_given())
        user_only = sorted(o.name for o in OPS if o.user_only)
        block = render(agent, user_only)
        for client in {c.rules: c for c in clients}.values():
            if updating and client.name in has_block:
                continue
            if read_block(self.root / client.rules) != block:
                out.append(rules_change(client, self.root, agent, user_only))
        return out

    def updates(self) -> list[Change]:
        """Plan what ``--update`` brings up to date in a setup an older release made.

        The rules and the MCP entries are rewritten where the scan found them, never added to a
        client that has none; remotes and runs go through ``remote_changes`` and ``imports``.

        :return: The changes.
        :raises ValueError: A client can't be registered."""
        from beamtime import __version__
        from beamtime.guide.rules import read_block, render
        from beamtime.ops.registry import OPS
        from beamtime.settings import resolve_agent
        from beamtime.setup.agents import ConfigError, client_named, register, rules_change
        from beamtime.setup.sdk import sdk_change
        from beamtime.setup.stale import moved_keys, stale_sdk, stale_skills

        a = self.answers
        out: list[Change] = []
        found = {f.client: client_named(f.client) for f in self.scan.agents}
        if "rules" in a.update and a.rules:
            agent = resolve_agent(self.agent_given())
            user_only = sorted(o.name for o in OPS if o.user_only)
            block = render(agent, user_only)
            files = {c.rules: c for f in self.scan.agents if f.has_block for c in [found[f.client]]}
            out += [
                rules_change(c, self.root, agent, user_only)
                for c in files.values()
                if read_block(self.root / c.rules) != block
            ]
        if "mcp" in a.update:
            for f in self.scan.agents:
                if not f.registered:
                    continue
                try:
                    out.append(
                        register(
                            found[f.client],
                            self.root,
                            self.scan.env,
                            home=self.scan.home,
                            which=self.which,
                        )
                    )
                except ConfigError as e:
                    raise ValueError(f"{found[f.client].label}: {e}") from e
        if "skills" in a.update and stale_skills(self.root) is not None:
            out.append(skills_change(self.root))
        if "settings" in a.update and (keys := moved_keys(self.root)):
            out.append(
                Change(
                    where="project",
                    label="beamtime.yaml",
                    before=f"sets {', '.join(keys)}",
                    after="removed",
                    run=partial(drop_keys, self.project_file, keys),
                )
            )
        if (
            "sdk" in a.update
            and stale_sdk(self.scan.env) is not None
            and (
                change := sdk_change(
                    self.scan.env, __version__, self.mcp_from_env(), root=self.root, upgrade=True
                )
            )
        ):
            out.append(change)
        return out

    def imports(self) -> list[Change]:
        """Plan one change per path to import runs from.

        :return: The changes.
        :raises ValueError: A path holds nothing to import or lies in this project's log dir."""
        from beamtime.setup.importers import detect

        out: list[Change] = []
        names: set[str] = set()
        for text in self.answers.imports:
            path = (self.root / expand_path(text)).resolve()
            if not path.exists():
                raise ValueError(f"--import {text}: no such file or folder")
            if path.is_relative_to((self.root / expand_path(self.logdir)).resolve()):
                raise ValueError(f"--import {text}: this is inside the project's own log dir")
            if (found := detect(path)) is None:
                raise ValueError(f"--import {text}: no runs found there")
            if found.kind == "beamtime":
                out.append(self.beamtime_import(text, path, names))
            else:
                out.append(self.runs_import(found, names))
        return out

    def beamtime_import(self, text: str, path: Path, names: set[str]) -> Change:
        """Plan copying a Beamtime log dir, with the bytes to copy in the review.

        A folder inside another log dir is imported through that log dir's root, and a project
        through its log dir, since membership keys start there.

        :param text: The path as typed.
        :param path: A log dir, a run, a folder inside a log dir, or a project.
        :param names: The folders below ``imported/`` taken by earlier imports; extended.
        :return: The change.
        :raises ValueError: The path is this project, whose own log dir it would import."""
        from beamtime.format.tree import is_run
        from beamtime.setup.importers import detect
        from beamtime.setup.importers.beamtime import Copier, copy_logdir

        source = path if is_run(path) else log_root(path)
        dest = self.root / expand_path(self.logdir)
        if source == self.root or source.is_relative_to(dest.resolve()):
            raise ValueError(f"--import {text}: this is the project's own log dir")
        found = detect(source)
        name = unique(import_name(source), names)
        size = Copier(logdir=dest, source=source, name=name).size()
        after = f"{source} -> imported/{name}/, {format_bytes(size)} copied byte for byte"
        if (path / "beamtime.yaml").is_file():
            after += f"\n{path} is a project, so its log dir is imported"
        elif source != path:
            after += f"\n{path} is inside this log dir, so all of it is imported"

        def run() -> str:
            done = copy_logdir(dest, source, name)
            return f"{done.runs} runs copied, {done.skipped} already there"

        return Change(
            where="import",
            label=found.label if found else "Beamtime runs",
            before=None,
            after=after,
            run=run,
        )

    def runs_import(self, found: "Found", names: set[str]) -> Change:
        """Plan reading another tool's runs into ``imported/<name>/``.

        :param found: What the path holds.
        :param names: The folders below ``imported/`` taken by earlier imports; extended.
        :return: The change."""
        from beamtime.setup.importers import csv, mlflow, tensorboard, wandb
        from beamtime.setup.importers.write import IMPORTED, write_run

        readers = {
            "tensorboard": tensorboard.runs,
            "wandb": wandb.runs,
            "mlflow": mlflow.runs,
            "csv": csv.runs,
        }
        read = readers[found.kind]
        name = unique(import_name(found.path), names)
        dest = self.root / expand_path(self.logdir)
        after = f"{found.path} -> {IMPORTED}/{name}/"
        if found.note:
            after += f"\n{found.note}"

        def run() -> str:
            n = 0
            for imported in read(found.path):
                group = "/".join(p for p in (IMPORTED, name, imported.group) if p)
                write_run(dest, group, imported, {"kind": found.kind, "path": str(found.path)})
                n += 1
            return f"{n} runs"

        return Change(where="import", label=found.label, before=None, after=after, run=run)

    def notes(self) -> Change | None:
        """Plan notes and memory files written as they are, unless an agent takes them over.

        :return: The change, or ``None`` without files or with ``--migrate-with``."""
        from beamtime.setup.importers import files
        from beamtime.setup.importers.notes import import_notes, read_text

        a = self.answers
        paths = [
            (self.root / expand_path(t)).resolve() for t in (*a.import_notes, *a.import_memory)
        ]
        if not paths or a.migrate_with is not None:
            return None
        for t, p in zip((*a.import_notes, *a.import_memory), paths, strict=True):
            if not p.exists():
                raise ValueError(f"--import-notes/--import-memory {t}: no such file or folder")
        texts = [f for p in paths for f in files(p)]
        skipped = [f.name for f in texts if read_text(f) is None]
        after = f"{len(texts) - len(skipped)} notes, as written"
        if skipped:
            after += f"\nbinary files skipped: {', '.join(skipped)}"

        def run() -> str:
            from beamtime.ops.context import Context

            (self.root / expand_path(self.logdir)).mkdir(parents=True, exist_ok=True)
            done = import_notes(Context.make(root=self.root, caller="cli"), paths)
            return f"{len(done.notes)} notes"

        return Change(where="import", label="notes", before=None, after=after, run=run)

    @staticmethod
    def read(path: Path) -> dict[str, Any]:
        """Read a settings file as written.

        :param path: The file.
        :return: Its mapping, empty when missing or not a mapping."""
        if not path.is_file():
            return {}
        import yaml

        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            return {}
        return data if isinstance(data, dict) else {}


def agent_value(key: str, text: str) -> Any:
    """Read the value of one ``--agent-set`` pair and check it against the key's rule.

    :param key: An agent setting.
    :param text: The value as typed.
    :return: The value, as a number where the key takes one.
    :raises ValueError: The value is not valid for the key."""
    import yaml

    from beamtime.settings import AGENT_KEYS, VALIDATOR_HINTS

    allowed = AGENT_KEYS[key]
    for value in (yaml.safe_load(text), text):
        if allowed is not None and (
            value in allowed if isinstance(allowed, tuple) else allowed(value)
        ):
            return value
    rule = (
        f"one of {', '.join(allowed)}" if isinstance(allowed, tuple) else VALIDATOR_HINTS[allowed]
    )
    raise ValueError(f"--agent-set {key}={text}: {key} is {rule}")


def skills_change(root: Path) -> Change:
    """Plan writing the Beamtime skills into ``.claude/skills``.

    :param root: The project root.
    :return: The change."""
    from beamtime.guide.skills import SKILLS, write_skills

    return Change(
        where="project",
        label=".claude/skills/",
        before=None,
        after=f"{len(SKILLS)} skills",
        run=lambda: f"{len(write_skills(root))} skills",
    )


def drop_keys(file: Path, keys: list[str]) -> None:
    """Remove top-level settings from a settings file, keeping the rest as written.

    :param file: The settings file.
    :param keys: The settings to remove."""
    from beamtime.settings import replace_entry

    for key in keys:
        replace_entry(file, key, "")


def release(version: str) -> tuple[int, ...]:
    """Read a version as numbers, so that releases compare.

    :param version: E.g. ``0.2.0``.
    :return: The leading numbers of its first three parts."""
    return tuple(int(n) for n in re.findall(r"\d+", version)[:3])


def plain_entries(logdir: str) -> set[str]:
    """List the ignore lines older setups wrote for a log dir.

    :param logdir: The log dir relative to the project.
    :return: The lines the marked block replaces."""
    name = logdir.strip("/")
    return {name, f"{name}/", f"/{name}", f"/{name}/", ".beamtime", ".beamtime/"}


def find_block(lines: list[str]) -> tuple[int, int] | None:
    """Find the marked block in the lines of a ``.gitignore``.

    :param lines: The lines.
    :return: The first line and the line after the last, or ``None``."""
    start = next((i for i, line in enumerate(lines) if line.startswith("# beamtime:")), None)
    if start is None:
        return None
    end = next((i for i in range(start, len(lines)) if lines[i] == BLOCK_END), None)
    return (start, end + 1) if end is not None else (start, start + 1)


def gitignore_text(old: str, logdir: str, mode: Literal["record", "none"]) -> str:
    """Put the marked block into a ``.gitignore``, in place of the old block and the plain entries.

    :param old: The file's text; empty when missing.
    :param logdir: The log dir relative to the project.
    :param mode: ``record`` keeps the research record in git, ``none`` ignores the whole log dir.
    :return: The new text."""
    name = logdir.strip("/")
    entries = (
        [f"{name}/**/_*", f"{name}/**/artifacts/", f"{name}/**/checkpoints/"]
        if mode == "record"
        else [f"{name}/"]
    )
    block = [BLOCK_HEADS[mode], *entries, ".beamtime/", BLOCK_END]
    lines = old.splitlines()
    span = find_block(lines)
    plain = plain_entries(logdir)
    out: list[str] = []
    placed = False
    i = 0
    while i < len(lines):
        if span and i == span[0]:
            out += block
            placed = True
            i = span[1]
        elif lines[i].strip() in plain:
            if not placed:
                out += block
                placed = True
            i += 1
        else:
            out.append(lines[i])
            i += 1
    if not placed:
        out += ["", *block] if out and out[-1] else block
    return "\n".join(out) + "\n"


def import_name(path: Path) -> str:
    """Name the folder below ``imported/`` for a source: the project's name for a log dir.

    :param path: The source.
    :return: The folder name."""
    if (path.parent / "beamtime.yaml").is_file():
        return path.parent.name
    return path.stem if path.is_file() else path.name


def unique(name: str, taken: set[str]) -> str:
    """Make a name that earlier imports of this plan don't use; records it.

    :param name: The wanted name.
    :param taken: The names in use; extended.
    :return: The name, with ``-2``, ``-3`` ... added when taken."""
    out, n = name, 1
    while out in taken:
        n += 1
        out = f"{name}-{n}"
    taken.add(out)
    return out


def log_root(path: Path) -> Path:
    """Find the root of the log dir a folder lies in, so a group is never imported as a root.

    A log dir is one this machine's index cache knows or the one a ``beamtime.yaml`` above names; a
    project's own ``beamtime.yaml`` names the log dir of a project folder.

    :param path: A folder.
    :return: The log dir's root, or the folder itself when it lies in none."""
    from beamtime.index.cache import known_logdirs
    from beamtime.setup.scan import read_project

    if (path / "beamtime.yaml").is_file():
        return read_project(path).logdir
    roots = [r.resolve() for r in known_logdirs()]
    roots += [
        read_project(parent).logdir
        for parent in path.parents
        if (parent / "beamtime.yaml").is_file()
    ]
    inside = [r for r in roots if path.is_relative_to(r)]
    return min(inside, key=lambda r: len(r.parts)) if inside else path


def format_bytes(n: int) -> str:
    """Write a size for the review.

    :param n: Bytes.
    :return: E.g. ``1.2 GB``."""
    size = float(n)
    for unit in ("B", "kB", "MB", "GB"):
        if size < 1000:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1000
    return f"{size:.1f} TB"


def show_rows(rows: dict[str, Any]) -> str:
    """Write settings as ``key: value`` lines for the review.

    :param rows: Keys and values.
    :return: One line per key."""
    import yaml

    def flow(value: Any) -> str:
        return yaml.safe_dump(value, default_flow_style=True, width=1000).splitlines()[0]

    return "\n".join(f"{k}: {flow(v)}" for k, v in rows.items())


def display_path(path: Path, home: Path) -> str:
    """Write a path with ``~`` for the home directory.

    :param path: The path.
    :param home: The home directory.
    :return: The path as shown."""
    return f"~/{path.relative_to(home)}" if path.is_relative_to(home) else str(path)


REVIEW_HEADS = {
    "project": "the project (shared through git)",
    "machine": "this machine",
    "import": "imports",
    "remote": "other machines",
}


def review(changes: list[Change]) -> list[str]:
    """Write the changes as text, grouped by where each lands.

    :param changes: The plan.
    :return: The lines."""
    out: list[str] = []
    for where, head in REVIEW_HEADS.items():
        group = [c for c in changes if c.where == where]
        if not group:
            continue
        out += [head]
        for c in group:
            out.append(f"  {c.label}")
            if c.before is not None:
                out += [f"    was: {line}" for line in c.before.splitlines()]
            out += [f"    {line}" for line in c.after.splitlines()]
        out.append("")
    return out[:-1] if out else out
