"""Settings in levels, like VS Code: built-in, user, project, then flags."""

import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Level = Literal["built-in", "user", "project", "flag"]

DEFAULTS: dict[str, Any] = {
    "logdir": "beamtime",
    "theme": "beamtime",
    # system, light or dark: the web UI's mode, unless a viewer picks another for themselves.
    "theme_mode": "system",
    # matplotlib style sheets for figures (scienceplots' and matplotlib's), as for plt.style.use.
    "figure_style": ["science", "nature"],
    # a folder (with {user}, ${VAR}, ~) or "memory"; None means the user cache dir.
    "cache": None,
    # project-only: a style plus overrides of the knobs in AGENT_KEYS.
    "agent": None,
    "remotes": {},
}
# what `beamtime set` (and the web UI's settings page) may write into beamtime.yaml.
SETTABLE = ("theme", "theme_mode", "figure_style")
MOVED = ("colormap", "colormap_diverging")
REMOTE_KEYS = ("host", "command", "cache", "path", "transport", "enabled")
PROJECT_ONLY = ("logdir", "agent")

STYLES = ("careful", "hands-on", "analysis", "custom")
PRESETS: dict[str, dict[str, Any]] = {
    "careful": {
        "launch_runs": "ask",
        "memory_updates": "after_verdicts",
        "save_views": "save",
        "research_record": "encouraged",
        "seeds": 3,
        "significance": 0.95,
        "memory_tokens": 1500,
        "proposal_words": 150,
        "render_rounds": 2,
        "custom_blocks": "builtin_first",
        "mcp_tools": "core",
    },
    "hands-on": {
        "launch_runs": "allowed",
        "memory_updates": "after_verdicts",
        "save_views": "save",
        "research_record": "encouraged",
        "seeds": 3,
        "significance": 0.95,
        "memory_tokens": 1500,
        "proposal_words": 150,
        "render_rounds": 2,
        "custom_blocks": "builtin_first",
        "mcp_tools": "core",
    },
    "analysis": {
        "launch_runs": "ask",
        "memory_updates": "suggest",
        "save_views": "save",
        "research_record": "off",
        "seeds": 3,
        "significance": 0.95,
        "memory_tokens": 1500,
        "proposal_words": 150,
        "render_rounds": 2,
        "custom_blocks": "builtin_first",
        "mcp_tools": "core",
    },
}
PRESETS["custom"] = PRESETS["careful"]


def positive_int(value: Any) -> bool:
    """Check for an integer of at least 1 (booleans don't count).

    :param value: The candidate.
    :return: Whether it is one."""
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def probability(value: Any) -> bool:
    """Check for a number strictly between 0 and 1.

    :param value: The candidate.
    :return: Whether it is one."""
    return isinstance(value, int | float) and not isinstance(value, bool) and 0 < value < 1


def nonempty_str(value: Any) -> bool:
    """Check for a non-empty string.

    :param value: The candidate.
    :return: Whether it is one."""
    return isinstance(value, str) and bool(value.strip())


# each knob's allowed values, or a validator; the last four are the user's conventions.
AGENT_KEYS: dict[str, tuple[str, ...] | Callable[[Any], bool]] = {
    "launch_runs": ("never", "ask", "allowed"),
    "memory_updates": ("suggest", "after_verdicts"),
    "save_views": ("draft", "save"),
    "research_record": ("off", "encouraged", "required"),
    "seeds": positive_int,
    "significance": probability,
    "memory_tokens": positive_int,
    "proposal_words": positive_int,
    "render_rounds": positive_int,
    "custom_blocks": ("builtin_first", "free"),
    "mcp_tools": ("core", "all"),
    "main_metric": nonempty_str,
    "direction": ("min", "max"),
    "seed_key": nonempty_str,
    "domain": ("ml", "simulation"),
}
VALIDATOR_HINTS: dict[Callable[[Any], bool], str] = {
    positive_int: "an integer of at least 1",
    probability: "a number between 0 and 1",
    nonempty_str: "a non-empty string",
}


