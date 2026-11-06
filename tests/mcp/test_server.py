import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from beamtime.ops.registry import OPS
from beamtime.synth import generate

anyio = pytest.importorskip("anyio")
pytest.importorskip("mcp")

from mcp.client.session import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402

BEAMTIME = Path(sys.executable).parent / ("beamtime.exe" if sys.platform == "win32" else "beamtime")


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


def test_tools_match_the_registry(project: Path) -> None:
    """Every operation except the user-only commands is a tool, with small definitions."""

    async def work(s):
        return (await s.list_tools()).tools

    tools = session(project, work)
    expected = {op.name.replace(" ", "_") for op in OPS if not op.user_only}
    assert {t.name for t in tools} == expected
    assert all(t.input_schema["type"] == "object" for t in tools)
    size = sum(len(json.dumps(t.model_dump(exclude_none=True, by_alias=True))) for t in tools)
    assert size / 4 < 6000


def test_calls_answer_and_errors_return_to_the_agent(project: Path) -> None:
    """A tool call answers with the canonical JSON; mistakes come back as tool errors."""

    async def work(s):
        ok = await s.call_tool("runs", {"from": "scaling/lr-sweep", "limit": 2})
        bad = await s.call_tool("runs", {"from": "scalng"})
        prompt = await s.get_prompt("review", {"group": "scaling"})
        return ok, bad, prompt

    ok, bad, prompt = session(project, work)
    answer = json.loads(ok.content[0].text)
    assert not ok.is_error and answer["kind"] == "runs" and len(answer["rows"]) == 2
    assert bad.is_error and "Did you mean 'scaling'" in bad.content[0].text
    assert "scaling" in prompt.messages[0].content.text


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
        return saved, yaml_text, note, theory, bad, memory, shown, prompts

    saved, yaml_text, note, theory, bad, memory, shown, prompts = session(project, work)
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
    assert all("agent/dropout" in t for t in texts)
