from pathlib import Path

import pytest

from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.settings import PRESETS, load, user_settings_path


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A project root whose user settings live in a temporary config dir.

    :param tmp_path: Pytest's temporary directory.
    :param monkeypatch: Pytest's monkeypatch.
    :return: The project root."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    root = tmp_path / "proj"
    root.mkdir()
    return root


def test_no_agent_is_careful(home: Path) -> None:
    """A project without ``agent`` behaves as careful, every knob marked default."""
    agent = load(home).agent
    assert agent.style == "careful"
    assert agent.launch_runs == "ask" and agent.seeds == 3
    assert set(agent.source.values()) == {"default"}
    assert agent.main_metric is None and "main_metric" not in agent.source


def test_presets_table() -> None:
    """The presets differ from careful in exactly the spec's knobs."""
    careful = PRESETS["careful"]
    assert {k for k, v in PRESETS["hands-on"].items() if v != careful[k]} == {"launch_runs"}
    assert {k for k, v in PRESETS["analysis"].items() if v != careful[k]} == {
        "memory_updates",
        "research_record",
    }


def test_proposal_words(home: Path) -> None:
    """Every preset allows 150 words; a project can set another count, and 0 is a problem."""
    assert {name: preset["proposal_words"] for name, preset in PRESETS.items()} == {
        name: 150 for name in PRESETS
    }
    (home / "beamtime.yaml").write_text("agent: {proposal_words: 80}\n")
    agent = load(home).agent
    assert agent.proposal_words == 80 and agent.source["proposal_words"] == "project"
    (home / "beamtime.yaml").write_text("agent: {proposal_words: 0}\n")
    s = load(home)
    assert s.agent.proposal_words == 150
    assert any("proposal_words" in problem for problem in s.problems)


def test_preset_with_override(home: Path) -> None:
    """A style resolves to its preset, single keys override it, each with its provenance."""
    (home / "beamtime.yaml").write_text(
        "agent: {style: hands-on, seeds: 5, main_metric: val/loss, direction: min}\n"
    )
    s = load(home)
    agent = s.agent
    assert not s.problems
    assert agent.launch_runs == "allowed" and agent.seeds == 5
    assert agent.source["launch_runs"] == "preset"
    assert agent.source["seeds"] == "project"
    assert agent.source["significance"] == "preset"
    assert (agent.main_metric, agent.direction, agent.seed_key) == ("val/loss", "min", None)
    assert agent.source["main_metric"] == "project"


def test_custom_starts_from_careful(home: Path) -> None:
    """The ``custom`` style starts from careful's values."""
    (home / "beamtime.yaml").write_text("agent: {style: custom, launch_runs: never}\n")
    agent = load(home).agent
    assert agent.style == "custom"
    assert agent.launch_runs == "never"
    assert agent.memory_updates == PRESETS["careful"]["memory_updates"]
    assert agent.research_record == "encouraged"


def test_mcp_tools_is_core_in_every_style_and_checked(home: Path) -> None:
    """The default is ``core`` in every style; a bad value names both choices."""
    assert all(preset["mcp_tools"] == "core" for preset in PRESETS.values())
    (home / "beamtime.yaml").write_text("agent: {style: analysis, mcp_tools: all}\n")
    assert load(home).agent.mcp_tools == "all"
    (home / "beamtime.yaml").write_text("agent: {mcp_tools: some}\n")
    s = load(home)
    assert any("core" in p and "all" in p for p in s.problems) and s.agent.mcp_tools == "core"


def test_agent_in_user_file_is_a_problem(home: Path) -> None:
    """``agent`` belongs to the project: in the user file it is reported and ignored."""
    path = user_settings_path()
    path.parent.mkdir(parents=True)
    path.write_text("agent: {style: hands-on}\n")
    s = load(home)
    assert any("belongs in the project" in p for p in s.problems)
    assert s.agent.style == "careful"


@pytest.mark.parametrize(
    "text, key",
    [
        ("{launch_runs: sometimes}", "launch_runs"),
        ("{seeds: 0}", "seeds"),
        ("{seeds: 2.5}", "seeds"),
        ("{seeds: true}", "seeds"),
        ("{significance: 1}", "significance"),
        ("{significance: 0}", "significance"),
        ("{direction: up}", "direction"),
        ("{mcp_tools: some}", "mcp_tools"),
        ("{style: wild}", "style"),
        ("{colour: red}", "colour"),
    ],
)
def test_agent_values_checked(home: Path, text: str, key: str) -> None:
    """An unknown knob or a value out of range is a problem, and the preset value is used."""
    (home / "beamtime.yaml").write_text(f"agent: {text}\n")
    s = load(home)
    assert any(key in p for p in s.problems)
    assert s.agent.seeds == 3 and s.agent.significance == 0.95
    assert s.agent.launch_runs == "ask" and s.agent.style == "careful"


def test_agent_not_a_mapping(home: Path) -> None:
    """A non-mapping ``agent`` is reported and ignored."""
    (home / "beamtime.yaml").write_text("agent: hands-on\n")
    s = load(home)
    assert any("agent is a mapping" in p for p in s.problems)
    assert s.agent.style == "careful"


def test_disabled_project_remote(home: Path) -> None:
    """``enabled: false`` in the user file merges over a project remote key by key."""
    (home / "beamtime.yaml").write_text(
        "remotes:\n  gpu: {host: g, path: /a}\n  cpu: {host: c, path: /b}\n"
    )
    path = user_settings_path()
    path.parent.mkdir(parents=True)
    path.write_text("remotes:\n  gpu: {enabled: false}\n")
    s = load(home)
    assert not s.problems
    assert set(s.remotes) == {"cpu"}
    assert s.get("remotes")["gpu"] == {"host": "g", "path": "/a", "enabled": False}
    assert ("remotes.gpu.enabled", False, "user") in s.flat()


def test_enabled_must_be_a_bool(home: Path) -> None:
    """A non-boolean ``enabled`` is reported and the remote stays enabled."""
    (home / "beamtime.yaml").write_text("remotes:\n  gpu: {host: g, path: /a, enabled: no_}\n")
    s = load(home)
    assert any("enabled is true or false" in p for p in s.problems)
    assert set(s.remotes) == {"gpu"}


def test_disabled_remote_hidden_from_status_shown_in_lists(ctx: Context, project: Path) -> None:
    """A disabled remote is absent from ``status`` and the context, present in ``source list``
    and ``settings``."""
    (project / "beamtime.yaml").write_text(
        "remotes:\n  gpu: {host: g, path: /a}\n  cpu: {host: c, path: /b}\n"
    )
    path = user_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("remotes:\n  gpu: {enabled: false}\n")
    ctx = Context.make(caller="cli")
    assert call("status", {}, ctx)["remotes"] == ["cpu"]
    assert ctx.remotes == ["cpu"]
    names = [row[0] for row in call("source list", {}, ctx)["rows"]]
    assert names == ["cpu", "gpu"]
    keys = [row[0] for row in call("settings", {}, ctx)["rows"]]
    assert "remotes.gpu.enabled" in keys
