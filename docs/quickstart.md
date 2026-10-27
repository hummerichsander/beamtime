# Quickstart

Beamtime records your training runs as plain folders in your repository and lets you and your coding
agent look at them from the command line or through MCP.

## Install and set up a project

```sh
pip install 'beamtime[serve]'      # or: uv add 'beamtime[serve]'
cd my-project                      # a git repository
beamtime init                      # beamtime.yaml, and beamtime/ in .gitignore
```

## Record a run

```python
import beamtime

run = beamtime.init(dir="scaling/lr-sweep", config={"lr": 3e-4},
                    proposal="lr 3e-4 converges fastest.")
for step in range(1000):
    loss = train_step()
    run.log({"train/loss": loss}, step=step)
run.finish()
```

Every run is a folder below `beamtime/`: `_run.json`, `_metrics.jsonl`, `_output.log` and friends.
Output, crashes, `SIGTERM` and resumes are recorded without further code. On a cluster, point
`BEAMTIME_LOGDIR` at scratch space.

## Look at runs

```sh
beamtime runs                                   # newest runs with their main metrics
beamtime runs scaling/lr-sweep --sort -metric.val/acc.max --limit 5
beamtime series scaling/lr-sweep -y train/loss  # curves as one line each
beamtime card <run id>                          # one run in detail
beamtime output <run id> --tail 50              # what it printed
beamtime timeline . --limit 20                  # what happened, in order
beamtime keys .                                 # what was logged
```

Add `--json` for the full answer. `beamtime doctor` checks the setup; `beamtime status` shows the
log dir, the index and whether a daemon keeps it live.

## Connect an agent

```sh
beamtime mcp install --client claude-code      # or cursor, codex
```

Then ask your agent, for example: "How did last night's runs go?" It uses the same operations as the
CLI. Agents only read and add; moving, deleting and setup stay with you (`beamtime mv`, `rm`, `gc`).
