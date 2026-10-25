# Layer 1: Storage format

Status: **draft, under discussion**

The storage format is the contract every other layer builds on. The SDK writes it, the index reads
it, remotes serve it (layer 4), and agents `cat` and `grep` it directly. It has to work on a laptop, a
workstation and a cluster filesystem (Lustre, GPFS, NFS) without a server or database.

## Scope

Beamtime **records** experiments; it never **runs** them. It does not launch jobs, schedule sweeps,
pick hyperparameters or talk to job schedulers. Beamtime only reads what the environment exposes
(host, git, scheduler variables if any) and stores what the run logs.

## Principles

1. **Beamtime adapts to the user's folders, not the other way round.** Runs live wherever the user
   puts them. Folders are the only hierarchy.
2. **Files are the source of truth.** Everything else (SQLite index, web UI, MCP answers) is derived
   and can be rebuilt with `beamtime reindex`.
3. **Every file has exactly one writer.** No two processes or machines ever modify the same file.
   State that several parties change is stored as new, immutable files, and the latest one wins.
   This makes concurrent jobs safe without locks, and lets agents on the cluster and writes sent
   from the laptop (layer 4) create files side by side without conflicts.
4. **Append or replace, never edit in place.** Streams are append-only JSONL. Whole-file state is
   written to a temp file and renamed, so readers never see a half-written file.
5. **Machine-written files start with `_`; authored files don't.** Everything Beamtime writes is
   prefixed (`_run.json`, `_metrics.jsonl`) and must not be edited by hand. Everything people and
   agents write (`proposal.yaml`, `notes/`, `view/`) has no prefix. This matches the reserved
   `_step` and `_t` keys inside the files.
6. **Machine-written files are JSON, authored files are YAML or Markdown.** Config values come from
   Python dicts and must round-trip exactly. Proposals and views are structured and written as YAML;
   notes are text and written as Markdown with YAML frontmatter.

## Root and log dirs

The **root** is the user's repository, like with TensorBoard. Beamtime adds one folder and one
optional file to it:

```
my-repo/
  beamtime.yaml        # optional: project settings (log dirs, remotes, packages, theme)
  src/ …
  beamtime/            # default log dir, gitignored
```

```yaml
# beamtime.yaml
logdirs: [beamtime]                      # scanned recursively for runs, default [beamtime]
remotes:                                 # layer 4
  cluster:
    host: cluster                        # ssh host alias
    path: /scratch/{user}/my-repo/beamtime
```

- The root is the nearest directory with `beamtime.yaml`, else the git root, else the working
  directory.

### Settings

Settings work like VS Code's: user settings are the default for every project, and a project's
`beamtime.yaml` overrides them.

| Level | File | Typical contents |
|---|---|---|
| built-in | – | Beamtime's defaults |
| user | `~/.config/beamtime/settings.yaml` | remotes you use everywhere (host, command, cache), personal packages, theme |
| project | `beamtime.yaml` in the root | log dirs, the project's remote paths, project packages, the project's default theme |
| session | command-line flags and environment variables | one-off overrides |

- Each level overrides the one above it. Mappings merge key by key, so a user-level remote can
  define `host`, `command` and `cache` once, and each project adds only its `path`:

  ```yaml
  # ~/.config/beamtime/settings.yaml
  remotes:
    cluster: {host: cluster, command: ~/venvs/bt/bin/beamtime, cache: /local/scratch/{user}/bt}
  ```
  ```yaml
  # beamtime.yaml
  remotes:
    cluster: {path: /scratch/{user}/proj/beamtime}
  ```

- Package lists combine both levels; a project entry replaces a user entry for the same package.
- Both files have the same schema. A few keys only make sense in one of them, e.g. `logdirs` in the
  project; a key in the wrong file is reported.
- `beamtime settings` shows the effective settings and, for each value, which level it came from.
- The theme a viewer picks in the UI is stored in their browser and wins over both files for that
  viewer.
