import json
from pathlib import Path

import pytest

from beamtime.views.theme import ThemeError, base, colormaps, names, pair, resolve


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A project root with a themes folder and no user themes.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: The root."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    (tmp_path / "themes").mkdir()
    return tmp_path


def write(root: Path, file: str, **theme) -> None:
    """Write a project theme.

    :param root: The project root.
    :param file: The theme's file name without ``.json``.
    :param theme: The theme's fields."""
    (root / "themes" / f"{file}.json").write_text(json.dumps({"schema": 1, **theme}))


def test_default_pair_comes_from_the_tokens(root: Path) -> None:
    """The default theme is the design system's, in both modes."""
    p = pair("beamtime", root)
    assert p["problems"] == []
    assert p["light"]["colors"]["paper"] == "#faf9f6"
    assert p["dark"]["colors"]["paper"] == "#1e1e1c"
    assert p["light"]["dashes"][0] == [] and p["light"]["dashes"][1] == [6, 3]
    assert p["light"]["stroke"] == 1.6
    # uPlot only scales whole pixel sizes on HiDPI screens.
    assert p["light"]["font"].startswith("13px ") and "IBM Plex Sans" in p["light"]["font"]


def test_a_theme_file_overrides_colors_only(root: Path) -> None:
    """A pair of files recolors the layout; what a file leaves out stays the default."""
    write(root, "atom-one-dark", name="Atom One Dark", type="dark",
          colors={"paper": "#282c34", "ink": "#abb2bf", "accent": "#61afef"})  # fmt: skip
    write(root, "atom-one-light", name="Atom One Light", type="light", colors={"paper": "#fafafa"})
    assert "atom-one" in names(root)
    p = pair("atom-one", root)
    assert p["problems"] == []
    assert p["dark"]["name"] == "Atom One Dark"
    assert p["dark"]["colors"]["paper"] == "#282c34"
    assert p["dark"]["colors"]["good"] == base("dark")["colors"]["good"]
    assert p["light"]["colors"]["paper"] == "#fafafa"


def test_a_single_file_serves_both_modes(root: Path) -> None:
    """One file is used for light and dark."""
    write(root, "solo", name="Solo", type="dark", colors={"paper": "#000000"})
    p = pair("solo", root)
    assert p["light"]["colors"]["paper"] == p["dark"]["colors"]["paper"] == "#000000"


def test_problems_are_reported_and_ignored(root: Path) -> None:
    """Unknown tokens and bad values are named; a missing theme falls back to the default."""
    write(root, "odd", name="Odd", type="light", colors={"nope": "#000000", "ink": "red"})
    t = resolve("odd", root)
    assert t["colors"]["ink"] == base("light")["colors"]["ink"]
    assert len(t["problems"]) == 2
    with pytest.raises(ThemeError, match="no theme 'gone'"):
        resolve("gone", root)
    p = pair("gone", root)
    assert "using the default theme" in p["problems"][0]
    assert p["light"]["colors"]["paper"] == "#faf9f6"


def test_ramps_are_the_built_in_defaults(root: Path) -> None:
    """The theme carries viridis and coolwarm; no setting changes them."""
    maps = colormaps()
    p = pair("beamtime", root)
    assert p["light"]["ramps"]["sequential"] == maps["sequential"]["viridis"]
    assert p["dark"]["ramps"]["diverging"] == maps["diverging"]["coolwarm"]