def expand_path(path: str, user: str | None = None) -> str:
    """Expand a configured path on this machine: ``{user}``, ``${VAR}`` and ``~``.

    :param path: The path as configured, e.g. ``/scratch/{user}/beamtime``.
    :param user: The user name for ``{user}``; default the current user.
    :return: The path."""
    import getpass

    name = user or getpass.getuser()
    return str(Path(os.path.expandvars(path.replace("{user}", name))).expanduser())


def user_settings_path() -> Path:
    """Locate the user settings file.

    :return: ``$XDG_CONFIG_HOME/beamtime/settings.yaml`` or ``~/.config/...``."""
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / "beamtime" / "settings.yaml"


@dataclass(frozen=True, kw_only=True)
class AgentSettings:
    """The agent knobs of a project, resolved from the style and the project's overrides."""

    style: str
    launch_runs: str
    memory_updates: str
    save_views: str
    research_record: str
    seeds: int
    significance: float
    memory_tokens: int
    proposal_words: int
    render_rounds: int
    custom_blocks: str
    mcp_tools: str
    main_metric: str | None = None
    direction: str | None = None
    seed_key: str | None = None
    domain: str | None = None
    source: dict[str, Literal["default", "preset", "project"]] = field(default_factory=dict)


@dataclass(kw_only=True)
class Settings:
    """The effective settings, each value with the level it came from."""

    values: dict[str, Any] = field(default_factory=dict)
    levels: dict[str, Level] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Read a top-level setting.

        :param key: E.g. ``logdir``.
        :param default: Returned when the key is missing.
        :return: The value."""
        return self.values.get(key, default)

    @property
    def remotes(self) -> dict[str, dict]:
        """The remotes this machine uses: those not switched off with ``enabled: false``.

        :return: Remote name to its fields."""
        return {
            name: conf
            for name, conf in (self.values.get("remotes") or {}).items()
            if isinstance(conf, dict) and conf.get("enabled", True)
        }

    @property
    def agent(self) -> AgentSettings:
        """The agent knobs: the style's preset, then the project's single keys.

        :return: The resolved knobs, each with where it came from."""
        return resolve_agent(self.values.get("agent") or {})

    def flat(self) -> list[tuple[str, Any, Level]]:
        """List every leaf setting with its level, for ``beamtime settings``.

        :return: ``(dotted key, value, level)`` sorted by key."""
        out = []

        def walk(prefix: str, value: Any) -> None:
            if isinstance(value, dict) and value:
                for k, v in value.items():
                    walk(f"{prefix}.{k}" if prefix else k, v)
            else:
                out.append((prefix, value, self.levels.get(prefix, "built-in")))

        walk("", self.values)
        return sorted(out)


def resolve_agent(given: dict[str, Any]) -> AgentSettings:
    """Resolve the agent knobs: the style's preset, then the single keys.

    :param given: The ``agent`` setting as written (valid values only), possibly empty.
    :return: The resolved knobs, each with where it came from."""
    style = given.get("style", "careful")
    knobs = dict(PRESETS[style])
    source = dict.fromkeys(knobs, "preset" if "style" in given else "default")
    for key in AGENT_KEYS:
        if key in given:
            knobs[key] = given[key]
            source[key] = "project"
    return AgentSettings(style=style, **knobs, source=source)


def read_level(path: Path, level: Level, problems: list[str]) -> dict[str, Any]:
    """Read one settings file, reporting misplaced and unknown keys.

    :param path: The file; missing files are empty.
    :param level: ``user`` or ``project``.
    :param problems: Collects problems found.
    :return: The file's settings without ``schema``."""
    if not path.is_file():
        return {}
    # PyYAML costs about 20 ms to import; only pay for it when there is a file.
    import yaml

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        problems.append(f"{path}: not valid YAML ({e}); ignored")
        return {}
    if not isinstance(data, dict):
        problems.append(f"{path}: expected a mapping; ignored")
        return {}
    data.pop("schema", None)
    for key in list(data):
        if key in MOVED:
            problems.append(
                f"{path}: {key} moved to the chart settings; this key no longer does anything"
            )
            del data[key]
        elif key not in DEFAULTS:
            problems.append(f"{path}: unknown setting {key!r}; known: {', '.join(DEFAULTS)}")
        elif level == "user" and key in PROJECT_ONLY:
            problems.append(f"{path}: {key!r} belongs in the project's beamtime.yaml; ignored")
            del data[key]
    if "figure_style" in data and not (
        isinstance(data["figure_style"], list)
        and all(isinstance(x, str) for x in data["figure_style"])
    ):
        problems.append(
            f"{path}: figure_style is a list of style names, e.g. [science, nature]; ignored"
        )
        del data["figure_style"]
    if "cache" in data and not (isinstance(data["cache"], str) and data["cache"].strip()):
        problems.append(f"{path}: cache is a folder or memory; ignored")
        del data["cache"]
    if data.get("theme_mode", "system") not in ("system", "light", "dark"):
        problems.append(f"{path}: theme_mode is system, light or dark; ignored")
        del data["theme_mode"]
    if "agent" in data:
        data["agent"] = check_agent(path, data["agent"], problems)
    for name, remote in (data.get("remotes") or {}).items():
        if not isinstance(remote, dict):
            problems.append(f"{path}: remote {name!r} must be a mapping")
            continue
        for key in remote:
            if key not in REMOTE_KEYS:
                problems.append(
                    f"{path}: remote {name!r} has unknown key {key!r}; "
                    f"known: {', '.join(REMOTE_KEYS)}"
                )
        if not isinstance(remote.get("enabled", True), bool):
            problems.append(f"{path}: remote {name!r}: enabled is true or false; ignored")
            del remote["enabled"]
    return data


