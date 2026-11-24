# Setup: `beamtime setup`

Status: **reviewed.** The experience follows the mockup ([10-setup-mockup.html](10-setup-mockup.html),
four scenarios; each step's margin names its flag and where the answer lands).

`beamtime setup` sets up a project for Beamtime: it asks a few questions, shows everything it will
change, and writes it only once the user confirms. It is often the first contact with Beamtime, so
it has to be short, plain and safe. One command covers five situations: a first setup, a teammate
joining a project that uses Beamtime already, a cluster login node, updating a setup made by an
older release, and changing an answer of a current setup.

## Principles

1. **Look first.** A local scan (no network, no ssh, under a second) fills every default. Most
   people press Enter through the questions.
2. **Yours to extend.** Detection only preselects. Every detected list takes the user's own entries
   (`+ Add a path`, `+ Add a host`), checked the same way as found ones.
3. **No trace before the review.** Nothing is written, installed, imported or logged into until the
   review is confirmed; ctrl-c at any point leaves the project and the machine as they were.
4. **One command.** Every answer is a flag. The review can print the whole setup as one
   `beamtime setup --yes ...` command, which makes the same setup on another machine or in a script.
5. **Two places.** Each answer says where it lands: the project's `beamtime.yaml` (shared through
   git) or the machine's `~/.config/beamtime/settings.yaml`. A teammate is asked only the machine's
   questions.
6. **Judgment goes to agents.** Turning existing notes and memory files into typed notes needs judgment.
   The wizard never calls a model; it hands that work to the user's agent through the MCP `migrate`
   prompt and can start the agent for them. Setup without any agent is a first-class path.
7. **Any terminal.** Arrow keys, space, Enter and number keys, on the standard library only; a
   numbered fallback where raw input is unavailable; no questions at all without a terminal.
8. **Beamtime's voice** ([design/README.md](../../design/README.md)): plain, short, no emoji, no
   exclamation marks.

