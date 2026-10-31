# Proposals and verdicts

Write down what you expect before you run, let Beamtime check it against the numbers, and record
what you concluded. Your agent can do every step for you; this page shows them by hand.

## 1. Say what you expect

The quickest way is a sentence in your script:

```python
run = beamtime.init(dir="scaling/lr-sweep", config={"lr": lr},
                    proposal="lr 3e-4 gives the best final val/acc.")
```

For a proposal Beamtime can check, write it as a file:

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

- **`plan`** lists the runs you intend; the group shows how many are done.
- **`predictions`** are what Beamtime checks. `compare` tests one setting against another; `each`
  tests every run or setting on its own. `margin` is how much better counts as better.

Once a run has recorded a proposal, that version is frozen. Changing it later makes a new version;
the old runs keep pointing at theirs.

## 2. Check

```sh
beamtime check scaling/lr-sweep
```

For each prediction: the measured values, the difference with a confidence interval over seeds, and
whether it holds. Until the plan is complete the result is marked provisional.

## 3. Conclude

```sh
beamtime note add scaling/lr-sweep --type verdict --proposal <version> \
    --verdict best-beats-high=confirmed --overall confirmed \
    --description "lr 3e-4 wins by about a point"
```

The group is now *concluded*. `beamtime groups .` lists every group with its status, check and
verdict.

## Notes

Besides verdicts there are four kinds of notes: `observation`, `question`, `idea` and `decision`.
In the browser, click **+** in the Notes panel; on the command line:

```sh
beamtime note add scaling/lr-sweep --type observation --description "lr 1e-2 diverges early"
```

A note can answer a question (`--resolves <id>`), correct an earlier note (`--supersedes <id>`), or
close a group without a proposal (`--completes <group>`).

## Memory

A group's memory is a short summary for agents to read first: what was tried, what worked, what
is open. Agents keep it up to date (`/beamtime:memory`); you can edit it in the browser or with
`beamtime memory update <group> memory.md`.
