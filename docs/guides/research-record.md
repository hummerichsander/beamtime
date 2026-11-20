# Proposals and verdicts

## 1. Say what you expect

A sentence in your script:

```python
run = beamtime.init(dir="scaling/lr-sweep", config={"lr": lr},
                    proposal="lr 3e-4 gives the best final val/acc.")
```

Or a file Beamtime can check:

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
```

- **`plan`**: the runs you intend; the group shows how many are done.
- **`predictions`**: what Beamtime checks. `compare` tests one setting against another, `each` tests
  every run or setting alone; `margin` is how much better counts as better.

A proposal version freezes once a run records it; a change makes a new version, and old runs keep
theirs.

## 2. Check

```sh
beamtime check scaling/lr-sweep
```

Per prediction: the measured values, the difference with a confidence interval over seeds, and
whether it holds. It is provisional until the plan is complete.

## 3. Conclude

```sh
beamtime note add scaling/lr-sweep --type verdict --proposal <version> \
    --verdict best-beats-high=confirmed --overall confirmed \
    --description "lr 3e-4 wins by about a point"
```

The group is now *concluded*. `beamtime groups .` lists every group with status, check and verdict.

## Notes

Other note types are `observation`, `question`, `idea` and `decision`. Click **+** in the Notes
panel, or:

```sh
beamtime note add scaling/lr-sweep --type observation --description "lr 1e-2 diverges early"
```

`--resolves <id>` answers a question, `--supersedes <id>` corrects a note, `--completes <group>`
closes a group without a proposal.

## Memory

A group's memory is the summary agents read first: what was tried, worked, is open. Agents keep it
current (`/beamtime:memory`); edit it in the browser or with `beamtime memory update <group> memory.md`.
