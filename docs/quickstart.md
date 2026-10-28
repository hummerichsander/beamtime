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

## Propose, check, conclude

Write down what a sweep should show before you launch it; every run started afterwards records it.

```yaml
# proposal.yaml
statement: lr 3e-4 gives the best final val/acc.
plan: {grid: {config.lr: [1e-4, 3e-4, 1e-3], config.seed: [0, 1, 2]}}
predictions:
  - name: best-beats-high
    reduce: {metric: val/acc, stat: last}
    test: compare
    a: {config.lr: 3e-4}
    b: {config.lr: 1e-3}
    op: ">"
    margin: 0.005
```

```sh
beamtime proposal set scaling/lr-sweep proposal.yaml
beamtime check scaling/lr-sweep                 # results with t-intervals; provisional until the grid is done
beamtime note add scaling/lr-sweep --type verdict --proposal <version> \
    --verdict best-beats-high=confirmed --overall confirmed \
    --description 'lr 3e-4 wins by about a point' < findings.md
beamtime folders .                              # status, check and verdict of every folder
beamtime memory update . memory.md              # the compressed summary agents read first
```

## Connect an agent

```sh
beamtime mcp install --client claude-code      # or cursor, codex
```

Then ask your agent, for example: "How did last night's runs go?" It uses the same operations as the
CLI. Agents only read and add; moving, deleting and setup stay with you (`beamtime mv`, `rm`, `gc`).
The prompts `/beamtime:proposal`, `/beamtime:verdict` and `/beamtime:memory` walk an agent through
the research loop.
