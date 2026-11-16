# Setting up a project

`beamtime setup` sets up a project and the machine you work on. It looks at what is there, asks a
few questions, shows everything it will change, and writes only after you confirm. Press Enter
through the questions to take what it found. Ctrl-c at any point leaves the project and the machine
as they were.

Up to 0.2 the command was `beamtime init`; it is `beamtime setup` now, with no old name. (The
`beamtime.init()` call in your script is unchanged.)

## What it asks

Which questions you get depends on where you run it:

| You are... | It asks |
|---|---|
| in a new project | where runs happen, the log dir, remote machines, agents and how much they do on their own, past work, git, the SDK |
| a teammate joining a project that uses Beamtime | only what is about your machine: your agents, which of the project's machines you use, how you reach them |
| on a cluster login node | what the machine does (`record` or `full`), where runs go (a link to scratch), the index cache |
| in a project set up with an older release | what to bring up to date, and only the questions that are new since |
| in a project that is set up and current | nothing up front: the list of your answers, and then only what you pick |

Every flow ends the same way: a review grouped by where each change lands (the project, this
machine, remote machines, imports), then `Write it`, `Change an answer`, or `Show the command and
quit`. The command it prints is a `beamtime setup --yes ...` that makes the same setup on another
machine or in a script.

## Without a terminal

Without a terminal, `beamtime setup` asks nothing. It prints the review and the command and writes
nothing. With `--yes` it writes. Nothing outside the project happens unless a flag names it: no
installs on remote machines, no ssh config, no SDK, and agents are registered only when `--agents`
names them. A session of an agent is never started.

```sh
beamtime setup --yes                          # beamtime.yaml, the log dir and .gitignore
beamtime setup --yes --agents claude-code     # and the MCP server and rules for Claude Code
```

## Flags

Every answer is a flag. Flags and questions make the same plan.

| Flag | What it answers | Example |
|---|---|---|
| `--runs here\|remote\|both` | where runs happen; decides the questions | `beamtime setup --yes --runs both --remote juwels` |
| `--logdir PATH` | the log dir; a path outside the project is linked in | `beamtime setup --yes --logdir runs` |
| `--link-logdir PATH` | make the log dir a link to `PATH` (scratch space) | `beamtime setup --yes --link-logdir '${SCRATCH}/myproject/beamtime'` |
| `--remote NAME[=HOST][:PATH]` | a remote machine: its name, how you reach it, its log dir there | `beamtime setup --yes --runs both --remote juwels:'${SCRATCH}/myproject/beamtime'` |
| `--skip-remote NAME` | a remote of the project that this machine doesn't use | `beamtime setup --yes --skip-remote lab-gpu` |
| `--install-remote NAME` | install this version of Beamtime there, after the review | `beamtime setup --yes --remote juwels --install-remote juwels` |
| `--ssh-share NAME` | add the ssh lines that share one login per session | `beamtime setup --yes --ssh-share juwels` |
| `--cache memory\|PATH` | the index cache of this machine | `beamtime setup --yes --cache memory` |
| `--agents A,B` / `--no-agents` | which agents get the MCP server and the rules | `beamtime setup --yes --agents claude-code,codex` |
| `--agent-style careful\|hands-on\|analysis` | how much agents do on their own | `beamtime setup --yes --agents claude-code --agent-style hands-on` |
| `--agent-set KEY=VALUE` | one agent setting, repeatable | `beamtime setup --yes --agents claude-code --agent-set seeds=5 --agent-set proposal_words=300` |
| `--no-rules` | register agents but write no rules block | `beamtime setup --yes --agents codex --no-rules` |
| `--import PATH` | runs to copy in; `''` for none | `beamtime setup --yes --import tb_logs/` |
| `--import-notes PATH`, `--import-memory PATH` | notes and memory files for your agent, or as notes | `beamtime setup --yes --import-notes NOTES.md` |
| `--git record\|none` | commit the research record, or ignore the whole log dir | `beamtime setup --yes --git none` |
| `--sdk` / `--no-sdk` | add the SDK to the project's environment | `beamtime setup --yes --sdk` |
| `--role record\|full` | on a cluster: only record runs, or also look at them | `beamtime setup --yes --role record` |
| `--update A,B` | stale items to bring up to date | `beamtime setup --yes --update rules,mcp` |
| `--migrate-with AGENT` | start an agent on your notes and memory | `beamtime setup --migrate-with claude-code` |
| `--check` | list what is stale and exit | `beamtime setup --check` |
| `--yes` | write without the review | `beamtime setup --yes` |
| `--root PATH` | another project's root | `beamtime setup --root ~/work/egnn --check` |

