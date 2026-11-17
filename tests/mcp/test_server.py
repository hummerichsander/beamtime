import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.ops.registry import BY_TOOL
from beamtime.synth import generate

anyio = pytest.importorskip("anyio")
pytest.importorskip("mcp")

from mcp.client.session import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

from beamtime.mcp.server import CORE, FAMILIES, build, content, slim  # noqa: E402

BEAMTIME = Path(sys.executable).parent / ("beamtime.exe" if sys.platform == "win32" else "beamtime")


def test_content_names_each_shots_mime_type_from_its_file(tmp_path: Path) -> None:
    """A render's images get the mime type their own file names, not a fixed image/png."""
    jpg, png = tmp_path / "page-light.jpg", tmp_path / "block-light.png"
    jpg.write_bytes(b"\xff\xd8\xff")
    png.write_bytes(b"\x89PNG\r\n\x1a\n")
    answer = {"shots": [{"file": str(jpg), "block": None}, {"file": str(png), "block": "b"}]}
    _, *images = content(answer)
    assert [i.mime_type for i in images] == ["image/jpeg", "image/png"]


def test_slim_drops_null_members_and_empty_defaults() -> None:
    """Optional parameters lose their ``null`` type and default; real defaults stay."""
    node = {
        "properties": {
            "a": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": None},
            "b": {"type": "array", "default": []},
            "c": {"anyOf": [{"enum": ["all"]}, {"type": "integer"}], "default": "all"},
        },
        "required": [],
        "additionalProperties": False,
    }
    assert slim(node) == {
        "properties": {
            "a": {"type": "string"},
            "b": {"type": "array"},
            "c": {"anyOf": [{"enum": ["all"]}, {"type": "integer"}], "default": "all"},
        }
    }


@pytest.fixture(scope="module")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A git project with a generated log dir.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The project root."""
    root = tmp_path_factory.mktemp("mcp") / "proj"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    generate(root / "beamtime", seed=0, now=datetime.now(timezone.utc))
    return root


def session(project: Path, work):
    """Run a coroutine against a live ``beamtime mcp`` process.

    :param project: The project root.
    :param work: ``async (ClientSession) -> result``.
    :return: The result."""

    async def main():
        params = StdioServerParameters(
            command=str(BEAMTIME), args=["mcp"], cwd=str(project), env=dict(os.environ)
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                return await work(s)

    return anyio.run(main)


def test_every_tool_is_core_or_in_one_family() -> None:
    """A new operation belongs to a family or is core: the families are disjoint and known."""
    members = [name for names in FAMILIES.values() for name in names]
    assert len(members) == len(set(members)) and set(members) <= set(BY_TOOL)
    assert set(CORE) | set(members) == set(BY_TOOL) and not set(CORE) & set(members)
    assert len(CORE) == 19 and set(FAMILIES) == {"views", "blocks", "runs", "export"}


def test_tools_match_the_registry(project: Path) -> None:
    """The listing is the core tools and ``tools_more``, small, and the same after a call."""

    async def work(s):
        before = (await s.list_tools()).tools
        await s.call_tool("tools_more", {"family": "views"})
        return before, (await s.list_tools()).tools

    before, after = session(project, work)
    assert [t.name for t in before] == [*CORE, "tools_more"]
    assert before == after
    assert all(t.input_schema["type"] == "object" for t in before)
    assert not any(name in CORE for name in FAMILIES["views"])


def test_tool_definitions_under_3500_tokens(project: Path) -> None:
    """The definitions of a fresh server, ``tools_more`` included, stay under 3.5k tokens."""

    async def work(s):
        return (await s.list_tools()).tools

    size = sum(
        len(json.dumps(t.model_dump(exclude_none=True, by_alias=True)))
        for t in session(project, work)
    )
    assert size / 4 < 3500


def test_no_list_changed_is_announced() -> None:
    """The listing never changes, so the server does not declare ``listChanged``."""
    options = build().create_initialization_options()
    assert not options.capabilities.tools.list_changed


def test_tools_more_describes_a_family(project: Path) -> None:
    """``tools_more`` with a family answers one compact line per tool; bad calls name the way."""

    async def work(s):
        return [
            await s.call_tool("tools_more", {"family": "views"}),
            await s.call_tool("tools_more", {"family": "nope"}),
            await s.call_tool("tools_more", {}),
        ]

    views, unknown, empty = session(project, work)
    lines = views.content[0].text.splitlines()
    assert not views.is_error and len(lines) == 8
    assert "view_new(group: string, from?: " in lines[0] and lines[0].endswith(".")
    assert "view_show(group?: string, version?: string): " in views.content[0].text
    for result in (unknown, empty):
        assert result.is_error
        assert all(name in result.content[0].text for name in FAMILIES)


def test_tools_more_calls_a_tool_like_a_direct_call(project: Path) -> None:
    """``tools_more`` with a tool returns what the direct call returns; a direct call still works."""

    async def work(s):
        args = {"group": "scaling/lr-sweep"}
        return [
            await s.call_tool("tools_more", {"tool": "view_show", "args": args}),
            await s.call_tool("tools_more", {"tool": "view_show", "args": json.dumps(args)}),
            await s.call_tool("view_show", args),
        ]

    through, through_text, direct = session(project, work)
    assert not direct.is_error and through.content == direct.content == through_text.content


def test_tools_more_args_errors_match_direct(project: Path) -> None:
    """A missing required parameter or an unknown key answers the direct call's error."""

    async def work(s):
        out = []
        for tool, args in (("view_new", {}), ("view_show", {"nope": 1})):
            out.append(await s.call_tool("tools_more", {"tool": tool, "args": args}))
            out.append(await s.call_tool(tool, args))
        out.append(await s.call_tool("tools_more", {"tool": "view_show", "args": [1]}))
        return out

    a, b, c, d, e = session(project, work)
    assert a.is_error and a.content == b.content
    assert c.is_error and c.content == d.content
    assert e.is_error and "object" in e.content[0].text


