# Lean agent surface

Base commit `9faa1fc`, branch `v0.3-benchmark`. Proposed 2026-11-17, based on the comparison benchmark's pilots
(`docs/plans/v0.3/benchmark/benchmark-plan.md`, L72) and the experiment branch `exp/lean-agent` (`b760023..9ce7b7e`,
not for merge). No breaking change to files on disk; the guide's default answer and the MCP tool list change, listed in
[Breaking changes](#breaking-changes).

Run a ticket with `/run-ticket <this file> <ID>` in a fresh session; review tickets marked `+ review` with
`/review-ticket <this file> <ID>` on a stronger model. `ticket.py status <this file>` shows what's done and what's
next.

## Goal

The outcome this plan commits to, checked against at the end and in every review:

- **Done means:** an agent working with Beamtime starts with less context and fewer failed calls, without losing any
  content. A bare `guide` is a short index of topics (the view guide is `guide views`); the rules tell agents to read
  the topic they need; the CLI accepts MCP tool names (`beamtime memory_show`) and its no-log-dir errors say how to fix
  them; the MCP server lists a core set of 19 tools and reaches the other families through the `tools_more` dispatcher.
- **Confirmed by:** the tests named per ticket; `uv run ruff check . && uv run ruff format --check . && uv run pytest -q`
  green; the MCP tool definitions of a fresh server measure under 3.5k tokens (chars / 4, `tests/mcp`); the benchmark's
  CLI and MCP sessions on seed 7 (3 reps) use at least 15 % fewer tokens than at `9faa1fc`, scores not lower (L72 of the
  benchmark plan measures it; the experiment gave −23 % CLI, −22 % MCP).
- **Out of scope:** shorter CLI `--help` texts and narrower default tables; Claude Code's own tool search (measured a
  net loss: more turns, twice as slow); changing what any operation returns.

## Findings

Evidence: **reproduced** (run), **real data** (seen in the user's data), **code** (read, not run; the ticket starts
with a failing test).

| # | Finding | Root cause | Evidence | Ticket |
|---|---|---|---|---|
| 1 | Every CLI/MCP session read ~7.7k chars at start, the largest single tool result | the rules say "Read `guide`" and a bare `guide` returns the 6.3k-char view-building guide (`guide/parts/overview.md`) | reproduced (pilot 093924) | G81 |
| 2 | Guide index alone cut CLI tokens 19 % in one rep | same | reproduced (pilot 101443) | G81 |
| 3 | CLI agents call `beamtime memory_show` and get a usage dump | the rules name tools "as over MCP"; the CLI has no underscore aliases | reproduced (transcripts) | C81 |
| 4 | Most CLI tool errors are exit 4 "no log dir" after an agent `cd`s out of the project | the message suggests `beamtime setup`, not `--root` | reproduced (27 → 16 errors with C81+G81) | C81 |
| 5 | MCP sessions carry ~9.3k tokens of tool definitions on every turn (17.8k first turn vs 8.2k CLI) | 43 tools listed; 15 view/block tools never used in analysis | reproduced | M81 |
| 6 | 19 core tools: definitions 23.3k → 12.7k chars, first turn 17.8k → 13.7k tokens | same | reproduced (pilot 102315) | M81 |
| 7 | Tool search: first turn 9.7k, but more turns, 2× slower, +23 % cost | a search turn per session | reproduced (pilot 101808) | none (Decision 5) |

## Brief

- **Guide** (G81): `guide/parts/index.md` (new) is the default answer: one line per topic, the Defaults section
  (`{{agent.defaults}}`) and nothing else; `overview.md` becomes `views.md`, topic `views`. Every topic stays listed
  in the index (test).
- **Rules** (G81): `guide/rules/rules.md` is unreleased (added after v0.2.1), so it changes in place, no history entry.
- **CLI** (C81): `cli.tool_names(argv)` rewrites the first command word when it is an MCP tool name
  (`BY_TOOL[name].name.split()`); every no-log-dir `OpError` names `--root <project>`.
