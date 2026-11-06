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

Groups are paths below the log dir; `@cluster/scaling` names a remote group; a run id works
wherever a group does.

### Reading (CLI and MCP)

| CLI | MCP | Does |
|---|---|---|
| `beamtime status` | `status` | daemon, indexer, sources and remotes, freshness, the web UI's URL |
| `beamtime guide [part] [group]` | `guide` | the agent guide ([layer 5](05-views.md#the-agent-guide)) |
| `beamtime memory show <group>` | `memory_show` | the memory of the group and every group above it, with a staleness hint |
| `beamtime keys <group>` | `keys` | metrics, config keys, data keys and tags |
| `beamtime groups <group>` | `groups` | the group tree with status, proposal, check, verdict and run counts |
| `beamtime runs <group>` | `runs` | a run table: `--where`, `--select`, `--sort`, `--limit` |
| `beamtime card <run>` | `card` | one run's card with its proposals' checks, verdicts and latest notes |
| `beamtime series <group> -y <key>` | `series` | curves: `--steps`, `--points`, `--by`, `--seeds` |
| `beamtime data <group> <key>` | `data` | logged tables, images (as references) and text |
| `beamtime file <view-group> <path>` | `file` | a data file stored with a view |
| `beamtime output <run>` | `output` | captured output: `--tail`, `--grep`, `--rank` |
| `beamtime resume <run>` | `resume` | what's needed to resume a killed or failed run by hand: command, cwd, step, checkpoint; it runs nothing |
| `beamtime timeline <group>` | `timeline` | notes and events in time order: `--types`, `--since` |
| `beamtime notes <group>` | `notes` | notes with descriptions; `--open` for open questions, `--current` without superseded notes, `--full` for bodies |
| `beamtime proposal show <group>` | `proposal_show` | the current proposal version, its earlier versions and their checks |
| `beamtime check <group>` | `check` | the predictions of the current proposal and their results |
| `beamtime importance <group> --target <field>` | `importance` | hyperparameter importance (v1.1) |
| `beamtime query <file or {…}>` | `query` | any query in its object form ([layer 3](03-index.md#query-language)) |

### Writing (CLI and MCP)

| CLI | MCP | Does |
|---|---|---|
| `beamtime note add <group>` | `note_add` | a note: `--type`, `--description`, `--resolves`, `--supersedes`, `--completes`, `--evidence`; for verdicts `--proposal <version>`, `--verdict <prediction>=<verdict>`, `--overall`; the check snapshot is added automatically; body from stdin |
| `beamtime name <run> <name>` | `name` | gives a run a display name (a new version in its `name/` folder) |
| `beamtime cp <run or group> <dest-group>` | `cp` | copies it under a new run id (or ids); `--name`, `--with-checkpoints`, `--with-record`; never modifies the source ([layer 1](01-storage.md#_artifactsjsonl)); on one remote (`@au/a @au/b`), across sources refused ([layer 4](04-remotes.md#routing-and-merging)) |
| `beamtime note rm <id>` | – | user only: moves a note and the versions it replaced to the trash |
| `beamtime proposal set <group> <file>` | `proposal_set` | saves a new proposal version; superseding a frozen version requires `--reason` |
| `beamtime memory update <group> <file>` | `memory_update` | saves a new memory version; warns beyond the size budget |

### Views and blocks (CLI and MCP)

| CLI | MCP | Does |
|---|---|---|
| `beamtime view new <group> [--from <example>] [--name <draft>]` | `view_new` | starts a draft in `.beamtime/drafts/<name>/` |
| `beamtime view validate <draft>` | `view_validate` | validation ([layer 5](05-views.md#validation)) |
| `beamtime view render <draft> [--block <id>] [--theme light\|dark] [--width <px>]` | `view_render` | screenshots (JPEG files in the CLI, images in MCP); a page shot is capped to 2,520 px tall, with `cut` naming what fell below it |
| `beamtime view save <draft> [--message <text>]` | `view_save` | saves a new view version; refuses a draft with errors |
| `beamtime view show <group> [--version <v>]` | `view_show` | the current view's YAML, pins and version |
| `beamtime view history <group>` | `view_history` | the version list |
| `beamtime view outdated [group]` | `view_outdated` | views pinned to older block versions |
| `beamtime view upgrade <group> [--block <name>]` | `view_upgrade` | re-pins to the newest block versions, validates, saves a new view version |
| `beamtime block list [group]` | `block_list` | library blocks available in a group, with descriptions and params |
| `beamtime block show <name> [group] [--version <v>]` | `block_show` | a block's definition and code |
| `beamtime block promote <group> <block-id> <name>` | `block_promote` | a block draft from a custom block of the group's view |
| `beamtime block fork <name> <new-name> [group]` | `block_fork` | a block draft copied from a block (`derived_from`) |
| `beamtime block validate <draft>` | `block_validate` | checks a block draft, rendering its examples |
| `beamtime block save <draft> [--group <g>] [--message <text>]` | `block_save` | saves a new block version |
| `beamtime export <group>` | `export` | `--html <dir>` or `--figures <dir>`, `--points`, `--size` ([layer 7](07-web-ui.md#static-export)) |

### User-only commands (CLI only)

These change the project or the machine. They are not MCP tools, and agents don't run them; they give
the user the command ([Policy](#policy)).

| Command | Does |
|---|---|
| `beamtime init` | sets up a project: adds the log dir to `.gitignore`, optionally creates `beamtime.yaml`, offers `mcp install`; `--instructions` adds Beamtime's agent rules to `AGENTS.md` (or `CLAUDE.md`) |
| `beamtime mcp install --client <name>` | registers `beamtime mcp` with an agent client (Claude Code, Codex, Cursor, …); `--instructions` adds the agent rules to the client's instruction file (`CLAUDE.md` for Claude Code, else `AGENTS.md`) |
| `beamtime demo [dir]` | generates a sample log dir from the evaluation generator (once, in `beamtime-demo/`) and serves it |
| `beamtime doctor` | checks root and log dir resolution, write access, Chromium, remote reachability and the remote's Beamtime version |
| `beamtime settings` | the effective settings and the level each value comes from |
| `beamtime serve [sources…]` | the web UI, indexer and remote connections (`cluster`, `cluster:group`, `host:/abs/path`); `--no-ui`, `--port` (default 8080, else the next free port), `--open`, `--watch` (restart on the same port when Beamtime's own code changes, for working on Beamtime), `--cache` (for the remotes); `--stdio` is what a laptop starts on a remote over ssh |
| `beamtime pull <source>:<group>` | a read-only offline snapshot; `--drop` removes it |
| `beamtime source add <name> <host:/path>`, `beamtime source list`, `beamtime source rm <name>` | configure remotes in the user settings (`--project`: `beamtime.yaml`); `add` probes ssh for the command unless given `--command` ([layer 4](04-remotes.md#configuration)) |
| `beamtime mv <run> <group>`, `beamtime mv <group> <new path>` | moves a run, or moves or renames a group (recorded in `_moves.jsonl`); refuses running runs |
| `beamtime rm <run or group>` | moves it into `_trash/` ([layer 1](01-storage.md#deleting-and-cleaning-up)) |
| `beamtime gc` | empties the trash and removes crashed runs without metrics |
| `beamtime reindex` | rebuilds the index from the files |
| `beamtime block export <name> [group] --to <dir>`, `beamtime block import <group> --from <path or git-url[@ref]>` | copy blocks between projects and git repositories ([layer 5](05-views.md#location)) |
| `beamtime set <key> <value>` | writes `theme`, `theme_mode` or `figure_style` into the project's `beamtime.yaml` (the web UI's settings page does the same) |
| `beamtime theme list`, `beamtime theme use <name>` | themes ([layer 5](05-views.md#theme)) |

Internal entry points: `beamtime serve --stdio` (started by a laptop over ssh) and `beamtime mcp` (the
MCP server, started by an agent client).

### Shared conventions

- **Global flags**: `--root` (another project), `--json` (the canonical answer), `--quiet`.
- **Writes take `--author`** (a person or model id; default: the local account) and record `user`, the
  local account ([research record](09-research-record.md#fields)).
- **Exit codes**: `0` success, `1` error, `2` wrong usage, `3` validation found errors, `4` not found.
- **Conditions** (`--where`, repeatable, combined with AND): field, operator, value, e.g.
  `config.lr<1e-3`, `run.status!=failed`, `run.name~lr-*`, `config.seed in 0,1,2`. Operators are
  `= != < <= > >= ~` (glob) and `in`; the first one outside quotes and brackets counts, so a field
  may be `config["a<b"]`. Values are numbers, `true`, `false`, `null` or text; quoted values stay
  text (`config.tag="1"`), and `in` items may be quoted to hold commas.

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
  on request. A page taller than `SHOT_HEIGHT` is clipped there, not shrunk: height, not width, is
  what costs visual tokens. `cut` ({page_height, shown_height, blocks_below}) names what fell
  below, so an agent calling `view_render --block <id>` for one of them knows it is looking at a
  block it hadn't already seen.
- **`data` returns images as references** and loads them only when asked, as thumbnails first.

### Prompts

MCP prompts appear as slash commands in clients such as Claude Code (`/beamtime:view`):

| Prompt | Starts |
|---|---|
| `view` | build or improve the view of a group |
| `proposal` | write a proposal with a plan and checkable predictions before a launch |
| `review` | summarize what changed in a group since a date: new runs, checks, failures |
| `debug` | find out why a run failed, from its output, card and curves |
| `verdict` | evaluate a proposal against its runs and write a verdict note |
| `compare` | compare two runs or groups: config differences, metric deltas, and a temporary view if it helps |
| `report` | summarize a group for others: findings, verdicts, open questions, as a view or an export |
| `memory` | update and compact a group's memory from the notes added since it was last written |

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
  reason, never edited), memory versions, view and block versions, exports, run copies (`cp` only
  ever adds a new run; it never touches the source).
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
- **Exit codes**: an invalid query or bad flag is wrong usage (2); a missing group, run or key is 4.
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
- **Prompts in M3**: `review`, `debug` and `compare`, which need only reading. M4 adds `proposal`,
  `verdict` and `memory`; `view` and `report` follow with the milestones that add their tools.
- **Two-word commands** (`note add`, `proposal show`, `proposal set`, `memory show`,
  `memory update`, `mcp install`) sit under a group command; a bare group prints its help.
- **Writes (M4).** `note add` and `memory update` read the body from stdin, `proposal set` the
  proposal, when no file is given; MCP passes `body`, or `proposal` as an object or YAML text.
  `--verdict prediction=verdict` and `--evidence` repeat; evidence is a run id, note id,
  `group#prediction`, `group@view-version` or an object such as `{metric, stat, run, value}`, and
  the run and note ids must exist. `--reason` fills `supersedes` with the current version. A write
  to a missing group creates it (not a reserved name, not inside a run), so a proposal can precede
  the first run. `author` defaults to the local account in the CLI and to `agent` in MCP, whose
  instructions ask for the model id. Validation errors exit with 3.
- **`status`** reports how many notes were added since the project memory's `covers_until`.
- **The agent rules** (`--instructions`) come from the guide package (`guide/parts/instructions.md`)
  and are written as one block between `<!-- beamtime:start -->` and `<!-- beamtime:end -->`; a
  rerun replaces the block and keeps the rest of the file.
- **`mcp install`** registers `beamtime --root <project> mcp`, so a client that keeps one
  user-wide config (Codex) still points at the right project. Claude Code uses
  `claude mcp add --scope project`, Cursor `.cursor/mcp.json`.
- **`gc` is a dry run** unless given `--yes`; `rm` and `mv` refuse runs whose heartbeat is fresh.
- **`serve` and `demo`** (M5) are user-only operations in the registry. `serve` refuses to start
  when another `serve` holds the root's lock and names its URL; Ctrl-C and SIGTERM stop it cleanly.
  The API of the web UI is the registry's non-user-only operations under their MCP names
  ([layer 7](07-web-ui.md#implementation-notes)).
- **Remotes** (M8): operations route by the source their target names (`@cluster/...`), listings on
  `.` merge ([layer 4](04-remotes.md#routing-and-merging)). Writes to a remote group record the
  laptop's author and the remote account as `user`. `pull` and `doctor` reach remotes through the
  same protocol; `status` lists the sources with their state.

## Decisions

- One operation set behind CLI, MCP, the web UI and the remote API; MCP tool names follow the CLI path.
- User-only commands (setup, serving, settings, moving, deleting, themes, block import and export)
  exist only in the CLI and are never run by agents.
- Compact text output, identical in terminals and pipes; `--json` for the canonical answer. Exit codes
  distinguish errors, usage, validation failures and missing items.
- MCP over stdio (`beamtime mcp`, also over ssh), with about 35 small tools, eight prompts, and token
  budgets with cursors.
- `beamtime init`, `demo`, `doctor` and `mcp install` cover onboarding.
