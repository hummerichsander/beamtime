# Setup: `beamtime init`

Status: **draft; for review before planning.** The experience is agreed in the mockup
([10-setup-mockup.html](10-setup-mockup.html), four scenarios; each step's margin names its flag and
where the answer lands); the decisions behind it are in `docs/plans/setup/decisions.md`.

`beamtime init` sets up a project for Beamtime: it asks a few questions, shows everything it will
change, and writes it only once the user confirms. It is often the first contact with Beamtime, so
it has to be short, plain and safe. One command covers four situations: a first setup, a teammate
joining a project that uses Beamtime already, a cluster login node, and updating a setup made by an
older release.

## Principles

1. **Look first.** A local scan (no network, no ssh, under a second) fills every default. Most
   people press Enter through the questions.
2. **Yours to extend.** Detection only preselects. Every detected list takes the user's own entries
   (`+ Add a path`, `+ Add a host`), checked the same way as found ones.
3. **No trace before the review.** Nothing is written, installed, imported or logged into until the
   review is confirmed; ctrl-c at any point leaves the project and the machine as they were.
4. **One command.** Every answer is a flag. The review can print the whole setup as one
   `beamtime init --yes ...` command, which makes the same setup on another machine or in a script.
5. **Two places.** Each answer says where it lands: the project's `beamtime.yaml` (shared through
   git) or the machine's `~/.config/beamtime/settings.yaml`. A teammate is asked only the machine's
   questions.
6. **Judgment goes to agents.** Turning old notes and memory files into typed notes needs judgment.
   The wizard never calls a model; it hands that work to the user's agent through the MCP `migrate`
   prompt and can start the agent for them. Setup without any agent is a first-class path.
7. **Any terminal.** Arrow keys, space, Enter and number keys, on the standard library only; a
   numbered fallback where raw input is unavailable; no questions at all without a terminal.
8. **Beamtime's voice** ([design/README.md](../../design/README.md)): plain, short, no emoji, no
   exclamation marks.