- **MCP families** (M81): `mcp/server.py` holds `FAMILIES: dict[str, tuple[str, ...]]` (views, blocks, runs, export) and
  `CORE` = every other non-user tool; the listing is `CORE` plus `tools_more`, and never changes. `tools_more(family)`
  describes a family's tools as compact text; `tools_more(tool, args)` calls any known non-core tool. A known tool
  outside the listed set still runs when called directly.
- **Setting** (M82): agent knob `mcp_tools: core | all`, default `core` in every style; `all` lists everything from the
  start.
- **Probe** (S81, done): Claude Code does not reload the tool list after `list_changed` (Decision 8); hence the
  dispatcher.

Done, for every ticket: its Done line holds; its Check passes; the spec documents say what the code does; its heading
is marked done in the ticket's own commit.

## How to execute

1. Checks: first `uv sync --all-extras` (without the `serve` extra, `tests/mcp`, `tests/ops`, `tests/remote` fail on
   `mcp_types`); `uv run ruff check . && uv run ruff format --check .`; subsets per ticket; the full suite
   `uv run pytest -q -n 2` (4 workers ran out of memory on this machine). `uv` is `~/.local/bin/uv`; unset `VIRTUAL_ENV`
   if uv warns.
2. Generated files: `docs/reference/cli.md` from `uv run python docs/site/reference.py` after any change to command
   help or parameter choices (G81 adds a `guide` part; M82 none); `tests/test_docs.py` checks it. Tickets run one at a
   time in this checkout.
3. Rules: CLAUDE.md's Python style; keep the CLI path light (no module-level heavy imports, `tests/test_budgets.py`);
   never touch `tests/golden/`.
4. Spec: `docs/design/05-views.md` § The agent guide (l. 686) and `docs/design/08-cli-mcp.md` § Tools (l. 165) are the
   spec; write deviations back in the same commit.
5. Ticket budget: 140k tokens per ticket session; split a ticket that would exceed it.
6. Recording: one commit per ticket, subject `<ID>: <what changed>`, which also appends ` — **done**` to the
   ticket's heading.

## Order

What's left runs in this order: G81 C81 S81 M81 M82 Z81

```
G81 ─ C81 ─ S81 ─ M81 ─ M82 ─ Z81      one at a time (shared checkout, cli.md)
```

After Z81, the benchmark plan's L72 runs its full batches on this surface.

## Decisions taken; say if you want otherwise

1. **Short index, content kept** (your decision): the default `guide` is an index; no topic loses text. Rejected:
   trimming topics, because the A/B showed the saving comes from not loading the view guide, not from shorter text.
2. **The Defaults section moves to the index** (proposed): it lists the knobs every agent acts on, not only view
   builders; `tests/guide` reads it from the default answer as today. Rejected: keeping it in `views`, which agents
   no longer read by default.
3. **MCP tool names work on the CLI** (your decision): an alias at parse time, not new subcommands, so `--help` and
   `cli.md` do not grow.
4. **Core set plus `tools_more` by family** (your decision; reached through the dispatcher, Decision 6): families views (8 `view_*`), blocks (6 `block_*`; `block export` and `block import` are user-only), runs
   (`wait`, `resume`, `output`, `file`, `timeline`, `digest`, `plan_missing`, `name`), export (`export`, `cp`).
   Rejected: one switch for all (a view task would also pay for blocks and run tools); a static core only (views would
   become unreachable over MCP).
5. **No tool search** (your decision after the pilot): it saved on the first turn but cost a search turn, more turns
   overall and twice the time. Rejected for the benchmark and for the docs' advice.
6. **`tools_more` is a dispatcher** (your decision, after S81): `tools_more(family)` returns that family's tool
   definitions as compact text (name, summary, params with type and required flag); `tools_more(tool=<name>,
   args={...})` calls any known non-core tool, validating `args` against that tool's msgspec params exactly as a
   direct call and returning errors the same way. An unknown family errors listing the valid families; an unknown
   tool errors listing the family's tools. Under `mcp_tools: core` (default) no `tools/list_changed` is sent and the
   core listing never changes, so `NotificationOptions` is not needed; `mcp_tools: all` lists every tool directly and
   omits `tools_more`. User-only operations stay refused through it. Rejected: a user-set fallback (the agent is left
   at a dead end and the user must edit `beamtime.yaml`); defaulting to `all` (loses the MCP saving).