def test_tools_more_remote_target(project: Path) -> None:
    """A nested ``@source/path`` target routes through the dispatcher as it does directly."""

    async def work(s):
        args = {"group": "@nowhere/scaling"}
        return [
            await s.call_tool("tools_more", {"tool": "view_show", "args": args}),
            await s.call_tool("view_show", args),
        ]

    through, direct = session(project, work)
    assert direct.is_error and through.content == direct.content


def test_tools_more_refuses_user_only(project: Path) -> None:
    """User-only commands and unknown or core tools are refused as they are directly."""

    async def work(s):
        return [
            await s.call_tool("tools_more", {"tool": "set", "args": {}}),
            await s.call_tool("set", {}),
            await s.call_tool("tools_more", {"tool": "view_nope"}),
            await s.call_tool("tools_more", {"tool": "runs"}),
        ]

    through, direct, close, core = session(project, work)
    assert through.is_error and direct.is_error and "unknown tool" in through.content[0].text
    assert all(name in close.content[0].text for name in FAMILIES["views"])
    assert core.is_error


def test_calls_answer_and_errors_return_to_the_agent(project: Path) -> None:
    """A tool call answers with the canonical JSON; mistakes come back as tool errors."""

    async def work(s):
        ok = await s.call_tool("runs", {"from": "scaling/lr-sweep", "limit": 2})
        bad = await s.call_tool("runs", {"from": "scalng"})
        prompt = await s.get_prompt("review", {"group": "scaling"})
        params = {"from": "scaling/lr-sweep", "y": ["train/loss"], "points": 20}
        return ok, bad, prompt, await s.call_tool("series", params)

    ok, bad, prompt, series = session(project, work)
    curve = json.loads(series.content[0].text)["curves"][0]
    assert {"y", "lo", "hi", "n"} <= set(curve) and not {"last", "min", "max", "count"} & set(curve)
    answer = json.loads(ok.content[0].text)
    assert not ok.is_error and answer["kind"] == "runs" and len(answer["rows"]) == 2
    assert bad.is_error and "Did you mean 'scaling'" in bad.content[0].text
    assert "scaling" in prompt.messages[0].content.text


def test_analysis_tools_answer_over_mcp(project: Path) -> None:
    """compare, digest, logs, diagnose, plan_missing and wait answer through the server; a
    wait never blocks past its cap, and a quoted argument is decoded."""

    async def work(s):
        names = ["scaling/lr-sweep", "tokenizer/bpe-vs-unigram"]
        return [
            await s.call_tool("compare", {"targets": names}),
            await s.call_tool("digest", {"group": names[0]}),
            await s.call_tool("logs", {"from": names[0], "tail": 1}),
            await s.call_tool("diagnose", {"from": names[0]}),
            await s.call_tool("plan_missing", {"group": names[0]}),
            await s.call_tool("wait", {"from": names[1], "timeout": '"5"'}),
        ]

    answers = [json.loads(r.content[0].text) for r in session(project, work)]
    assert [a["kind"] for a in answers] == [
        "compare", "digest", "logs", "diagnose", "plan missing", "wait"
    ]  # fmt: skip
    assert answers[-1]["met"]


