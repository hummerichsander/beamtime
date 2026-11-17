"""Probe: does Claude Code reload the tool list after ``tools/list_changed``?

Runs one ``claude -p`` session against a stub stdio server with tools ``a`` and ``more``; ``more``
adds ``b`` and sends the notification. Prints ``reloaded: yes`` when the session called ``b``
successfully.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import anyio
import mcp_types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.stdio import stdio_server

PROMPT = "Call the tool `more` of the stub server, then the tool `b`. Say what `b` answered."
TOOLS = {
    name: types.Tool(name=name, input_schema={"type": "object"}) for name in ("a", "more", "b")
}


def stub() -> Server:
    """Build the stub server.

    :return: The server."""
    listed = ["a", "more"]

    async def list_tools(ctx, params) -> types.ListToolsResult:
        return types.ListToolsResult(tools=[TOOLS[name] for name in listed])

    async def call_tool(ctx, params) -> types.CallToolResult:
        if params.name == "more":
            listed.append("b")
            await ctx.session.send_tool_list_changed()
        return types.CallToolResult(content=[types.TextContent(text=f"{params.name} ok")])

    return Server("stub", on_list_tools=list_tools, on_call_tool=call_tool)


async def serve() -> None:
    """Serve the stub over stdio."""
    server = stub()
    async with stdio_server() as (read, write):
        await server.run(
            read,
            write,
            server.create_initialization_options(NotificationOptions(tools_changed=True)),
        )


def called(transcript: str, tool: str) -> bool:
    """Tell whether a stream-json transcript holds a successful call of a stub tool.

    :param transcript: The session's stdout.
    :param tool: The tool name without prefix.
    :return: Whether the call ran and did not fail."""
    ids, failed = set(), set()
    for line in transcript.splitlines():
        try:
            message = json.loads(line)
        except ValueError:
            continue
        content = (message.get("message") or {}).get("content")
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use" and block.get("name") == f"mcp__stub__{tool}":
                ids.add(block["id"])
            if block.get("type") == "tool_result" and block.get("is_error"):
                failed.add(block.get("tool_use_id"))
    return bool(ids - failed)


def main() -> None:
    """Run the session and print the verdict."""
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory() as tmp:
        config = Path(tmp) / "mcp.json"
        stub_config = {"command": sys.executable, "args": [str(Path(__file__).resolve()), "--stub"]}
        config.write_text(json.dumps({"mcpServers": {"stub": stub_config}}))
        command = [
            "claude", "-p", PROMPT, "--output-format", "stream-json", "--verbose",
            "--strict-mcp-config", "--mcp-config", str(config), "--allowedTools", "mcp__stub__*",
        ]  # fmt: skip
        done = subprocess.run(command, capture_output=True, text=True, timeout=120, cwd=tmp)
    if "--verbose" in sys.argv:
        print(done.stdout, done.stderr)
    print(f"claude: {version}")
    print(f"reloaded: {'yes' if called(done.stdout, 'b') else 'no'}")


if __name__ == "__main__":
    if "--stub" in sys.argv:
        anyio.run(serve)
    else:
        main()