7. **Calling an unlisted known tool still works** (proposed): listing is only what the client sees; dispatch keeps
   `BY_TOOL`. Rejected: refusing, which would break clients that cache an older list.
8. **Claude Code does not reload the list** (measured by S81, `bench/agents/probes/list_changed.py`, claude 2.1.322, two
   runs): a stub server declared `tools: {listChanged: true}`, its tool `more` added `b` and sent
   `notifications/tools/list_changed`; the session called `more` successfully, but `b` was never offered (ToolSearch
   found only `a` and `more`) and could not be called. So a family cannot be added to the listing mid-session, and
   `tools_more` is a dispatcher (Decision 6, your decision) instead of a switch.

## G. Guide

### G81. The guide's default answer is an index (sonnet + review) — reproduced — **done**

- **Touches:** new `src/beamtime/guide/parts/index.md`; `src/beamtime/guide/parts/overview.md` → `views.md`
  (`## Defaults` and `## More` moved to the index); `src/beamtime/guide/__init__.py` (`TOPICS` 16, `guide` 78–98);
  `src/beamtime/ops/registry.py` (`GuideParams.part` 449–472); `src/beamtime/guide/rules/rules.md` (l. 7–8);
  `src/beamtime/guide/skills.py` (`SKILLS["beamtime-views"]` 7); `src/beamtime/mcp/server.py` (`INSTRUCTIONS` 19–30,
  `PROMPTS["view"]` 116); `tests/guide/test_guide.py` (`NAMES` 18, l. 56–66, 135–140, `defaults_of` 167);
  `tests/ops/test_ops.py` (`test_instructions_block` 428); `docs/design/05-views.md` § The agent guide (686–709);
  `docs/guides/agents.md` (l. 60); `docs/reference/cli.md` (generated).
- **Read:** `docs/design/05-views.md` § Progressive disclosure (l. 692); the experiment's diff
  `git show b760023 -- src/beamtime/guide src/beamtime/ops/registry.py`.
- **Check:** `uv run pytest -q -n 2 tests/guide tests/ops/test_ops.py tests/mcp tests/test_docs.py`;
  `uv run beamtime guide | wc -c` under 1500.
- **Done:** a bare `guide` returns the index with the Defaults section and every topic named; `guide views` returns
  today's overview text minus Defaults and More; the rules block says "`guide` lists its topics; read the one you need
  before working with runs, proposals, notes or views."; the `view` prompt and the views skill name `guide views`.
- **Risks:** a topic added to `TOPICS` but not to the index → `test_every_topic_is_listed_in_the_index`; the Defaults
  section lost → `test_defaults_without_agent_are_all_marked_default`; a stale block with the old line still
  recognised and updated → `test_instructions_block`.
- **Stop if:** something outside the listed files reads `overview.md` by name.

