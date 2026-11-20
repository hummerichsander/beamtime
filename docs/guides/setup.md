# Setting up a project

`beamtime setup` sets up the project and this machine, writing only after you confirm the changes. Enter takes what it found; Ctrl-c leaves everything as it was.

## What it asks

| You are... | It asks |
|---|---|
| in a new project | where runs happen, the log dir, remotes, agents and how much they do, past work, git, the SDK |
| joining a project that uses Beamtime | only about your machine: your agents, which remotes you use, how you reach them |
| on a cluster login node | the machine's role (`record` or `full`), where runs go (a link to scratch), the index cache |
| in a project set up by an older release | what to update, and only the new questions |
| in a current project | nothing: it lists your answers to pick from |

The review groups changes by where they land: `Write it`, `Change an answer`, or `Show the command
and quit`, whose `beamtime setup --yes ...` repeats the setup elsewhere.

## Flags and scripts

Every answer is a flag; the [command reference](../reference/cli.md#beamtime-setup-you) lists them.
Without a terminal, setup prints the review and the command and writes nothing; `--yes` writes.
Nothing outside the project changes unless a flag names it.

```sh
beamtime setup --yes                                     # beamtime.yaml, the log dir, .gitignore
beamtime setup --yes --agents claude-code,codex --agent-style hands-on
beamtime setup --yes --runs both --remote juwels:'${SCRATCH}/myproject/beamtime' --install-remote juwels
beamtime setup --yes --import tb_logs/                   # past runs; --import '' for none
```

- `--agents` takes `claude-code`, `codex`, `cursor`, `vscode`, `gemini`, `opencode`, `windsurf` or
  `other` (prints the MCP config to paste).
- `--agent-set KEY=VALUE` (repeatable, or `k=v,k=v`) sets one [`agent` setting](settings.md#agent).

## Agents

Each agent gets the MCP server and a rules block in its instruction file (`CLAUDE.md`, `AGENTS.md`
or `GEMINI.md`) telling it to keep findings in notes and memory. A rerun replaces only the block
between the `beamtime` markers; `--no-rules` writes none.

Presets for how much agents do on their own:

- **careful**: they propose and analyze, you launch runs.
- **hands-on**: they may launch runs too.
- **analysis only**: no proposals; tables, charts and pages.

`Choose each setting` shows every key, including proposal length (100, 150 or 300 words). The
choice goes to `agent` in `beamtime.yaml` ([Settings](settings.md#agent)); set the main metric, seed
key and domain there yourself.

## Past work

Setup copies earlier runs into the log dir under `imported/` as ordinary runs with `imported_from`.
Originals are never touched; a second import copies only what is new.

| Source | What comes in |
|---|---|
| TensorBoard | scalars, with `hparams.yaml` (Lightning) as config; no images, histograms or text |
| Weights & Biases (offline) | config, summary and, where readable, the metrics |
| MLflow | file store and `mlflow.db`: params, metrics, tags, status; no artifacts |
| CSV | one run per file; a `step`, `epoch` or `iteration` column is the step, other numeric columns are metrics |
| Beamtime | runs with their proposals, notes, memory, views and library blocks |

- **Keras**: every folder with event files is one run, so `train/` and `validation/` become two runs
  with the same metric names.
- **W&B history** needs `wandb` below 0.30 where setup runs; otherwise the run gets its config and
  its summary as one step, and the review says so.
- **Beamtime runs outside the log dir** are copied in by default, also under `--yes`.
- **Checkpoints** are copied too; the review shows the size.

Notes and memory files (`NOTES.md`, a `notes/` folder, Claude Code's project memory;
`--import-notes`, `--import-memory`) become typed notes through your agent. After writing, setup
offers to start the agent, copy the prompt, or wait; `beamtime setup --migrate-with claude-code`
starts it later. `--yes` never starts a session.

## Updating

After an upgrade, run `beamtime setup` again. Data never needs converting; setup lists what went
stale (rules block, MCP command, skills, settings, SDK, Beamtime on a remote, runs outside the log
dir), ticked, and asks only new questions. It never removes a
rules block, and a block you edited by hand is listed but not ticked.

```sh
beamtime setup --check                   # stale items; exit 3 if any, 0 if none
beamtime setup --yes                     # update all of them
beamtime setup --yes --update rules,mcp  # update some
```

`beamtime status` flags an outdated rules block.

## Changing an answer

In a current project, `beamtime setup` lists your answers; pick one to ask again (with the
questions it turns on), or go straight to `Review the changes`. After editing `agent` in
`beamtime.yaml`, the list flags the rules block; without a terminal run
`beamtime setup --yes --update rules`.

## Git and the SDK

By default the research record (proposals, notes, memory, views) is committed and run data is
ignored through a marked block in `.gitignore`; `--git none` ignores the whole log dir. A linked log
dir (`--link-logdir`) is machine-local, so that checkout commits no record.

`--sdk` adds `beamtime` with the project's tool (`uv`, `poetry`, `conda` or `pip`); setup asks only
when the environment runs Python 3.10+ without Beamtime.
