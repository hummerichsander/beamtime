# Layer 1: Storage format

Status: **draft, under discussion**

The storage format is the contract every other layer builds on. The SDK writes it, the index reads
it, sync copies it, and agents `cat` and `grep` it directly. It has to work on a laptop and on a
cluster filesystem (Lustre, GPFS, NFS) without a server or database.

## Scope

Beamtime **records** experiments; it never **runs** them. It does not launch jobs, schedule sweeps,
pick hyperparameters or talk to SLURM. Launching stays with SLURM, scripts or the agent. Beamtime
only reads what the environment exposes (e.g. SLURM variables) and stores what the run logs.

## Principles

1. **Beamtime adapts to the user's folders, not the other way round.** Runs live wherever the user
   puts them. Folders are the only hierarchy.
2. **Files are the source of truth.** Everything else (SQLite index, web UI, MCP answers) is derived
   and can be rebuilt with `beamtime reindex`.
3. **Every file has exactly one writer.** No two processes or machines ever modify the same file.
   State that several parties change is stored as new, immutable files, and the latest one wins.
   This makes concurrent HPC jobs safe without locks and turns sync into a plain union of files.
4. **Append or replace, never edit in place.** Streams are append-only JSONL. Whole-file state is
   written to a temp file and renamed, so readers never see a half-written file.
5. **Machine-written files are JSON, human- or agent-authored files are YAML.** Config values come
   from Python dicts and must round-trip exactly; hypotheses, results and notes are written by
   people and agents and should be pleasant to read and edit.

## Root and log dirs

The **root** is the user's repository, like with TensorBoard. Beamtime adds one folder and one
optional file to it:

```
my-repo/
  beamtime.yaml        # optional: log dirs and remotes, committed with the code
  src/ …
  beamtime/            # default log dir, gitignored
```

```yaml
# beamtime.yaml
logdirs: [beamtime]                      # scanned recursively for runs, default [beamtime]
remotes:                                 # layer 4
  hpc: user@login.cluster.de:/scratch/me/my-repo/beamtime
```

- The root is the nearest directory with `beamtime.yaml`, else the git root, else the working
  directory.
- `BEAMTIME_LOGDIR` overrides where new runs go, typically scratch on a cluster.
- The index cache lives outside the repo in `~/.cache/beamtime/<root-hash>/`, so nothing
  machine-specific ends up in the repo and SQLite never touches a cluster filesystem.

## Folders

Below a log dir, the user organizes runs in ordinary folders. A folder that contains a `run.json`
is a **run**; every other folder is a **group**. Directions, sweeps and ablations are all just
groups:

```
beamtime/
  scaling/                          # group: a research direction
    hypothesis.yaml
    notes/
    lr-sweep/                       # group: a sweep
      hypothesis.yaml
      report.page.yaml              # a page about this sweep
      lr_fit.parquet                # data the page uses
      20261024-101532-k3m9xq2a/     # run
      20261024-101533-p2x8fq1c/     # run
  tokenizer/
    bpe-vs-unigram/ …
```

Every folder, run or group, can carry the same three kinds of annotations:

| File | Meaning |
|---|---|
| `hypothesis.yaml` | What is expected for the runs in this folder, and why. |
| `results/<ts>-<rand>.yaml` | Verdicts on the hypothesis; the newest is current. |
| `notes/<ts>-<rand>.yaml` | Free comments, decisions, dead ends. |

This replaces the earlier separate concepts:

- **Projects** are top-level groups.
- **Sweeps** are groups whose runs come from one launch. There is no `sweep.yaml`; the SLURM array
  id is recorded per run.
- **The journal** is the notes on a group, or on the log dir itself for project-wide entries.
- **Pages** are `*.page.yaml` files in the folder they report on (layer 5).
- **Derived data** is any data file next to the page that uses it; a page refers to it by relative
  path. Provenance is written in a note or the page itself, not in a separate format.

The **timeline** is not stored. The index builds it from run events, results and notes across all
folders.

## Runs

### Identity

- **Run id:** `20261024-101532-k3m9xq2a`, i.e. UTC start time plus 8 random base32 characters
  (40 bits). It sorts chronologically and is unique without coordination: 1000 array tasks starting
  in the same second have a collision chance of about 5e-7. The directory is created with an
  exclusive `mkdir`, and a collision simply retries.
- **Run name:** a human-readable label (`lr-3e-4-warmup`). Optional; if missing, one is generated
  (`quiet-boson-7`). The name lives in `run.json` and can change; the id never does.
- The run directory is named by its id and created inside the folder passed to
  `beamtime.init(dir=...)`. Runs can be moved between folders freely; the id travels with them.

### Directory

