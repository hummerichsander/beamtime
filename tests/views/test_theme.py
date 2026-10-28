import json
from pathlib import Path

import pytest

from beamtime.views.theme import CORE, SHELL, ThemeError, pair, resolve


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


def test_default_pair_is_complete(root: Path) -> None:
    """Both default variants define every core and shell token."""
    themes = pair("beamtime", root)
    assert themes["problems"] == []
    for mode in ("light", "dark"):
        t = themes[mode]
        assert t["type"] == mode
        assert set(CORE) | set(SHELL) == set(t["colors"])
        assert len(t["data"]["categorical"]) == 8 and t["fonts"]["serif"]
    assert themes["dark"]["sizes"] == themes["light"]["sizes"]


def test_a_dozen_colors_make_a_theme(root: Path) -> None:
    """Missing tokens come from the default of the same type; the shell follows own colors."""
    write(root, "night", name="Night", type="dark", colors={"bg": "#000000", "surface": "#111111",
                                                             "accent": "#ff8800"})  # fmt: skip
    t = resolve("night", root)
    assert t["colors"]["bg"] == "#000000" and t["colors"]["fg"] == "#eceae4"
    assert t["colors"]["sidebar.bg"] == "#111111" and t["colors"]["focus"] == "#ff8800"
    assert t["data"]["categorical"][0] == "#3987e5"
    assert t["problems"] == []


def test_extends_and_explicit_shell_tokens(root: Path) -> None:
    """A theme extends another; explicit shell tokens win over the fallback."""
    write(root, "base", name="Base", type="light", colors={"accent": "#123456"})
    write(root, "child", name="Child", type="light", extends="base",
          colors={"sidebar.bg": "#eeeeee", "bogus": "#000"})  # fmt: skip
    t = resolve("child", root)
    assert t["colors"]["accent"] == "#123456" and t["colors"]["button.bg"] == "#123456"
    assert t["colors"]["sidebar.bg"] == "#eeeeee"
    assert t["problems"] == ["theme 'child': unknown color 'bogus'"]


def test_pairs_single_files_and_errors(root: Path) -> None:
    """A name picks its -light/-dark pair, a single file serves both, errors fall back."""
    write(root, "lab-light", name="Lab Light", type="light", colors={"accent": "#aa0000"})
    write(root, "lab-dark", name="Lab Dark", type="dark", colors={"accent": "#ff5555"})
    themes = pair("lab", root)
    assert themes["light"]["colors"]["accent"] == "#aa0000"
    assert themes["dark"]["colors"]["accent"] == "#ff5555"

    assert pair("lab-dark", root)["light"]["name"] == "Lab Dark"

    write(root, "a", name="A", type="light", extends="b")
    write(root, "b", name="B", type="light", extends="a")
    with pytest.raises(ThemeError, match="cycle"):
        resolve("a", root)
    broken = pair("a", root)
    assert broken["light"]["name"] == "Beamtime Light" and "cycle" in broken["problems"][0]
    assert "no theme 'missing'" in pair("missing", root)["problems"][0]

    (root / "themes" / "bad.json").write_text('{"schema": 1, "name": "Bad", "type": "sepia"}')
    assert "bad.json" in pair("bad", root)["problems"][0]
