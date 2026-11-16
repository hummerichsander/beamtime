from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

import pytest

from beamtime.guide.rules import END, RELEASES, START, read_block, release_of, render, write_block
from beamtime.settings import AgentSettings, Settings

HISTORY = files("beamtime.guide") / "rules" / "history"
USER_ONLY = ["setup", "serve", "settings"]


def agent(**given: str) -> AgentSettings:
    """Resolve the agent settings of a project.

    :param given: The ``agent`` mapping of ``beamtime.yaml``.
    :return: The resolved knobs."""
    return Settings(values={"agent": given} if given else {}).agent


@pytest.mark.parametrize("style", ["careful", "hands-on", "analysis"])
def test_render_each_preset(style: str) -> None:
    """Every preset renders the spec's block, with its launch and record lines."""
    text = render(agent(style=style), USER_ONLY)
    assert text.startswith("## Experiments: Beamtime is the record")
    assert "Never run user commands (setup, serve, settings);" in text
    assert "{{" not in text
    assert ("Ask before you launch a run." in text) == (style != "hands-on")
    assert ("You may launch runs." in text) == (style == "hands-on")
    assert ("`proposal_set`" in text) == (style != "analysis")


def test_render_record_required_and_conventions() -> None:
    """A required record, detected conventions and a seed count show in the block."""
    text = render(
        agent(
            research_record="required",
            seeds=5,
            main_metric="val/loss",
            direction="min",
            seed_key="config.seed",
        ),
        USER_ONLY,
    )
    assert "Never launch a run without a proposal with predictions (`proposal_set`); 5 seeds" in text
    assert "Main metric val/loss (lower is better), seeds in config.seed." in text
    assert "Main metric" not in render(agent(), USER_ONLY)


def test_release_of_history() -> None:
    """The texts of 0.1.0 and 0.2.0 are named by the newest release that wrote them."""
    for name, release in RELEASES.items():
        text = (HISTORY / name).read_text()
        assert release_of(text) == release
        assert release_of(f"{START}\n{text.strip()}\n{END}\n") == release


@pytest.mark.parametrize(
    "given",
    [
        {},
        {"style": "hands-on"},
        {"style": "analysis", "seeds": 7},
        {"research_record": "required", "main_metric": "val/loss", "seed_key": "config.seed"},
        {"main_metric": "a.b[0]+(x)", "direction": "max"},
    ],
)
def test_release_of_fresh_render(given: dict) -> None:
    """A fresh render matches the current release under any settings."""
    assert release_of(render(agent(**given), USER_ONLY)) == version("beamtime")


def test_match_escapes() -> None:
    """A placeholder value with regex characters still matches."""
    text = render(agent(main_metric="val/loss", seed_key="seed (a|b)"), ["x.y", "z"])
    assert release_of(text) == version("beamtime")


def test_edited_block_matches_nothing() -> None:
    """A block edited by hand has no release."""
    text = render(agent(), USER_ONLY)
    assert release_of(text.replace("Look things", "Find things")) is None
    assert release_of(text + "\n- Always be brief.") is None


def test_write_block_keeps_outside_text(tmp_path: Path) -> None:
    """The block is added, replaced and left alone; text around it stays byte for byte."""
    file = tmp_path / "AGENTS.md"
    assert write_block(file, "old") == "added"
    assert file.read_text() == f"{START}\nold\n{END}\n"

    outside = "# Mine  \n\n\ttabs and trailing space \n"
    file.write_bytes(f"{outside}\n{START}\nold\n{END}\n\n\nAfter\n\n".encode())
    assert write_block(file, "new") == "updated"
    assert file.read_bytes() == f"{outside}\n{START}\nnew\n{END}\n\n\nAfter\n\n".encode()
    assert write_block(file, "new") == "unchanged"
    assert read_block(file) == "new"


def test_write_block_appends_to_text(tmp_path: Path) -> None:
    """A file without a block gets one after a blank line."""
    file = tmp_path / "CLAUDE.md"
    file.write_text("# Mine\n")
    write_block(file, "rules")
    assert file.read_text() == f"# Mine\n\n{START}\nrules\n{END}\n"
    assert read_block(tmp_path / "missing.md") is None


def test_crlf_block(tmp_path: Path) -> None:
    """A CRLF file keeps its line ends, and its block still names the release."""
    file = tmp_path / "AGENTS.md"
    file.write_bytes(b"# Mine\r\n")
    text = render(agent(), USER_ONLY)
    write_block(file, text)
    raw = file.read_bytes()
    assert raw.startswith(b"# Mine\r\n\r\n" + START.encode() + b"\r\n")
    assert b"\n" not in raw.replace(b"\r\n", b"")
    assert release_of(read_block(file)) == version("beamtime")

    assert write_block(file, text) == "unchanged"
    assert write_block(file, "other") == "updated"
    assert file.read_bytes().startswith(b"# Mine\r\n\r\n")


def test_crlf_round_trip(tmp_path: Path) -> None:
    """A block read from a CRLF file has LF line ends and writes back unchanged."""
    file = tmp_path / "AGENTS.md"
    file.write_bytes(b"# Mine\r\n")
    text = render(agent(), USER_ONLY)
    write_block(file, text)
    assert read_block(file) == text
    assert write_block(file, read_block(file)) == "unchanged"
    assert b"\r\r" not in file.read_bytes()
