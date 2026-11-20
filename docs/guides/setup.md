# Setting up a project

`beamtime setup` sets up a project and the machine you work on. It looks at what is there, asks a
few questions, shows every change, and writes only after you confirm. Enter takes what it found;
Ctrl-c leaves everything as it was.

## What it asks

| You are... | It asks |
|---|---|
| in a new project | where runs happen, the log dir, remote machines, agents and how much they do on their own, past work, git, the SDK |
| a teammate joining a project that uses Beamtime | only what is about your machine: your agents, which of the project's machines you use, how you reach them |
| on a cluster login node | what the machine does (`record` or `full`), where runs go (a link to scratch), the index cache |
| in a project set up with an older release | what to bring up to date, and only the questions that are new since |
| in a project that is set up and current | nothing up front: the list of your answers, and then only what you pick |

Every flow ends in a review grouped by where each change lands (project, this machine, remotes,
imports): `Write it`, `Change an answer`, or `Show the command and quit`. The printed command,
`beamtime setup --yes ...`, makes the same setup on another machine or in a script.

## Without a terminal

Without a terminal, `beamtime setup` prints the review and the command and writes nothing; `--yes`
writes. Nothing outside the project happens unless a flag names it (remote installs, ssh config, the
SDK, agents via `--agents`). No agent session is started.

```sh
beamtime setup --yes                          # beamtime.yaml, the log dir and .gitignore
beamtime setup --yes --agents claude-code     # and the MCP server and rules for Claude Code
```

## Flags

Every answer is a flag; flags and questions make the same plan.

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

Each agent you pick gets the MCP server in its config and a rules block in its instruction file
(`CLAUDE.md`, `AGENTS.md` or `GEMINI.md`): findings go into notes and the memory, not loose files.
The block sits between `beamtime` markers; a rerun replaces only the block. `Skip` (or `--no-rules`)
writes none.

Presets for how much agents do on their own:

- **careful**: they propose and analyze, you launch runs.
- **hands-on**: they may launch runs too.
- **analysis only**: no proposals; tables, charts and pages.

`Choose each setting` shows every knob, including `proposal length` (100, 150 or 300 words). The
choice goes to `beamtime.yaml` under `agent` ([Settings](settings.md#agent)). Set the main metric,
seed key and domain there yourself.

## Past work

`beamtime setup` copies earlier runs into the log dir under `imported/`, as ordinary runs with
`imported_from`. Originals are never touched; a second import copies only what is new.

| Source | What comes in |
|---|---|
| TensorBoard | scalars, with `hparams.yaml` (Lightning) as config; images, histograms and text are left out |
| Weights & Biases (offline runs) | config, summary and, where the history can be read, the metrics |
| MLflow | the file store and `mlflow.db`: params, metrics, tags and status; artifacts are left out |
| CSV | one run per file; a `step`, `epoch` or `iteration` column is the step, other numeric columns are metrics |
| Beamtime | runs, with their proposals, notes, memory, views and library blocks |

- **Keras / TensorBoard callback**: every folder with event files is one run, so a fit's `train/`
  and `validation/` come in as two runs with the same metric names.
- **Weights & Biases**: reading an offline run's history needs `wandb` below 0.30 in the environment
  that runs `beamtime setup`. Otherwise the run comes in with its config and its summary as one
  step, and the review says so.
- **Beamtime runs outside the log dir** are copied in by default, also under `--yes`; `--import ''`
  declines. In a project with neither `beamtime.yaml` nor a log dir, the wizard offers them ticked;
  without a terminal, name them with `--import`.
- **Large files**: checkpoints are copied too; the review shows the bytes.

Notes and memory files (`NOTES.md`, a `notes/` folder, Claude Code's project memory) become typed
notes through your agent. After the write, the wizard offers to start the agent, copy the prompt for
an editor agent, or leave it for later.

```sh
beamtime setup --migrate-with claude-code
```

starts it later, skipping the questions: on a terminal it starts the agent, without one it prints
the command. `--yes` never starts a session.

## Updating

After an upgrade, run `beamtime setup` again. Data never needs converting. What can go stale is the
setup around it: the rules block, the MCP command, the skills, an unread setting, the SDK, Beamtime
on a remote, and runs outside the log dir. The wizard lists the stale items, all ticked, and asks
only the new questions. Setup never removes a rules block.

```sh
beamtime setup --check          # one line per stale item; exit 3 if there is one, 0 if not
beamtime setup --yes            # bring every stale item up to date
beamtime setup --yes --update rules,mcp
```

`beamtime status` flags an outdated rules block. A block you edited by hand is listed but not ticked.

## Changing an answer

In a current project, `beamtime setup` lists your answers (where runs happen, remotes, agents, how
much they do, rules, git, SDK). Pick one to ask it again, with any questions it turns on, then
review. `Review the changes` goes straight to the review.

After you edit `agent` in `beamtime.yaml`, the list flags the stale rules block and the review
rewrites it; without a terminal, `beamtime setup --yes --update rules`. `--check` and `status` stay
quiet, since the setup is current.

On a set-up cluster checkout, the cluster questions come again; unchanged answers end with "Nothing
to change."

## Git and the SDK

By default the research record (proposals, notes, memory, views) is committed and run data is
ignored through a marked block in `.gitignore`. `--git none` ignores the whole log dir. A linked log
dir (`--link-logdir`) is machine-local, so that checkout commits no record; the review says so.

`--sdk` adds `beamtime` with the project's tool (`uv add`, `poetry add`, `conda` or `pip`). It is
asked only when the environment lacks Beamtime and runs Python 3.10 or newer.