`init` is a user-only command ([layer 8](08-cli-mcp.md#user-only-commands-cli-only)): agents never run
it; `beamtime status` and `beamtime init --check` tell them when the setup is stale, and they hand the
user the command.

## The flow

The scan decides which of four flows runs; the steps are those of the mockup.

| Flow | When | Asks |
|---|---|---|
| first setup | no `beamtime.yaml` and no log dir in the root | where runs happen, log dir, remotes, agents, agent behaviour, agent rules, past work, git, SDK |
| teammate | `beamtime.yaml` exists, and this machine lacks part of it (a project remote not in the user settings, no agent registered here) | agents on this machine, which project remotes to use, how to reach them, ssh sharing |
| cluster | a scheduler on `PATH` (`sbatch`, `qsub`, `bsub`), no display, or `$HOME` on a network filesystem | role, where runs go (a link to scratch), the cache, agents only with role `full` |
| update | the setup is older than this release, or anything in [Updating](#updating-an-older-setup) is stale | what to bring up to date (all ticked), and only questions new since that release |

The cluster flow combines with the others: a cluster checkout with a `beamtime.yaml` from git asks the
cluster questions and skips the project's. Every flow ends with the same three steps: **review**
(grouped by where each change lands; `Write it`, `Change an answer`, `Show the command and quit`),
**apply** (one line per change in the review's order, stopping at the first failure and naming what
was done; a rerun picks up what is still missing), and **done** (three next steps for this project,
with code for its framework).

Running `beamtime init` in a project that is set up and current says so in one line and asks nothing.

### The scan

`setup/scan.py` reads only local files and runs no subprocess slower than a `--version`. It finds:

| Fact | From |
|---|---|
| project | `beamtime.yaml`, the log dir and its counts (runs, notes, proposals, memories) |
| git | the git root, branch, clean or dirty; `.gitignore` entries for the log dir |
| python | the project environment and its tool: `uv` (`uv.lock` or `[tool.uv]`), `poetry` (`poetry.lock`), `conda` (`environment.yml`, an active `CONDA_PREFIX`), `pip` (`.venv/`, `venv/`, `requirements*.txt`); its Python version and whether it has Beamtime, read from its `site-packages` (`beamtime-*.dist-info`), not by importing |
| code | the framework (`lightning`, `pytorch_lightning` imported by a `*.py` at depth ≤ 2), job scripts (`*.sbatch`, `#SBATCH` lines; hosts they name) |
| past runs | TensorBoard event files, `wandb/offline-run-*`, `mlruns/` and `mlflow.db`, Beamtime runs (`_run.json`) outside the log dir; Beamtime log dirs this machine's index cache knows (other projects) |
| notes and memory | `NOTES.md`, `notes/`, `notebook/`, `journal/`, `*.md` in a `docs/notes`-like folder; Claude Code's project memory (`~/.claude/projects/<escaped root>/memory/`) |
| agents | per client in the [client table](#agent-clients): its project files, its command on `PATH`; its instruction files and the Beamtime rules block in them, with its release |
| conflicts | lines in instruction files that send experimental results elsewhere (`NOTES.md`, "results", "experiment log", "keep notes in"), by a small fixed pattern list; reported with file and line |
| ssh hosts | `Host` entries of `~/.ssh/config` (and its `Include`s), without wildcards |
| disks | the filesystem type of `$HOME`, `~/.cache`, `$SCRATCH`-like variables and `/tmp` (`/proc/mounts` on Linux) |
| stale items | the checks of [Updating](#updating-an-older-setup) |

The scan's answer to "which flow" is one value: `cluster` when any cluster condition holds (it wins over
the others and combines with them in the flow), else `teammate`, else `update` for a log dir without a
`beamtime.yaml`, `first` for neither, and `current` for a `beamtime.yaml` with nothing missing. A job
script names a host when an ssh alias or host name appears in it as a whole word; the environment
is `None` when the project has none. `no display` counts only on Linux; macOS and Windows always have one.

The other projects' log dirs come from the index cache: each cache records the log dir it indexes as
`logdir` in its `meta` table (new with this release; written on open, so a cache in use since
gains it the next time it is opened), and the scan reads it from every cache directory without walking
the disk. Log dirs that no longer exist are left out. They are offered, never ticked.

## Answers, flags and settings

Every answer is a field of one msgspec struct, `setup.plan.Answers`, filled either by the prompts or
by the flags; one function turns `Answers` plus the scan into the plan, so flags and prompts can't
drift. The review's "Show the command" prints the flags that reproduce the answers that differ from
the scan's defaults, plus `--yes`.

| Flag | Answer | Lands in |
|---|---|---|
| `--runs here\|remote\|both` | where runs happen | decides the questions |
| `--logdir <path>` | the log dir; a path outside the project is linked in (`--link-logdir`) | `beamtime.yaml: logdir` |
| `--link-logdir <path>` | make the project's log dir a link to `<path>` (scratch on a cluster) | a symlink in the checkout |
| `--remote <name>[=<host>][:<path>]` (repeatable) | a remote: its source name, how this machine reaches it, its log dir there | `path` to `beamtime.yaml`; `host`, `command` to the user settings |
| `--skip-remote <name>` (repeatable) | a project remote this machine doesn't use | user settings: `remotes.<name>.enabled: false` |
| `--install-remote <name>` (repeatable) | `pip install --user beamtime==<this version>` there, after the review | the remote's `~/.local` |
| `--ssh-share <name>` (repeatable) | add ControlMaster lines for a host with a second factor | `~/.ssh/config` |
| `--cache memory\|<path>` | the index cache of this machine | user settings: `cache` |
| `--agents a,b,...` \| `--no-agents` | which agent clients get the MCP server and rules | each client's config, see [Agent clients](#agent-clients) |
| `--agent-style careful\|hands-on\|analysis` | the agent preset | `beamtime.yaml: agent.style` |
| `--agent-set k=v,...` | single agent settings | `beamtime.yaml: agent.<k>` |
| `--no-rules` | no rules block | – |
| `--import <path>` (repeatable) | runs to copy in (TensorBoard, W&B offline, MLflow, CSV, Beamtime) | `imported/<name>/` in the log dir |
| `--import-notes <path>`, `--import-memory <path>` (repeatable) | notes and memory files | the agent hand-off, or notes as written |
| `--git record\|none` | commit the research record, or ignore the whole log dir | `.gitignore` |
| `--sdk` \| `--no-sdk` | add the SDK to the project environment with its own tool | `pyproject.toml`, `requirements.txt`, ... |
| `--role record\|full` | on a cluster: only record runs, or also look at them here | decides the questions |
| `--update <items>` | stale items to bring up to date: `rules`, `mcp`, `skills`, `settings`, `sdk`, `remote:<name>`; default all | per item |
| `--migrate-with <agent>` | start this agent with the `migrate` prompt after the apply step | – |
| `--check` | list what is stale and exit (0 nothing, 3 something); asks and writes nothing | – |
| `--yes` | write without the review | – |

`--remote` parses as name, then `=host` if present, then `:path`; a path starts with `/`, `~` or `$`.
`--remote juwels:'${SCRATCH}/egnn/beamtime'` names the source and the host `juwels`;
`--remote lab-gpu=jdoe@lab-gpu.example.org` gives a teammate's way to reach a project remote.

**Without a terminal** (stdin or stdout not a TTY) the wizard asks nothing. It builds `Answers` from
the flags and the conservative defaults: nothing outside the project happens unless a flag names it
(no remote installs, no ssh config, no imports, no SDK, no agent start), and detected agents are
registered only when `--agents` names them. Without `--yes` it prints the review and the command and
exits 0 without writing; with `--yes` it applies. `init --check` never needs a terminal.

### Settings

The setup adds two settings ([layer 1](01-storage.md#settings)) and one remote key:

```yaml
# ~/.config/beamtime/settings.yaml (this machine)
cache: /tmp/{user}/beamtime-cache   # or memory; default: the user cache dir if on a local disk
remotes:
  juwels: {host: juwels, command: ~/.local/bin/beamtime}
  lab-gpu: {enabled: false}         # a project remote this machine skips
```
```yaml
# beamtime.yaml (the project)
schema: 1
logdir: beamtime
agent:
  style: careful
  main_metric: val/loss
  direction: min
  seed_key: config.seed
  domain: ml
remotes:
  juwels: {path: "${SCRATCH}/egnn-md/beamtime"}
```

- **`cache`** may be set at both levels, and with the placeholders of remote paths (`{user}`,
  `${VAR}`, `~`), so one project value can serve a whole team. See [The cache](#the-cache).
- **`agent`** is project-only, like `logdir`: agent choice is personal, agent behaviour is the team's.
  See [Agent settings](#agent-settings).
- **`remotes.<name>.enabled`** (default `true`): `false` hides a project remote on this machine;
  `serve`, `status` and listings skip it.
- Values the user leaves at their defaults are not written; the review shows them as
  "default, not written".

## The cache

Today `cache_dir()` reads `BEAMTIME_CACHE` and `XDG_CACHE_HOME`, and `serve --stdio` takes `--cache`.
An MCP server started by an agent client doesn't inherit the shell's `BEAMTIME_CACHE`, so on a
cluster the CLI, MCP and `serve` could disagree on the cache. The cache becomes one setting, resolved
by one function for every consumer (CLI, `serve`, MCP, `serve --stdio`, `pull`, `doctor`):

```python
def resolve_cache(logdir: Path, settings: Settings | None = None) -> Cache:
    """Where the index of a log dir lives on this machine."""
```

`Cache` has `path` (the directory for this log dir), `kind` (`disk` or `memory`), `refused` (the
filesystem type of a configured path that was refused, or `None`) and `source` (what decided: `--cache`,
`BEAMTIME_CACHE`, `project settings`, `user settings` or `default`). Without settings only the
environment counts. The value comes from, first match:

1. `serve --stdio --cache` sent by the laptop (`remotes.<name>.cache` in the laptop's settings; it is a
   `flag`-level `cache` setting of that process), then `BEAMTIME_CACHE` (a session override, as today);
2. the `cache` setting (project over user);
3. the built-in default: `$XDG_CACHE_HOME/beamtime` or `~/.cache/beamtime`.

Then:

- Placeholders expand on this machine (`{user}`, `${VAR}`, `~`), as remote paths do.
- **A path on NFS, Lustre, GPFS, BeeGFS, CIFS or sshfs is refused** (SQLite's locking is unsafe
  there), and the cache falls back to memory with `refused` set; `status` and `doctor` say why. This
  applies to the built-in default too, so a cluster whose `$HOME` is on NFS gets memory without any
  setting.
- **`memory`** means no index survives the process: each process indexes into its own temporary
  directory on local disk (`tempfile.mkdtemp`), deleted when that `Index` closes. A `serve` with a memory cache
  still publishes `serve.lock`, `serve.json` and its token, in `<tmp>/beamtime-<uid>/<logdir hash>/`
  (mode 0700), so a CLI call or MCP server on the same machine finds it and answers through it
  ([layer 3](03-index.md#freshness-the-daemon)). Its daemon and its requests share one temporary index for the
  session (removed when it stops), as `serve --stdio` does.
- `serve --stdio` keeps its behaviour: memory unless a cache is configured, now also from the remote
  machine's own `cache` setting. It no longer sets `BEAMTIME_CACHE`, and the remote's own `BEAMTIME_CACHE` does not make its cache persistent: only `--cache` or the setting do. Its memory is one temporary
  directory for the whole session (removed when stdin closes), so its requests share their index; an
  `Index` per request would index again each time.

`cache_dir(logdir, settings=None)` remains as the path of `resolve_cache()` for callers that only need
it. Every consumer passes its `ctx.settings` (`Index(settings=...)`, `Daemon(settings=...)`,
`query.run(settings=...)`). `doctor` shows the resolved cache, its kind and its source.

## Remotes

The wizard adds remotes the way `beamtime source add` does ([layer 4](04-remotes.md#configuration)),
for any number of hosts:

1. **Hosts** come from `~/.ssh/config` (preselected when a job script names them) and from the user
   (`+ Add a host`: an alias or `user@host`).
2. **One probe for all**, in parallel, before any question about them: `ssh -o BatchMode=yes
   -o ConnectTimeout=10 <host> <one line>` reports the login (key, needs a second factor, unknown
   host), `beamtime --version` and the command found (`probe_command`, [layer 4](04-remotes.md#configuration)),
   `python3 --version`, and the filesystem type of the default path's parent. A login that needs a
   password or code fails under `BatchMode` with `keyboard-interactive` and is reported as such.
3. **Per host**: install if missing, then its log dir path (default: `${SCRATCH}/<project>/beamtime`
   where the host has `$SCRATCH`, else `~/<project>/beamtime`). Variables expand on that host.
4. **Install** is `ssh <host> 'python3 -m pip install --user beamtime[serve]==<this version>'`,
   run after the review, as the last apply step. A remote Python older than 3.11 can't run the CLI:
   the step says so and offers only skipping or the command with another interpreter.
5. **Second factor**: for a host that needs one, the wizard offers these lines, shown in full,
   appended to `~/.ssh/config` as a marked block, then `ssh -fN <host>` in the same terminal so ssh
   asks for the password and code itself:

   ```
   # beamtime: one login per session for juwels
   Host juwels
     ControlMaster auto
     ControlPath ~/.ssh/cm-%r@%h-%p
     ControlPersist 12h
   ```

A remote's `path` goes to `beamtime.yaml` (shared); its `host` and `command` go to the user settings.
A teammate's own added host goes to their settings only.

## Agents and MCP

### Agent clients

`setup/agents.py` holds one entry per client: where its MCP config lives, which instruction file it
reads, whether its config is shared through git, and how to start it with a prompt.

| Client | MCP config | Shared | Rules file | Start with the migrate prompt |
|---|---|---|---|---|
| Claude Code | `.mcp.json` (`mcpServers`) | yes | `CLAUDE.md` | `claude "/beamtime:migrate ..."` |
| Codex | `~/.codex/config.toml` (`[mcp_servers.beamtime]`) | no, user-wide | `AGENTS.md` | `codex "Run the beamtime migrate prompt ..."` |
| Cursor | `.cursor/mcp.json` (`mcpServers`) | yes | `AGENTS.md` | – (copy the prompt) |
| VS Code (Copilot) | `.vscode/mcp.json` (`servers`, `type: stdio`) | yes | `AGENTS.md` | – |
| Gemini CLI | `.gemini/settings.json` (`mcpServers`) | yes | `GEMINI.md` | `gemini -i "Run the beamtime migrate prompt ..."` |
| opencode | `opencode.json` (`mcp.beamtime`, `type: local`) | yes | `AGENTS.md` | – |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | no, user-wide | `AGENTS.md` | – |
| Another agent | printed at the end, to paste | – | `AGENTS.md` | – |

Claude Code also gets the skills ([layer 8](08-cli-mcp.md#skills-and-plugin)) in `.claude/skills/`.
Config files are edited as data (JSON, or the one TOML table appended or replaced between its
header and the next), keeping every other server and key. `beamtime mcp install --client <name>`
stays as the one-client form of the same code; `--client other` prints the JSON.

`register(client, root, env)` returns a `Change` (`setup/plan.py`) whose `run` writes the config. A
shared client (Claude Code, Cursor, VS Code, Gemini CLI, opencode) gets the portable command in its
project file; when none is portable, Claude Code (`projects.<root>.mcpServers` in `~/.claude.json`),
Cursor (`~/.cursor/mcp.json`) and VS Code (the user `mcp.json`) get this machine's command in their
machine config with `--root <abs>`. Gemini CLI and opencode have no machine scope here, so a
non-portable command is an error that says to install with `uv tool install 'beamtime[serve]'`. A
config that does not parse is an error naming the file; nothing is overwritten.
`rules_change(client, root, agent, user_only)` returns the `Change` that writes the rules block into
the client's rules file.

### The MCP command

The command must keep working when environments change: a recreated `.venv`, an upgraded tool
install, a teammate's machine. It never points into a project virtualenv when anything else works.
`setup/agents.py:mcp_command()` takes the first that applies:

| Case | Command |
|---|---|
| a uv project whose environment has `beamtime[serve]` (or gets it with `--sdk`) | `uv run --project <root> beamtime mcp` |
| a conda environment with `beamtime[serve]` | `conda run --no-capture-output -n <env> beamtime mcp` (`-n base` for the conda install itself) |
| a tool install on `PATH` with the serve extra (pipx, `uv tool`, `pip --user`, a global or conda-base install) | `beamtime mcp` in shared files; the absolute path of that launcher in this machine's files |
| none of these, but `uv` is on `PATH` | `uvx --from 'beamtime[serve]' beamtime mcp` |
| a pip virtualenv only | its `bin/beamtime` by absolute path, in this machine's files only; `init --check` reports it when it is gone |

- **The uv command** names the project as `.` in shared files and by its absolute root in machine
  files. A project whose Python is older than 3.11 cannot host the server and falls through, as does
  a launcher found inside the project or its environment.
- **Shared files hold only portable commands.** A command that names this machine (an absolute
  path) goes into the client's machine-level config instead (Claude Code's local scope in
  `~/.claude.json`, Cursor's `~/.cursor/mcp.json`, VS Code's user `mcp.json`), never into a file git
  shares.
- **The root.** User-wide configs (Codex, Windsurf) get `--root <absolute root>`, as today. Shared
  configs get the client's workspace variable where it has one (`${workspaceFolder}` in VS Code and
  Cursor) and otherwise rely on the client starting the server in the project, which Claude Code,
  Gemini CLI and opencode do.
- **Checking a candidate**: `<command> --version` must answer, and the serve extra must be present.
  `beamtime --version` gains a second word when the serve extra is missing
  (`beamtime 0.3.0 (no serve extra)`), so one call answers both. `setup/agents.py:check_command()`
  runs it with a 5 s timeout and returns the version and whether the serve extra is present.
- `--sdk` in a uv project adds `beamtime` to the dependencies and `beamtime[serve]` to the dev group,
  so the published package doesn't depend on the serve extra while `uv run beamtime mcp` works.

### Agent settings

`beamtime.yaml: agent` holds the knobs that `beamtime guide` and the rules block read. A preset names
a set of values; single keys override it.

| Key | Values | careful | hands-on | analysis |
|---|---|---|---|---|
| `launch_runs` | `never`, `ask`, `allowed` | `ask` | `allowed` | `ask` |
| `memory_updates` | `suggest`, `after_verdicts` | `after_verdicts` | `after_verdicts` | `suggest` |
| `save_views` | `draft`, `save` | `save` | `save` | `save` |
| `research_record` | `off`, `encouraged`, `required` | `encouraged` | `encouraged` | `off` |
| `seeds` | an integer ≥ 1 | 3 | 3 | 3 |
| `significance` | a number in (0, 1) | 0.95 | 0.95 | 0.95 |
| `memory_tokens` | an integer ≥ 1 | 1500 | 1500 | 1500 |
| `render_rounds` | an integer ≥ 1 | 2 | 2 | 2 |
| `custom_blocks` | `builtin_first`, `free` | `builtin_first` | `builtin_first` | `builtin_first` |
| `main_metric`, `direction` | a metric key; `min` or `max` | detected | detected | detected |
| `seed_key` | a config field | detected (`config.seed`) | | |
| `domain` | `ml`, `simulation` | detected (`ml`) | | |

- `style` is `careful` (default), `hands-on`, `analysis` or `custom` (the wizard's "Choose each
  setting", which starts from careful). The file stores `style`, the keys that differ from the preset,
  and the detected conventions; readers resolve the preset first. A preset's values change only with
  a changelog line.
- **Careful is today's behaviour.** A project without `agent` behaves as careful, so nothing changes
  for existing projects.
- **Detected conventions** come from the project's runs when there are any: `main_metric` is the
  metric most runs log under a `val`-like prefix with `loss`, `acc`, `error` or `mae` in its name
  (`views/defaults.py:ordered_metrics`), `direction` from the name (`acc` higher, `loss`, `error`,
  `mae` lower); `seed_key` is the config key named `seed` or `*_seed` that varies; `domain` is `ml`
  when the code uses a deep-learning framework, else `simulation`. Without runs they are left out.
- **The knobs are guidance, not enforcement.** Beamtime never runs experiments, so it cannot refuse a
  launch; `research_record: required` tells agents never to launch without a proposal. The files
  keep meaning the same everywhere: a proposal's own `significance` default stays 0.95
  ([research record](09-research-record.md#statistics)); `agent.significance` is what agents write
  into the proposals they draft. `memory update` warns beyond `memory_tokens` instead of the fixed
  1.5k.
- **Fixed, never settable**: writes are additive; agents never run user-only commands; agents ask
  through the tools rather than reading run files.
- Unknown keys and values outside the table are settings problems, reported by `beamtime settings`
  and `doctor`, and the default is used.

### How `beamtime guide` reads them

The guide's parts keep their text and gain placeholders for the knobs, written `{{agent.seeds}}`,
filled from the effective agent settings when a part is read. The overview's `## Defaults` section is
generated: one line per knob that agents act on, each value marked by where it comes from:

```
## Defaults

From this project's beamtime.yaml (agent: careful); the user's own instructions take precedence.

- Ask before you launch a run. (careful)
- Write a proposal with predictions before a launch; 3 seeds per point; significance 0.95. (default)
- Main metric val/loss, lower is better; seeds in config.seed. (detected, in beamtime.yaml)
- After a verdict or decision, update the group's memory; keep it near 1500 tokens. (default)
- Save views when they pass validation; at most 2 render rounds. (default)
- Reuse built-in and library blocks before writing a custom block. (default)
- Never run user commands; hand the user the exact command. (fixed)
```

A value equal to the built-in careful preset is marked `default`; one set by the project names the
preset or `beamtime.yaml`; detected conventions say `detected`. `guide` reads the settings through the
same `Context` as every operation, so a remote group's guide reads the remote project's settings.

### The rules block

Exactly two choices: write the rules (Beamtime is the record), or skip (`--no-rules`, nothing is
written; a later `beamtime init` offers it again). The block goes into each chosen client's rules
file between `<!-- beamtime:start -->` and `<!-- beamtime:end -->`; a rerun replaces only the block.
It is generated from the agent settings by `guide/rules.py` from the template `guide/rules/rules.md`,
so text and settings agree:

```markdown
## Experiments: Beamtime is the record

This project's experimental record lives in Beamtime: runs, proposals, notes and memory. Look things
up there, and write findings there. Tools are named as over MCP; the CLI is `beamtime <name>` with
spaces for `_`.

- Start each session with `memory_show`, then `status`. Read `guide` before working with runs,
  proposals, notes or views.
- Questions about past experiments: answer from `notes`, `memory_show` and `runs`, not from
  recollection or loose files.
- Results, conclusions, dead ends and open questions go into a note on the run or group
  (`note_add`); what should outlive the session goes into the memory (`memory_update`). Not into this
  file, NOTES.md or your own memory; your own memory keeps coding preferences.
- {{record_line}}
- {{launch_line}}
- {{conventions}}
- Ask with the tools; don't parse run files. Writes add new files; never edit, move or delete in the
  log dir. Name yourself (your model id) as author.
- Never run user commands ({{user_only}}); hand the user the exact command.
- A group on another source is `@<name>/<group>`; `status` lists the sources.
```

- `record_line`: `off` leaves the line out; `encouraged` is "Before a run, write a proposal with
  predictions (`proposal_set`), {{seeds}} seeds per point."; `required` is "Never launch a run without
  a proposal with predictions (`proposal_set`); {{seeds}} seeds per point."
- `launch_line`: "Never launch runs yourself.", "Ask before you launch a run.", or "You may launch
  runs."
- `conventions` is "Main metric {{main_metric}} ({{direction_word}}), seeds in {{seed_key}}." with the
  parts that were detected (`direction_word` is "lower is better" or "higher is better"); without any, the
  line is left out.
- `user_only` is generated from the registry, as the MCP instructions are.
- `release_of(block)` turns each template into a pattern: a placeholder matches any text on its line,
  the lines of `record_line` and `conventions` may be missing, whitespace matches any whitespace.

**Conflicts.** When the scan finds an instruction that sends results elsewhere (e.g. "keep results in
NOTES.md", with file and line), the rules step names it, and the agent hand-off folds that section
into Beamtime: the `migrate` prompt asks the agent to show the diff of the instruction file and edit
it only after the user agrees. The wizard itself never edits text outside the markers.

### The `migrate` prompt

A new MCP prompt in `mcp/server.py` `PROMPTS`, the ninth:

| Prompt | Arguments | Starts |
|---|---|---|
| `migrate` | `paths` (notes and memory files, space-separated), `conflict` (`file:line`, optional) | fold notes and memory files into the record, and an instruction file's experiment section into Beamtime |

It asks the agent to read `guide notes` and `guide memory`, then each file; to write each finding as
a typed note (`observation`, `decision`, `idea`, `question`, `verdict`) on the group it concerns,
linking the imported runs it cites as evidence; to draft the project's memory from those notes; for a
conflict, to show the diff that replaces the experiment section of the instruction file with a pointer
to Beamtime, and edit only after the user agrees; never to delete or change the source files; to name
itself as author. The hand-off step offers each chosen client that can start with a prompt, "Copy the
prompt" (for editor agents), or "Later" (`beamtime init --migrate-with <agent>` brings it back).
Starting one replaces the wizard's process with the agent's interactive session in the same terminal
(`os.execvp`), so the user watches it and can steer.

## Past work

### Importers

`setup/importers/` has one module per source, each with `detect(path) -> Found | None` (what is there
and how many runs, fast) and `runs(path) -> Iterator[Imported]` (one run's metadata, config and
metric rows). One writer turns an `Imported` into a run folder under `imported/<name>/` of the log
dir, with the format package's writers (`_run.json`, `_config.json`, `_metrics.jsonl`, the card and
the preview), so imported runs are ordinary runs. The originals are never touched.

| Source | Reads | Without |
|---|---|---|
| TensorBoard | event files (TFRecord framing and the `Event`/`Summary` protobuf messages decoded in pure Python: scalars as `simple_value` and as scalar tensors); `hparams.yaml` next to them (Lightning) as config | images, histograms and text are not imported |
| W&B offline | `offline-run-*/files/config.yaml`, `wandb-metadata.json` (host, git, command), `wandb-summary.json`; the history from the `.wandb` file through the `wandb` package's datastore reader | without `wandb` installed, the summary only, and the review says so |
| MLflow | the file store (`mlruns/<exp>/<run>/meta.yaml`, `metrics/`, `params/`, `tags/`) and the SQLite store (`mlflow.db`: `runs`, `metrics`, `params`, `tags`) with the standard library; status, times, git commit from `mlflow.source.git.commit` | artifacts are not imported |
| CSV | one run per file; a `step` (or `epoch`, `iteration`) column as the step, the other numeric columns as metrics | config |
| Beamtime | a log dir or runs outside the log dir, copied as they are ([below](#beamtime-log-dirs)) | – |

- **Ids and times.** A new run id from the original start time (so imported runs sort where they
  happened), `created_at` and `ended_at` from the source, `status` from the source where it has one
  (MLflow, W&B) and `finished` otherwise.
- **Groups.** `imported/<name>/` keeps the source's structure below it (TensorBoard version folders,
  MLflow experiments, W&B runs by name), so the user can move groups later with `beamtime mv`.
- **Provenance.** Every imported run records where it came from in `_run.json: imported_from`
  ([layer 1](01-storage.md#_runjson)).
- **Twice is once.** A run whose `imported_from.path` (and source id) is already in the log dir is
  skipped, so a rerun imports only what is new.
- **The interface.** `Imported(name, created_at, ended_at, status, config, rows, host, git, command,
  source_id)` holds one run (times as unix seconds, `rows` as `{"_step": n, "<key>": value}` records);
  `write_run(logdir, dest, imported, provenance)` is the one writer. It writes the config, the metric
  lines, the card and the preview (`synth/summary.py:card_and_preview`) and `_run.json` last, so a
  crash leaves a folder no reader sees. `find_imported` walks `imported/` only. `detect` tells a
  path's source from file names alone (`events.out.tfevents.*`, `offline-run-*/*.wandb`,
  `mlflow.db` and `meta.yaml` beside `params/` or `metrics/`, `_run.json`, `*.csv`), skipping `.git`,
  `.venv` and `node_modules`; `Found(kind, path, n, label)` carries the count and the review's line.
- **CSV details.** The first of `step`, `epoch`, `iteration` (any case) is the step; without one the
  row index is. Rows are written in step order. Cells that are not numbers, empty cells and columns
  that begin with `_` are skipped. A CSV carries no times, so `created_at` and `ended_at` are the
  file's modification time and every row's `_t` is `created_at`.

### Beamtime log dirs

Found inside the project (runs outside the log dir), among the log dirs this machine's cache knows,
and in typed paths. They copy with their proposals, notes, memory, views and blocks, without
conversion, since every file reads in every later release:

- The tree is copied under `imported/<name>/`; run ids and version ids stay.
- `_run.json` is rewritten as `cp` rewrites it ([layer 1](01-storage.md#_runjson)): proposal
  membership keys gain the `imported/<name>/` prefix, and `imported_from` is added. Every other file is
  copied byte for byte.
- Group paths named inside the copied authored files (evidence, links, `completes`) keep naming the
  old paths. The import records one move per top-level group in `_moves.jsonl`, with a `within` field:
  `{schema: 1, from: "scaling", to: "imported/egnn-v1/scaling", within: "imported/egnn-v1", t}`. A
  move with `within` maps only paths named by files below `within`, so a native `scaling/` group is
  untouched. Moves without `within` behave as before.
- The source's own `_moves.jsonl` entries are appended with both paths prefixed and the same `within`.
- A run id that exists in the log dir already is skipped (it was imported before).

Reading another project's runs in place (a local-path source) is out of scope.

### Notes and memory files

With an agent, they go to the `migrate` prompt. Without one ("None", or the hand-off left for later
and `--yes` given), each file comes in as written: one `observation` note on the log dir per file,
its body the file's text, its description the file name or first heading, author the local account.

## Git and the SDK

`--git record` (the default) replaces the log dir's ignore entry with the run data only, so the
research record is reviewed and shared through git:

```gitignore
# beamtime: run data stays out; proposals, notes, memory and views are committed
beamtime/**/_*
beamtime/**/artifacts/
beamtime/**/checkpoints/
.beamtime/
```

`--git none` ignores `beamtime/` and `.beamtime/`. Entries are written as one marked block, replaced
on a rerun. A linked log dir (`--link-logdir`) is machine-local: the link itself goes into
`.git/info/exclude`, and git can't see through it, so the review says that this checkout doesn't
commit the record.

`--sdk` adds Beamtime with the project's own tool: `uv add beamtime` (and the dev group, [above](#the-mcp-command)),
`poetry add beamtime`, `conda run -n <env> python -m pip install beamtime` for conda, or
`<venv>/bin/python -m pip install beamtime` plus a `beamtime` line in `requirements.txt` for pip. The
SDK needs Python 3.10; an older project Python is named in the step and the default becomes No.

## Updating an older setup

Updating is `beamtime init` again. Data never migrates: every file reads in every later release. What
goes stale is the setup around it, and each item has a check in `setup/stale.py` that returns
`Stale(item, before, after)` or nothing:

| Item | Stale when | Update |
|---|---|---|
| `rules` | the block differs from what this release generates for the project's agent settings | replace the block |
| `mcp` | a client's MCP command doesn't start (`--version` fails) or isn't what `mcp_command()` picks now | rewrite that entry |
| `skills` | `.claude/skills/beamtime-*` differs from this release's skills | rewrite them |
| `settings` | a key this release no longer reads (the `MOVED` keys, e.g. `colormap`) | remove it, keeping the rest of the file |
| `sdk` | the project environment has an older Beamtime | the tool's upgrade command |
| `remote:<name>` | the remote's Beamtime is older than this one | `pip install --user -U` there, after the review |
| runs | Beamtime runs in the project outside the log dir | an import into the log dir |

- **The setup's release** is found without stamps: `guide/rules/history/` keeps the rules text of
  every release that changed it (0.1.0, 0.2.0, this release's template), and the block is matched
  against each, with the template's placeholders as wildcards. The newest matching release names the
  setup ("set up with 0.1.1" names the last release that wrote that text). A block that matches none
  was edited by hand: its update is offered unticked, with the diff.
- The wizard first checks the data and says it is fine (runs, notes, proposals and views read as
  they are; the index rebuilds once if its schema changed), then lists the stale items, all ticked,
  then asks only the questions new since the setup's release (e.g. agent behaviour and the rules
  choice for a 0.1 setup), and ends with the few changes a person would notice, from a short list kept
  per release in `setup/changes.py`.
- **`beamtime init --check`** runs the checks without a terminal, prints one line per stale item and
  exits 3 if there is one, 0 otherwise; for CI and for agents, who hand the user `beamtime init`.
- **`beamtime status`** (and the MCP `status`) adds one line when the rules block is from an older
  release: "set up with 0.1.1; `beamtime init` updates it". Only the rules check runs there, since it
  reads two small files.

## The terminal

`setup/term.py` has the prompt primitives, on the standard library only: `select`, `multi` (with
`+ Add ...` rows that run a check on the typed value), `text`, `form` (rows of choices), `task` (lines
appearing as work finishes) and the review.

- **Keys**: arrows or `j`/`k`, space toggles, Enter confirms, number keys pick a row, `q` or ctrl-c
  quits. Raw input through `termios` on POSIX and `msvcrt` on Windows, behind one `keys()`
  generator (`up`, `down`, `left`, `right`, `space`, `enter`, `esc`, `backspace`, `digit:<n>`,
  `char:<c>`, `ctrl-c`). In a text field and in the `+ Add` row, letters and digits are typed and
  `q` is not a quit key; Esc leaves the `+ Add` row. A check that returns a string shows it in
  place and keeps the row open. The terminal's attributes are restored (flushing unread keys) on
  every exit, ctrl-c included, which raises `Aborted`.
- **Multi-select**: the cursor starts on the first ticked row; Enter confirms the ticked set; after
  the user moves to an unticked row, Enter ticks it too and confirms. The footer shows how many are
  selected.
- **Fallback**: where raw input is unavailable (`TERM=dumb`, an editor's terminal without it), each
  question prints numbered rows and reads a line (`2`, `1,3`, Enter for the default).
- **Answered steps** collapse to one line each (title and the answer's summary), as in the mockup.
- **Styling** uses ANSI colors from the design tokens' terminal mapping, dropped with `NO_COLOR` or a
  pipe ([layer 8](08-cli-mcp.md#output)).
  `Term.detect()` makes the choice (raw keys on a terminal that is not `TERM=dumb`, colors unless
  `NO_COLOR`). Without color no color escapes are written; the cursor movement that redraws an
  active step stays, since it only runs on a terminal. Lines are cut to the terminal's width with
  an ellipsis, so a long hint never wraps the rail.
- **Ctrl-c** restores the terminal and prints "Nothing was written." before the apply step; during it,
  what was done so far.
- **Import budget**: the wizard's modules load only when `init` runs; the plain CLI path stays within
  `tests/test_budgets.py`.

## Module layout

| Module | Holds |
|---|---|
| `setup/scan.py` | `Scan` and `scan(root)`: the facts above, local only |
| `setup/plan.py` | `Answers` (msgspec, one field per flag), `Change` (where it lands, label, before, after) and `plan(scan, answers) -> list[Change]` |
| `setup/apply.py` | runs a plan in order; stops at the first failure and names what was done |
| `setup/flow.py` | the steps of the four flows: which questions, their defaults from the scan |
| `setup/term.py` | the prompt primitives |
| `setup/agents.py` | the client table, `mcp_command()`, registering, the rules block written to files |
| `setup/remotes.py` | the parallel probe, installs, ssh sharing |
| `setup/importers/` | `tensorboard`, `wandb`, `mlflow`, `csv`, `beamtime`, and the one run writer |
| `setup/stale.py`, `setup/changes.py` | the update checks; the noticeable changes per release |
| `guide/rules.py`, `guide/rules/` | the rules template, its history, rendering and matching |
| `index/cache.py` | `resolve_cache()` |
| `settings.py` | `cache`, `agent` (presets, validation, resolution), `remotes.<name>.enabled` |

`ops/admin.py:init` becomes the entry that builds `Answers` from flags and either runs the flow (a
terminal, no `--yes`) or plans and applies directly. `mcp install` calls `setup/agents.py`.

## Testing

- **Scan fixtures**: small project trees per scenario (first setup, teammate, cluster, update from
  0.1.1), built in `tmp_path`; the scan's facts are asserted, with `/proc/mounts` and `~/.ssh/config`
  pointed at fixture files.
- **Flags and prompts agree**: for each scenario, answers given by the scripted prompts and by the
  printed `--yes` command produce the same plan.
- **No trace**: every scenario aborted at every step leaves the tree and the fake home byte-identical.
- **The terminal**: the primitives run against a pseudo-terminal (`pty`) with scripted keys; the
  numbered fallback reads from a pipe.
- **Importers**: small checked-in fixtures per source (a TensorBoard event file, an MLflow file store
  and `mlflow.db`, a W&B offline run, a CSV) and a golden Beamtime log dir; imported runs answer `runs`
  and `series` like native ones; a second import adds nothing.
- **The MCP command**: per environment kind, the chosen command, and that shared files never get an
  absolute path.
- **Updating**: a project set up with each earlier release's files is detected as that release, and
  `--check` exits 3, then 0 after `init --yes`.
- **Remotes**: the probe and the install over real ssh in the Docker test (`BEAMTIME_DOCKER=1`).

## Decisions

- One command, `beamtime init`, for first setups, teammates, clusters and updates; no separate migrate
  wizard.
- Nothing is written before the review; every answer is a flag; without a terminal nothing is asked
  and nothing outside the project happens unless a flag names it.
- `cache` is a setting at both levels with placeholders, resolved by one function for every consumer;
  network filesystems are refused for memory, also for the built-in default.
- `agent` in `beamtime.yaml` holds a preset and overrides; careful is today's behaviour; the knobs are
  guidance and never change what files mean.
- The rules block is generated from the agent settings; two choices, write it or skip.
- The MCP command is portable in shared files and never points into a project virtualenv when anything
  else works.
- Imports copy, never move; each imported run records `imported_from`; Beamtime log dirs copy without
  conversion and keep their paths meaningful through moves scoped with `within`.
- The wizard never calls a model; the `migrate` prompt hands judgment to the user's agent.
