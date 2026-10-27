# Layer 8: CLI and MCP

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

The CLI and the MCP server are how people and agents work with Beamtime outside the browser. Both are
thin frontends over one set of **operations**, which is also the API of `serve`
([layer 4](04-remotes.md#protocol)) and what the web UI calls.

## Principles

1. **One operation set, several frontends.** Every operation has a CLI command and, unless it is a
   user-only command, an MCP tool with the same parameters and answer.
2. **One naming rule.** The MCP tool is the CLI command path with `_` for spaces:
   `beamtime note add` ↔ `note_add`, `beamtime runs` ↔ `runs`.
3. **Fast.** A one-shot command answers in about 60–100 ms including Python startup: standard-library
   argument parsing, lazy imports, no NumPy, an installed console script rather than `uv run`. The
   import time is checked in CI.
4. **Small answers by default.** More must be asked for, and every answer says when it was cut and how
   to get the rest.
5. **Errors that help.** Every error says what went wrong and what to do, with the closest matches for
   unknown names.
6. **Agent writes are additive.** Nothing an agent can do deletes data; writes create new files.

## Operations

Folders are paths below the log dir; `@cluster/scaling` names a remote folder; a run id works
wherever a folder does.

### Reading (CLI and MCP)

| CLI | MCP | Does |
|---|---|---|
| `beamtime status` | `status` | daemon, indexer, sources and remotes, freshness, the web UI's URL |
| `beamtime guide [part] [folder]` | `guide` | the agent guide ([layer 5](05-views.md#the-agent-guide)) |
| `beamtime memory show <folder>` | `memory_show` | the memory of the folder and every folder above it, with a staleness hint |
| `beamtime keys <folder>` | `keys` | metrics, config keys, data keys and tags |
| `beamtime folders <folder>` | `folders` | the folder tree with status, proposal, check, verdict and run counts |
| `beamtime runs <folder>` | `runs` | a run table: `--where`, `--select`, `--sort`, `--limit` |
| `beamtime card <run>` | `card` | one run's card with its proposals' checks, verdicts and latest notes |
| `beamtime series <folder> -y <key>` | `series` | curves: `--steps`, `--points`, `--group`, `--seeds` |
| `beamtime data <folder> <key>` | `data` | logged tables, images (as references) and text |
| `beamtime file <view-folder> <path>` | `file` | a data file stored with a view |
| `beamtime output <run>` | `output` | captured output: `--tail`, `--grep`, `--rank` |
| `beamtime timeline <folder>` | `timeline` | notes and events in time order: `--types`, `--since` |
| `beamtime notes <folder>` | `notes` | notes with descriptions; `--open` for open questions, `--full` for bodies |
| `beamtime proposal show <folder>` | `proposal_show` | the current proposal version, its earlier versions and their checks |
| `beamtime check <folder>` | `check` | the predictions of the current proposal and their results |
| `beamtime importance <folder> --target <field>` | `importance` | hyperparameter importance (v1.1) |
| `beamtime query <file or {…}>` | `query` | any query in its object form ([layer 3](03-index.md#query-language)) |

### Writing (CLI and MCP)

| CLI | MCP | Does |
|---|---|---|
| `beamtime note add <folder>` | `note_add` | a note: `--type`, `--description`, `--resolves`, `--supersedes`, `--completes`, `--evidence`; for verdicts `--proposal <version>`, `--verdict <prediction>=<verdict>`, `--overall`; the check snapshot is added automatically; body from stdin |
| `beamtime proposal set <folder> <file>` | `proposal_set` | saves a new proposal version; superseding a frozen version requires `--reason` |
| `beamtime memory update <folder> <file>` | `memory_update` | saves a new memory version; warns beyond the size budget |

### Views and blocks (CLI and MCP)

| CLI | MCP | Does |
|---|---|---|
| `beamtime view new <folder> [--from <example>]` | `view_new` | starts a draft |
| `beamtime view validate <draft>` | `view_validate` | validation ([layer 5](05-views.md#validation)) |
| `beamtime view render <draft>` | `view_render` | screenshots (PNG files in the CLI, images in MCP) |
| `beamtime view save <draft>` | `view_save` | saves a new view version |
| `beamtime view show <folder>` | `view_show` | the current view's YAML, pins and version |
| `beamtime view history <folder>` | `view_history` | the version list |
| `beamtime view outdated [folder]` | `view_outdated` | views pinned to older block versions |
| `beamtime view upgrade <view> [--block <name>]` | `view_upgrade` | re-pins and validates a view |
| `beamtime block list [folder]` | `block_list` | library blocks with descriptions |
| `beamtime block promote <view> <block-id> <name>` | `block_promote` | turns a custom block into a library block |
| `beamtime block fork <name> <new-name>` | `block_fork` | copies a block as a starting point |
| `beamtime block validate <draft>` | `block_validate` | checks a block draft |
| `beamtime block save <draft>` | `block_save` | saves a new block version |
| `beamtime export <folder>` | `export` | `--html`, `--figures`, `--points` ([layer 7](07-web-ui.md#static-export)) |

### User-only commands (CLI only)

These change the project or the machine. They are not MCP tools, and agents don't run them; they give
the user the command ([Policy](#policy)).

| Command | Does |
|---|---|
| `beamtime init` | sets up a project: adds the log dir to `.gitignore`, optionally creates `beamtime.yaml`, offers `mcp install` |
| `beamtime mcp install --client <name>` | registers `beamtime mcp` with an agent client (Claude Code, Codex, Cursor, …) |
| `beamtime demo` | generates a sample log dir from the evaluation generator and serves it |
| `beamtime doctor` | checks root and log dir resolution, write access, Chromium, remote reachability and the remote's Beamtime version |
| `beamtime settings` | the effective settings and the level each value comes from |
| `beamtime serve [sources…]` | the web UI, indexer and remote connections; `--no-ui`, `--port`, `--cache` |
| `beamtime pull <source>:<folder>` | a read-only offline snapshot; `--drop` removes it |
| `beamtime mv <run> <folder>` | moves a run; refuses running runs |
| `beamtime rm <run or folder>` | moves it into `_trash/` ([layer 1](01-storage.md#deleting-and-cleaning-up)) |
| `beamtime gc` | empties the trash and removes crashed runs without metrics |
| `beamtime reindex` | rebuilds the index from the files |
| `beamtime block export <name> <folder>`, `beamtime block import <folder>` | copy blocks between projects |
| `beamtime theme list`, `beamtime theme use <name>` | themes ([layer 5](05-views.md#theme)) |

Internal entry points: `beamtime serve --stdio` (started by a laptop over ssh) and `beamtime mcp` (the
MCP server, started by an agent client).

### Shared conventions

- **Global flags**: `--root` (another project), `--json` (the canonical answer), `--quiet`.
- **Writes take `--author`** (a person or model id; default: the local account) and record `user`, the
  local account ([research record](09-research-record.md#fields)).
- **Exit codes**: `0` success, `1` error, `2` wrong usage, `3` validation found errors, `4` not found.

## Output

- **Text by default, the same in a terminal and in a pipe**, so agents see what people see. Only
  terminal styling is dropped in a pipe. Text costs agents roughly a third of the tokens of the same
  answer as JSON. It is compact: aligned columns without box drawing, compact numbers, one line per
  item, and a final line with meta:

  ```
  $ beamtime runs scaling/lr-sweep --select config.lr,metric.val/acc.max --sort -metric.val/acc.max --limit 3
  run                       config.lr  val/acc.max
  boosted-kaon-42           3e-4       0.931
  prompt-photon-7           1e-4       0.924
  displaced-muon-13         1e-3       0.918
  3 of 20 runs · live (daemon running) · --limit to see more
  ```

- **`--json`** gives the canonical answer of [layer 3](03-index.md#answers), identical to MCP.
- **Curves in text** are a short summary per run (first, min, max, last, trend) with a sparkline.

## MCP

### Transport

`beamtime mcp` speaks MCP over stdio. `beamtime mcp install` registers it with a client; on a cluster
without a local Beamtime, the client runs `ssh cluster beamtime mcp`. Through a running local
`serve`, MCP sees all sources, local and remote. MCP over HTTP comes with the server
([layer 6](06-server.md)).

### Tools

The tools are the operations above, without the user-only commands: about 35 small tools.

- **Small definitions.** Each tool has a short description and a precise schema; how to use them well
  lives in `guide`, loaded on demand. All tool definitions together stay under about 6k tokens.
- **Writes take `author`**, the model id.
- **`view_render` returns images** scaled to about 1280 px wide, one for the page and one per block
  on request.
- **`data` returns images as references** and loads them only when asked, as thumbnails first.

### Prompts

MCP prompts appear as slash commands in clients such as Claude Code (`/beamtime:view`):

| Prompt | Starts |
|---|---|
| `view` | build or improve the view of a folder |
| `proposal` | write a proposal with a plan and checkable predictions before a launch |
| `review` | summarize what changed in a folder since a date: new runs, checks, failures |
| `debug` | find out why a run failed, from its output, card and curves |
| `verdict` | evaluate a proposal against its runs and write a verdict note |
| `compare` | compare two runs, groups or folders: config differences, metric deltas, and a temporary view if it helps |
| `report` | summarize a folder for others: findings, verdicts, open questions, as a view or an export |
| `memory` | update and compact a folder's memory from the notes added since it was last written |

### Token budgets

| Answer | Default | Override |
|---|---|---|
| run table | 50 rows | `limit` |
| curves | 100 points per curve | `points` |
| notes, timeline | descriptions only, 30 entries | `full`, `limit` |
| output | last 50 lines | `tail`, `grep` |
| any answer | about 8k tokens; beyond that the answer is cut and returns a `next` cursor | `cursor` |

Every answer carries meta: freshness, whether it was cut or downsampled, how many items matched, and
a hint for getting more.

## Policy

The guide states these as defaults ([layer 5](05-views.md#defaults)):

- **User-only commands are never run by agents**, neither through MCP (they are not tools) nor
  through the agent's own shell. The agent gives the user the exact command to enter, e.g.
  `beamtime serve --no-ui` or `beamtime rm 20261024-101532-k3m9xq2a`. This is an instruction, not an
  enforcement: Beamtime cannot tell who types a command.
- **Agent writes are additive**: notes, proposal versions (a frozen version is superseded with a
  reason, never edited), memory versions, view and block versions, exports.
- **Live data**: before working with running runs, agents check `status`; if no daemon runs, they ask
  the user to start `beamtime serve --no-ui`.

## Implementation notes

- **Argument parsing with `argparse`**, with each command's module imported only when it runs.
- **The MCP server** uses the official MCP Python SDK in `beamtime[serve]`, through its low-level
  server API, with tool schemas generated from the same msgspec structs as the CLI and the API.

## Implementation notes

Decided while building the CLI and MCP server (milestone M3):

- **One registry** (`beamtime.ops.registry`) holds every operation: its CLI path, a msgspec parameter
  struct, a one-line summary and whether it is user-only. CLI flags and MCP tool schemas are generated
  from the same structs; implementations are imported only when an operation runs, which keeps
  `beamtime runs` at about 100–120 ms.
- **`beamtime query`** takes a file or an inline object as its argument (`beamtime query '{runs:
  {from: .}}'`), since `--json` is the global flag for JSON output.
- **Exit codes**: an invalid query or bad flag is wrong usage (2); a missing folder, run or key is 4.
- **Text output** puts the run name first and the full run id last, so agents can copy ids; seed
  groups show how many runs they have (`--json` lists them); curves are one line each with first,
  min, max, last, a trend arrow and a sparkline.
- **Runs can be named by a unique id suffix or by name** in `card`, `output`, `mv` and `rm`.
- **Cursors** are offsets into the answer's items; answers above about 8k tokens (32k characters of
  JSON) are cut at whole items with `meta.next`. `output` keeps the last lines instead.
- **MCP answers** are the canonical answer as compact JSON, with `null` meta fields dropped; operation
  errors are tool errors with the same message, so agents can correct themselves. Parameters that
  agents can't guess (`where`, `select`, `sort`, `seeds`, `y`, `x`, `steps`, `query`) carry short
  descriptions; all tool definitions together are about 2k tokens.
- **Prompts in M3**: `review`, `debug` and `compare`, which need only reading; `view`, `proposal`,
  `verdict`, `report` and `memory` follow with the milestones that add their tools.
- **`mcp install`** registers `beamtime --root <project> mcp`, so a client that keeps one
  user-wide config (Codex) still points at the right project. Claude Code uses
  `claude mcp add --scope project`, Cursor `.cursor/mcp.json`.
- **`gc` is a dry run** unless given `--yes`; `rm` and `mv` refuse runs whose heartbeat is fresh.

## Decisions

- One operation set behind CLI, MCP, the web UI and the remote API; MCP tool names follow the CLI path.
- User-only commands (setup, serving, settings, moving, deleting, themes, block import and export)
  exist only in the CLI and are never run by agents.
- Compact text output, identical in terminals and pipes; `--json` for the canonical answer. Exit codes
  distinguish errors, usage, validation failures and missing items.
- MCP over stdio (`beamtime mcp`, also over ssh), with about 35 small tools, eight prompts, and token
  budgets with cursors.
- `beamtime init`, `demo`, `doctor` and `mcp install` cover onboarding.
