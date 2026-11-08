"""The generated skills name guide topics and copy no guide text; the prompts name real topics."""

import json
import re
from pathlib import Path

from beamtime.guide import TOPICS, read
from beamtime.mcp.server import PROMPTS
from beamtime.mcp.skills import SKILLS
from beamtime.ops import call
from beamtime.ops.context import Context


def test_mcp_install_writes_skills_that_name_topics(ctx: Context, project: Path) -> None:
    """Each skill names its guide topics and carries no line of their text, so it can't go stale."""
    call("mcp install", {"client": "cursor", "skills": True}, ctx)
    for name, (_, topics) in SKILLS.items():
        text = (project / ".claude" / "skills" / name / "SKILL.md").read_text()
        assert text.startswith(f"---\nname: {name}\n")
        for topic in topics:
            assert f"`beamtime guide {topic}`" in text
            lines = (line.strip() for line in read(f"{topic}.md").splitlines())
            assert not [line for line in lines if len(line) > 40 and line in text], topic


def test_prompts_and_skills_cover_every_guide_topic() -> None:
    """Every guide topic is named by a skill or a prompt, and every name points at a real topic."""
    named = {t for _, topics in SKILLS.values() for t in topics}
    for _, arguments, template in PROMPTS.values():
        named |= set(re.findall(r"`guide ([a-z-]+)`", template))
    assert set(TOPICS) <= named
    assert named <= set(TOPICS) | {"examples", "blocks"}


def test_build_plugin_writes_the_layout(tmp_path: Path) -> None:
    """The plugin directory has a manifest, one skill per generated skill and an MCP config."""
    import runpy

    script = Path(__file__).parents[2] / "scripts" / "build-plugin"
    runpy.run_path(str(script), run_name="build")["build"](tmp_path / "plugin")
    manifest = json.loads((tmp_path / "plugin" / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "beamtime"
    for name in SKILLS:
        assert (tmp_path / "plugin" / "skills" / name / "SKILL.md").exists()
    config = json.loads((tmp_path / "plugin" / ".mcp.json").read_text())
    assert config["mcpServers"]["beamtime"]["args"] == ["mcp"]
