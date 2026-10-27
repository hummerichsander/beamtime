"""Settings in levels, like VS Code: built-in, user, project, then flags."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Level = Literal["built-in", "user", "project", "flag"]

DEFAULTS: dict[str, Any] = {"logdir": "beamtime", "theme": "beamtime", "remotes": {}}
REMOTE_KEYS = ("host", "command", "cache", "path")
PROJECT_ONLY = ("logdir",)


def user_settings_path() -> Path:
    """Locate the user settings file.

    :return: ``$XDG_CONFIG_HOME/beamtime/settings.yaml`` or ``~/.config/...``."""
    base = os.environ.get("XDG_CONFIG_HOME")
    return (Path(base) if base else Path.home() / ".config") / "beamtime" / "settings.yaml"


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
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        problems.append(f"{path}: not valid YAML ({e}); ignored")
        return {}
    if not isinstance(data, dict):
        problems.append(f"{path}: expected a mapping; ignored")
        return {}
    data.pop("schema", None)
    for key in list(data):
        if key not in DEFAULTS:
            problems.append(f"{path}: unknown setting {key!r}; known: {', '.join(DEFAULTS)}")
        elif level == "user" and key in PROJECT_ONLY:
            problems.append(f"{path}: {key!r} belongs in the project's beamtime.yaml; ignored")
            del data[key]
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
    return data


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