1. `index.md`: a `# Beamtime guide` heading, one line "Read the topic you need: `guide <topic>`", a bullet list
   naming every topic in `TOPICS` plus `examples` and `blocks` with a half-line each (the experiment's text is a start),
   then `## Defaults` with `{{agent.defaults}}`. About 25 lines.
2. `guide()`: `case None` reads `index.md` (plus `about(ctx, group)` as today); `"views"` joins `TOPICS` first; the
   answer's `part` is `"index"` for the default.
3. Rules line as in Done; `test_instructions_block` replaces `"Read the old guide"` against the new wording.
4. `05-views.md`: the Progressive disclosure table gets a `guide` row (index, ~300 tokens) and a `guide views` row
   (workflow, design principles, format, ~1.5k).

## C. CLI

### C81. MCP tool names on the CLI and a no-log-dir hint (sonnet) — reproduced — **done**

- **Touches:** `src/beamtime/cli/__init__.py` (new `tool_names` before `main` 328; `main` 339); `src/beamtime/ops/reading.py`
  (l. 73–75, 215); `src/beamtime/ops/authored.py` (l. 34); `src/beamtime/ops/admin.py` (l. 470); `tests/test_cli.py`;
  `docs/design/08-cli-mcp.md` § Shared conventions (l. 115).
- **Read:** the experiment's diff `git show 9ce7b7e -- src/beamtime`.
- **Check:** `uv run pytest -q -n 2 tests/test_cli.py tests/ops`; `uv run pytest -q -n0 tests/test_budgets.py`.
- **Done:** `beamtime memory_show`, `beamtime proposal_show g` and `beamtime --root P note_add ...` run as their spaced
  commands; `beamtime runs` from outside a project prints "no log dir at …; run from the project folder or pass
  `--root <project>`" and exits 4; plain commands parse as before.
- **Risks:** a value that contains `_` after `--root` (`--root my_proj runs`) → `test_tool_names_skip_root_value`; a
  group named like a tool (`beamtime runs memory_show`) is left alone → `test_tool_names_only_first_word`; the CLI path
  gets heavier → `tests/test_budgets.py`.

1. `tool_names(argv: list[str]) -> list[str]`: skip options and the value after `--root`; at the first positional, if it
   contains `_` and is in `BY_TOOL`, splice in `op.name.split()`; return `argv` unchanged otherwise. Import `BY_TOOL`
   inside the function only if `main` does not already load the registry (check `test_budgets`).
2. One wording for every no-log-dir error: `f"no log dir at {ctx.logdir}; run from the project folder or pass
   `--root <project>`"`, followed by the existing second sentence where there is one.

## S. Probe

### S81. Does Claude Code reload the tool list? (sonnet) — code — **done**

- **Touches:** new `bench/agents/probes/list_changed.py`; this plan (Decision 8 added, M81's step 3 settled).
- **Read:** the `mcp` package's low-level server: `grep -rn "list_changed\|tools_changed\|send_tool_list_changed"
  .venv/lib/python3.11/site-packages/mcp`.
- **Check:** `uv run python bench/agents/probes/list_changed.py` prints `reloaded: yes` or `reloaded: no` and the
  `claude` version.
- **Done:** the probe ran one real `claude -p` session (about $0.05) against a stub stdio server with tools `a` and
  `more`, where `more` adds `b` and sends `tools/list_changed`, and the prompt asks to call `more`, then `b`; Decision 8
  records the result and the version.
- **Stop if:** the `mcp` package has no way to send the notification from a tool handler; record that instead.

1. The stub uses the same `mcp.server.lowlevel.Server` API as `src/beamtime/mcp/server.py` (`on_list_tools`,
   `on_call_tool`), with `NotificationOptions(tools_changed=True)` in the initialization options.
2. Run `claude -p --output-format stream-json --verbose --strict-mcp-config --mcp-config <tmp>.json
   --allowedTools "mcp__stub__*"` with a 120 s timeout; `reloaded: yes` when the transcript shows a successful call
   of `b`.

## M. MCP tools

### M81. Core tools and the `tools_more` dispatcher (sonnet + review) — reproduced — **done**

- **Touches:** `src/beamtime/mcp/server.py` (`INSTRUCTIONS` 19–30, `tools` 90–97, `build` 266–318); new `FAMILIES`,
  `CORE`; `tests/mcp/test_server.py`; `docs/design/08-cli-mcp.md` § Tools (165–180); `CHANGELOG.md`.
- **Read:** Decisions 4, 6, 7; `docs/design/08-cli-mcp.md` § Token budgets (l. 206); the experiment's `edca1d7`.
- **Check:** `uv run pytest -q -n 2 tests/mcp tests/ops/test_registry.py`; the size test below.
- **Done:** a fresh server lists the 19 core tools plus `tools_more`, under 3.5k tokens (chars of the JSON / 4); the
  listing is the same after any `tools_more` call and no `tools/list_changed` is sent;
  `tools_more(family="views")` answers the eight `view_*` tools as compact text (name, summary, params with type and
  required flag); `tools_more(tool="view_show", args={...})` returns what `view_show` returns; an unknown family is an
  error naming the four families, an unknown tool an error listing the family's tools; a user-only tool through
  `tools_more` is refused as it is directly; calling `view_show` directly still works.
- **Risks:** a new operation added later belongs to no family and silently joins the core →
  `test_every_tool_is_core_or_in_one_family`; a bad `args` shape (not an object, a missing required parameter, an
  unknown key) answers the same error as the direct call → `test_tools_more_args_errors_match_direct`; a nested
  `@source/path` target routes through the dispatcher like a direct call → `test_tools_more_remote_target`; a
  user-only tool (`set`, `setup`, `serve`) called through the dispatcher stays refused →
  `test_tools_more_refuses_user_only`; the definitions outgrow the budget with `tools_more` included →
  `test_tool_definitions_under_3500_tokens`.
- **Stop if:** the dispatcher cannot share the direct call's validation and error path without duplicating it.

1. `FAMILIES` as in Decision 4; `CORE = frozenset(BY_TOOL) - union of FAMILIES`; assert at import that the families are
   disjoint and inside `BY_TOOL`.
2. `list_tools` returns `CORE` plus `tools_more` (schema: `family` one of the four with a one-line description each,
   `tool` a string, `args` an object); the listing is fixed per server, no notification, `NotificationOptions` stays
   at its default.
3. `tools_more(family)`: one line per tool, `name(param: type, other?: type): summary`, built from the op's msgspec
   params (the `schema` helper); an unknown family is an error naming the four.
4. `tools_more(tool, args)`: look the tool up in `BY_TOOL` (a family tool, not user-only), then run the same path as
   `call_tool` (`decoded`, `remote.answer`, the same error results), so factor that path into one method both call.
   An unknown tool is an error listing the family's tools when the name shares a prefix, else the families.
5. `INSTRUCTIONS`: one sentence on `tools_more`; the `view_*` sentence says to read `tools_more views` first and call
   `tools_more` with `tool` and `args`.
6. `08-cli-mcp.md` § Tools: core, families, the dispatcher, the 3.5k-token budget (replacing "about 35 small tools …
   under about 6k tokens").

### M82. The `mcp_tools` setting (sonnet) — code

- **Touches:** `src/beamtime/settings.py` (`PRESETS` 7–60, `AGENT_KEYS` 73, `AgentSettings` 141); `src/beamtime/mcp/server.py`
  (`list_tools`); `tests/test_settings.py`; `tests/mcp/test_server.py`; `docs/guides/settings.md` (table l. 61);
  `docs/design/08-cli-mcp.md` § Tools.
- **Check:** `uv run pytest -q -n 2 tests/test_settings.py tests/mcp tests/guide`.
- **Done:** `agent: {mcp_tools: all}` in `beamtime.yaml` lists every tool from the start and omits `tools_more`; the default is `core` in every
  style; an invalid value is a settings error naming `core` and `all`; the guide's Defaults section does not list it
  (it is for the user, not the agent).
- **Risks:** the setting read once at import instead of per session → `test_mcp_tools_setting_per_project`; the guide's
  defaults test breaks on the new knob → `tests/guide`.

1. Knob `mcp_tools: str` with choices `("core", "all")`, `"core"` in each preset.
2. `list_tools` reads it from `Context.make(root=root, caller="mcp").settings.agent` once per session: `all` lists
   every non-user tool without `tools_more`.

## Z. Close

### Z81. Changelog and the measurement hand-off (haiku) — code

- **Touches:** `CHANGELOG.md` (0.3.0); `docs/plans/v0.3/benchmark/benchmark-plan.md` (L72's text: run on this
  surface and report against `9faa1fc`); `bench/agents/README.md` (one line).
- **Check:** `uv run ruff check . && uv run ruff format --check . && uv run pytest -q -n 2`.
- **Done:** the changelog lists the index, the aliases, the core tools and `mcp_tools`; L72 names the Goal's 15 %
  check; the full suite is green.

## Breaking changes

| What | Before | After | Migration |
|---|---|---|---|
| `guide` (no part) | the view guide | an index of topics plus defaults | `guide views` for the old text |
| MCP tool list | all 43 tools | 19 core + `tools_more` | call `tools_more` (family, or tool and args), or set `agent: {mcp_tools: all}` |
| rules block | "Read `guide` before …" | "`guide` lists its topics; read the one you need …" | `beamtime setup --instructions` rewrites it |

## Not verified

- Whether other MCP clients reload the tool list after `tools/list_changed` (S81 measured Claude Code only, 2.1.322).
- That agents find and use `tools_more` without extra failed calls (benchmark L72).
- That the 15 % saving holds on seeds 8 and 9 and on Haiku (benchmark L72).