```
20261024-101532-k3m9xq2a/
  run.json                  # identity, environment, status          [run, replaced]
  config.json               # hyperparameters                        [run, replaced]
  hypothesis.yaml           # what we expect and why                 [run, frozen]
  heartbeat                 # last-alive timestamp                   [run, replaced]
  metrics.jsonl             # scalar stream                          [run, append]
  media.jsonl               # index of non-scalar values             [run, append]
  media/<key>/<step>.<ext>  # images, tables, figures                [run, create]
  events.jsonl              # lifecycle events for the timeline      [run, append]
  output.log                # captured stdout/stderr                 [run, append]
  summary.json              # final and user-set summary values      [run, replaced]
  artifacts.jsonl           # files produced, by copy or reference   [run, append]
  env/                      # git.diff, requirements.txt             [run, create]
  results/                  # verdicts                               [annotation, create]
  notes/                    # comments                               [annotation, create]
```

- **Run-owned** files are written only by the training process and stop changing once it ends.
- **Annotation** files are written afterwards by humans or agents, from any machine. Each is a new
  file with a unique name, so annotations written on the laptop and on the cluster never conflict.

### `run.json`

```json
{
  "schema": 1,
  "id": "20261024-101532-k3m9xq2a",
  "name": "lr-3e-4-warmup",
  "tags": ["resnet18", "cifar10"],
  "status": "running",
  "created_at": "2026-10-24T10:15:32.104Z",
  "ended_at": null,
  "exit": null,
  "attempts": [
    {"started_at": "2026-10-24T10:15:32Z", "host": "gpu042", "slurm_job_id": "8812345"}
  ],
  "hypothesis_frozen_at": "2026-10-24T10:15:41Z",
  "hypothesis_sha256": "9f2c…",
  "host": {"hostname": "gpu042", "user": "ada", "os": "Linux", "python": "3.11.9"},
  "slurm": {"job_id": "8812345", "array_job_id": "8812300", "array_task_id": "45",
            "partition": "gpu", "nodelist": "gpu042", "gpus": "a100:1"},
  "git": {"commit": "57878f1", "branch": "master", "dirty": true, "remote": "…"},
  "command": ["python", "train.py", "--lr", "3e-4"],
  "cwd": "/home/ada/proj",
  "beamtime_version": "0.1.0"
}
```

**Status** is one of `running`, `finished`, `failed` (exception), `killed` (signal, e.g. SLURM
timeout or preemption). An extra value is derived when reading, never written: a `running` run whose
heartbeat is older than a threshold (default 5 min) is shown as `lost`.

**Attempts** support SLURM requeue and manual resume: a resumed run keeps its id, adds an attempt,
and keeps appending to the same streams.

### `config.json`

Plain JSON of the hyperparameters, nested as given. It can be extended while the run is going
(e.g. parameter count known after model build), but keys are never removed.

### `metrics.jsonl`

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

Size check: 100k steps × 30 keys is about 50 MB of JSONL. That is fine to append, sync and parse
incrementally; the index reads from the last byte offset it has seen.

### `media.jsonl` and `media/`

Non-scalar values are files, indexed by a JSONL line:

```json
{"_step": 500, "_t": 1761301022.0, "key": "samples", "type": "image", "path": "media/samples/500.png"}
{"_step": 500, "_t": 1761301022.0, "key": "val/conf", "type": "table", "path": "media/val__conf/500.parquet"}
{"_step": 500, "_t": 1761301022.0, "key": "grad_norm_hist", "type": "histogram", "bins": [...], "counts": [...]}
```

Types: `image`, `histogram` (inline, it is small), `table` (parquet), `figure` (Vega-Lite JSON or a
matplotlib-rendered PDF/PNG), `text`.

### `events.jsonl`

Lifecycle events that feed the timeline: `created`, `hypothesis_frozen`, `attempt_started`,
`finished`, `failed`, `killed`, plus anything the user logs with `run.event("lr decayed")`.

### `output.log`

stdout and stderr as the process wrote them. Always captured, with no switch to turn it off: agents
need it most when a run failed, and that is exactly the run nobody thought to configure.

The only limit is size, so a runaway print loop cannot fill a cluster quota. Beyond a cap (default
10 MB) the head is kept and the tail rotates, so both the start and the moment of death survive.
The exact rotation scheme belongs to the SDK design (layer 2).

### `summary.json`

Last, min and max of every scalar, plus values set explicitly (`run.summary["test/acc"] = 0.93`).
Written at the end of the run and periodically while it runs, so agents get the gist of a run from
one small file.

### `artifacts.jsonl`

```json
{"name": "best.ckpt", "path": "artifacts/best.ckpt", "size": 47185920, "kind": "checkpoint"}
{"name": "final.ckpt", "uri": "/scratch/me/ckpts/run42/final.ckpt", "size": 1.2e10, "kind": "checkpoint"}
```

Small files are copied into `artifacts/`. Large ones are stored by reference (`uri`) and never
copied or synced; the reference records where they live.

## Hypotheses

