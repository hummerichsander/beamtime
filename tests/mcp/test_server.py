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
        prompt = await s.get_prompt("review", {"folder": "scaling"})
        return ok, bad, prompt

    ok, bad, prompt = session(project, work)
    answer = json.loads(ok.content[0].text)
    assert not ok.is_error and answer["kind"] == "runs" and len(answer["rows"]) == 2
    assert bad.is_error and "Did you mean 'scaling'" in bad.content[0].text
    assert "scaling" in prompt.messages[0].content.text
