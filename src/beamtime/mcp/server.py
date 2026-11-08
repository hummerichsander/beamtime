"""The MCP server: the operations as tools over stdio, plus prompts."""

import json
import mimetypes
from pathlib import Path
from typing import Any

import anyio
import mcp_types as types
import msgspec
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from beamtime import remote
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL, Op

INSTRUCTIONS = (
    "Beamtime records ML experiments as runs in groups below a log dir. Start in an "
    "unfamiliar group with `keys`; check `status` before working with live runs. "
    "Before designing an experiment read `memory_show`; before a launch write the "
    "proposal with `proposal_set`; judge results with `check` and a verdict note "
    "(`note_add`), never claiming more than the check says. Writes are additive and pass "
    "`author` (your model id). Answers are cut at about 8k tokens; pass `cursor` from "
    "`meta.next` for more. To build a group's page, read `guide` and use the `view_*` "
    "tools. User-only commands (serve, init, mv, rm, gc, settings, doctor, "
    "reindex) are not tools: give the user the command."
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
    return slim(root)


def slim(node: Any) -> Any:
    """Drop what costs agents tokens and tells them nothing: ``null`` and empty defaults, the
    ``null`` member of a nullable type (an optional parameter is left out), empty ``required`` and
    ``additionalProperties: false``.

    :param node: A JSON schema node.
    :return: The node, slimmed."""
    if isinstance(node, list):
        return [slim(x) for x in node]
    if not isinstance(node, dict):
        return node
    out = {k: slim(v) for k, v in node.items() if not (k == "default" and v in (None, [], {}))}
    if out.get("required") == []:
        del out["required"]
    # the server rejects unknown parameters anyway; the schema need not say so 40 times.
    if out.get("additionalProperties") is False:
        del out["additionalProperties"]
    if len(members := out.get("anyOf", [])) == 2 and {"type": "null"} in members:
        rest = next(m for m in members if m != {"type": "null"})
        del out["anyOf"]
        out |= rest
    return out


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
    "view": (
        "Build or improve the view of a group: the page that shows its result.",
        [
            ("group", "the group, e.g. scaling/lr-sweep", True),
            ("idea", "what the view should show; default: the group's result", False),
        ],
        text(
            """Build the Beamtime view of group {group}. Aim: {idea}. Read `guide` first
            (and `guide examples`, `guide charts`, `guide kit`), then look at the group:
            `keys`, `memory_show`,
            `proposal_show`, `check`, `notes`, `view_show` and `block_list`. Decide the one question
            the view answers and the finding the data supports, no stronger than the
            check. Start a draft with `view_new` (group, and `from` an example when the
            current view isn't a good start) and edit the file it names with your own
            tools. Run `view_validate` until no errors remain, then `view_render` and go
            through `guide checklist` for every block; fix and render again, at most two
            rounds, then ask the user if something is still off. Save with `view_save`
            (draft, message, author) and give the user the page's URL path. If the view
            uses library blocks with newer versions (`view_outdated`), offer `view_upgrade`;
            if a custom block you wrote would serve other groups, offer to promote it."""
        ),
    ),
    "review": (
        "Summarize what changed in a group since a date: new runs, checks, failures.",
        [
            ("group", "the group, e.g. scaling/lr-sweep", False),
            ("since", "a date like 2026-10-25; default: the last day", False),
        ],
        text(
            """Review what happened in Beamtime group {group} since {since}. Use
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
            """Find out why Beamtime run {run} failed or misbehaved. Read `guide analysis`
            first, then its `card`
            (status, error, warnings, recent events), its `output` (tail 80, then grep
            for Error|Traceback|nan if needed) and the `series` of its loss near the
            end. Name the cause, the evidence and a fix. If the run is still running,
            say so and check `status` for freshness."""
        ),
    ),
    "compare": (
        "Compare two runs or groups: config differences and metric deltas.",
        [("a", "a run id or group", True), ("b", "a run id or group", True)],
        text(
            """Compare {a} and {b} in Beamtime. Read `guide analysis` first, then call
            `compare` with both: it lists the config keys that differ, whether the code is
            the same and the metrics side by side. For groups with seeds, back it with
            `series` `by` the differing config key. Say which is better, by how much, and
            how sure that is given the number of runs."""
        ),
    ),
    "proposal": (
        "Write a proposal with a plan and checkable predictions before a launch.",
        [
            ("group", "the group the runs will go into", True),
            ("idea", "what the experiment is meant to show", False),
        ],
        text(
            """Write the Beamtime proposal for group {group} before any run starts, so
            every run records it. Idea: {idea}. Read `guide proposals` and
            `guide predictions` first, then read `memory_show` {group} and the
            open questions (`notes`, open) it points to, and `keys` of related groups for
            the exact metric and config names. The proposal has a one-sentence
            `statement`, a `rationale`, an optional `confidence` (0 to 1, your belief
            before any data), a `plan` (`{{runs: N}}` or `{{grid: {{config.lr: [...],
            config.seed: [0, 1, 2]}}}}`), and named `predictions`. An automatic prediction
            has `reduce: {{metric, stat: last|first|min|max|mean, steps: [a, b]}}`,
            optional `where`, `seeds: config.seed` for repetitions, and either `test: each`
            with `op` and `value` (or `ref: {{run: <id>}}`) or `test: compare` with `a`,
            `b`, `op`, `margin` and optional `pair_by`. Plan at least three seeds per point:
            the check uses t-intervals and gives `insufficient` with fewer than two. Use
            `kind: manual` with a `description` for claims a number can't decide. Save it
            with `proposal_set` (group, proposal, author) and show the user the launch
            command; you don't launch runs yourself unless asked."""
        ),
    ),
    "verdict": (
        "Judge a proposal against its check and write a verdict note.",
        [("group", "the group whose proposal is judged", True)],
        text(
            """Write the verdict on the Beamtime proposal of {group}. Read `guide verdicts`
            first, then `proposal_show`
            and `check` {group}: each prediction's result, effect, interval and points, and
            whether the result is provisional (plan not complete). Look at the evidence:
            `runs` with the predicted metrics, `series` of the key curves, and `card` plus
            `output` of failed runs. Judge every prediction as confirmed, refuted or
            inconclusive. Follow the check unless you have a reason not to, and if you
            disagree, say why in the body. Never claim more than the check supports:
            `insufficient`, `inconclusive` and provisional results stay that way. Write
            the note with `note_add` (type verdict, proposal = the version, verdict per
            prediction, overall, a one-line description, evidence with run ids and
            group#prediction links, author); the check snapshot is added automatically.
            Then update the memory (the `memory` prompt)."""
        ),
    ),
    "memory": (
        "Update and compact a group's memory from the notes since its last update.",
        [("group", "the group; . for the project", False)],
        text(
            """Update the Beamtime memory of {group}. Read `guide memory` and `guide notes`
            first, then `memory_show` {group} (the
            current memory and how many notes came since) and `notes` {group} with full
            bodies for the new ones. Rewrite the memory, don't append: keep the sections
            Current understanding, Decisions and conventions, Dead ends, Open questions and
            Active; fold concluded experiments into one line each; drop what no longer
            matters. Every line ends with a link to its evidence, like
            [[20261025-170200-m4p7]] or [[scaling/warmup#warmup-helps]]. Stay under about
            1.5k tokens. Save it with `memory_update` (group, body, author)."""
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
            context = Context.make(root=root, caller="mcp")
            return remote.answer(op.name, params.arguments or {}, context)

        try:
            answer = await anyio.to_thread.run_sync(run)
        except OpError as e:
            return error(str(e))
        return types.CallToolResult(content=content(answer))

    async def list_prompts(ctx: Any, params: Any) -> types.ListPromptsResult:
        return types.ListPromptsResult(prompts=prompts())

    async def get_prompt(ctx: Any, params: types.GetPromptRequestParams) -> types.GetPromptResult:
        if params.name not in PROMPTS:
            raise ValueError(f"unknown prompt {params.name!r}")
        description, arguments, template = PROMPTS[params.name]
        given = params.arguments or {}
        values = {
            "group": given.get("group") or ".",
            "since": given.get("since") or "the last day",
            "idea": given.get("idea") or "ask the user if it is unclear",
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


def content(answer: dict[str, Any]) -> list[Any]:
    """Turn an answer into tool content: JSON, and the screenshots of a render as images.

    :param answer: The operation's answer.
    :return: The content blocks."""
    import base64

    images = []
    for shot in answer.get("shots") or []:
        if shot.get("file") and Path(shot["file"]).is_file():
            data = base64.b64encode(Path(shot["file"]).read_bytes()).decode()
            mime = mimetypes.guess_type(shot["file"])[0] or "image/png"
            images.append(types.ImageContent(data=data, mime_type=mime))
    text = json.dumps(answer, separators=(",", ":"), default=str)
    return [types.TextContent(text=text), *images]


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
