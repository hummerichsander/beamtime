"""Settings in levels, like VS Code: built-in, user, project, then flags."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

Level = Literal["built-in", "user", "project", "flag"]

DEFAULTS: dict[str, Any] = {
    "logdir": "beamtime",
    "theme": "beamtime",
    # system, light or dark: the web UI's mode, unless a viewer picks another for themselves.
    "theme_mode": "system",
    # the matplotlib colormaps of numeric groups and heatmaps: sequential, and around a center.
    "colormap": "viridis",
    "colormap_diverging": "coolwarm",
    # matplotlib style sheets for figures (scienceplots' and matplotlib's), as for plt.style.use.
    "figure_style": ["science", "nature"],
    "remotes": {},
}
# what `beamtime set` (and the web UI's settings page) may write into beamtime.yaml.
SETTABLE = ("theme", "theme_mode", "colormap", "colormap_diverging", "figure_style")
REMOTE_KEYS = ("host", "command", "cache", "path", "transport")
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
    if "figure_style" in data and not (
        isinstance(data["figure_style"], list)
        and all(isinstance(x, str) for x in data["figure_style"])
    ):
        problems.append(
            f"{path}: figure_style is a list of style names, e.g. [science, nature]; ignored"
        )
        del data["figure_style"]
    if data.get("theme_mode", "system") not in ("system", "light", "dark"):
        problems.append(f"{path}: theme_mode is system, light or dark; ignored")
        del data["theme_mode"]
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


def write_project(root: Path, key: str, value: Any) -> Path:
    """Set one top-level setting in the project's ``beamtime.yaml``, keeping the rest as written.

    :param root: The project root.
    :param key: The setting, one of ``SETTABLE``.
    :param value: Its value.
    :return: The file."""
    import re

    import yaml

    path = root / "beamtime.yaml"
    text = path.read_text() if path.is_file() else "schema: 1\n"
    # flow style keeps a list on one line ([science, nature]); dumping it inside a list leaves the
    # value without YAML's document end marker.
    flow = yaml.safe_dump([value], default_flow_style=True, allow_unicode=True).strip()
    entry = f"{key}: {flow[1:-1]}\n"
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
    path.write_text(text)
    return path