A hypothesis can sit on a run or on a group. On a group it covers all runs below it.

```yaml
statement: Warmup over 500 steps removes the loss spike at lr=3e-4.
rationale: The spike at step 120 matches the Adam second-moment estimate still warming up.
predictions:
  - name: no-spike
    metric: train/loss
    stat: max
    steps: [100, 300]
    op: "<"
    value: 2.5
  - name: beats-baseline
    metric: val/acc
    stat: max
    op: ">"
    ref: {run: 20261020-091204-a7c2kd9e}
    margin: 0.005
```

A blank hypothesis is `statement: ""` with no predictions. Every run has one; groups have one only
if someone writes it.

### Freezing

A hypothesis can be edited until data exists that it makes claims about. Then it is frozen, and
predictions are frozen with it, so they cannot be adjusted after seeing results.

- **Run:** frozen when the run logs its first metric. The SDK records time and SHA-256 in
  `run.json`.
- **Group:** frozen when the next run below it starts. That run's SDK creates
  `hypothesis.frozen.json` next to it (exclusive create, so concurrent array tasks don't clash)
  with time and SHA-256.

A group hypothesis written after some of its runs already exist is only checked against runs that
started after the freeze. Claims about data that was already visible are not predictions.

Any later edit shows up as a hash mismatch.

### Predictions

A prediction is a claim about one number that can be checked against the logged data.

| Field | Meaning |
|---|---|
| `name` | Optional label, shown in the UI and in results. |
| `metric` | Scalar key from `metrics.jsonl` or `summary.json`. |
| `stat` | How to reduce the series to one number: `last`, `min`, `max`, `mean`. |
| `steps` | Optional `[start, end]` window (inclusive) before reducing. |
| `op` | `<`, `<=`, `>`, `>=`. |
| `value` | Threshold to compare against… |
| `ref` + `margin` | …or another run's value of the same `metric` and `stat`, plus an optional margin. |

On a group, these forms apply to each run below it. Two more forms make claims across the runs:

```yaml
predictions:
  - name: monotonic
    metric: val/loss
    stat: last
    trend: decreasing            # increasing | decreasing, ordered by `over`
    over: config.n_params
    tolerance: 0.01              # optional: allowed violation between neighbours
  - name: warmup-wins
    metric: val/acc
    stat: max
    best: max                    # which direction is best
    where: {config.warmup: 500}  # the best run must match this config
```

Group predictions can average over seeds first, so that one lucky seed cannot confirm a
hypothesis. With `seeds: config.seed`, runs that differ only in that config key are merged into one
point by taking the mean of their reduced values, and the prediction is evaluated on those points.

Each prediction evaluates to `pass`, `fail` or `pending` (metric not logged yet, runs still going,
or reference run missing). The combined **check** is `pass` if all predictions pass, `fail` if any
fails once the runs have ended, and `pending` otherwise.

The check is computed by the index and never stored, because it follows deterministically from the
frozen hypothesis and the data. It is a proposal: the verdict of record is a result written by a
human or agent, which may disagree with the check and say why.

## Results and notes

```yaml
# results/20261024-142210-p8d2.yaml
verdict: confirmed            # confirmed | refuted | inconclusive
summary: No spike with warmup; val/acc peaks at 0.931.
evidence:
  - metric: val/acc
    stat: max
    value: 0.931
author: claude-opus-5-5
```

The newest result is the current verdict; older ones remain as history. Notes have the same shape
minus `verdict` and `evidence`.

## Write protocol

| Kind | How | Durability |
|---|---|---|
| Replaced (`run.json`, `summary.json`, …) | write `.<name>.tmp`, then `os.replace` | `fsync` on run end |
| Appended (`*.jsonl`, `output.log`) | one `write()` per line, buffered flush every few seconds | `fsync` on run end |
| Created (media, annotations, freeze records) | write to temp name, then rename | none needed |
| Heartbeat | replaced every 30 s | none |

## Versioning

Every `run.json` carries `schema`. Readers accept all known versions; `beamtime migrate` rewrites
old runs. Unknown fields are kept, never dropped.

## Decisions

- The root is the user's repo; runs live in user-chosen folders under log dirs, found by
  `run.json`.
- Folders are the only hierarchy. Projects, sweeps and journal are groups and their notes.
- Every folder can carry a hypothesis, results and notes.
- Hypotheses carry machine-checkable predictions; the index computes a check, the verdict of record
  stays a written result.
- `output.log` is always captured; there is no switch to turn it off.
- Media types: `image`, `histogram`, `table`, `figure`, `text`.
- Beamtime records experiments and never runs them.

- `trend` predictions take an optional `tolerance`; group predictions can average over seeds.

## To revisit

- **Hypotheses, predictions, results and notes** get a thorough design pass of their own later. The
  sections above fix where these files live and how they freeze; their contents are provisional.
