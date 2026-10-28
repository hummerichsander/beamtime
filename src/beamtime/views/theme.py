"""Themes: token files with light and dark variants, ``extends`` and shell fallbacks."""

import os
from pathlib import Path
from typing import Any, Literal

import msgspec

BUILTIN = Path(__file__).parent / "themes"
DEFAULT = {"light": "beamtime-light", "dark": "beamtime-dark"}
CORE = (
    "bg", "surface", "surface-raised", "border", "grid", "fg", "muted", "subtle", "link",
    "accent", "selection", "dim", "good", "bad", "warn", "info",
    "running", "finished", "failed", "killed", "lost",
)  # fmt: skip
# shell token -> core token it falls back to; modelled on VS Code's workbench colors.
SHELL = {
    "sidebar.bg": "surface",
    "sidebar.fg": "fg",
    "topbar.bg": "bg",
    "statusbar.bg": "surface",
    "statusbar.fg": "muted",
    "list.active": "selection",
    "list.hover": "surface-raised",
    "input.bg": "bg",
    "input.border": "border",
    "button.bg": "accent",
    "button.fg": "bg",
    "badge.bg": "surface-raised",
    "badge.fg": "fg",
    "focus": "accent",
    "tooltip.bg": "surface-raised",
    "scrollbar": "border",
}
SECTIONS = ("data", "fonts", "sizes", "shape")


class ThemeError(Exception):
    """A theme that can't be loaded."""


class ThemeFile(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """One theme file as written."""

    schema: int
    name: str
    type: Literal["light", "dark"]
    extends: str | None = None
    colors: dict[str, str | float] = msgspec.field(default_factory=dict)
    data: dict[str, Any] = msgspec.field(default_factory=dict)
    fonts: dict[str, str] = msgspec.field(default_factory=dict)
    sizes: dict[str, float] = msgspec.field(default_factory=dict)
    shape: dict[str, Any] = msgspec.field(default_factory=dict)


def theme_dirs(root: Path | None) -> list[Path]:
    """List where themes come from, later ones overriding earlier ones.

    :param root: The project root, or ``None``.
    :return: The built-in, user and project theme folders."""
    base = os.environ.get("XDG_CONFIG_HOME")
    user = (Path(base) if base else Path.home() / ".config") / "beamtime" / "themes"
    return [BUILTIN, user] + ([root / "themes"] if root is not None else [])


def available(root: Path | None) -> dict[str, Path]:
    """Find every theme file by name.

    :param root: The project root, or ``None``.
    :return: Theme name (the file name without ``.json``) to its path."""
    out: dict[str, Path] = {}
    for d in theme_dirs(root):
        if d.is_dir():
            out |= {p.stem: p for p in sorted(d.glob("*.json"))}
    return out


def read(path: Path) -> ThemeFile:
    """Read and validate a theme file.

    :param path: The file.
    :return: The theme as written."""
    try:
        return msgspec.json.decode(path.read_bytes(), type=ThemeFile)
    except (OSError, msgspec.DecodeError, msgspec.ValidationError) as e:
        raise ThemeError(f"theme {path}: {e}") from None


def resolve(name: str, root: Path | None) -> dict[str, Any]:
    """Resolve a theme: its ``extends`` chain, the default of its type, shell fallbacks.

    :param name: The theme name.
    :param root: The project root, or ``None``.
    :return: ``name``, ``type``, ``colors`` (core and shell tokens), ``data``, ``fonts``,
        ``sizes``, ``shape`` and ``problems``."""
    files = available(root)
    chain = load_chain(name, files)
    kind = chain[0][1].type
    if DEFAULT[kind] not in (n for n, _ in chain):
        chain += load_chain(DEFAULT[kind], files)
    problems = [
        f"theme {n!r}: unknown color {k!r}"
        for n, t in chain
        for k in t.colors
        if k not in CORE and k not in SHELL
    ]
    colors: dict[str, Any] = {}
    for _, t in reversed(chain):
        colors |= {k: v for k, v in t.colors.items() if k in CORE}
    # shell tokens come from the user's own files, else from that theme's core colors.
    own = [t for n, t in chain if n not in DEFAULT.values()]
    for token, core in SHELL.items():
        given = next((t.colors[token] for t in own if token in t.colors), None)
        colors[token] = given if given is not None else colors[core]
    out: dict[str, Any] = {"name": chain[0][1].name, "type": kind, "colors": colors}
    for section in SECTIONS:
        merged: dict[str, Any] = {}
        for _, t in reversed(chain):
            merged |= getattr(t, section)
        out[section] = merged
    return out | {"problems": problems}


def load_chain(name: str, files: dict[str, Path]) -> list[tuple[str, ThemeFile]]:
    """Load a theme and the themes it extends.

    :param name: The theme name.
    :param files: The available themes.
    :return: ``(name, theme)`` pairs, the named theme first."""
    chain: list[tuple[str, ThemeFile]] = []
    current: str | None = name
    while current is not None:
        if current in (n for n, _ in chain):
            raise ThemeError(f"theme {name!r}: extends forms a cycle at {current!r}")
        if current not in files:
            raise ThemeError(f"no theme {current!r}; themes: {', '.join(sorted(files))}")
        chain.append((current, read(files[current])))
        current = chain[-1][1].extends
    return chain


def pair(setting: str, root: Path | None) -> dict[str, Any]:
    """Resolve the light and dark variant a ``theme`` setting names.

    ``beamtime`` names ``beamtime-light`` and ``beamtime-dark``; the name of a single
    theme file is used for both modes.

    :param setting: The ``theme`` setting.
    :param root: The project root, or ``None``.
    :return: ``{light, dark, problems}``; on errors the default pair with the problem."""
    files = available(root)
    if f"{setting}-light" in files and f"{setting}-dark" in files:
        names = {"light": f"{setting}-light", "dark": f"{setting}-dark"}
    else:
        names = {"light": setting, "dark": setting}
    try:
        out = {mode: resolve(n, root) for mode, n in names.items()}
        problems = sorted({p for t in out.values() for p in t.pop("problems")})
    except ThemeError as e:
        out = {mode: resolve(n, None) for mode, n in DEFAULT.items()}
        problems = [f"{e}; using the default theme"]
        for t in out.values():
            t.pop("problems")
    return out | {"problems": problems}