`--agents` names `claude-code`, `codex`, `cursor`, `vscode`, `gemini`, `opencode`, `windsurf` or
`other` (which prints the MCP config to paste). `--agent-set` takes the keys of the
[`agent` setting](settings.md#agent); `k=v,k=v` in one flag also works.

## Agents

Each agent you pick gets the MCP server in its own config, and a block of rules in its instruction
file (`CLAUDE.md`, `AGENTS.md` or `GEMINI.md`) that says Beamtime is the record: findings go into
notes and the memory, not into loose files. The block sits between `beamtime` markers and a rerun
replaces only the block, so your own text around it stays. Choose `Skip` (or `--no-rules`) to write
no block.

How much agents do on their own is one of three presets: **careful** (they propose and analyze, you
launch runs), **hands-on** (they may launch runs too) and **analysis only** (no proposals; tables,
charts and pages). `Choose each setting` shows every knob, including `proposal length` (100, 150 or
300 words). The choice is written to `beamtime.yaml` under `agent`; see [Settings](settings.md#agent).
The main metric, seed key and domain are not asked: set them under `agent:` yourself.

## Past work

`beamtime setup` copies earlier runs into the log dir, under `imported/`, as ordinary runs that
remember where they came from (`imported_from`). The originals are never touched, and importing the
same folder twice copies only what is new.

| Source | What comes in |
|---|---|
| TensorBoard | scalars, with `hparams.yaml` (Lightning) as config; images, histograms and text are left out |
| Weights & Biases (offline runs) | config, summary and, where the history can be read, the metrics |
| MLflow | the file store and `mlflow.db`: params, metrics, tags and status; artifacts are left out |
| CSV | one run per file; a `step`, `epoch` or `iteration` column is the step, other numeric columns are metrics |
| Beamtime | runs, with their proposals, notes, memory, views and library blocks |

A few things to know:

- **Keras and the TensorBoard callback.** Every folder with event files is one run. Keras writes
  `train/` and `validation/` side by side, so a fit comes in as two runs, one per folder, both
  with the same metric names; they are not merged into one run with a training and a validation
  curve.
- **Weights & Biases.** Reading the history of an offline run needs the `wandb` package in the
  environment that runs `beamtime setup`. Its reader was checked up to `wandb` 0.28.2 and is gone in
  0.30. With `wandb` 0.30 or newer, or without it, the run comes in with its config and its summary as a single step,
  and the review says so.
- **Beamtime runs outside the log dir** (an old log dir, runs from before you moved the log dir) are
  copied in by default, also under `--yes`. They are a copy; the originals stay. `--import ''`
  declines. In a project with neither a `beamtime.yaml` nor a log dir yet, the wizard offers them
  ticked, and without a terminal you name them with `--import`.
- **Large files.** Checkpoints are copied too; the review shows how many bytes it will copy.

Notes and memory files (`NOTES.md`, a `notes/` folder, Claude Code's project memory) are turned into
typed notes by your agent, since that takes judgment. After the write, the wizard offers to start the
agent on them, to copy the prompt for an editor agent, or to leave it for later.

```sh
beamtime setup --migrate-with claude-code
```

starts the agent later. In a set-up project it skips the questions: on a terminal it starts the agent
in the project at once, and without a terminal it prints the command to run. `--yes` never starts a
session.

## Updating

After you upgrade Beamtime, run `beamtime setup` again. Your data never needs migrating: every file
reads in every later release. What goes stale is the setup around it: the rules block in your
instruction files, an MCP command that no longer starts, the skills, a setting this release no longer
reads, the SDK in your environment, Beamtime on a remote machine, and Beamtime runs outside the log
dir. The wizard checks the data first and says it is fine, then lists the stale items, all ticked, and
asks only what is new since your setup. Skipping the rules question keeps the old rules block as it
is; setup never removes one.

```sh
beamtime setup --check          # one line per stale item; exit 3 if there is one, 0 if not
beamtime setup --yes            # bring every stale item up to date
beamtime setup --yes --update rules,mcp
```

`beamtime status` says in one line when the rules block is from an older release. A rules block you
edited by hand is listed but not ticked.

## Changing an answer

In a project that is set up and current, `beamtime setup` opens the list of your answers with their
current values: where runs happen, the remotes, the agents, how much they do, the rules, git and the
SDK. Pick one to ask it again (and the questions it newly turns on: choosing an agent where there
was none also asks how much it does and the rules), then review the change. `Review the changes`
goes straight to the review.

If you edit `agent` in `beamtime.yaml`, the rules block in `CLAUDE.md` no longer matches it. The list
says so, and the review rewrites the block. Without a terminal, `beamtime setup --yes --update rules`
does the same; `--check` and `status` stay quiet, because the setup is current.

On a cluster checkout that is already set up, the cluster questions come again, and the wizard ends
with "Nothing to change." when your answers change nothing.

## Git and the SDK

By default the research record (proposals, notes, memory, views) is committed and run data stays out
of git, through a marked block in `.gitignore`. `--git none` ignores the whole log dir. A linked log
dir (`--link-logdir`) is local to the machine, so that checkout doesn't commit the record, and the
review says so.

`--sdk` adds `beamtime` to the project's environment with the project's own tool (`uv add`,
`poetry add`, `conda` or `pip`). It is asked only when the environment doesn't have Beamtime and its
Python is 3.10 or newer.
