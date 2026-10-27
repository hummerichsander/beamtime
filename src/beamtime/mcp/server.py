"""The MCP server: the operations as tools over stdio, plus prompts."""

import json
from pathlib import Path
from typing import Any

import anyio
import mcp_types as types
import msgspec
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL, Op

INSTRUCTIONS = (
    "Beamtime records ML experiments as run folders below a log dir. Start in an "
    "unfamiliar folder with `keys`; check `status` before working with live runs. "
    "Answers are cut at about 8k tokens; pass `cursor` from `meta.next` for more. "
    "User-only commands (serve, init, mv, rm, gc, settings, doctor, reindex) are not "
    "tools: give the user the command."
)


def schema(op: Op) -> dict[str, Any]:
    """Build a tool's input schema from its parameter struct.

    :param op: The operation.
    :return: A JSON schema with ``type: object`` at the root."""
    full = msgspec.json.schema(op.params)
    defs = full.get("$defs", {})
    root = dict(defs.pop(full["$ref"].split("/")[-1]))
    root.pop("title", None)
    root.pop("description", None)
    if defs:
        root["$defs"] = defs
    return root


def tools() -> list[types.Tool]:
    """List the tools: every operation except the user-only commands.

    :return: The tool definitions."""
    return [
        types.Tool(name=name, description=op.summary, input_schema=schema(op))
        for name, op in BY_TOOL.items()
    ]


def text(paragraph: str) -> str:
    """Join a wrapped paragraph into one line.

    :param paragraph: The paragraph as written in the source.
    :return: The paragraph with single spaces."""
    return " ".join(paragraph.split())


PROMPTS: dict[str, tuple[str, list[tuple[str, str, bool]], str]] = {
    "review": (
        "Summarize what changed in a folder since a date: new runs, checks, failures.",
        [
            ("folder", "the folder, e.g. scaling/lr-sweep", False),
            ("since", "a date like 2026-10-25; default: the last day", False),
        ],
        text(
            """Review what happened in Beamtime folder {folder} since {since}. Use
            `timeline` (from, since) for events and notes, `runs` sorted by
            -run.created_at for new runs with their key metrics, and `card` plus
            `output` (tail) for every failed, killed or lost run. Report what ran,
            what finished, what failed and why, which curves look off, and what to do
            next. Be concise; cite run ids."""
        ),
    ),
    "debug": (
        "Find out why a run failed, from its output, card and curves.",
        [("run", "the run id", True)],
        text(
            """Find out why Beamtime run {run} failed or misbehaved. Read its `card`
            (status, error, warnings, recent events), its `output` (tail 80, then grep
            for Error|Traceback|nan if needed) and the `series` of its loss near the
            end. Name the cause, the evidence and a fix. If the run is still running,
            say so and check `status` for freshness."""
        ),
    ),
    "compare": (
        "Compare two runs, groups or folders: config differences and metric deltas.",
        [("a", "a run id or folder", True), ("b", "a run id or folder", True)],
        text(
            """Compare {a} and {b} in Beamtime. For runs, read both `card`s and list
            config differences and metric deltas (last, max, min). For folders, use
            `keys` and `runs` with the shared metrics (seeds: config.seed when there
            are seeds) and `series` grouped by the differing config key. Say which is
            better, by how much, and how sure that is given the number of runs."""
        ),
    ),
}


def prompts() -> list[types.Prompt]:
    """List the prompts.

    :return: The prompt definitions."""
    return [
        types.Prompt(
            name=name,
            description=description,
            arguments=[
                types.PromptArgument(name=a, description=d, required=r) for a, d, r in arguments
            ],
        )
        for name, (description, arguments, _) in PROMPTS.items()
    ]


def build(root: str | Path | None = None) -> Server:
    """Build the server for a project.

    :param root: The project root, or ``None`` to find it from the working directory.
    :return: The server."""
    from importlib.metadata import version

    async def list_tools(ctx: Any, params: Any) -> types.ListToolsResult:
        return types.ListToolsResult(tools=tools())

    async def call_tool(ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
        if (op := BY_TOOL.get(params.name)) is None:
            return error(f"unknown tool {params.name!r}")

        def run() -> dict[str, Any]:
            return call(op.name, params.arguments or {}, Context.make(root=root, caller="mcp"))

        try:
            answer = await anyio.to_thread.run_sync(run)
        except OpError as e:
            return error(str(e))
        text = json.dumps(answer, separators=(",", ":"), default=str)
        return types.CallToolResult(content=[types.TextContent(text=text)])

    async def list_prompts(ctx: Any, params: Any) -> types.ListPromptsResult:
        return types.ListPromptsResult(prompts=prompts())

    async def get_prompt(ctx: Any, params: types.GetPromptRequestParams) -> types.GetPromptResult:
        if params.name not in PROMPTS:
            raise ValueError(f"unknown prompt {params.name!r}")
        description, arguments, template = PROMPTS[params.name]
        given = params.arguments or {}
        values = {
            "folder": given.get("folder") or ".",
            "since": given.get("since") or "the last day",
            **{k: v for k, v in given.items() if v},
        }
        text = template.format_map(values)
        message = types.PromptMessage(role="user", content=types.TextContent(text=text))
        return types.GetPromptResult(description=description, messages=[message])

    return Server(
        "beamtime",
        version=version("beamtime"),
        instructions=INSTRUCTIONS,
        on_list_tools=list_tools,
        on_call_tool=call_tool,
        on_list_prompts=list_prompts,
        on_get_prompt=get_prompt,
    )


def error(message: str) -> types.CallToolResult:
    """Return an operation error to the agent, so it can correct itself.

    :param message: What went wrong and what to do.
    :return: The tool result."""
    return types.CallToolResult(content=[types.TextContent(text=message)], is_error=True)


async def run(root: str | Path | None = None) -> None:
    """Serve over stdio until the client disconnects.

    :param root: The project root, or ``None``."""
    server = build(root)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())