- `BEAMTIME_LOGDIR` overrides where new runs go, e.g. scratch space on a cluster.
- The index cache lives outside the repo in `~/.cache/beamtime/<root-hash>/`, so nothing
  machine-specific ends up in the repo and SQLite never touches a cluster filesystem.

## Folders

Below a log dir, the user organizes runs in ordinary folders. A folder that contains a `_run.json`
is a **run**; every other folder is a **group**. Directions, sweeps and ablations are all just
groups:

```
beamtime/
  scaling/                          # group: a research direction
    proposal.yaml
    view/                           # shown here and inherited by everything below
    notes/
    lr-sweep/                       # group: a sweep
      proposal.yaml
      view/                         # overrides the inherited one for this sweep
      20261024-101532-k3m9xq2a/     # run
      20261024-101533-p2x8fq1c/     # run
  tokenizer/
    bpe-vs-unigram/ …
```

Every folder, run or group, can carry the same three kinds of authored files:

| File | Meaning |
|---|---|
| `proposal.yaml` | What is expected for the runs in this folder, and why. |
| `notes/<ts>-<rand>.md` | Comments, decisions, dead ends, and verdicts on the proposal. |
| `view/<ts>-<rand>.yaml` | The folder's view; the newest version is shown. |

This covers what other tools model as separate concepts:

- **Projects** are top-level groups.
- **Sweeps** are groups whose runs come from one launch. There is no sweep file; scheduler job
  information is recorded per run.
