"""Mine real sessions for what agents get wrong: python bench/agents/mine.py [--projects DIR].

Counts Beamtime tool calls, their errors (with the first line of the message) and reads of the log
dir's raw files over Claude Code transcripts (``~/.claude/projects/*/*.jsonl``). The common errors
are the first tasks of the harness; run it again to see whether a change to the guide moved them.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

PREFIX = "mcp__beamtime__"
RAW = re.compile(r"/_[a-z][\w-]*\.(?:json|jsonl|npy|bin|log|col|txt)\b")


def events(file: Path) -> list[dict[str, Any]]:
    """Read a transcript, skipping lines that aren't JSON.

    :param file: A ``.jsonl`` transcript.
    :return: Its events."""
    out = []
    for line in file.read_text(errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def mine(projects: Path) -> dict[str, Counter]:
    """Count tool calls, errors and raw reads over all transcripts.

    :param projects: The folder of per-project transcript folders.
    :return: Counters ``calls``, ``errors`` (tool and first line of the message) and ``raw_reads``
        (the tool and the machine-written file it read)."""
    counts = {"calls": Counter(), "errors": Counter(), "raw_reads": Counter()}
    for file in projects.glob("*/*.jsonl"):
        names: dict[str, str] = {}
        for event in events(file):
            content = (event.get("message") or {}).get("content")
            for part in content if isinstance(content, list) else []:
                if part.get("type") == "tool_use":
                    names[part["id"]] = part["name"]
                    if part["name"].startswith(PREFIX):
                        counts["calls"][part["name"].removeprefix(PREFIX)] += 1
                    elif part["name"] in ("Read", "Grep", "Glob") and (
                        m := RAW.search(json.dumps(part.get("input")))
                    ):
                        counts["raw_reads"][f"{part['name']} {m.group(0)[:60]}"] += 1
                elif part.get("type") == "tool_result" and part.get("is_error"):
                    name = names.get(part.get("tool_use_id"), "")
                    if name.startswith(PREFIX):
                        text = json.dumps(part.get("content"))
                        message = text.strip('"[]{}').replace("\\n", " ")[:100]
                        counts["errors"][f"{name.removeprefix(PREFIX)}: {message}"] += 1
    return counts


def main() -> None:
    """Print the counts."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args()
    for title, counter in mine(args.projects).items():
        print(f"\n## {title} ({sum(counter.values())})")
        for key, n in counter.most_common(args.top):
            print(f"{n:5d}  {key}")


if __name__ == "__main__":
    main()
