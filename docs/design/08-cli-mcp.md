# Layer 8: CLI and MCP

Status: **draft, under discussion**

The CLI and the MCP server are how people and agents work with Beamtime outside the browser. Both
are thin frontends over the same core library and the same API ([layer 4](04-remotes.md#protocol));
everything one can do, the other can too, with the exceptions listed under [Policy](#policy).

## Principles

1. **One surface, two clients.** Every MCP tool has a CLI command with the same name, parameters and
   answer; the CLI adds commands for setup and administration.
2. **Fast.** A one-shot command answers in about 60–100 ms including Python startup
   ([layer 3](03-index.md#benchmarks)): standard-library argument parsing, lazy imports, no NumPy on
   the hot path, an installed console script rather than `uv run`.
3. **Small answers by default.** Defaults keep output short; more must be asked for. Every answer
   says when it was cut and how to get the rest.
4. **Errors that help.** Every error says what went wrong, why, and what to do, with the closest
   matches for unknown names.
5. **Additive writes.** Nothing an agent can do deletes data. Writes create new files (notes, view
   versions, block versions), and a frozen proposal cannot change.

## Commands

### Project and setup

| Command | Does |
|---|---|
| `beamtime init` | sets up a project: adds the log dir to `.gitignore`, optionally creates `beamtime.yaml`, offers to register the MCP server with installed agent clients |
| `beamtime status` | daemon, indexer, sources and remotes, freshness, the web UI's URL |
| `beamtime settings` | effective settings and the level each value comes from ([layer 1](01-storage.md#settings)) |
| `beamtime guide [part] [folder]` | the agent guide ([layer 5](05-views.md#the-agent-guide)) |
| `beamtime mcp install --client <name>` | registers `beamtime mcp` with an agent client (Claude Code, Codex, Cursor, …) in its own configuration |
| `beamtime reindex`, `beamtime migrate` | rebuild the index; rewrite old files to the current schema |

### Serving

| Command | Does |
|---|---|
| `beamtime serve [sources…]` | web UI, indexer and remote connections ([layer 7](07-web-ui.md)); `--no-ui`, `--port`, `--cache`, `--with <package>` |
| `beamtime serve --stdio` | API over stdin/stdout, started by a laptop over ssh ([layer 4](04-remotes.md#mode-1-remote-query)) |
| `beamtime mcp` | MCP server over stdio; `serve` also offers MCP over HTTP at `/mcp` |
| `beamtime pull <source>:<folder>` | read-only offline snapshot ([layer 4](04-remotes.md#mode-3-pull)) |

### Reading

| Command | Does |
|---|---|
| `beamtime keys <folder>` | metrics, config keys, data keys and tags in a folder |
| `beamtime runs <folder>` | run table: `--where`, `--select`, `--sort`, `--limit` |
| `beamtime card <run>` | one run's card, with its proposal check, verdict and latest notes |
| `beamtime series <folder> -y <key>` | curves: `--steps`, `--points`, `--group`, `--seeds` |
| `beamtime data <folder> <key>` | logged tables, images (as file paths) and text |
| `beamtime output <run>` | captured output: `--tail`, `--grep`, `--rank` |
| `beamtime folders <folder>` | the folder tree with proposals, checks, verdicts and run counts |
| `beamtime timeline <folder>` | notes and events in time order: `--types`, `--since` |
| `beamtime notes <folder>` | notes with descriptions; `--open` for open questions, `--full` adds bodies |
| `beamtime memory <folder>` | the memory of the folder and every folder above it, with a staleness hint |
| `beamtime check <folder>` | the proposal's predictions and their current results |
| `beamtime importance <folder> --target <field>` | hyperparameter importance |
| `beamtime query <file>` / `--json '{…}'` | any query in its object form ([layer 3](03-index.md#query-language)) |

### Writing

| Command | Does |
|---|---|
| `beamtime note <folder>` | adds a note: `--type`, `--description`, `--resolves`, `--supersedes`, `--completes`; verdicts take `--verdict <prediction>=<verdict>` and snapshot the check; body from stdin |
| `beamtime proposal <folder> [file]` | shows the current proposal version or saves a new one; a frozen version requires `--supersedes-reason` |
| `beamtime memory update <folder> [file]` | saves a new memory version |
| `beamtime mv <run> <folder>` | moves a run between folders |

### Views and blocks

| Command | Does |
|---|---|
| `beamtime view new <folder> [--from <example>]` | starts a draft, optionally from an example |
| `beamtime view validate <draft>` | validation ([layer 5](05-views.md#validation)) |
| `beamtime view render <draft>` | screenshots as PNG files |
| `beamtime view save <draft>` | saves a new version |
| `beamtime view show <folder>` | the current view's YAML, pins and version |
| `beamtime view history <folder>` | the version list |
| `beamtime view outdated [folder]`, `beamtime view upgrade <view>` | outdated block pins and upgrades |
| `beamtime block list\|promote\|fork\|validate\|save\|export` | the block library ([layer 5](05-views.md#block-library)) |
| `beamtime export <folder>` | `--html`, `--pdf`, `--figures`, `--points` ([layer 7](07-web-ui.md#static-export)) |

### Themes and packages

| Command | Does |
|---|---|
| `beamtime theme list\|use\|import\|validate` | themes ([layer 5](05-views.md#theme)) |
| `beamtime install\|remove\|update\|list\|search` | packages ([layer 5](05-views.md#packages)) |

### Shared conventions

- **Folders** are paths below the log dir; `@cluster/scaling` names a remote folder; a run id works
  wherever a folder does.
- **Global flags**: `--root` (another project), `--json` (the canonical answer), `--quiet`.
- **Writes take `--author`** (a person or a model id); `user` is the local account
  ([layer 1](01-storage.md#notes)).
- **Exit codes**: `0` success, `1` error, `2` wrong usage, `3` validation found errors, `4` not
  found. Scripts and agents can branch on them.

## Output

- **Text by default, the same in a terminal and in a pipe**, so agents calling the CLI see what
  people see, and a command behaves the same wherever it runs. Only terminal styling (colors) is
  dropped in a pipe. Text costs agents roughly a third of the tokens of the same answer as JSON,
  which repeats every column name in every row. The text is compact: aligned columns without box drawing, compact numbers, one line per
  item, and a final line with meta:

  ```
  $ beamtime runs scaling/lr-sweep --select config.lr,metric.val/acc.max --sort -metric.val/acc.max --limit 3
  run                       config.lr  val/acc.max
  boosted-kaon-42           3e-4       0.931
  prompt-photon-7           1e-4       0.924
  displaced-muon-13         1e-3       0.918
  3 of 20 runs · live (daemon running) · --limit to see more
  ```

- **`--json`** gives the canonical JSON answer of [layer 3](03-index.md#answers), identical to MCP.
- **Curves in text** are shown as a short summary per run (first, min, max, last, trend) with a
  sparkline, not as thousands of numbers; `--json` gives the points.

## MCP

### Transports

- **stdio**: `beamtime mcp`, registered with a client by `beamtime mcp install`. On a cluster without
  a local Beamtime, the client runs `ssh cluster beamtime mcp`.
- **HTTP**: `serve` exposes MCP at `/mcp`, with the same token as the web UI; the self-hosted server
  ([layer 6](06-server.md)) uses this.
- Through the local `serve`, MCP sees all sources, local and remote, like the CLI.

### Tools

| Group | Tools |
|---|---|
| Orientation | `status`, `guide`, `memory`, `keys`, `folders` |
| Reading | `runs`, `card`, `series`, `data`, `output`, `timeline`, `notes`, `check`, `importance` |
| Writing | `note_add`, `proposal_set`, `memory_update` |
| Views | `view_new`, `view_validate`, `view_render`, `view_save`, `view_show`, `view_outdated`, `view_upgrade` |
| Blocks | `block_list`, `block_promote`, `block_fork`, `block_validate`, `block_save` |
| Export | `export` |

- **Small definitions.** Each tool has a short description and a precise schema; how to use them
  well lives in `guide`, loaded on demand. All tool definitions together stay under about 6k tokens.
- **Writes take `author`**, the model id; `user` comes from the local account or the token.
- **`view_render` returns images** directly, scaled to about 1280 px wide, one for the page and one
  per block on request.
- **`data` returns images as references** and loads them only when asked, as thumbnails first.

### Prompts

MCP prompts appear as slash commands in clients such as Claude Code (`/beamtime:view`). Beamtime
offers a few for its most common tasks, each a short instruction that starts the agent on the right
tools:

| Prompt | Starts |
|---|---|
| `view` | build or improve the view of a folder |
| `proposal` | write a proposal with checkable predictions before a launch |
| `review` | summarize what changed in a folder since a date: new runs, checks, failures |
| `debug` | find out why a run failed, from its output, card and curves |
| `verdict` | evaluate a proposal against its runs and write a verdict note |
| `compare` | compare two runs, groups or folders: config differences, metric deltas, and a temporary comparison view if it helps |
| `report` | summarize a folder for others, e.g. a group meeting: findings, verdicts, open questions, as a view or a PDF export |
| `memory` | update and compact a folder's memory from the notes added since it was last written |

### Token budgets

| Answer | Default | Override |
|---|---|---|
| run table | 50 rows, columns from `select` or a compact default | `limit` |
| curves | 100 points per curve | `points` |
| notes, timeline | descriptions only, 30 entries | `full`, `limit` |
| output | last 50 lines | `tail`, `grep` |
| any answer | about 8k tokens; beyond that the answer is cut and returns a `next` cursor | `cursor` |

Every answer carries meta: freshness, whether it was cut or downsampled, how many items matched, and
a hint for getting more.

## Policy

The guide states these as defaults ([layer 5](05-views.md#defaults)), which users can change in their
own agent instructions:

- **Not exposed as MCP tools, and not run by agents at all**: installing, removing and updating
  packages, changing settings, starting `serve`, moving runs. These change the project or the
  machine, so they stay with the user. An agent gives the user the exact CLI command to enter
  (e.g. `beamtime install -l git:github.com/lab/beamtime-physics-blocks@v1.2`) and does not run it
  through its own shell tool.
- This is an instruction, not an enforcement: Beamtime cannot tell who types a command. The guide
  states it plainly, and the MCP surface simply doesn't offer these actions.
- **Exposed but additive**: notes, proposals (until frozen), view and block versions, exports.
- **Live data**: before working with running runs, agents check `status`; if the daemon isn't
  running, they ask the user to start `beamtime serve --no-ui`.

## Implementation notes

- **Argument parsing with `argparse`** from the standard library, with each command's module imported
  only when it runs, so startup stays small.
- **The MCP server** uses the official MCP Python SDK in `beamtime[serve]`; the tool schemas are
  generated from the same msgspec structs as the CLI and the API, so the three cannot drift apart.

## Decisions

- CLI and MCP mirror each other: same names, parameters and answers; the CLI adds setup and
  administration.
- Compact text output by default, identical in terminals and pipes; `--json` for the canonical
  answer. Exit codes distinguish errors, usage, validation failures and missing items.
- MCP over stdio (`beamtime mcp`, also over ssh) and HTTP (`/mcp` on `serve`), with about 30 small
  tools, prompts as slash commands, and token budgets with cursors.
- Agents never install packages, change settings, start servers or move runs, neither through MCP
  nor through their shell; they give the user the command to enter. Every agent write is additive.
- Eight prompts: `view`, `proposal`, `review`, `debug`, `verdict`, `compare`, `report`, `memory`.
- `beamtime init` and `beamtime mcp install` set up projects and agent clients.
