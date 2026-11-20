"""The rules block for agent instruction files, rendered from the agent settings."""

import re
from collections.abc import Iterable
from importlib.resources import files
from pathlib import Path
from typing import Literal

from beamtime.settings import AgentSettings

START, END = "<!-- beamtime:start -->", "<!-- beamtime:end -->"
# the instruction files of the agent clients (tests keep this equal to the client table's).
RULES_FILES = ("CLAUDE.md", "AGENTS.md", "GEMINI.md")
# the newest release that wrote each history text.
RELEASES = {"0.1.0.md": "0.1.1", "0.2.0.md": "0.2.1"}
LAUNCH = {
    "never": "Never launch runs yourself.",
    "ask": "Ask before you launch a run.",
    "allowed": "You may launch runs.",
}
DIRECTION = {"min": "lower is better", "max": "higher is better"}
OPTIONAL = ("record_line", "conventions")
LINE = re.compile(r"^- \{\{(\w+)\}\}\n|\{\{(\w+)\}\}", re.MULTILINE)
TOKEN = re.compile(
    r"(?P<optional>^- \{\{(?:" + "|".join(OPTIONAL) + r")\}\}\n)"
    r"|(?P<placeholder>\{\{\w+\}\})|(?P<space>\s+)|(?P<text>(?:(?!\{\{)\S)+)",
    re.MULTILINE,
)


def render(agent: AgentSettings, user_only: Iterable[str]) -> str:
    """Render the rules block for a project's agent settings.

    :param agent: The agent settings.
    :param user_only: The names of the user-only commands.
    :return: The block's text, without markers."""
    values = {
        "record_line": record_line(agent),
        "launch_line": LAUNCH[agent.launch_runs],
        "conventions": conventions(agent),
        "user_only": ", ".join(user_only),
    }

    def fill(found: re.Match[str]) -> str:
        if found[1] is not None:
            return f"- {value}\n" if (value := values[found[1]]) else ""
        return values[found[2]]

    return LINE.sub(fill, template("rules.md")).strip()


def record_line(agent: AgentSettings) -> str:
    """Say whether launches need a proposal, or nothing when the record is off.

    :param agent: The agent settings.
    :return: The line's text."""
    match agent.research_record:
        case "off":
            return ""
        case "encouraged":
            return (
                "Before a run, write a proposal with predictions (`proposal_set`), "
                f"{agent.seeds} seeds per point."
            )
        case "required":
            return (
                "Never launch a run without a proposal with predictions (`proposal_set`); "
                f"{agent.seeds} seeds per point."
            )
        case other:
            raise ValueError(f"unknown research_record {other!r}")


def conventions(agent: AgentSettings) -> str:
    """Name the project's main metric and seed key, as far as it sets them.

    :param agent: The agent settings.
    :return: The sentence, or an empty string when the project sets none."""
    parts = []
    if agent.main_metric:
        direction = f" ({DIRECTION[agent.direction]})" if agent.direction else ""
        parts.append(f"Main metric {agent.main_metric}{direction}")
    if agent.seed_key:
        parts.append(f"seeds in {agent.seed_key}" if parts else f"Seeds in {agent.seed_key}")
    return f"{', '.join(parts)}." if parts else ""


def release_of(block: str) -> str | None:
    """Name the release that wrote a rules block.

    :param block: The block's text, with or without markers.
    :return: The current version for what this release renders, the newest release that wrote
        an older text, or ``None`` for a block edited by hand."""
    from importlib.metadata import version

    text = block.replace(START, "").replace(END, "").strip()
    if re.fullmatch(pattern(template("rules.md")), text):
        return version("beamtime")
    for name in sorted(RELEASES, reverse=True):
        if re.fullmatch(pattern(template(f"history/{name}")), text):
            return RELEASES[name]
    return None


def outdated_release(root: Path) -> str | None:
    """Name the oldest release behind the rules blocks of a project, if any is older than this one.

    :param root: The project root.
    :return: The release, or ``None`` without a block, with current blocks, or with hand-edited
        ones."""
    from importlib.metadata import version

    found = []
    for name in RULES_FILES:
        if (file := root / name).is_file() and (block := read_block(file)) is not None:
            if (release := release_of(block)) is not None and release != version("beamtime"):
                found.append(release)
    return min(found, key=lambda r: [int(n) for n in re.findall(r"\d+", r)], default=None)


def pattern(template: str) -> str:
    """Turn a template into a regular expression.

    Placeholders match any text on a line, the lines of the optional ones may be missing and
    whitespace runs match any whitespace.

    :param template: The template text.
    :return: The pattern."""
    out = []
    for token in TOKEN.finditer(template.strip()):
        match token.lastgroup:
            case "optional":
                out.append(r"(?:-\s+.+?\s+)?")
            case "placeholder":
                out.append(".+?")
            case "space":
                out.append(r"\s+")
            case _:
                out.append(re.escape(token[0]))
    return "".join(out)


def template(name: str) -> str:
    """Read a template of the rules block.

    :param name: ``rules.md`` or ``history/<release>.md``.
    :return: The text."""
    return (files(__package__) / "rules" / name).read_text(encoding="utf-8")


def read_block(file: Path) -> str | None:
    """Read the rules block from an instruction file.

    :param file: The instruction file.
    :return: The block's text without markers and with ``\n`` line ends, or ``None`` if the file
        has none."""
    text = file.read_bytes().decode() if file.exists() else ""
    if (found := find_block(text)) is None:
        return None
    return text[found[0] + len(START) : found[1]].strip().replace("\r\n", "\n")


def write_block(file: Path, block: str) -> Literal["added", "updated", "unchanged"]:
    """Write the rules block into an instruction file, replacing a previous one.

    Text outside the markers stays byte for byte.

    :param file: The instruction file, created if missing.
    :param block: The block's text, without markers.
    :return: What happened."""
    text = file.read_bytes().decode() if file.exists() else ""
    newline = "\r\n" if "\r\n" in text else "\n"
    marked = f"{START}\n{block}\n{END}".replace("\r\n", "\n").replace("\n", newline)
    if (found := find_block(text)) is None:
        gap = newline if text and not text.endswith(newline * 2) else ""
        file.write_bytes((text + gap + marked + newline).encode())
        return "added"
    updated = text[: found[0]] + marked + text[found[1] + len(END) :]
    if updated == text:
        return "unchanged"
    file.write_bytes(updated.encode())
    return "updated"


def find_block(text: str) -> tuple[int, int] | None:
    """Find the markers of the rules block.

    :param text: The file's text.
    :return: The offsets of the start and end markers, or ``None`` if the block is missing."""
    if (start := text.find(START)) == -1 or (end := text.find(END, start)) == -1:
        return None
    return start, end
