"""Themes: the design system's tokens, with theme files overriding their colors, and colormaps."""

import json
import os
import re
from math import ceil
from pathlib import Path
from typing import Any, Literal

import msgspec

TOKENS = Path(__file__).parent / "tokens.json"
COLORMAPS = Path(__file__).parent / "colormaps.json"
DEFAULT = "beamtime"
DEFAULT_COLORMAPS = {"sequential": "viridis", "diverging": "coolwarm"}
HEX = re.compile(r"#[0-9a-fA-F]{6}")


class ThemeError(Exception):
    """A theme that can't be loaded."""


class ThemeFile(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """One theme file as written."""

    schema: int
    name: str
    type: Literal["light", "dark"]
    colors: dict[str, str] = msgspec.field(default_factory=dict)


def tokens() -> dict[str, Any]:
    """Read the design tokens.

    :return: The contents of ``tokens.json``."""
    return json.loads(TOKENS.read_text())


def colormaps() -> dict[str, dict[str, list[str]]]:
    """Read the colormaps sampled from matplotlib.

    :return: ``sequential`` and ``diverging``, each a colormap's name to its colors."""
    data = json.loads(COLORMAPS.read_text())
    return {kind: data[kind] for kind in DEFAULT_COLORMAPS}


def theme_dirs(root: Path | None) -> list[Path]:
    """List where theme files come from, later ones overriding earlier ones.

    :param root: The project root, or ``None``.
    :return: The user and project theme folders."""
    base = os.environ.get("XDG_CONFIG_HOME")
    user = (Path(base) if base else Path.home() / ".config") / "beamtime" / "themes"
    return [user] + ([root / "themes"] if root is not None else [])


def available(root: Path | None) -> dict[str, Path]:
    """Find every theme file by name.

    :param root: The project root, or ``None``.
    :return: Theme name (the file name without ``.json``) to its path."""
    out: dict[str, Path] = {}
    for d in theme_dirs(root):
        if d.is_dir():
            out |= {p.stem: p for p in sorted(d.glob("*.json"))}
    return out


def names(root: Path | None) -> list[str]:
    """List the themes a ``theme`` setting can name: a pair by its name without the suffix.

    :param root: The project root, or ``None``.
    :return: The sorted names, the default included."""
    return sorted({DEFAULT} | {re.sub(r"-(light|dark)$", "", n) for n in available(root)})


def read(path: Path) -> ThemeFile:
    """Read and validate a theme file.

    :param path: The file.
    :return: The theme as written."""
    try:
        return msgspec.json.decode(path.read_bytes(), type=ThemeFile)
    except (OSError, msgspec.DecodeError, msgspec.ValidationError) as e:
        raise ThemeError(f"theme {path}: {e}") from None


def base(kind: Literal["light", "dark"], t: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve the default theme of a type: what every theme starts from.

    :param kind: ``light`` or ``dark``.
    :param t: The design tokens, when already read.
    :return: ``name``, ``type``, ``colors``, ``dashes``, ``stroke`` and ``font``."""
    t = t if t is not None else tokens()
    small = next(s for g in t["type"]["groups"] for s in g["styles"] if s["name"] == "small")
    dash = [x["value"] for x in t["dash"]["tokens"]]
    stroke = next(x["value"] for x in t["stroke"]["tokens"] if x["name"] == "stroke-data")
    # whole pixels: uPlot scales fonts with /(\d+)px/, which reads 12.5px as 5px on HiDPI screens.
    size = ceil(float(small["fontSize"].removesuffix("px")))
    return {
        "name": f"Beamtime {kind.capitalize()}",
        "type": kind,
        "colors": {c["name"]: c["value"][kind] for c in t["color"]["tokens"]},
        "dashes": [[] if d == "none" else [float(x) for x in d.split()] for d in dash],
        "stroke": float(stroke.removesuffix("px")),
        "font": f"{size}px {t['type']['families']['sans']}",
    }


def resolve(name: str, root: Path | None) -> dict[str, Any]:
    """Resolve a theme: its colors over the defaults of its type.

    :param name: The theme's name, or ``beamtime-light`` and ``beamtime-dark`` for the defaults.
    :param root: The project root, or ``None``.
    :return: :func:`base`'s keys and ``problems``."""
    files = available(root)
    if name in (f"{DEFAULT}-light", f"{DEFAULT}-dark") and name not in files:
        return base(name.removeprefix(f"{DEFAULT}-")) | {"problems": []}  # type: ignore[arg-type]
    if name not in files:
        raise ThemeError(f"no theme {name!r}; themes: {', '.join(names(root))}")
    theme = read(files[name])
    out = base(theme.type)
    problems = []
    for token, value in theme.colors.items():
        if token not in out["colors"]:
            problems.append(f"theme {name!r}: unknown color {token!r}")
        elif not HEX.fullmatch(value):
            problems.append(f"theme {name!r}: {token} must be #rrggbb, not {value!r}")
        else:
            out["colors"][token] = value
    return out | {"name": theme.name, "problems": problems}


def ramps(sequential: str | None, diverging: str | None) -> tuple[dict[str, list[str]], list[str]]:
    """Look up the colors of the chosen colormaps.

    :param sequential: The ``colormap`` setting.
    :param diverging: The ``colormap_diverging`` setting.
    :return: ``sequential`` and ``diverging`` colors, and problems with unknown names."""
    maps = colormaps()
    chosen = {"sequential": sequential, "diverging": diverging}
    out: dict[str, list[str]] = {}
    problems = []
    for kind, name in chosen.items():
        if name is not None and name not in maps[kind]:
            problems.append(f"no {kind} colormap {name!r}; using {DEFAULT_COLORMAPS[kind]}")
            name = None
        out[kind] = maps[kind][name or DEFAULT_COLORMAPS[kind]]
    return out, problems


def pair(
    setting: str,
    root: Path | None,
    colormap: str | None = None,
    colormap_diverging: str | None = None,
) -> dict[str, Any]:
    """Resolve the light and dark variant a ``theme`` setting names, with the chosen colormaps.

    ``beamtime`` names the design system's own pair; the name of a pair of files ``x-light`` and
    ``x-dark`` names both; the name of a single theme file is used for both modes.

    :param setting: The ``theme`` setting.
    :param root: The project root, or ``None``.
    :param colormap: The sequential colormap's name.
    :param colormap_diverging: The diverging colormap's name.
    :return: ``{light, dark, problems}``; on errors the default pair with the problem."""
    files = available(root)
    if setting == DEFAULT or (f"{setting}-light" in files and f"{setting}-dark" in files):
        chosen = {"light": f"{setting}-light", "dark": f"{setting}-dark"}
    else:
        chosen = {"light": setting, "dark": setting}
    try:
        out = {mode: resolve(n, root) for mode, n in chosen.items()}
        problems = sorted({p for t in out.values() for p in t.pop("problems")})
    except ThemeError as e:
        out = {"light": base("light"), "dark": base("dark")}
        problems = [f"{e}; using the default theme"]
    scales, missing = ramps(colormap, colormap_diverging)
    return {mode: t | {"ramps": scales} for mode, t in out.items()} | {
        "problems": problems + missing
    }