def check_agent(path: Path, agent: Any, problems: list[str]) -> dict[str, Any] | None:
    """Keep the valid parts of the ``agent`` setting, reporting the rest.

    :param path: The settings file.
    :param agent: The value as written.
    :param problems: Collects problems found.
    :return: The style and knobs that are valid, or ``None`` without any."""
    if not isinstance(agent, dict):
        problems.append(f"{path}: agent is a mapping with a style and knobs; ignored")
        return None
    out = {}
    for key, value in agent.items():
        allowed = STYLES if key == "style" else AGENT_KEYS.get(key)
        if allowed is None:
            problems.append(
                f"{path}: unknown agent setting {key!r}; known: style, {', '.join(AGENT_KEYS)}"
            )
        elif isinstance(allowed, tuple):
            if value in allowed:
                out[key] = value
            else:
                problems.append(
                    f"{path}: agent.{key} is one of {', '.join(allowed)}, not {value!r}; "
                    "using the preset"
                )
        elif allowed(value):
            out[key] = value
        else:
            problems.append(
                f"{path}: agent.{key} is {VALIDATOR_HINTS[allowed]}, not {value!r}; "
                "using the preset"
            )
    return out or None


def merge(
    base: dict[str, Any],
    top: dict[str, Any],
    level: Level,
    levels: dict,
    prefix: str = "",
) -> dict[str, Any]:
    """Merge a level onto the ones below it, key by key.

    :param base: The merged lower levels.
    :param top: This level's settings.
    :param level: This level's name.
    :param levels: Collects the level of every leaf.
    :param prefix: The dotted path so far.
    :return: The merged settings."""
    out = dict(base)
    for k, v in top.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = merge(out[k], v, level, levels, path)
        else:
            out[k] = v
            for leaf in [p for p in levels if p == path or p.startswith(f"{path}.")]:
                del levels[leaf]
            mark(path, v, level, levels)
    return out


def mark(path: str, value: Any, level: Level, levels: dict) -> None:
    """Record the level of a value and every leaf below it.

    :param path: The dotted key.
    :param value: The value.
    :param level: The level it came from.
    :param levels: The provenance map."""
    if isinstance(value, dict) and value:
        for k, v in value.items():
            mark(f"{path}.{k}", v, level, levels)
    else:
        levels[path] = level


