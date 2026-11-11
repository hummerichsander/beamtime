"""The agent skills: generated from one table, each naming guide topics and copying none."""

import json
from pathlib import Path

SKILLS: dict[str, tuple[str, tuple[str, ...]]] = {
    "beamtime-views": (
        "Build or change the Beamtime view of a group: charts, the kit, library blocks. Use when "
        "the user asks for a page, a figure or a dashboard of runs logged with Beamtime.",
        ("charts", "kit", "kit-api", "library", "anti-patterns"),
    ),
    "beamtime-record": (
        "Write Beamtime's research record: proposals, predictions, notes, verdicts and memory. "
        "Use before a launch or when judging results logged with Beamtime.",
        ("proposals", "predictions", "notes", "verdicts", "memory"),
    ),
    "beamtime-analysis": (
        "Analyze runs logged with Beamtime: queries, failed runs, comparisons and remote "
        "sources. Use when the user asks about runs, metrics or a group's results.",
        ("queries", "analysis", "remote"),
    ),
}


def skill_text(name: str) -> str:
    """Write one skill: a trigger description and the guide topics to read, no guide text.

    :param name: The skill name, a key of ``SKILLS``.
    :return: The ``SKILL.md`` file."""
    description, topics = SKILLS[name]
    read = "\n".join(f"- `beamtime guide {topic}`" for topic in topics)
    return (
        f"---\nname: {name}\ndescription: {json.dumps(description)}\n---\n\n"
        "Beamtime records numerical experiments as runs in groups. Before acting, run "
        "`beamtime guide` and the topics below (MCP: `guide` with `part`) and follow them. "
        "Writes are additive; user-only commands are handed to the user, never run.\n\n"
        f"{read}\n"
    )


def write_skills(root: Path) -> list[Path]:
    """Write the skills into a project's ``.claude/skills``.

    :param root: The project root.
    :return: The files written."""
    written = []
    for name in SKILLS:
        path = root / ".claude" / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(skill_text(name))
        written.append(path)
    return written
