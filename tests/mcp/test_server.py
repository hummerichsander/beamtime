import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.ops.registry import BY_TOOL
from beamtime.synth import generate
from tests.conftest import index_fully

anyio = pytest.importorskip("anyio")
pytest.importorskip("mcp")

from mcp.client.session import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

from beamtime.mcp.server import (  # noqa: E402
    CORE,
    FAMILIES,
    INSTRUCTIONS,
    PROMPTS,
    build,
    content,
    instructions,
    prompt_text,
    schema,
    slim,
)

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
    index_fully(root / "beamtime")
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
    assert len(CORE) == 20 and set(FAMILIES) == {"views", "blocks", "runs", "export", "scripts"}


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


def test_script_tool_runs_code_with_bt(project: Path) -> None:
    """``script`` is in the ``scripts`` family, not core; through ``tools_more`` it answers what the
    CLI prints."""

    async def work(s):
        listed = {t.name for t in (await s.list_tools()).tools}
        family = await s.call_tool("tools_more", {"family": "scripts"})
        code = {"code": "print(bt.status()['kind'])"}
        done = await s.call_tool("tools_more", {"tool": "script", "args": code})
        return listed, family, done

    listed, family, done = session(project, work)
    assert "script" not in CORE and "script" not in listed
    assert family.content[0].text.startswith("script(code: string, timeout?: ")
    assert not done.is_error and json.loads(done.content[0].text)["stdout"] == "status\n"


def test_prompts_reach_family_tools_through_tools_more() -> None:
    """A prompt that names a family tool says it is called through ``tools_more``."""
    members = {name for names in FAMILIES.values() for name in names}
    for name, (_, arguments, _) in PROMPTS.items():
        body = prompt_text(name, {a: "x" for a, _, _ in arguments})
        if members & set(re.findall(r"`(\w+)`", body)):
            assert "tools_more" in body, name
    assert "`tools_more`" in instructions()


def test_all_names_no_tools_more_in_instructions_or_prompts() -> None:
    """Under ``mcp_tools: all`` no instruction or prompt text mentions ``tools_more``."""
    assert "tools_more" not in instructions("all")
    for name, (_, arguments, _) in PROMPTS.items():
        body = prompt_text(name, {a: "x" for a, _, _ in arguments}, "all")
        assert "tools_more" not in body and "{more_" not in body, name
    view = prompt_text("view", {"group": "g"}, "all")
    assert "call the `view_*` and `block_*` tools directly" in view


def test_tool_definitions_under_12000_characters(project: Path) -> None:
    """The definitions of a fresh server, ``tools_more`` and the instructions included, stay under
    12k characters of JSON."""

    async def work(s):
        return (await s.list_tools()).tools

    size = sum(
        len(json.dumps(t.model_dump(exclude_none=True, by_alias=True)))
        for t in session(project, work)
    )
    assert size + len(INSTRUCTIONS) < 12_000


def test_instructions_name_the_where_ops() -> None:
    """The instructions carry the ``where`` operators once; a schema only points to them."""
    assert "ops eq ne lt le gt ge in nin has exists glob" in INSTRUCTIONS
    assert "Start a work session with `status`" in INSTRUCTIONS
    assert "metric.a.nonfinite_step" in INSTRUCTIONS
    assert "`memory_show`" not in INSTRUCTIONS
    where = schema(BY_TOOL["runs"])["properties"]["where"]
    assert where["description"] == "see instructions: where"


def test_instructions_name_hidden_once() -> None:
    """``hidden`` is explained in the instructions and left out of every tool schema."""
    assert "hidden: true includes hidden runs" in INSTRUCTIONS
    assert all("hidden" not in schema(op).get("properties", {}) for op in BY_TOOL.values())


def test_defaults_an_absent_key_reads_are_dropped() -> None:
    """No schema lists the ``"."`` default of ``from`` or ``group``; the operation reads it anyway."""
    for op in BY_TOOL.values():
        if op.params is None:
            continue
        properties = schema(op).get("properties", {})
        assert all(properties.get(key, {}).get("default") != "." for key in ("from", "group"))


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
    assert not views.is_error and len(lines) == 9
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
    """User-only commands and unknown tools are refused as they are directly."""

    async def work(s):
        return [
            await s.call_tool("tools_more", {"tool": "set", "args": {}}),
            await s.call_tool("set", {}),
            await s.call_tool("tools_more", {"tool": "view_nope"}),
        ]

    through, direct, close = session(project, work)
    assert through.is_error and direct.is_error and "unknown tool" in through.content[0].text
    assert all(name in close.content[0].text for name in FAMILIES["views"])


def test_tools_more_runs_a_core_tool(project: Path) -> None:
    """A core tool through ``tools_more`` returns what the direct call returns, also for bad args."""

    async def work(s):
        good = {"from": "scaling/lr-sweep", "limit": 2}
        bad = {"from": "scalng"}
        return [
            await s.call_tool("tools_more", {"tool": "runs", "args": good}),
            await s.call_tool("runs", good),
            await s.call_tool("tools_more", {"tool": "runs", "args": bad}),
            await s.call_tool("runs", bad),
        ]

    through, direct, bad_through, bad_direct = session(project, work)
    assert not direct.is_error and through.content == direct.content
    assert bad_direct.is_error and bad_through.content == bad_direct.content