- **The journal** is the notes on a group, or on the log dir itself for project-wide entries.
- **Reports and dashboards** are views, one per folder (see [Views](#views)).
- **Reusable view blocks** live in `blocks/` folders, inherited down the tree like views (layer 5).
  `notes/`, `view/` and `blocks/` are reserved folder names and never count as groups.
- **Derived data** is any data file stored with the view that uses it.

The **timeline** is not stored. The index builds it from run events and notes across all folders.

## Views

Agents build views from Beamtime's building blocks (layer 5). Every folder shows exactly one:

1. its own view, if it has one;
2. otherwise the view of the nearest ancestor group that has one;
3. otherwise Beamtime's built-in default: proposal with check, run table, main metric curves, and
   every logged table, image and text, so nothing a run logs is ever invisible.

A view is **rendered for the folder being viewed**, not for the folder that defines it. Queries are
relative to the viewed folder: `from: .` means all runs below it. One view in `scaling/` therefore
shows all scaling runs when viewing `scaling/`, only the sweep's runs when viewing
`scaling/lr-sweep/`, and a single run when viewing a run. A subgroup or run that needs something
different defines its own view, which in turn is inherited further down.

### Structure

A view has a fixed frame and a free body:

- **Frame**, owned by Beamtime and identical on every view: folder, proposal with its check, current
  verdict, run status. An agent cannot break it, and every view starts the same way.
- **Body**, built freely by the agent from two kinds of blocks, mixed as needed:
  1. **Widgets**: declarative layout (row, grid, tabs, section) and content (charts, tables,
     images, stats, notes).
  2. **Custom blocks**: the agent's own code (an ES module), sandboxed in an iframe without network
     access, built on Beamtime's `bt` kit with Preact, Vega-Lite and other bundled libraries.

All data comes through declared queries, and one theme keeps the visual language common: colors,
fonts, and the same color for the same run everywhere. The details are designed in layer 5.

### Versions

Each save of a view is a new file in `view/`, and the newest one is shown. This keeps the one-writer
rule when agents on the laptop and on the cluster both revise it, and keeps the history of how a
report evolved. `beamtime view edit` hides the versioning from agents.

### Data

Building blocks get their data in one of two ways:

1. **Queries on run data**, the normal case. A widget names what it wants
   (`{from: ., y: val/loss, color: config.lr}`) and contains no values. The index answers from
   `_metrics.jsonl`, `_data.jsonl`, `_run_card.json` and `_config.json` and downsamples long
   curves. Queries follow the viewed folder, so they stay correct when a view is inherited, and
   update while runs go on. Derived values that can be computed from the query result (aggregates,
   regression fits, smoothing, densities) are computed in the chart with Vega-Lite transforms, so
   they follow the viewed folder too. This is the preferred way to show analysis.
2. **Data files**, for analysis that transforms cannot express (e.g. a fit done in SciPy). They are
   tables like the ones runs log, so building blocks treat both alike. The agent saves them with the
   view into `view/data/<sha8>-<name>.parquet` (or `.csv`, `.json`). They are named by content hash,
   so they are immutable and an older view version keeps showing the data it was built with. A data
   file describes the folder that defines the view, not the viewed folder: when the view is
   inherited, building blocks using it carry a label such as "data from `scaling/`".

Custom block code is stored the same way, as `view/code/<sha8>-<name>.js`. Provenance of a
data file (the script or notebook that made it) is recorded in a note.

## Runs

### Identity

- **Run id:** `20261024-101532-k3m9xq2a`, i.e. UTC start time plus 8 random base32 characters
  (40 bits). It sorts chronologically and is unique without coordination: 1000 jobs starting in the
  same second have a collision chance of about 5e-7. The directory is created with an exclusive
  `mkdir`, and a collision simply retries.
- **Run name:** a human-readable label (`lr-3e-4-warmup`). Optional; if missing, one is generated
  from high-energy physics vocabulary as adjective, particle and number: `boosted-kaon-42`,
  `prompt-photon-7`, `displaced-muon-13`. The name lives in `_run.json` and can change; the id
  never does.
- The run directory is named by its id and created inside the folder passed to
  `beamtime.init(dir=...)`. Runs can be moved between folders freely; the id travels with them.

### Directory

```
20261024-101532-k3m9xq2a/
  _run.json                 # identity, environment, status          [run, replaced]
  _config.json              # hyperparameters                        [run, replaced]
  _run_card.json            # compact summary for agents and tables  [run, replaced]
  _preview.json             # downsampled curves of every metric     [run, replaced]
  _heartbeat                # last-alive timestamp                   [run, replaced]
  _metrics.jsonl            # scalar stream                          [run, append]
  _data.jsonl               # tables, images, text                   [run, append]
  _data/<key>/<step>.<ext>  # files for large tables and images      [run, create]
  _events.jsonl             # lifecycle events for the timeline      [run, append]
  _output.log               # captured stdout/stderr                 [run, append]
  _output.rank<N>.log       # output of other ranks (layer 2)        [rank N, append]
  _artifacts.jsonl          # files produced, by copy or reference   [run, append]
  _env/                     # git.diff, packages.txt                 [run, create]
  proposal.yaml             # what we expect and why                 [authored, frozen]
  notes/                    # comments and verdicts                  [authored, create]
  view/                     # overrides the inherited view           [authored, create]
```

- **Run-owned** files (prefixed) are written only by the training process and stop changing once it
  ends.
- **Authored** files are written by humans or agents, from any machine. Notes and views are new
  files with unique names, so files written on the laptop and on the cluster never conflict. A
  run's `proposal.yaml` is written at `init` and frozen at the first logged metric.
- Directories written by other tools (e.g. Lightning's `checkpoints/`) keep their own names.

### `_run.json`

```json
{
  "schema": 1,
  "id": "20261024-101532-k3m9xq2a",
  "name": "boosted-kaon-42",
  "tags": ["resnet18", "cifar10"],
  "status": "running",
  "created_at": "2026-10-24T10:15:32.104Z",
  "ended_at": null,
  "exit": null,
  "attempts": [
    {"started_at": "2026-10-24T10:15:32Z", "host": "gpu042", "scheduler_job_id": "8812345"}
  ],
  "proposal_frozen_at": "2026-10-24T10:15:41Z",
  "proposal_sha256": "9f2c…",
  "host": {"hostname": "gpu042", "user": "ada", "os": "Linux", "python": "3.11.9"},
  "scheduler": {"kind": "slurm", "job_id": "8812345", "array_job_id": "8812300",
                "array_task_id": "45", "partition": "gpu", "nodes": "gpu042"},
  "git": {"commit": "57878f1", "branch": "master", "dirty": true, "remote": "…"},
  "command": ["python", "train.py", "--lr", "3e-4"],
  "cwd": "/home/ada/proj",
  "beamtime_version": "0.1.0"
}
```

`scheduler` is absent when no job scheduler is detected. Its `kind` names the scheduler (`slurm`,
`pbs`, `lsf`, `kubernetes`, …); the other fields are whatever that scheduler exposes, mapped to
common names where they exist (`job_id`, `nodes`, `partition`). Detection is part of the SDK
(layer 2).

**Status** is one of `running`, `finished`, `failed` (exception), `killed` (signal: Ctrl-C,
scheduler timeout, preemption). An extra value is derived when reading, never written: a `running`
run whose heartbeat is older than a threshold (default 5 min) is shown as `lost`.

**Attempts** support continuing a run (layer 2): a resumed run keeps its id, adds an attempt, and
keeps appending to the same streams.

### `_config.json`

Plain JSON of the hyperparameters, nested as given. It can be extended while the run is going
(e.g. parameter count known after model build), but keys are never removed.

### `_metrics.jsonl`

One JSON object per `log()` call:

```json
{"_step": 120, "_t": 1761300941.21, "train/loss": 2.31, "lr": 0.0003}
{"_step": 121, "_t": 1761300941.48, "train/loss": 2.29}
```

- `_step` (int, monotonic per attempt) and `_t` (unix time) are reserved; user keys must not start
  with `_`. Other x-axes (`epoch`, `tokens`) are just logged as keys.
- Keys are sparse: each line holds only what was logged.
- `/` in keys forms groups (`train/loss`, `val/acc`).
- `NaN` and `Infinity` are written as Python's JSON literals; diverging runs must be recordable.
- Each line is written with a single `write()` and flushed periodically. A reader ignores a trailing
  line without newline (the writer is mid-write or was killed).

Size check: 100k steps × 30 keys is about 50 MB of JSONL. That is fine to append, transfer and parse
incrementally; the index reads from the last byte offset it has seen.

### `_data.jsonl` and `_data/`

**Runs record data; views present it.** A run logs four kinds of data: scalars (in
`_metrics.jsonl`) and the three non-scalar kinds below, each indexed by one line in `_data.jsonl`.
Nothing a run logs is a chart; charts are built only in views (layer 5).

| Kind | Stored as | Typical use |
|---|---|---|
| `table` | inline `columns` up to 1000 cells, else `_data/<key>/<step>.parquet` | per-class metrics, predictions, distributions |
| `image` | `_data/<key>/<step>.png` | generated samples, attention maps, plots only the run can draw |
| `text` | inline up to 4 KB, else `_data/<key>/<step>.txt` | generated text, prompts |

```json
{"_step": 500, "_t": 1761301022.0, "key": "samples", "kind": "image", "path": "_data/samples/500.png"}
{"_step": 500, "_t": 1761301022.0, "key": "val/per_class", "kind": "table", "path": "_data/val__per_class/500.parquet"}
{"_step": 500, "_t": 1761301022.0, "key": "grads/layer3", "kind": "table", "columns": {"bin_start": [...], "bin_end": [...], "count": [...]}}
```

A histogram is a table with `bin_start`, `bin_end` and `count`, so a series of histograms over
steps is just a table logged at many steps. `/` in keys becomes `__` in file paths.

### `_events.jsonl`

Lifecycle events that feed the timeline: `created`, `proposal_frozen`, `attempt_started`,
`finished`, `failed`, `killed`, plus anything the user logs with `run.event("lr decayed")`.

### `_output.log`

stdout and stderr as the process wrote them. Always captured, with no switch to turn it off: agents
need it most when a run failed, and that is exactly the run nobody thought to configure.

The only limit is size, so a runaway print loop cannot fill a disk quota. Beyond a cap (default
10 MB) the head is kept and the tail rotates, so both the start and the moment of death survive.
The exact rotation scheme belongs to the SDK design (layer 2).

### `_run_card.json`

The run card is the first thing an agent reads about a run, and what run tables are built from. It
condenses the run into one small file (under about 10 KB), written periodically while the run goes
on and at its end.

```json
{
  "status": "finished",
  "duration_s": 15320,
  "steps": 50000,
  "steps_per_s": 3.26,
  "error": null,
  "metrics": {
    "val/acc": {
      "first": 0.10, "last": 0.929, "ema_last": 0.927,
      "min": 0.10, "min_step": 0, "max": 0.931, "max_step": 47000,
      "mean": 0.84, "count": 500, "last_step": 50000,
      "nonfinite": 0, "slope_last10pct": 0.0001
    }
  },
  "values": {"test/acc": 0.931}
}
```

| Field | Meaning |
|---|---|
| `duration_s`, `steps`, `steps_per_s` | How long the run went and how fast. |
| `error` | Last exception line of a failed run, so the cause is visible without opening the log. |
| `metrics.<key>.first`, `last`, `min`, `max`, `mean`, `count` | The basic shape of every scalar. |
| `min_step`, `max_step`, `last_step` | Where the extremes happened and how far the metric got. |
| `ema_last` | Exponentially smoothed last value; the raw last value of a noisy metric is misleading. |
| `nonfinite` | Count of NaN and Inf values: divergence at a glance. |
| `slope_last10pct` | Slope over the last 10% of steps: is the metric still moving? |
| `values` | Values set explicitly (`run.card["test/acc"] = 0.931`), e.g. final test results. |

Proposal checks and verdicts are not part of the card, since the run doesn't know them. CLI and MCP
add them when they show a card (layer 3).

### `_preview.json`

A downsampled copy of every metric's curve, written by the run itself next to the run card. With
the card and the preview, run tables and overview charts need no index, which matters most on
remotes, where the index lives in memory (layer 4).

```json
{
  "bucket_width": 64,
  "metrics": {
    "train/loss": {
      "first_bucket": 0,
      "min": [2.31, 1.92, ...], "max": [2.48, 2.05, ...], "last": [2.29, 1.95, ...],
      "mean": [2.37, 1.99, ...], "count": [64, 64, ...]
    }
  }
}
```

- Bucket `i` covers steps `[i * bucket_width, (i + 1) * bucket_width)`. The width is a power of two
  and doubles, merging neighbouring buckets, whenever a metric would exceed 512 buckets, so every
  metric has between 256 and 512 buckets once it is long enough. Edges stay fixed between rewrites,
  so live curves don't jitter.
- Min and max per bucket keep spikes visible; mean and count allow exact means over whole buckets.
- Empty buckets of sparse metrics are `null`.
- The size is a few hundred KB at most (20 metrics × 512 buckets × 5 values). It is rewritten with
  the run card, every 60 s and at the end.

### `_artifacts.jsonl`

```json
{"name": "best.ckpt", "path": "artifacts/best.ckpt", "size": 47185920, "kind": "checkpoint"}
{"name": "final.ckpt", "uri": "/scratch/me/ckpts/run42/final.ckpt", "size": 1.2e10, "kind": "checkpoint"}
```

Small files are copied into `artifacts/`. Large ones are stored by reference (`uri`) and never
copied or pulled; the reference records where they live. Checkpoints written by Lightning land in
`checkpoints/` inside the run directory (layer 2); they are listed by reference too and excluded
from pulls.

## Proposals

A proposal states what a folder's runs are expected to show, and why. It can sit on a run or on a
group; on a group it covers all runs below it.

```yaml
statement: Warmup over 500 steps removes the loss spike at lr=3e-4.
rationale: The spike at step 120 matches the Adam second-moment estimate still warming up.
predictions:
  - name: no-spike
    reduce: {metric: train/loss, stat: max, steps: [100, 300]}
    op: "<"
    value: 2.5
  - name: beats-baseline
    reduce: {metric: val/acc, stat: max}
    op: ">"
    ref: {run: 20261020-091204-a7c2kd9e}
    margin: 0.005
```

A blank proposal is `statement: ""` with no predictions. Every run has one; groups have one only if
someone writes it.

### Freezing

A proposal can be edited until data exists that it makes claims about. Then it is frozen, and its
predictions with it, so they cannot be adjusted after seeing results.

- **Run:** frozen when the run logs its first metric. The SDK records time and SHA-256 in
  `_run.json`.
- **Group:** frozen when the next run below it starts. That run's SDK creates `_frozen.json` next to
  the proposal (exclusive create, so concurrent jobs don't clash) with time and SHA-256.

A group proposal written after some of its runs already exist is only checked against runs that
started after the freeze. Claims about data that was already visible are not predictions.

Any later edit shows up as a hash mismatch.

### Predictions

Every prediction is evaluated in the same four steps:

1. **Select** the runs it is about: all runs below the folder that started after the freeze,
   optionally narrowed by `select` (status, tags, config values). On a run, this is the run itself.
2. **Reduce** each run to one number: `reduce: {metric, stat, steps}` takes the metric's series,
   restricts it to the optional `steps: [start, end]` window, and reduces it with `stat` (`last`,
   `min`, `max`, `mean`).
3. **Merge seeds** (groups only, optional): with `seeds: config.seed`, runs whose configs are
   identical except for that key are merged into one point, the mean of their numbers. One lucky
   seed then cannot confirm a claim.
4. **Test** the resulting points with one of four tests:

| `test` | Claim | Fields |
|---|---|---|
| `each` (default) | every point satisfies the comparison | `op` (`<`, `<=`, `>`, `>=`), and `value` or `ref` + optional `margin` |
| `trend` | the points rise or fall when ordered by a config key | `over: config.<key>`, `direction: increasing \| decreasing`, optional `tolerance` (allowed violation between neighbours) |
| `best` | the best point has a given config | `best: max \| min`, `where: {config.<key>: value}` |
| `compare` | subset `a` beats subset `b` | `a` and `b` (config filters), `op`, optional `margin`; compares the means of the two subsets |

`ref: {run: <id>}` compares against another run's number, reduced the same way. On a run, only
`each` makes sense, so `test` is omitted.

A group example with the full pipeline:

```yaml
statement: Warmup improves peak validation accuracy across model sizes.
predictions:
  - name: warmup-helps
    select: {status: finished}
    reduce: {metric: val/acc, stat: max}
    seeds: config.seed
    test: compare
    a: {config.warmup: 500}
    b: {config.warmup: 0}
    op: ">"
    margin: 0.005
  - name: bigger-is-better
    reduce: {metric: val/loss, stat: last}
    seeds: config.seed
    test: trend
    over: config.n_params
    direction: decreasing
    tolerance: 0.01
```

### Evaluation

Each prediction evaluates to `pass`, `fail` or `pending`:

- `pending` while any selected run is still going, a metric is not logged yet, or a `ref` run is
  missing.
- Selected runs that `failed`, were `killed` or are `lost` are left out of the test and reported
  next to the result, so a claim cannot pass silently by losing its counterexamples.
- The combined **check** of a proposal is `pass` if all predictions pass, `fail` if any fails, and
  `pending` otherwise.

The check is computed by the index and never stored, because it follows deterministically from the
frozen proposal and the data. It is a proposal of its own: the verdict of record is a note with a
verdict, written by a human or agent, which may disagree with the check and say why.

## Notes

Notes are the running record of a folder: comments, decisions, dead ends, and verdicts. They follow
the format of Claude Code's memory files: Markdown with a YAML frontmatter, one note per file.

```markdown
---
description: Warmup removes the loss spike; val/acc peaks at 0.931.
type: verdict
verdict: confirmed
evidence:
  - {metric: val/acc, stat: max, value: 0.931}
author: claude-opus-5-5
user: ada
---

No spike in any of the 5 seeds. The baseline [[20261020-091204-a7c2kd9e]] spikes at step 120 in
every seed. Next: check whether 200 warmup steps suffice, see [[scaling/warmup-length]].
```

| Field | Meaning |
|---|---|
| `description` | One line, required. Shown in the timeline and listings, and what agents read to decide whether the body is worth loading. |
| `type` | `observation`, `decision`, `idea` or `verdict`. |
| `verdict` | Only for `type: verdict`: `confirmed`, `refuted` or `inconclusive`. |
| `evidence` | Optional, for verdicts: the numbers the verdict rests on. |
| `author` | Who wrote it: a person or a model id. |
| `user` | The account it was written for: the local user in v1, the authenticated user on a server (layer 6). Views and library blocks carry `author` and `user` as well. |

- The body is optional and short. Most notes are a description plus a few lines.
- `[[...]]` links to a run id, a folder path below the log dir, or another note's file name. The
  index resolves links, so the UI can show backlinks.
- The newest `verdict` note is the folder's current verdict on its proposal; older ones remain as
  history.
- Unlike memory files, notes are never edited or deleted. A correction is a new note, which keeps
  the one-writer rule and the history.

## Write protocol

| Kind | How | Durability |
|---|---|---|
| Replaced (`_run.json`, `_run_card.json`, …) | write `._<name>.tmp`, then `os.replace` | `fsync` on run end |
| Appended (`_*.jsonl`, `_output.log`) | one `write()` per line, buffered flush every few seconds | `fsync` on run end |
| Created (data files, notes, views, freeze records) | write to temp name, then rename | none needed |
| Heartbeat | replaced every 30 s | none |

## Versioning

Every `_run.json` carries `schema`. Readers accept all known versions; `beamtime migrate` rewrites
old runs. Unknown fields are kept, never dropped.

## Decisions

- The root is the user's repo; runs live in user-chosen folders under log dirs, found by
  `_run.json`.
- Folders are the only hierarchy. Projects, sweeps and the journal are groups and their notes.
- Machine-written files start with `_`; authored files (`proposal.yaml`, `notes/`, `view/`) don't.
- Beamtime is not tied to a job scheduler; scheduler details are one optional `scheduler` field.
- Every folder can carry a proposal, notes and a view. Notes are Markdown with frontmatter, like
  Claude Code memory files; a note of type `verdict` is a result.
- Views are inherited by subgroups and runs and rendered relative to the viewed folder; any folder
  can override. Each save is a new version. A fixed frame is owned by Beamtime; the body is free,
  built from declarative widgets and sandboxed custom code blocks.
- View data comes from relative queries plus Vega-Lite transforms; data files are the exception,
  immutable and tied to the defining folder.
- Proposals carry machine-checkable predictions, evaluated as select, reduce, merge seeds, test. The
  index computes a check; the verdict of record is a note with a verdict.
- The run card (`_run_card.json`) is a compact summary of each run for agents and run tables.
- The preview (`_preview.json`) holds 256–512 min/max/last/mean buckets per metric, written by the
  run, so overview charts need no index.
- Generated run names use high-energy physics vocabulary (`boosted-kaon-42`).
- `_output.log` is always captured; there is no switch to turn it off.
- Runs record data, views present it. Runs log scalars, tables, images and text; histograms are
  tables, and charts exist only in views.
- Beamtime records experiments and never runs them.

## To revisit

- **Proposals, predictions and notes** get a thorough design pass of their own later. The sections
  above fix where these files live, how they freeze and how predictions are evaluated; field names
  are provisional.
- **Agent instructions for views** (design rules, preferred libraries, the validate-and-screenshot
  loop) are designed with layer 5.
