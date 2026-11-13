"""What ``beamtime init`` changes: the answers, the changes and the command."""

import shlex
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import msgspec

if TYPE_CHECKING:
    from beamtime.ops.registry import InitParams
    from beamtime.setup.scan import Scan

PATH_START = ("/", "~", "$")
UPDATE_ITEMS = ("rules", "mcp", "skills", "settings", "sdk")


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
        if not name:
            raise ValueError(f"--remote {text!r}: no name")
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

        :param scan: The facts of the project and the machine.
        :return: The answers without any flag."""
        logdir = scan.project.logdir
        inside = logdir.is_relative_to(scan.root.resolve())
        return cls(
            logdir=logdir.relative_to(scan.root.resolve()).as_posix() if inside else str(logdir),
            update=list(scan.stale),
        )

    @classmethod
    def from_params(cls, p: "InitParams", scan: "Scan") -> "Answers":
        """Fill the answers from the flags, and what a flag leaves open from the scan.

        :param p: The parameters of ``init``.
        :param scan: The facts of the project and the machine.
        :return: The answers.
        :raises ValueError: A flag value is malformed, or two flags contradict each other."""
        from beamtime.settings import AGENT_KEYS
        from beamtime.setup.agents import CLIENTS

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
        for item in filter(None, p.agent_set):
            key, sep, value = item.partition("=")
            if not sep or key not in AGENT_KEYS:
                raise ValueError(
                    f"--agent-set {item!r}: write KEY=VALUE with a key of {', '.join(AGENT_KEYS)}"
                )
            agent_set[key] = value
        return cls(
            runs=p.runs or base.runs,
            logdir=p.logdir or base.logdir,
            link_logdir=p.link_logdir,
            remotes=[Remote.parse(t) for t in p.remote],
            skip_remotes=list(p.skip_remote),
            install_remotes=list(p.install_remote),
            ssh_share=list(p.ssh_share),
            cache=p.cache,
            agents=[a for a in p.agents if a],
            agent_style=p.agent_style or base.agent_style,
            agent_set=agent_set,
            rules=base.rules and not p.no_rules or p.instructions,
            imports=list(p.import_),
            import_notes=list(p.import_notes),
            import_memory=list(p.import_memory),
            git=p.git or base.git,
            sdk=p.sdk or base.sdk and not p.no_sdk,
            role=p.role or base.role,
            update=base.update if p.update is None else [u for u in p.update if u],
            migrate_with=p.migrate_with,
        )


def flags(answers: Answers, scan: "Scan") -> list[str]:
    """List the flags that turn the scan's defaults into the answers, in flag table order.

    :param answers: The answers.
    :param scan: The facts the defaults come from.
    :return: One string per flag, its value quoted for a shell."""
    base = Answers.defaults(scan)
    out = []
    for f in msgspec.structs.fields(Answers):
        value, default = getattr(answers, f.name), getattr(base, f.name)
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
                pairs = ",".join(f"{k}={v}" for k, v in value.items())
                out.append(f"--agent-set {shlex.quote(pairs)}")
            case "rules":
                out.append("--no-rules")
            case "imports":
                out += [f"--import {shlex.quote(v)}" for v in value]
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
    """Write the ``beamtime init --yes`` command that makes the same plan, one flag to a line.

    :param answers: The answers.
    :param scan: The facts the defaults come from.
    :return: The command as a shell line with ``\\`` continuations."""
    words = ["beamtime init --yes", *flags(answers, scan)]
    return " \\\n  ".join(words)