def test_record_writes_and_prompts(project: Path) -> None:
    """Agents write proposals, notes and memory through tools; the prompts name them."""
    proposal = {
        "statement": "Dropout helps.",
        "predictions": [{"name": "p", "reduce": {"metric": "val/acc"}, "op": ">", "value": 0.5}],
    }

    async def work(s):
        saved = await s.call_tool(
            "proposal_set", {"group": "agent/dropout", "proposal": proposal, "author": "m"}
        )
        yaml_text = await s.call_tool(
            "proposal_set", {"group": "agent/other", "proposal": "statement: From YAML.\n"}
        )
        note = await s.call_tool(
            "note_add",
            {"group": "agent/dropout", "type": "idea", "description": "Try 0.2.", "body": "x"},
        )
        theory = await s.call_tool(
            "note_add",
            {"group": "agent/dropout", "type": "theory", "description": "Dropout regularizes."},
        )
        bad = await s.call_tool("note_add", {"group": "agent", "type": "idea", "description": ""})
        memory = await s.call_tool("memory_update", {"group": "agent", "body": "- idea [[x]]"})
        shown = await s.call_tool("memory_show", {"group": "agent/dropout"})
        prompts = [
            await s.get_prompt(name, {"group": "agent/dropout"})
            for name in ("proposal", "verdict", "memory")
        ]
        migrate = await s.get_prompt(
            "migrate", {"paths": "old/NOTES.md", "conflict": "AGENTS.md:4"}
        )
        prompts.append(migrate)
        listed = {
            p.name: [a.name for a in p.arguments or []] for p in (await s.list_prompts()).prompts
        }
        return saved, yaml_text, note, theory, bad, memory, shown, prompts, listed

    saved, yaml_text, note, theory, bad, memory, shown, prompts, listed = session(project, work)
    for result in (saved, yaml_text, note, theory, memory, shown):
        assert not result.is_error, result.content[0].text
    path = project / "beamtime" / json.loads(saved.content[0].text)["path"]
    assert "author: m" in path.read_text()
    note_path = project / "beamtime" / json.loads(note.content[0].text)["path"]
    assert "author: agent" in note_path.read_text()
    theory_path = project / "beamtime" / json.loads(theory.content[0].text)["path"]
    assert "type: theory" in theory_path.read_text()
    assert bad.is_error and "one line" in bad.content[0].text
    assert json.loads(shown.content[0].text)["chain"][-1]["group"] == "agent"
    texts = [p.messages[0].content.text for p in prompts]
    assert "proposal_set" in texts[0] and "note_add" in texts[1] and "memory_update" in texts[2]
    assert all("agent/dropout" in t for t in texts[:3])
    migrate_text = texts[3]
    assert listed["migrate"] == ["paths", "conflict"]
    for name in ("guide notes", "guide memory", "note_add", "memory_update", "AGENTS.md:4"):
        assert name in migrate_text
    assert (
        "old/NOTES.md" in migrate_text and "Never delete or change the source files" in migrate_text
    )
    assert "Show the diff before" in migrate_text


def test_arguments_sent_as_json_text_are_decoded_once() -> None:
    """``"all"`` sent as ``"\\"all\\""`` and a list as text decode; plain strings stay as they are."""
    from beamtime.mcp.server import decoded
    from beamtime.ops.registry import BY_NAME

    series = BY_NAME["series"]
    got = decoded(
        series,
        {"points": '"all"', "y": '["val/acc"]', "x": "_step", "band": '"std"', "from": "scaling"},
    )
    assert got == {"points": "all", "y": ["val/acc"], "x": "_step", "band": "std", "from": "scaling"}
    assert decoded(series, {"points": "500"}) == {"points": 500}
    note = BY_NAME["note add"]
    assert decoded(note, {"body": '"quoted"', "group": "[1]"}) == {"body": '"quoted"', "group": "[1]"}