def load(root: Path | None, flags: dict[str, Any] | None = None) -> Settings:
    """Load the effective settings of a project.

    :param root: The project root holding ``beamtime.yaml``, or ``None``.
    :param flags: Settings given on the command line.
    :return: The merged settings with provenance and problems."""
    problems: list[str] = []
    levels: dict[str, Level] = {}
    values: dict[str, Any] = {}
    values = merge(values, DEFAULTS, "built-in", levels)
    values = merge(values, read_level(user_settings_path(), "user", problems), "user", levels)
    if root is not None:
        project = read_level(root / "beamtime.yaml", "project", problems)
        values = merge(values, project, "project", levels)
    values = merge(values, flags or {}, "flag", levels)
    return Settings(values=values, levels=levels, problems=problems)


def write_project(root: Path, key: str, value: Any) -> Path:
    """Set one top-level setting in the project's ``beamtime.yaml``, keeping the rest as written.

    :param root: The project root.
    :param key: The setting, one of ``SETTABLE``.
    :param value: Its value.
    :return: The file."""
    return write_key(root / "beamtime.yaml", key, value)


def write_key(path: Path, key: str, value: Any) -> Path:
    """Set one top-level setting in a settings file, keeping the rest as written.

    :param path: The settings file (user or project), created if missing.
    :param key: The setting.
    :param value: Its value.
    :return: The file."""
    import yaml

    # flow style keeps a list on one line ([science, nature]); dumping it inside a list leaves the
    # value without YAML's document end marker.
    flow = yaml.safe_dump([value], default_flow_style=True, allow_unicode=True).strip()
    return replace_entry(path, key, f"{key}: {flow[1:-1]}\n")


def write_agent(path: Path, agent: dict[str, Any]) -> Path:
    """Set the ``agent`` setting of a project's ``beamtime.yaml`` as a block, keeping the rest.

    :param path: The project settings file, created if missing.
    :param agent: The style and the knobs that differ from its preset.
    :return: The file."""
    import yaml

    entry = yaml.safe_dump({"agent": agent}, sort_keys=False, allow_unicode=True)
    return replace_entry(path, "agent", entry)


def replace_entry(path: Path, key: str, entry: str) -> Path:
    """Put a top-level entry into a settings file in place of the key's old block.

    :param path: The settings file, created if missing.
    :param key: The top-level key.
    :param entry: The key's new text, ending in a newline.
    :return: The file."""
    import re

    from beamtime.format.io import write_bytes_replaced

    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.is_file() else "schema: 1\n"
    lines = text.splitlines(keepends=True)
    start = next(
        (i for i, line in enumerate(lines) if re.match(rf"{re.escape(key)}\s*:", line)), None
    )
    if start is None:
        text = text + ("" if text.endswith("\n") else "\n") + entry
    else:
        # the key's block: its line and the indented or blank lines after it.
        end = start + 1
        while end < len(lines) and (
            lines[end].startswith((" ", "\t", "-")) or not lines[end].strip()
        ):
            end += 1
        text = "".join([*lines[:start], entry, *lines[end:]])
    # replaced, not rewritten: writes at once can't interleave; a reader never sees half a file.
    write_bytes_replaced(path, text.encode())
    return path


def write_remote(path: Path, name: str, conf: dict[str, Any]) -> Path:
    """Add or update one remote in a settings file, keeping the rest of it as written.

    :param path: The settings file (user or project), created if missing.
    :param name: The remote's name.
    :param conf: Its fields (``host``, ``command``, ``cache``, ``path``); ``None`` values are
        left out.
    :return: The file."""
    import yaml

    data = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path.is_file() else {}
    remotes = dict(data.get("remotes") or {})
    remotes[name] = {k: v for k, v in conf.items() if v is not None}
    return write_key(path, "remotes", remotes)


def remove_remote(path: Path, name: str) -> bool:
    """Remove one remote from a settings file, keeping the rest of it as written.

    :param path: The settings file.
    :param name: The remote's name.
    :return: Whether it was there."""
    import yaml

    if not path.is_file():
        return False
    remotes = dict((yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("remotes") or {})
    if remotes.pop(name, None) is None:
        return False
    write_key(path, "remotes", remotes)
    return True