`setup` is a user-only command ([layer 8](08-cli-mcp.md#user-only-commands-cli-only)): agents never run
it; `beamtime status` and `beamtime setup --check` tell them when the setup is stale, and they hand the
user the command.

## The flow

The scan decides which of five flows runs; the steps are those of the mockup.

| Flow | When | Asks |
|---|---|---|
| first setup | no `beamtime.yaml` and no log dir in the root | where runs happen, log dir, remotes, agents, agent behaviour, agent rules, past work, git, SDK |
| teammate | `beamtime.yaml` exists, and this machine lacks part of it: a project remote not in the user settings, or an agent client installed here (its command on `PATH`) that Beamtime isn't registered in | agents on this machine, which project remotes to use, how to reach them, ssh sharing |
| cluster | a scheduler on `PATH` (`sbatch`, `qsub`, `bsub`), no display, or `$HOME` on a network filesystem | role, where runs go (a link to scratch), the cache, agents only with role `full` |
| update | the setup is older than this release, or anything in [Updating](#updating-an-older-setup) is stale | what to bring up to date (all ticked), and only questions new since that release |
| reconfigure | `beamtime.yaml` exists and nothing is missing or stale (the scan's `current`) | nothing up front: the list of every answer with its current value, then only what the user picks ([Reconfiguring](#reconfiguring)) |

The cluster flow combines with the others: a cluster checkout with a `beamtime.yaml` from git asks the
cluster questions and skips the project's. Every flow ends with the same three steps: **review**
(grouped by where each change lands; `Write it`, `Change an answer`, `Show the command and quit`),
**apply** (one line per change in the review's order, stopping at the first failure and naming what
was done; a rerun picks up what is still missing), and **done** (three next steps for this project,
with code for its framework).

Running `beamtime setup` in a terminal in a project that is set up and current opens the list of answers
([Reconfiguring](#reconfiguring)); without a terminal it plans from the flags as always and says
"already set up" when there is nothing to change.

### The wizard

`setup/flow.py` runs the steps. A `Step` has an `id`, a `title`, `ask(term, answers, scan)` (asks and
writes the answer into `Answers`), `when(answers, scan)` and, for steps that hold an answer, a
`summary(answers, scan)`. `run(term, scan, answers) -> Answers | None` asks the steps in order, then
shows the review and returns the answers on `Write it`, and `None` for `Show the command and quit`
(which prints `command()`) or ctrl-c (which prints "Nothing was written."). `setup()` is `run`, then
`plan()` and `apply()` as one `Setting up` task, then the next steps. `ops/admin.py:setup` (the
operation, with its `SetupParams`) calls `flow.setup()` when stdin and stdout are
terminals and there is no `--yes`, for every flow the scan picks; every other case plans from the
flags as [above](#answers-flags-and-settings). The teammate, cluster and update steps are further lists
for the same engine; `run` takes the list of the scan's flow, and for `current` it runs
`reconfigure()` instead of the steps in order.

- **`Change an answer`** lists the steps that hold an answer (their `summary` as the hint) and jumps
  to the chosen one; the later steps ask again, each starting on the answer it has, so one change costs
  one Enter per later question. The answers are one mutable `Answers`, which is also what a step reads
  as its default.
- **What is preselected.** `fill()` sets, where a flag left the plain default of
  `Answers.defaults`: `runs` to `both` when a job script and ssh hosts were found, the found agents,
  `sdk` when the environment lacks Beamtime and can take it. The project's own `agent` (its style and
  the single keys that differ from that preset) is already `Answers.defaults`, for flags and prompts
  alike, so a project's choice is the default and never the built-in preset; a project with single
  keys starts on `Choose each setting`, whose form starts from the project's resolved values. Past work is preselected when found in the project; Beamtime
  log dirs of other projects are offered and never ticked. `git` starts on `record`.
- **Conventions are not asked** (see [Agent settings](#agent-settings)); the style step says where to
  set them.
- **The first setup** asks, in this order: where runs happen; the log dir (not for `remote`); the
  machines (not for `here`), then one probe of all of them and per machine the install question
  (only where the probe found no Beamtime) and the log dir there; the agents (`None` skips the next
  three); the style (`Choose each setting` adds the form of the single keys); the rules; past work;
  git; the SDK (only for an environment without Beamtime). A machine whose Python can't run Beamtime
  is named and left out. The default log dir of a machine is `${SCRATCH}/<project>/beamtime` where the
  probe saw `$SCRATCH` (`Probe.scratch`), else `~/<project>/beamtime`.
- **Typed paths** (`+ Add a host`, `+ Add a path`) are checked when typed, as the found ones are. A path
  inside another project's log dir is imported through that log dir's root, and the review shows the bytes
  to copy ([Beamtime log dirs](#beamtime-log-dirs)).

### The teammate and cluster flows

Both skip every project question: `beamtime.yaml` is the team's, and the review lists it as `unchanged`
(a file without `logdir` or `agent` already means the default, and neither is written back). Nothing
asks for the style or the rules: a teammate or a cluster doesn't choose the team's agent behaviour, so
choosing agents writes no `agent` block (a style from `--agent-style` or `--agent-set` still does). Past
work, git and the SDK are not asked either; `git` follows the checkout's own `.gitignore` block (a
`none` block stays `none`), and `fill()` preselects neither the SDK nor `runs: both`. In both flows
`fill()` preselects only the agent clients installed here (command on `PATH`), not those a project file
merely names.

**The teammate** asks, in this order (strings of the mockup's `MATE`):

1. *Which coding agents do you use on this machine?* The installed clients are ticked; a client that
   is registered already plans no change.
2. *Which of the project's machines do you use?* One row per remote of `beamtime.yaml` (hint: in or
   not in `~/.ssh/config`, or the host of the user's own setting), ticked unless this machine skipped
   it before, plus `+ Add a host` for the person's own. An unticked remote becomes `--skip-remote`; a
   typed host goes to the user's settings only. Asked only when the project names remotes.
3. One probe of the picked machines ([Remotes](#remotes)); a project remote that is no alias of
   `~/.ssh/config`, has no `@` and no host in the user's settings is not probed and says so.
4. *Log in to `<host>` once per session?* for each alias whose probe says `needs_code`: add the
   `ControlMaster` lines and log in (`--ssh-share`), show them and ask again, or skip the host (it
   becomes `--skip-remote`).
5. *How do you reach `<remote>`?* for each project remote left without a way in: a host or alias
   (`--remote <name>=<host>`, probed at once), empty skips the remote.

Installing Beamtime on a machine is not part of this flow; `--install-remote` still plans it.

**The cluster** asks:

1. *What should this machine do?* `record` or `full`; `record` empties the agents.
2. *Where should runs go on this cluster?* link the log dir to `${SCRATCH}/<project>/<logdir>` (the
   first scratch-like variable the scan found; recommended; the default is to keep when the log dir already holds runs as a plain folder), keep it in the checkout, or another place (`--link-logdir`).
3. *Keep an index on this cluster between connections?* `No` (memory, written as `cache: memory`
   only where the default isn't memory already) or `Yes` in `/tmp/{user}/beamtime-cache`; the person's
   own value in the user settings is offered as a third row.
4. *Which coding agents run on this node?* only for `full`, terminal agents (clients with a start
   command, `other`, `None`).

A cluster checkout without a `beamtime.yaml` gets the same questions; the review then shows what is
written to it. The done step names the next command per flow: on a teammate's machine the team's runs and a
prompt for the agent, on a cluster that jobs need no change and the `beamtime source add` line for the
laptop.

### Reconfiguring

A project that is set up and current (the scan's flow `current`) opens the wizard on the `Change an
answer` screen, starting from what is set up rather than from the defaults:

- **The saved answers.** `Answers.saved(scan)` is `Answers.defaults(scan)` (the log dir, the project's
  `agent`) plus what this checkout and machine have: `runs` is `both` when `beamtime.yaml` names
  remotes, else `here`; `remotes` are the project's enabled remotes with their `path` from
  `beamtime.yaml` and their `host` from the user settings; `skip_remotes` the ones this machine
  switched off; `agents` the clients the scan found registered; `rules` whether a registered client's
  rules file holds the block (on when none is registered); `git` is `none` when `.gitignore` holds the
  `none` block, else `record`. Nothing is preselected on top (`fill()` is not called), so
  `plan(scan, Answers.saved(scan))` is empty, except for the rules refresh below. Flags given on the
  command line apply on top of the saved answers (`Answers.from_params(p, scan, base=...)`).
- **The list.** Every step of the first setup that holds an answer and applies is one row, its
  `summary` as the hint, plus a last row `Review the changes`. Picking a step asks that step only, then
  each later step that did not apply before the pick and applies now (choosing an agent where there was
  none asks the style and the rules; `both` where runs were `here` asks the machines), then shows the
  usual review. `Change an answer` at the review comes back to the list. The cursor starts on the first
  step, or on `Review the changes` when the saved answers already plan a change.
  The intro says "Set up with <version>. Pick what to change."; a review of answers that plan nothing
  says "Nothing to change." and ends.
- **A rules block that no longer matches the settings.** When a registered client's rules file holds a
  block of this release that differs from what `beamtime.yaml: agent` generates now (the settings were
  edited after the setup), the saved answers plan that block's rewrite; the list says so in one line
  above the rows ("The rules in CLAUDE.md don't match beamtime.yaml; the review rewrites them."). This
  is not a stale item: `setup --check` and `status` stay quiet about it, since the release is current.
  Without a terminal, `beamtime setup --yes --update rules` rewrites it.
- `Show the command` prints the command of the answers as everywhere, so it names the registered agents;
  running it plans the same changes.

### The update flow

The scan picks it for a project whose setup is stale ([Updating](#updating-an-older-setup)). It asks, in
this order (strings of the mockup's `UPGRADE`), after an intro that names the setup's release ("its setup
is from 0.1.1"; the oldest release behind a rules block, `setup_release()`):

1. *Checking runs, notes and views*, a task that says the data needs nothing (runs, notes and
   proposals, views and the index) before anything is asked.
2. *Checking juwels* (one probe of every enabled remote the project or this machine names that ssh
   can reach): a remote whose Beamtime is older than this one is marked `!` and becomes the item
   `remote:<name>` (`stale_remote()`), ticked.
3. *What should be brought up to <version>?*: one row per `Scan.stale` item, with its before and after,
   plus the remotes of step 2, all ticked except a hand-edited rules block, and `+ Add a path` for more
   past work (the check of the first setup). The ticks are `Answers.update`, a `runs` row's folder is an
   `Answers.imports` entry, an added path fills the import answers as in the first setup.
4. *How much should agents do on their own?*, its form and *Tell agents that Beamtime is the record?*,
   marked "New since your setup", only when agents are registered and the setup is from before 0.3.0
   (or its release is unknown). `Answers.agents` is the clients with a registration, so a client the
   setup never registered stays out. *Skip* leaves the rules blocks as they are; it never removes one.

The review opens with "your data  nothing is rewritten" and the log dir's counts, lists the changes
as everywhere, and ends with "kept as they are" and the names of the items left unticked (a rules
block is kept as well when the answer is *Skip*). In an update flow the plan changes skills and the
rules blocks that exist only through `--update`: an unticked item is not planned by the agent
answers either. The apply task is called *Updating*. The wizard ends with "Beamtime <version> is set up.
Nothing in beamtime/ was rewritten.", `changes.py:since(setup release, this release)` and, when rules
were written, "Agents read the new rules from their next session on." Without a terminal `setup
--yes` plans the same from the flags.

### The scan

`setup/scan.py` reads only local files and runs no subprocess slower than a `--version`. It finds:

| Fact | From |
|---|---|
| project | `beamtime.yaml`, the log dir and its counts (runs, notes, proposals, memories) |
| git | the git root, branch, clean or dirty; `.gitignore` entries for the log dir |
| python | the project environment and its tool: `uv` (`uv.lock` or `[tool.uv]`), `poetry` (`poetry.lock`), `conda` (`environment.yml`, an active `CONDA_PREFIX`), `pip` (`.venv/`, `venv/`, `requirements*.txt`); its Python version and whether it has Beamtime, read from its `site-packages` (`beamtime-*.dist-info`), not by importing |
| code | the framework (`lightning`, `pytorch_lightning` imported by a `*.py` at depth ≤ 2), job scripts (`*.sbatch`, `#SBATCH` lines; hosts they name) |
| past runs | TensorBoard event files, `wandb/offline-run-*`, `mlruns/` and `mlflow.db`, Beamtime runs (`_run.json`) outside the log dir; Beamtime log dirs this machine's index cache knows (other projects) |
| notes and memory | `NOTES.md`, `notes/`, `notebook/`, `journal/`, `*.md` in a `docs/notes`-like folder; Claude Code's project memory (`~/.claude/projects/<escaped root>/memory/`, the root's absolute path with every character outside `A-Za-z0-9-` as `-`, so `/` and `.` but also a space or `~`) |
| agents | per client in the [client table](#agent-clients): its project files, its command on `PATH`; its instruction files and the Beamtime rules block in them, with its release |
| conflicts | lines in instruction files that send experimental results elsewhere (`NOTES.md`, "results", "experiment log", "keep notes in"), by a small fixed pattern list; reported with file and line |
| ssh hosts | `Host` entries of `~/.ssh/config` (and its `Include`s), without wildcards |
| disks | the filesystem type of `$HOME`, `~/.cache`, `$SCRATCH`-like variables and `/tmp` (`/proc/mounts` on Linux) |
| stale items | the checks of [Updating](#updating-an-older-setup) |

The scan's answer to "which flow" is one value: `cluster` when any cluster condition holds (it wins over
the others and combines with them in the flow), else `teammate` (a `beamtime.yaml` with a remote the user
settings lack, or with an installed agent client whose config, project or user, doesn't list the
`beamtime` server; a person who declines the registration is asked again by the next plain `setup`), else `update` for a log dir without a
`beamtime.yaml`, `first` for neither, and `current` for a `beamtime.yaml` with nothing missing. A job
script names a host when an ssh alias or host name appears in it as a whole word; the environment
is `None` when the project has none. `no display` counts only on Linux; macOS and Windows always have one.

The agents are the clients of the table with a project file (their MCP config, `.claude/`, `.cursor/`,
`.gemini/`, `CLAUDE.md`, `GEMINI.md`) or their command on `PATH`; a shared `AGENTS.md` alone names none.
Each carries its rules file, whether its config lists the `beamtime` server (`registered`, read with `agents.py`'s `is_registered` over the project file, the machine's file and the user-wide file) and, when the rules file holds the block, the release that wrote it. Past runs are
looked for to depth 3 below the root, outside the log dir, hidden folders and environments; a folder
with event files, `offline-run-*` folders, `mlruns/`, `mlflow.db` or a `_run.json` is a source, and
sibling folders of one kind merge into their parent (`tb_logs/model/version_0`, `version_1` are one
source, `tb_logs/model`). CSV files are never looked for, only taken from a path the user adds.

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
| `--remote <name>[=<host>][:<path>]` (repeatable) | a remote: its source name (no `@`, `/`, `=` or `:`, the rule of `source add`), how this machine reaches it, its log dir there | `path` to `beamtime.yaml`; `host`, `command` to the user settings |
| `--skip-remote <name>` (repeatable) | a project remote this machine doesn't use | user settings: `remotes.<name>.enabled: false` |
| `--install-remote <name>` (repeatable) | `pip install --user beamtime==<this version>` there, after the review | the remote's `~/.local` |
| `--remote-command <name>=<command>` (repeatable) | how the remote's shell starts Beamtime, as the probe found it | user settings: `remotes.<name>.command` |
| `--ssh-share <name>` (repeatable) | add ControlMaster lines for a host with a second factor | `~/.ssh/config` |
| `--cache memory\|<path>` | the index cache of this machine | user settings: `cache` |
| `--agents a,b,...` \| `--no-agents` | which agent clients get the MCP server and rules | each client's config, see [Agent clients](#agent-clients) |
| `--agent-style careful\|hands-on\|analysis` | the agent preset | `beamtime.yaml: agent.style` |
| `--agent-set k=v` (repeatable; `k=v,k=v` also parses) | single agent settings; the printed command has one flag per key, so a value may hold commas | `beamtime.yaml: agent.<k>` |
| `--no-rules` | no rules block | – |
| `--import <path>` (repeatable; `''` for none) | runs to copy in (TensorBoard, W&B offline, MLflow, CSV, Beamtime); default the Beamtime runs of a stale `runs` item | `imported/<name>/` in the log dir |
| `--import-notes <path>`, `--import-memory <path>` (repeatable) | notes and memory files | the agent hand-off, or notes as written |
| `--git record\|none` | commit the research record, or ignore the whole log dir | `.gitignore` |
| `--sdk` \| `--no-sdk` | add the SDK to the project environment with its own tool | `pyproject.toml`, `requirements.txt`, ... |
| `--role record\|full` | on a cluster: only record runs, or also look at them here | decides the questions |
| `--update <items>` | stale items to bring up to date: `rules`, `mcp`, `skills`, `settings`, `sdk`, `remote:<name>`; default all ticked (runs are `--import`) | per item |
| `--migrate-with <agent>` | start this agent with the `migrate` prompt after the apply step | – |
| `--check` | list what is stale and exit (0 nothing, 3 something); asks and writes nothing | – |
| `--yes` | write without the review | – |

`--remote` parses as name, then `=host` if present, then `:path`; a path starts with `/`, `~` or `$`.
`--remote juwels:'${SCRATCH}/egnn/beamtime'` names the source and the host `juwels`;
`--remote lab-gpu=jdoe@lab-gpu.example.org` gives a teammate's way to reach a project remote.

`Answers.defaults(scan)` holds the conservative answers (the log dir the scan found, careful, rules on,
everything that reaches outside the project off, `update` the scan's stale items); `Answers.from_params`
fills what a flag leaves open from it (or from `base`, the saved answers when
[reconfiguring](#reconfiguring)) and refuses unknown agents, agent keys or `--update` items, a
malformed `--remote` and contradicting pairs (`--agents` with `--no-agents`, `--sdk` with `--no-sdk`). `--check` and `--yes`
steer the command and are not answers. `--instructions`, the old form of the rules flag, stays as a
hidden alias that sets `rules`. `command(answers, scan)` prints `beamtime setup --yes` and one line per
flag whose answer differs from the defaults, values quoted for a shell; running it gives equal
`Answers`. A flag that undoes a default has its own form (`--no-agents`, `--no-sdk`, `--no-rules`,
`--update ''`, `--import ''`).

**Without a terminal** (stdin or stdout not a TTY) the wizard asks nothing. It builds `Answers` from
the flags and the conservative defaults: nothing outside the project happens unless a flag names it
(no remote installs, no ssh config, no imports, no SDK, no agent start), and detected agents are
registered only when `--agents` names them. Without `--yes` it prints the review and the command and
exits 0 without writing; with `--yes` it applies. `setup --check` never needs a terminal.

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

The cache is one setting, resolved by one function for every consumer (CLI, `serve`, MCP,
`serve --stdio`, `pull`, `doctor`), since an MCP server started by an agent client doesn't inherit
the shell's environment:

```python
def resolve_cache(logdir: Path, settings: Settings | None = None) -> Cache:
    """Where the index of a log dir lives on this machine."""
```

`Cache` has `path` (the directory for this log dir), `kind` (`disk` or `memory`), `refused` (the
filesystem type of a configured path that was refused, or `None`) and `source` (what decided: `--cache`,
`BEAMTIME_CACHE`, `project settings`, `user settings` or `default`). Without settings only the
environment counts. The value comes from, first match:

1. `serve --stdio --cache` sent by the laptop (`remotes.<name>.cache` in the laptop's settings; it is a
   `flag`-level `cache` setting of that process), then `BEAMTIME_CACHE` (a session override);
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
- `serve --stdio` uses memory unless `--cache` or the remote machine's own `cache` setting configures
  a cache; the remote's `BEAMTIME_CACHE` does not. Its memory is one temporary directory for the whole
  session (removed when stdin closes), so its requests share their index.

`cache_dir(logdir, settings=None)` is the path of `resolve_cache()` for callers that only need it. Every consumer passes its `ctx.settings` (`Index(settings=...)`, `Daemon(settings=...)`,
`query.run(settings=...)`). `doctor` shows the resolved cache, its kind and its source.

## Remotes

The wizard adds remotes the way `beamtime source add` does ([layer 4](04-remotes.md#configuration)),
for any number of hosts:

1. **Hosts** come from `~/.ssh/config` (preselected when a job script names them) and from the user
   (`+ Add a host`: an alias or `user@host`).
2. **One probe for all**, in parallel, before any question about them: `ssh -o BatchMode=yes
   -o ConnectTimeout=10 <host> <one line>` reports the login (key, needs a second factor, unknown
   host), the command found and its `beamtime --version` ([layer 4](04-remotes.md#configuration)),
   `python3 --version`, and the filesystem type of the default path's parent. A login that needs a
   password or code fails under `BatchMode` with `keyboard-interactive` and is reported as such.
   `setup/remotes.py:probe(hosts, paths) -> dict[str, Probe]` runs one ssh per host in threads, each
   with a 30 s timeout that fails that host alone; a `Probe` has `status` (`ok`, `needs_code`,
   `unknown_host`, `no_beamtime`, `old_python`, or `failed` with the reason), `command`, `version`,
   `python`, `fstype` and `scratch` (whether `$SCRATCH` is set there). The command is the first
   `beamtime` that answers `--version`, tried in this order: a venv (`.venv`, `venv`, `env`, `.env`) in the
   log dir or any folder above it, the `PATH` of a non-interactive ssh shell (then just `beamtime`),
   `~/.local/bin` (pip `--user`, pipx, uv tools), venvs one or two levels below home or `$SCRATCH`, then conda
   environments; a path under home is written with `~`. The probe runs before the path is asked, on the
   default path; once a typed path differs, that host is probed again with it, so a project's own venv
   beside its log dir is found.
3. **Per host**: its log dir path (default: `${SCRATCH}/<project>/beamtime` where the host has
   `$SCRATCH`, else `~/<project>/beamtime`; variables expand on that host), then install if the probe of
   that path found no Beamtime. A found command other than `beamtime` is kept as `--remote-command`.
4. **Install** is `ssh <host> 'python3 -m pip install --user beamtime[serve]==<this version>'`,
   run after the review, as the last apply step. A remote Python older than 3.11 can't run the CLI:
   the step says so and offers only skipping or the command with another interpreter.
   `--install-remote <name>` plans exactly this change (`where: remote`, over `BatchMode` ssh, pinned to
   the running version); the name must be a remote of the answers or the settings.
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

   `--ssh-share <name>` plans two changes: the block, left out when the file already has the marker
   line (so it is appended once; the file is created with mode 600), and `ssh -fN <host>`, run
   attached to the terminal (no captured streams), skipped when `ssh -O check` finds the master open.
   The name is a remote or an alias of the ssh config, and the host must be an alias, not `user@host`.
   Both are planned only when asked for, and come last in the plan, after the settings and imports, so
   the installs can use the shared login.

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
| a pip virtualenv only | its `bin/beamtime` by absolute path, in this machine's files only; `setup --check` reports it when it is gone |

- **The uv command** names the project as `.` in shared files and by its absolute root in machine
  files. A project whose Python is older than 3.11 cannot host the server and falls through, as does
  a launcher found inside the project or its environment.
- **Shared files hold only portable commands.** A command that names this machine (an absolute
  path) goes into the client's machine-level config instead (Claude Code's local scope in
  `~/.claude.json`, Cursor's `~/.cursor/mcp.json`, VS Code's user `mcp.json`), never into a file git
  shares.
- **The root.** User-wide configs (Codex, Windsurf) get `--root <absolute root>`. Shared
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
| `proposal_words` | an integer ≥ 1 | 150 | 150 | 150 |
| `memory_tokens` | an integer ≥ 1 | 1500 | 1500 | 1500 |
| `render_rounds` | an integer ≥ 1 | 2 | 2 | 2 |
| `custom_blocks` | `builtin_first`, `free` | `builtin_first` | `builtin_first` | `builtin_first` |
| `mcp_tools` | `core`, `all` | `core` | `core` | `core` |
| `main_metric`, `direction` | a metric key; `min` or `max` | not set | not set | not set |
| `seed_key` | a config field | not set | | |
| `domain` | `ml`, `simulation` | not set | | |

- `style` is `careful` (default), `hands-on`, `analysis` or `custom` (the wizard's "Choose each
  setting", which starts from careful). The file stores `style`, the keys that differ from the preset,
  and the conventions the user set; readers resolve the preset first.
- **The chosen style is written.** `setup` (wizard or `--agent-style`) writes the chosen style with the
  single keys that differ from its preset; choosing another preset drops the project's old single keys,
  and the conventions in the file stay. A file that already resolves to the same values is left as
  written. A preset's values change only with
  a changelog line.
- **Careful is the default.** A project without `agent` behaves as careful.
- **Conventions are the user's.** The wizard neither asks for nor guesses `main_metric`, `direction`,
  `seed_key` and `domain`, not from the runs and not from the code. The user sets them afterwards under
  `agent:` in `beamtime.yaml`, and the agent step says where. Without them the guide and the rules
  block leave the convention line out. A value the project already has stays as it is.
- **The knobs are guidance, not enforcement.** Beamtime never runs experiments, so it cannot refuse a
  launch; `research_record: required` tells agents never to launch without a proposal. The files
  keep meaning the same everywhere: a proposal's own `significance` default stays 0.95
  ([research record](09-research-record.md#statistics)); `agent.significance` is what agents write
  into the proposals they draft. `memory update` warns beyond `memory_tokens`.
- **`proposal_words`** is the length agents keep a proposal to, counted as the whitespace-separated
  words of its `statement`, its `rationale` and every prediction's `description` (names, filters and
  numbers don't count). `proposal set` (`proposal_set`) writes a longer proposal anyway and adds one
  line to its answer: "warning: 212 words, beyond this project's limit of 150 (agent.proposal_words);
  a proposal is frozen once a run records it, so shorten it now". It never refuses. The wizard asks
  for it in `Choose each setting` (100, 150 or 300 words; another value of the file is kept as a row),
  and `--agent-set proposal_words=<n>` sets it.
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
- Keep a proposal near 150 words: statement, rationale and prediction descriptions. (default)
- Main metric val/loss, lower is better; seeds in config.seed. (beamtime.yaml)
- After a verdict or decision, update the group's memory; keep it near 1500 tokens. (default)
- Save views when they pass validation; at most 2 render rounds. (default)
- Reuse built-in and library blocks before writing a custom block. (default)
- Never run user commands; hand the user the exact command. (fixed)
```

A value equal to the built-in careful preset is marked `default`; one set by the project names the
preset or `beamtime.yaml`; the four conventions only ever come from the file, so they are marked
`beamtime.yaml`. The proposal length line is left out when `research_record` is `off`, like the rules
block's `record_line`; the proposals part of the guide names the limit too
(`{{agent.proposal_words}}`). The rules block does not carry the limit. `guide` reads the settings through the
same `Context` as every operation, so a remote group's guide reads the remote project's settings.

### The rules block

Exactly two choices: write the rules (Beamtime is the record), or skip (`--no-rules`, nothing is
written; a later `beamtime setup` offers it again). The block goes into each chosen client's rules
file between `<!-- beamtime:start -->` and `<!-- beamtime:end -->`; a rerun replaces only the block.
It is generated from the agent settings by `guide/rules.py` from the template `guide/rules/rules.md`,
so text and settings agree:

```markdown
## Experiments: Beamtime is the record

This project's experimental record lives in Beamtime: runs, proposals, notes and memory. Look things
up there, and write findings there. Tools are named as over MCP; the CLI is `beamtime <name>` with
spaces for `_`.

- Start a work session with `status` (it includes the memory).
  `guide` lists its topics; read the one you need before writing proposals, notes or views. For a
  question about data, go straight to the narrowest tool below. A usage error prints the
  operation's help, so no `--help` first.
- Questions about past experiments: answer from `notes`, `status` and `runs`, not from recollection
  or loose files.
- Results, conclusions, dead ends and open questions go into a note on the run or group
  (`note_add`); what should outlive the session goes into the memory (`memory_update`). Not into this
  file, NOTES.md or your own memory; your own memory keeps coding preferences.
- {{record_line}}
- {{launch_line}}
- {{conventions}}
- Ask with the tools; never parse run files. Writes add new files; never edit, move or delete in the
  log dir. Name yourself (your model id) as author.
- Never run user commands ({{user_only}}); hand the user the exact command.
- A group on another source is `@<name>/<group>`; `status` lists the sources.

| Question | Tool or field |
|---|---|
| Which runs, how did they end, their settings | `runs` (`where`, `sort`, `limit`) |
| Best, mean or last value per setting | `runs` with `metric.<key>.<stat>` and `by` |
| At which step was the best value | `metric.<key>.min_step`, `max_step` |
| Where did a metric go NaN or infinite | `metric.<key>.nonfinite_step` |
| Where did a metric rise k times above its minimum | `metric.<key>.rise_step:<k>` (`rise_step`: k = 10) |
| One metric at the step of another | `metric.<a>[<b>.min_step]`, e.g. `metric.train/loss[val/loss.min_step]` |
| How did a metric evolve | `series` |
| What differs between runs or groups | `compare` |
| Which runs look wrong | `diagnose` |
| Have the runs finished | `wait` |
| Does the data support the prediction | `check` |
| All of it for my own script | `runs` or `series` with `to: name.csv`, once; the answer lists the columns |
```

- `record_line`: `off` leaves the line out; `encouraged` is "Before a run, write a proposal with
  predictions (`proposal_set`), {{seeds}} seeds per point."; `required` is "Never launch a run without
  a proposal with predictions (`proposal_set`); {{seeds}} seeds per point."
- `launch_line`: "Never launch runs yourself.", "Ask before you launch a run.", or "You may launch
  runs."
- `conventions` is "Main metric {{main_metric}} ({{direction_word}}), seeds in {{seed_key}}." with the
  parts the project sets (`direction_word` is "lower is better" or "higher is better"); without any, the
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
itself as author. The hand-off step comes after the write, when an agent was chosen and there are
notes or memory files, or an instruction conflict whose rules block was written. It offers each chosen
client that can start with a prompt (it has a start command and its program is on `PATH`), "Copy the
prompt" (for editor agents), or "Later" (`beamtime setup --migrate-with <agent>` brings it back).
Starting one replaces the wizard's process with the agent's interactive session in the same terminal
(`os.execvp`, in the project root), so the user watches it and can steer. `start_command(client, paths,
conflict)` builds the command: `claude "/beamtime:migrate <paths> <file:line>"`, or the client's start
command with "Run the beamtime migrate prompt with paths ... and conflict ..." for Codex and Gemini CLI.
"Copy" puts that sentence on the clipboard with the first of `pbcopy`, `wl-copy`,
`xclip -selection clipboard` and `clip` that is on `PATH`, and prints it when there is none. With an
agent chosen, the review leaves notes and memory files to the hand-off (`migrate_with` is the first
chosen agent), so the command the wizard prints carries `--migrate-with`; "Later" leaves them unwritten.

`beamtime setup --migrate-with <agent>` alone, in a set-up project, skips the questions and the list of
answers: on a terminal it starts the agent at once (an agent without a start command gets "Copy"), and
without one it prints the command to run. It hands over the notes and memory files the scan found, or
those named by `--import-notes` and `--import-memory`, and the first instruction conflict. With `--yes`
in any flow it writes first and then prints the command; it never starts a session without a terminal.

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
| W&B offline | `offline-run-*/files/config.yaml`, `wandb-metadata.json` (host, git, command), `wandb-summary.json`; the history from the `.wandb` file through the `wandb` package's datastore reader | without `wandb` installed, the summary as a one-step run, and the review says so (`Found.note`) |
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
  source_id, group, skipped)` holds one run (times as unix seconds, `rows` as `{"_step": n, "<key>": value}` records);
  `group` is the folder below the source's destination that the run belongs in (empty when the source
  has no structure; the MLflow experiment's name); `skipped` counts what the source holds that was
  left out, by kind (TensorBoard's non-scalar summaries), for the review's line. `write_run(logdir, dest, imported, provenance)` is
  the one writer. It writes the config, the metric
  lines, the card and the preview (`synth/summary.py:card_and_preview`) and `_run.json` last, so a
  crash leaves a folder no reader sees. `find_imported` walks `imported/` only. `detect` tells a
  path's source from file names alone (`events.out.tfevents.*`, `offline-run-*/*.wandb`,
  `mlflow.db` and `meta.yaml` beside `params/` or `metrics/`, `_run.json`, `*.csv`), skipping `.git`,
  `.venv`, `node_modules` and `__pycache__`; `Found(kind, path, n, label, note)` carries the count, the
  review's line and a note (W&B: that the history needs the package).
- **CSV details.** The first of `step`, `epoch`, `iteration` (any case) is the step; without one the
  row index is. Rows are written in step order. Cells that are not numbers, empty cells and columns
  that begin with `_` are skipped. A CSV carries no times, so `created_at` and `ended_at` are the
  file's modification time and every row's `_t` is `created_at`.

- **MLflow details.** `runs` reads every `mlflow.db` and every file-store run folder (`meta.yaml`
  beside `params/` or `metrics/`) at or below the path; `detect` counts them without reading
  metrics. The group is the experiment's name. Runs with `lifecycle_stage: deleted`, runs of deleted
  experiments and the file store's `.trash` are skipped. The status is `FINISHED`, `FAILED` or
  `KILLED` as `finished`, `failed` or `killed` (`RUNNING` and `SCHEDULED` as `running`), by name or,
  in the file store, by the `RunStatus` number. The name is the run name, else the `mlflow.runName`
  tag, else the first eight characters of the id. Params are the config; MLflow stores them as text,
  so numbers and `True`/`False` are read as such. A metric point is a `{"_step", "_t", key}` record;
  points of different keys at one step share a record, and a key logged twice at a step starts
  another record, so no point is lost and the order is the order logged. Metric `is_nan` rows become
  NaN. The git commit is the `mlflow.source.git.commit` tag; the source id is MLflow's run id.

- **TensorBoard details.** Every folder with `events.out.tfevents.*` files at or below the path is one
  run; the group is the folder's path below the path (Lightning's `version_<n>`; empty for the path
  itself), the name is the folder's name and the source id is the group (`.` for the path itself,
  so the run is found again on a rerun). The event files of a folder
  merge by step, in file name order; a tag logged twice at a step starts another record, as for
  MLflow. A truncated last record ends a file quietly. Checksums are not checked. `created_at` and
  `ended_at` are the first and last wall times, `status` is `finished`. A scalar is a `simple_value`
  or a rank-0 float32/float64 tensor (`tensor_content`, `float_val` or `double_val`); every other
  summary is left out and counted in `skipped` by the kind (`images`, `histograms`, `audio`, the
  plugin's name for tensors, `tensors` without one), each tag once. `hparams.yaml` in the folder is
  the config, empty when unreadable. Values stay as stored, so a float32 reads as its double.

- **W&B details.** Every `offline-run-*` folder with a `.wandb` file at or below the path is one run;
  the name and the source id are the run id (the folder name after its last `-`), the group is empty.
  `config.yaml` entries are `{desc, value}` and import as their `value`, without `_wandb` and
  `wandb_version`. `host` is `{hostname, os, python}` from `wandb-metadata.json`, `git` as it stands
  there, and the command is `executable`, `program` and `args`. `created_at` is `startedAt`, else the
  summary's `_timestamp` less its `_runtime`, else the folder's modification time; `ended_at` is the
  summary's `_timestamp`, else `created_at` plus `_runtime`. The status is `failed` for a non-zero
  `exit_code` (or `exitcode`) in the summary, then the metadata, and `finished` otherwise. The history
  reader is `wandb.sdk.internal.datastore.DataStore` (`open_for_scan`, `scan_data`) with
  `wandb.proto.wandb_internal_pb2.Record`, whose `history` records carry `item.key` or `nested_key`
  and `item.value_json`; both exist in `wandb` 0.12.21 to 0.28.2 (checked) and not in 0.30.0, where
  the reader counts as missing. A history record is a `{"_step", "_t", key}` record: the numeric values
  only, keys that begin with `_` and booleans and text left out, media (`{"_type": ...}`) counted in
  `skipped` by type. A run cut off mid-write keeps the records before the cut. When there is no
  history, the summary's numeric values are the run's one record at step 0.

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
- A run id that exists in the log dir already is skipped (it was imported before); a second import
  therefore copies runs the source gained since and authored files it lacks, and records no move twice.

`setup/importers/beamtime.py:copy_logdir(logdir, source, name) -> Copied(runs, skipped)` does it, with
its own walk instead of `detect`/`runs`:

- **What is copied.** Run folders whole (checkpoints included), and the authored folders (`proposal/`,
  `notes/`, `view/`, `memory/`, `blocks/`) of every group and of the source's root, so a library block at
  the source root is found by the views below `imported/<name>/`. Trash (`_trash/`), `.beamtime/` and
  machine-written files at group level are left behind, and so is the destination log dir when the source
  contains it. A source that is itself one run copies that run. Authored files that exist already are left
  as they are.
- **`_run.json`.** `proposals` and `proposal_hashes` keys other than `.` gain the prefix;
  `imported_from` is `{kind: "beamtime", path: <the run's folder in the source>, id, host, at}`, replacing
  an earlier one. The file's modification time (the heartbeat) is kept, so a run that was lost stays lost.
- **Moves.** One scoped move per top-level group of the source; then the source's own moves, prefixed, and
  the old first folder of each of those gets a scoped move too (`a` to `imported/<name>/a`), so a path
  named before the source's own move reaches the copy. A scoped move renames no folder on disk, so
  `moved_scope` in `format/moves.py` needs no change for it.

`copy_logdir` takes a log dir's root as its source, since proposal membership keys start there. When
the path found or typed lies inside a log dir (one the index cache knows, or the one a `beamtime.yaml`
above it names), `plan()` passes that log dir's root and the review's line says so ("... is inside this
log dir, so all of it is imported"); a project folder passes its log dir (its `beamtime.yaml` names it),
a single run is passed as it is, and this project or a path inside its own log dir is refused. A subfolder is never imported as if it were a root. Checkpoints and other large
files are copied byte for byte, and the import's line in the review shows the bytes to copy
(`Copier.size()`), so the cost is known before the user confirms.

Reading another project's runs in place (a local-path source) is out of scope.

### Notes and memory files

With an agent, they go to the `migrate` prompt. Without one ("None", or the hand-off left for later
and `--yes` given), each file comes in as written: one `observation` note on the log dir per file,
its body the file's text, its description the file name or first heading, author the local account.
A folder gives one note per file below it. The notes go through the `note add` operation, so author
and user are the local account as for every authored write. Binary files are skipped, and the review
names them.

## Git and the SDK

`--git record` (the default) replaces the log dir's ignore entry with the run data only, so the
research record is reviewed and shared through git:

```gitignore
# beamtime: run data stays out; proposals, notes, memory and views are committed
beamtime/**/_*
beamtime/**/artifacts/
beamtime/**/checkpoints/
.beamtime/
# end beamtime
```

`--git none` ignores `beamtime/` and `.beamtime/`. Entries are written as one marked block, from its
`# beamtime:` header line to `# end beamtime`, replaced on a rerun; an older plain `beamtime/` or
`.beamtime/` line is taken out, and the block stands where the first of them stood. A linked log dir (`--link-logdir`) is machine-local: the link itself goes into
`.git/info/exclude` (as `/beamtime`, without a trailing slash, since a link is not a folder to git), and
git can't see through it, so the review says that this checkout doesn't commit the record. The target
is created when missing; an existing log dir that holds files is never replaced by a link, and a plan
that would do so is refused before anything is written. A `--logdir` outside the project means the
same as a link there: `beamtime.yaml` keeps the default name and the link points at the path.

`--sdk` adds Beamtime with the project's own tool: `uv add beamtime` (and the dev group, [above](#the-mcp-command)),
`poetry add beamtime`, `conda run -n <env> python -m pip install beamtime` for conda, or
`<venv>/bin/python -m pip install beamtime` plus a `beamtime` line in `requirements.txt` for pip. The
SDK needs Python 3.10; an older project Python is named in the step and the default becomes No.
`setup/sdk.py:sdk_change()` plans it as argument lists run in the project root with
`subprocess.run(check=True)`; `sdk_blocker()` gives the reason when the Python is too old, and then
`sdk_change()` returns `None`. `plan()` calls it only for `--sdk`, refuses with the reason when there is
no environment or its Python is too old, and leaves the step out when the environment has this release or
a newer one (with the serve extra where the MCP command runs from it). A conda environment gets `beamtime[serve]` when the MCP command runs
from it; a pip project without a virtualenv only gets the `requirements.txt` line.

## Updating an older setup

Updating is `beamtime setup` again. Data never migrates: every file reads in every later release. What
goes stale is the setup around it, and each item has a check in `setup/stale.py` that returns
`Stale(item, before, after)` or nothing:

| Item | Stale when | Update |
|---|---|---|
| `rules` | the block is from an older release (a hand-edited block is listed, unticked) | replace the block |
| `mcp` | a registered MCP command doesn't start (`--version` fails, run in the project root) or isn't what `mcp_command()` picks now (`--root` aside); nothing is listed when no command could replace it | rewrite that entry |
| `skills` | the project has Beamtime skills and one differs from this release's or is missing | rewrite them |
| `settings` | a key this release no longer reads (the `MOVED` keys, e.g. `colormap`) | remove it, keeping the rest of the file |
| `sdk` | the project environment has an older Beamtime | the tool's upgrade command |
| `remote:<name>` | the remote's Beamtime is older than this one | `pip install --user -U` there, after the review |
| `runs` | Beamtime runs in the project outside the log dir, whose run names the log dir lacks | an import into the log dir (the default `--import`, `--import ''` declines) |

- **The setup's release** is found without stamps: `guide/rules/history/` keeps the rules text of
  every earlier release that changed it (`0.1.0.md`, `0.2.0.md`), `guide/rules/rules.md` is this
  release's template, and the block is matched against each, with the template's placeholders as
  wildcards (`guide/rules.py:release_of`). The newest matching release names the
  setup ("set up with 0.1.1" names the last release that wrote that text). A block that matches none
  was edited by hand: its update is offered unticked, with the diff.
- The wizard first checks the data and says it is fine (runs, notes, proposals and views read as
  they are; the index rebuilds once if its schema changed), then lists the stale items, all ticked,
  then asks only the questions new since the setup's release (e.g. agent behaviour and the rules
  choice for a 0.1 setup), and ends with the few changes a person would notice, from a short list kept
  per release in `setup/changes.py`.
- **`beamtime setup --check`** runs the checks without a terminal, prints one line per stale item
  (`item: before -> after`) and exits 3 if there is one (the answer's `meta.exit`), 0 otherwise; for CI
  and for agents, who hand the user `beamtime setup`. It is local: `remote:<name>` needs a probe, so
  `stale_remote(name, version)` is checked by the wizard after its probe and `--update remote:<name>`
  installs there without a check.
- **`Scan.stale`** holds the items (`Stale(item, before, after, ticked, path)`) of a project that has a
  `beamtime.yaml` or a log dir; a set-up project with any is in the `update` flow. `Answers.defaults`
  ticks the items of `--update` (all but `runs` and an unticked one) and makes each `runs` item's folder
  an `--import`. `plan()` plans each ticked item: the rules block of every file that has one, every
  registered MCP entry, the skills, the removal of moved keys from `beamtime.yaml`, the SDK upgrade
  (`uv add 'beamtime>=X'` and its kin) and the remote install. `setup/changes.py:since(release, current)`
  gives the lines for the end of the wizard.
- **`beamtime status`** (and the MCP `status`, as the answer's `setup`) adds one line when the rules block
  is from an older release: "set up with 0.1.1; `beamtime setup` updates it". Only the rules check runs
  there, since it reads two small files (`guide/rules.py:outdated_release`, over `RULES_FILES`); nothing
  of `beamtime.setup` is imported.

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
- **Import budget**: the wizard's modules load only when `setup` runs; the plain CLI path stays within
  `tests/test_budgets.py`.

## Module layout

| Module | Holds |
|---|---|
| `setup/scan.py` | `Scan` and `scan(root)`: the facts above, local only |
| `setup/plan.py` | `Answers` (msgspec, one field per flag; `defaults()`, `saved()`, `from_params()`), `Change` (where it lands, label, before, after, run) and `plan(scan, answers) -> list[Change]`; `review(changes)` writes the plan as text |
| `setup/apply.py` | `apply(changes, say) -> list[Change]` runs a plan in order; `ApplyError(done, failed, error)` stops it at the first failure and names what was done |
| `setup/flow.py` | `Step`, `run()`, `setup()` and `reconfigure()` ([The wizard](#the-wizard), [Reconfiguring](#reconfiguring)), the questions of each flow (`FirstSetup`, `Teammate`, `Cluster`, `Update`), their defaults from the scan |
| `setup/term.py` | the prompt primitives |
| `setup/agents.py` | the client table, `mcp_command()`, registering, the rules block written to files |
| `setup/remotes.py` | the parallel probe (`probe_host` also used by `source add`), the remote name rule, installs, ssh sharing |
| `setup/importers/` | `tensorboard`, `wandb`, `mlflow`, `csv`, `beamtime`, and the one run writer |
| `setup/stale.py`, `setup/changes.py` | `Stale`, `find()` and one check per item; the noticeable changes per release (`since()`) |
| `guide/rules.py`, `guide/rules/` | the rules template, its history, rendering and matching |
| `index/cache.py` | `resolve_cache()` |
| `settings.py` | `cache`, `agent` (presets, validation, resolution), `remotes.<name>.enabled` |

`ops/admin.py:setup` is the entry that builds `Answers` from flags and either runs the flow (a
terminal, no `--yes`) or plans and applies directly.

`plan()` orders the changes project, machine, agents, imports, then the remote ones of `--ssh-share` and
`--install-remote`; `where` groups them in the review. What it decides:

- **`beamtime.yaml`** gets `logdir`, `agent` and remote `path`s, only where the file lacks the value or
  says another. An `agent` the project has already is kept; `--agent-style` and `--agent-set` change it
  on top. `style` is written with the agent choice, so a project that chose agents records `careful`.
  `--agent-set` values are read as YAML and checked against the key's rule (`seeds=abc`, `launch_runs=x`
  and `significance=1.5` are refused with the rule), so numbers are written as numbers.
- **This machine's settings** get `cache` when `--cache` names one, the `host` of each `--remote` (the
  name when no host is given), `command: ~/.local/bin/beamtime` for a remote that `--install-remote`
  installs, else the `--remote-command` (plain `beamtime` only to replace another command), and `enabled: false` for `--skip-remote`. A value that is already there is not written, so a
  rerun writes nothing and a default is never written.
- **Agents**: per client the MCP registration (left out when already registered, unless `--update mcp`),
  the skills for Claude Code (when they differ), and one rules block per rules file (left out when the
  file has the block this release generates). `--instructions` without `--agents` names the one client
  whose rules file the old flag chose.
- **Imports** as above; notes and memory files come in as written (`note add`) unless `--migrate-with`
  hands them to an agent. The log dir is created for them if missing.
- Every refusal (an unknown or contradicting answer, a log dir that is not empty where a link would go,
  a path that holds nothing to import, a client that can't be registered) is a `ValueError` raised by
  `plan()`, before anything is written.

`setup` without `--yes` and without a terminal prints the review and the command, writes nothing and exits
0; with `--yes` it applies, and a failing change ends the answer with an error naming what was done. `mcp install` calls `setup/agents.py`.

## Testing

- **Scan fixtures**: small project trees per scenario (first setup, teammate, cluster, update from
  0.1.1), built in `tmp_path`; the scan's facts are asserted, with `/proc/mounts` and `~/.ssh/config`
  pointed at fixture files.
- **Flags and prompts agree**: for each scenario, answers given by the scripted prompts and by the
  printed `--yes` command produce the same plan.
- **No trace**: every scenario aborted at every step leaves the tree and the fake home byte-identical.
- **The terminal**: the primitives run against a pseudo-terminal (`pty`) with scripted keys; the
  numbered fallback reads from a pipe. A whole flow is scripted one prompt at a time: the test waits for
  the prompt's title on the screen, then types its keys (keys typed ahead are flushed when the next
  prompt enters raw mode).
- **Importers**: small checked-in fixtures per source (a TensorBoard event file, an MLflow file store
  and `mlflow.db`, a W&B offline run, a CSV) and a golden Beamtime log dir; imported runs answer `runs`
  and `series` like native ones; a second import adds nothing.
- **The MCP command**: per environment kind, the chosen command, and that shared files never get an
  absolute path.
- **Updating**: a project set up with each earlier release's files is detected as that release, and
  `--check` exits 3, then 0 after `setup --yes`.
- **Remotes**: the probe and the install over real ssh in the Docker test (`BEAMTIME_DOCKER=1`).

## Decisions

- One command, `beamtime setup`, for first setups, teammates, clusters and updates.
- Nothing is written before the review; every answer is a flag; without a terminal nothing is asked
  and nothing outside the project happens unless a flag names it.
- `cache` is a setting at both levels with placeholders, resolved by one function for every consumer;
  network filesystems are refused for memory, also for the built-in default.
- `agent` in `beamtime.yaml` holds a preset and overrides; careful is the default; the knobs are
  guidance and never change what files mean.
- The rules block is generated from the agent settings; two choices, write it or skip.
- The MCP command is portable in shared files and never points into a project virtualenv when anything
  else works.
- Imports copy, never move; each imported run records `imported_from`; Beamtime log dirs copy without
  conversion and keep their paths meaningful through moves scoped with `within`.
- The wizard never calls a model; the `migrate` prompt hands judgment to the user's agent.
- The command is `beamtime setup`; there is no `beamtime init`. `beamtime.init()` is the SDK's call.
- A current setup reconfigures: the list of answers starting from what is set up, asking only what the
  user picks; a rules block whose settings changed is refreshed there, not reported by `--check`.
- `agent.proposal_words` (default 150) is guidance: the guide names it, `proposal set` warns beyond it
  and never refuses.
