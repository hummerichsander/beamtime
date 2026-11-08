# Proposals

A proposal says what an experiment is for and what would count as an answer, before the runs exist.
Runs record the proposal version that was current when they started; a version is evaluated only
against the runs that recorded it.

## Write one before launching

```yaml
statement: Warmup removes the loss spike above lr 1e-4.
rationale: Spikes appear at step 120 in the baseline runs [[20261020-110000-ab12]].
confidence: 0.7
plan: {grid: {config.lr: [1e-4, 3e-4, 1e-3], config.seed: [0, 1, 2]}}
predictions:
  - name: no-spike
    reduce: {metric: train/loss, stat: max, steps: [100, 200]}
    seeds: config.seed
    op: "<"
    value: 2.0
```

`beamtime proposal set <group> --file p.yaml` (MCP `proposal_set`) saves a version. Fields:
`statement`, `rationale`, `confidence` (belief before any data), `plan`, `predictions`,
`significance` (default 0.95, or `none`), `supersedes`. See `guide predictions` for the predictions.

## Plans

A plan says when the experiment is complete, so a check is not final after two of fifteen runs.

- `plan: {runs: 15}`: complete when 15 runs of this version have ended.
- `plan: {grid: {config.lr: [...], config.seed: [...]}}`: every grid point has an ended run.
- `plan: children`: the plans of all subgroups are complete (a group of sweeps).
- No plan: a `decision` note with `completes: [<group>]` declares it. Use for exploration.

Until the plan is complete, every result is provisional and the check shows the progress.

## Versions

- Before any run records a version, saving again replaces it freely.
- After that it is frozen. A new version must say what it replaces and why:
  `proposal_set` with `reason`, e.g. "train/loss is logged as train/loss_step". The old version stays
  and is still evaluated against its runs.
- Runs started after the new version record the new one; do not edit a frozen file.

## Habits

- Predict what you would be surprised by, with a number. A prediction that every outcome satisfies
  is not one.
- Name predictions in kebab-case; notes and views link them as `[[group#name]]`.
- A run started without a proposal gets a blank one; the group's proposal still applies to it
  through membership.