def test_mcp_tools_setting_per_project(project: Path, tmp_path: Path) -> None:
    """``agent: {mcp_tools: all}`` lists every tool without ``tools_more``; another project keeps core."""
    other = tmp_path / "all"
    other.mkdir()
    (other / ".git").mkdir()
    (other / "beamtime.yaml").write_text("agent: {mcp_tools: all}\n", encoding="utf-8")

    async def work(s):
        return [t.name for t in (await s.list_tools()).tools]

    listed = session(other, work)
    assert listed == list(BY_TOOL) and "tools_more" not in listed
    assert session(project, work) == [*CORE, "tools_more"]


def test_mcp_tools_setting_reaches_instructions_and_prompts(project: Path, tmp_path: Path) -> None:
    """The server's own root decides the instructions at start and the prompts per call."""
    other = tmp_path / "all"
    other.mkdir()
    (other / ".git").mkdir()
    (other / "beamtime.yaml").write_text("agent: {mcp_tools: all}\n", encoding="utf-8")

    async def work(s):
        return (await s.get_prompt("view", {"group": "scaling"})).messages[0].content.text

    assert build(other).instructions == instructions("all")
    assert build(project).instructions == instructions("core")
    assert "tools_more" not in session(other, work)
    assert "tools_more" in session(project, work)


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
    assert "author: m" in path.read_text(encoding="utf-8")
    note_path = project / "beamtime" / json.loads(note.content[0].text)["path"]
    assert "author: agent" in note_path.read_text(encoding="utf-8")
    theory_path = project / "beamtime" / json.loads(theory.content[0].text)["path"]
    assert "type: theory" in theory_path.read_text(encoding="utf-8")
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
    assert got == {
        "points": "all",
        "y": ["val/acc"],
        "x": "_step",
        "band": "std",
        "from": "scaling",
    }
    assert decoded(series, {"points": "500"}) == {"points": 500}
    assert decoded(BY_NAME["runs"], {"depth": "2", "from": "2"}) == {"depth": 2, "from": "2"}
    note = BY_NAME["note add"]
    assert decoded(note, {"body": '"quoted"', "group": "[1]"}) == {
        "body": '"quoted"',
        "group": "[1]",
    }


def test_mcp_registers_with_its_client_after_a_call(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The MCP server is listed as ``mcp`` with its root, the client's name after one tool call,
    and not at all after it exits."""
    from mcp_types import Implementation

    from beamtime.index.procs import listed

    monkeypatch.setenv("BEAMTIME_RUNTIME", str(tmp_path / "rt"))

    async def main():
        params = StdioServerParameters(
            command=str(BEAMTIME), args=["mcp"], cwd=str(project), env=dict(os.environ)
        )
        async with stdio_client(params) as (read, write):
            info = Implementation(name="probe-client", version="1")
            async with ClientSession(read, write, client_info=info) as s:
                await s.initialize()
                before = listed()[0]
                await s.call_tool("runs", {"from": "scaling/lr-sweep", "limit": 1})
                return before, listed()[0]

    before, after = anyio.run(main)
    assert [r["kind"] for r in after] == ["mcp"] and before[0]["client"] is None
    assert after[0]["root"] == str(project.resolve()) and after[0]["client"] == "probe-client"
    assert listed() == ([], [])


def test_mcp_runs_without_a_registry(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A runtime base that can't be written costs the record, not the server."""
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    monkeypatch.setenv("BEAMTIME_RUNTIME", str(blocker / "rt"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    errlog = tmp_path / "err.txt"

    async def main():
        params = StdioServerParameters(
            command=str(BEAMTIME), args=["mcp"], cwd=str(project), env=dict(os.environ)
        )
        with errlog.open("w", encoding="utf-8") as errfile:
            async with stdio_client(params, errlog=errfile) as (read, write):
                async with ClientSession(read, write) as s:
                    await s.initialize()
                    return await s.call_tool("runs", {"from": "scaling/lr-sweep", "limit": 1})

    result = anyio.run(main)
    assert not result.is_error
    assert "not listed in the process registry" in errlog.read_text(encoding="utf-8")


def test_mcp_call_survives_a_failed_registry_update(
    project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A registry that vanishes after start costs the client's name, not the tool call."""
    runtime = tmp_path / "rt"
    monkeypatch.setenv("BEAMTIME_RUNTIME", str(runtime))
    errlog = tmp_path / "err.txt"

    async def main():
        params = StdioServerParameters(
            command=str(BEAMTIME), args=["mcp"], cwd=str(project), env=dict(os.environ)
        )
        with errlog.open("w", encoding="utf-8") as errfile:
            async with stdio_client(params, errlog=errfile) as (read, write):
                async with ClientSession(read, write) as s:
                    await s.initialize()
                    shutil.rmtree(runtime / "procs")
                    return await s.call_tool("runs", {"from": "scaling/lr-sweep", "limit": 1})

    result = anyio.run(main)
    assert not result.is_error
    assert "not listed in the process registry" in errlog.read_text(encoding="utf-8")


def test_mcp_without_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Outside a project the server still starts and registers, with the working directory as root."""
    from beamtime.index.procs import listed

    monkeypatch.setenv("BEAMTIME_RUNTIME", str(tmp_path / "rt"))
    where = tmp_path / "nowhere"
    where.mkdir()

    async def main():
        params = StdioServerParameters(
            command=str(BEAMTIME), args=["mcp"], cwd=str(where), env=dict(os.environ)
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as s:
                await s.initialize()
                return listed()[0]

    [record] = anyio.run(main)
    assert record["kind"] == "mcp" and record["root"] == str(where.resolve())
