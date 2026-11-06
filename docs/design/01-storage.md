# Layer 1: Storage format

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

The storage format is the contract every other layer builds on. The SDK writes it, the index reads
it, remotes serve it ([layer 4](04-remotes.md)), and agents `cat` and `grep` it directly. It has to
work on a laptop, a workstation and a cluster filesystem (Lustre, GPFS, NFS) without a server or
database.

## Scope

Beamtime **records** experiments; it never **runs** them. It does not launch jobs, schedule sweeps,
pick hyperparameters or talk to job schedulers. It only reads what the environment exposes (host,
git, scheduler variables if any) and stores what the run logs.

## Principles

1. **Beamtime adapts to the user's folders, not the other way round.** Runs live wherever the user
   puts them. Folders are the only hierarchy.
2. **Files are the source of truth.** Everything else (index, web UI, MCP answers) is derived and can
   be rebuilt with `beamtime reindex`.
3. **Every file has exactly one writer.** No two processes or machines ever modify the same file.
   State that several parties change is stored as new, immutable files, and the newest one counts.
4. **Append or replace, never edit in place.** Streams are append-only JSONL. Whole-file state is
   written to a temp file and renamed, so readers never see a half-written file.
5. **Machine-written files start with `_`; authored files don't.** Everything Beamtime writes is
   prefixed (`_run.json`, `_metrics.jsonl`) and must not be edited by hand. Everything people and
   agents write (`proposal/`, `notes/`, `view/`, `memory/`, `blocks/`) has no prefix. This matches
   the reserved `_step` and `_t` keys inside the files.
6. **Machine-written files are JSON; authored files are YAML or Markdown.** Config values come from
   Python dicts and must round-trip exactly. Proposals and views are structured YAML; notes and
   memory are Markdown with YAML frontmatter.
7. **Every file states its schema version** in a `schema` field, and readers accept every version
   forever. Old runs are never rewritten. JSON Lines streams carry no per-line `schema`; their lines
   follow the schema of the run's `_run.json`.

## Root and log dir

The **root** is the user's repository, like with TensorBoard. Beamtime adds one folder and one
optional file to it:

```
my-repo/
  beamtime.yaml        # optional: project settings
  src/ …
  beamtime/            # the log dir, gitignored
```

- **Finding the root**, in order: `--root` or `beamtime.init(dir=<absolute path>)`; the nearest
  directory with `beamtime.yaml` above the working directory; the same search above the training
  script's location (`__main__.__file__`); the git root; the working directory. Batch jobs often
  start outside the repo, so the script's location is the second anchor; a fallback to the working
  directory is recorded as a warning event in the run.
- **The log dir** is `beamtime/` in the root, or `logdir` in the settings. `BEAMTIME_LOGDIR` overrides
  it for new runs, e.g. scratch space on a cluster; this is the documented cluster recipe.
- **The index cache** lives outside the repo in `~/.cache/beamtime/<logdir-hash>/`, so nothing
  machine-specific ends up in the repo and SQLite never touches a cluster filesystem. The hash is
  of the resolved log dir, so a `BEAMTIME_LOGDIR` on scratch space gets its own cache.
  `BEAMTIME_CACHE` (or `XDG_CACHE_HOME`) moves the cache, e.g. to a local disk on a login node.

### Settings

Settings work like VS Code's: user settings are the default for every project, and a project's
`beamtime.yaml` overrides them.

| Level | File | Typical contents |
|---|---|---|
| built-in | – | Beamtime's defaults |
| user | `~/.config/beamtime/settings.yaml` | remotes used everywhere (`host`, `command`, `cache`), theme |
| project | `beamtime.yaml` in the root | `logdir`, the project's remote paths, the project's default theme |
| session | command-line flags and environment variables | one-off overrides |

- Each level overrides the one above it. Mappings merge key by key, so a user-level remote defines
  `host`, `command` and `cache` once and each project adds only its `path`:

  ```yaml
  # ~/.config/beamtime/settings.yaml
  remotes:
    cluster: {host: cluster, command: ~/venvs/bt/bin/beamtime, cache: /local/scratch/{user}/bt}
  ```
  ```yaml
  # beamtime.yaml
  schema: 1
  logdir: beamtime
  theme: beamtime
  theme_mode: system            # system, light or dark
  figure_style: [science, nature]   # matplotlib style sheets for PDF figures, as for plt.style.use
  remotes:
    cluster: {path: /scratch/{user}/proj/beamtime}
  ```

- Both files have the same schema. A key that only makes sense in one of them (`logdir` in the
  project) is reported when it appears in the other.
- `beamtime settings` shows the effective settings and, for each value, which level it came from.
- Settings changed in the web UI (theme, mode, figure styles) are written to the project's
  `beamtime.yaml` with `beamtime set <key> <value>`, a user command; the file keeps its other keys
  and comments.

## Folders

Below the log dir, the user organizes runs in ordinary folders. A folder that contains a `_run.json`
is a **run**; every other folder is a **group** (Beamtime's commands, tools and UI always say
*group*). Directions, sweeps and ablations are all groups:

```
beamtime/
  memory/                           # the project's memory
  scaling/                          # group: a research direction
    proposal/                       # versions of the direction's proposal
    view/                           # this group's view
    notes/
    memory/
    lr-sweep/                       # group: a sweep
      proposal/
      view/                         # the sweep's own view
      20261024-101532-k3m9xq2a/     # run
      20261024-101533-p2x8fq1c/     # run
  tokenizer/
    bpe-vs-unigram/ …
```

Folders carry authored files, each kind in its own folder and versioned by new files:

| Folder | On | Contents |
|---|---|---|
| `proposal/<id>.yaml` | groups and runs | what is expected for the runs in this group, and why |
| `notes/<id>.md` | groups and runs | observations, decisions, ideas, questions, verdicts |
| `view/<id>.yaml` | groups and runs | the group's view; the newest version is shown |
| `memory/<id>.md` | groups and the log dir | a compressed summary of the notes below |
| `blocks/<name>/<id>.yaml` | groups and the log dir | reusable view blocks for this group and below |

`<id>` is a version id (`20261025-091200-x8k2`: UTC time plus 4 random base32 characters). Proposals,
notes and memory are specified in [the research record](09-research-record.md), views and blocks in
[layer 5](05-views.md).

This covers what other tools model as separate concepts:

- **Projects** are top-level groups.
- **Sweeps** are groups whose runs come from one launch; scheduler job information is recorded per
  run.
- **The journal** is the notes on a group, or on the log dir itself for project-wide entries.
- **Reports and dashboards** are views, one per group.

**Reserved names** never count as groups: the authored folders above, every name starting with `_`
(including `_trash/` in the log dir) or `.` (hidden folders such as `.ipynb_checkpoints/`), and inside
runs `artifacts/` and `checkpoints/`.

The **timeline** is not stored. The index builds it from run events and notes.

## Views in storage

How views look and behave is [layer 5](05-views.md). For storage:

- **No inheritance.** A group or run shows its own newest view, else Beamtime's built-in default.
- **Versions.** Each save is a new file in `view/`; the newest counts. Drafts live outside `view/`
  until saved, in `.beamtime/drafts/` of the project root.
- **Files belonging to a view version** are stored next to it and named by content hash, so they are
  immutable and an older version keeps working:
  - `view/data/<sha8>-<name>.parquet` (or `.csv`, `.json`): data files for analysis that queries
    cannot express, read through the `file` query ([layer 3](03-index.md#query-kinds));
  - `view/code/<sha8>-<name>.js`: custom block code.

## Runs

### Identity

- **Run id:** `20261024-101532-k3m9xq2a`, the UTC start time plus 8 random base32 characters (40
  bits). It sorts chronologically and is unique without coordination: 1000 jobs starting in the same
  second collide with a chance of about 5e-7. The directory is created with an exclusive `mkdir`; a
  collision retries.
- **Run name:** a human-readable label (`lr-3e-4-warmup`). If missing, one is generated from
  high-energy physics vocabulary: `boosted-kaon-42`, `prompt-photon-7`. The name lives in `_run.json`
  and can change; the id never does.
- The run directory is named by its id. Runs can be moved between groups (`beamtime mv`); the id and
  everything recorded in the run travel with it.

### Directory

```
20261024-101532-k3m9xq2a/
  _run.json                 # identity, environment, status, proposals   [run, replaced, heartbeat]
  _config.json              # hyperparameters                            [run, replaced]
  _run_card.json            # compact summary                            [run, replaced]
  _preview.json             # downsampled curves                         [run, replaced]
  _metrics.jsonl            # scalar stream                              [run, append]
  _data.jsonl               # tables, images, text                       [run, append]
  _data/<key>/<step>.<ext>  # files for large tables and images          [run, create]
  _events.jsonl             # lifecycle events                           [run, append]
  _output.log               # captured output, head                      [run, append]
  _output.tail.log          # captured output, rotating tail             [run, rotated]
  _output.tail.prev.log     # the previous tail segment                  [run, rotated]
  _output.rank<N>.log       # output of rank N (and its tail files)      [rank N, append]
  _artifacts.jsonl          # files produced, by copy or reference       [run, append]
  _env/                     # git.diff, packages.txt                     [run, create]
  artifacts/                # small copied artifacts                     [run, create]
  checkpoints/              # Lightning's checkpoints, if any            [other tool]
  proposal/                 # the run's own proposal versions            [authored]
  notes/                    # notes on this run                          [authored]
  view/                     # the run's own view                         [authored]
```

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
    {"started_at": "2026-10-24T10:15:32Z", "host": "gpu042", "resume_step": null}
  ],
  "proposals": {
    ".": "20261024-101532-a1b2",
    "scaling": "20261020-140000-q7w3",
    "scaling/lr-sweep": "20261023-090000-z9y8"
  },
  "proposal_hashes": {
    ".": "9c1d4e07b2a5f318",
    "scaling": "3e6f4cb965dfafe7",
    "scaling/lr-sweep": "a07b33c1e8d2f940"
  },
  "job_key": "slurm:8812300:45",
  "host": {"hostname": "gpu042", "user": "ada", "os": "Linux", "python": "3.10.14"},
  "scheduler": {"kind": "slurm", "job_id": "8812345", "array_job_id": "8812300",
                "array_task_id": "45", "partition": "gpu", "nodes": "gpu042"},
  "git": {"commit": "57878f1", "branch": "master", "dirty": true, "remote": "…"},
  "command": ["python", "train.py", "--lr", "3e-4"],
  "cwd": "/home/ada/proj",
  "beamtime_version": "0.1.0",
  "copied_from": {"id": "20261020-090000-z1a2b3c4", "path": "scaling/lr-sweep", "at": "2026-10-24T10:20:00Z"}
}
```

- **`proposals`** records, at `init`, the proposal version the run ran under: its own (`.`) and the
  newest version of every ancestor group that has a proposal, keyed by path relative to the log dir.
  This is the run's membership in each proposal, explicit and independent of clocks or later moves
  ([the research record](09-research-record.md#versions)).
- **`proposal_hashes`** has the same keys and the first 16 hex characters of the SHA-256 of each
  recorded proposal file, so an edit of a frozen version is detected. Runs written before M4 lack it
  and are simply not checked for edits.
- **`job_key`** identifies the launch, so other ranks of the same job can find the run
  ([layer 2](02-sdk.md#distributed-training)): the scheduler's job and array ids, or
  `torchrun:<TORCHELASTIC_RUN_ID>`.
- **`scheduler`** is absent when no job scheduler is detected. `kind` names it (`slurm`, `pbs`, `lsf`,
  `kubernetes`, …); the other fields are what it exposes, mapped to common names.
- **Status** is `running`, `finished`, `failed` (exception) or `killed` (a signal: Ctrl-C, scheduler
  timeout, preemption). `exit` says how it ended: `{"code": 1}` or `{"signal": "SIGTERM"}`. **`lost`** is derived when reading: a `running` run whose heartbeat is older
  than 5 minutes.
- **Heartbeat.** The SDK updates the modification time of `_run.json` every 30 seconds (`os.utime`),
  which costs no rename on cluster filesystems. In a pulled snapshot, staleness is judged relative to
  the time of the snapshot.
- **Attempts** support continuing a run ([layer 2](02-sdk.md#resume)): a resumed run keeps its id and
  adds an attempt with the step it resumed from.
- **`copied_from`** is set by `beamtime cp` ([layer 8](08-cli-mcp.md)): the source run's id, its path
  at copy time, and when the copy was made. `created_at` and `attempts` are not touched, since that
  data is from the original run; `proposals` and `proposal_hashes` keep only the run's own entry
  (`.`) and gain the destination's ancestors, as a new run would. `key` goes and `job_key` becomes
  `null`: the copy is no launch's run, and resuming the source's key must never continue the copy.

### `_config.json`

Plain JSON of the hyperparameters, nested as given, with a top-level `schema`. Keys can be added while
the run goes on (e.g. a parameter count known after model build), never removed.

### `_metrics.jsonl`

One JSON object per `log()` call:

```json
{"_step": 120, "_t": 1761300941.21, "train/loss": 2.31, "lr": 0.0003}
{"_step": 121, "_t": 1761300941.48, "train/loss": 2.29}
```

- `_step` (an integer, non-decreasing within an attempt) and `_t` (unix time) are reserved; user
  keys must not start with `_`. Other x-axes (`epoch`, `tokens`) are logged as keys.
- Keys are sparse: each line holds only what was logged. `/` in keys forms groups (`train/loss`).
- `NaN` and `Infinity` are written as Python's JSON literals; diverging runs must be recordable.
- Each line is written with a single `write()` and flushed periodically. Readers ignore a trailing
  line without a newline until it is complete, and skip and count complete lines that don't parse
  (a writer killed mid-line, followed by a resumed attempt).
- **Attempts.** When a run resumes from step `s`, the new attempt's lines follow in the same file. For
  steps from `s` on, the newer attempt wins; the index marks attempt boundaries from `_events.jsonl`
  and drops the overlapped points of the older attempt, so steps stay sorted for every reader.

Size check: 100k steps × 30 keys is about 50 MB of JSONL; the index reads it incrementally from the
last byte offset it has seen.

### `_data.jsonl` and `_data/`

**Runs record data; views present it.** A run logs four kinds of data: scalars (in `_metrics.jsonl`)
and the three kinds below, each indexed by one line in `_data.jsonl`. Nothing a run logs is a chart.

| Kind | Stored as | Typical use |
|---|---|---|
| `table` | inline `columns` up to 1000 cells, else `_data/<key>/<step>.parquet` (`.json` with `columns` when PyArrow is missing) | per-class metrics, predictions, distributions |
| `image` | `_data/<key>/<step>.png` | generated samples, attention maps, plots only the run can draw |
| `text` | inline up to 4 KB, else `_data/<key>/<step>.txt` | generated text, prompts |

```json
{"_step": 500, "_t": 1761301022.0, "key": "samples", "kind": "image", "path": "_data/samples/500.png"}
{"_step": 500, "_t": 1761301022.0, "key": "grads/layer3", "kind": "table", "columns": {"bin_start": [...], "bin_end": [...], "count": [...]}}
```

A histogram is a table with `bin_start`, `bin_end` and `count`. `/` in keys becomes `__` in paths.
Images may carry a `caption`. A second file for the same key and step gets a suffix (`500-1.png`).

### `_events.jsonl`

Lifecycle and diagnostic events, which feed the timeline. Each line has the time `_t`, the step
`_step` where one applies, the event `kind`, and the kind's fields:

```json
{"_t": 1761300932.1, "kind": "attempt_started", "resume_step": null, "metrics_offset": 0}
{"_t": 1761300936.0, "_step": 4, "kind": "user", "message": "lr decayed", "factor": 0.5}
{"_t": 1761300942.0, "_step": 9, "kind": "failed", "traceback": "Traceback (most recent call last): …"}
```

| Event | When |
|---|---|
| `created`, `attempt_started` (with `resume_step` and the byte offset in `_metrics.jsonl`) | at `init` |
| `finished`, `failed` (with the traceback), `killed` (with the signal) | at the end |
| `requeue_requested` | a scheduler asked to requeue (e.g. Lightning's `SIGUSR1`) |
| `config_conflict` | a resumed run brought a different config; the diff is recorded, not applied |
| `warning` | an SDK problem that was absorbed (a dropped step, a failed write, a root fallback) |
| `copied` (with `from`, the source run's id) | written into the copy by `beamtime cp` |
| `user` (with `message` and the event's data) | `run.event("lr decayed", factor=0.5)` |

### `_output.log`

stdout and stderr as the process wrote them. Always captured, with no switch to turn it off: agents
need it most when a run failed. Beyond a size cap (default 10 MB) the head stays in `_output.log` and
the tail rotates between `_output.tail.log` and `_output.tail.prev.log`, so both the start and the
moment of death survive ([layer 2](02-sdk.md#output-capture)). Each tail segment starts with a
`[beamtime: output segment N]` line, so readers can tell which segments were not kept. Ranks other than 0 write
`_output.rank<N>.log` with the same scheme.

### `_run_card.json`

The run card is the first thing an agent reads about a run, and what run tables are built from. It
is small (under about 10 KB) and rewritten every 3 minutes and at the end.

```json
{
  "schema": 1,
  "status": "finished",
  "duration_s": 15320,
  "steps": 50000,
  "steps_per_s": 3.26,
  "error": null,
  "warnings": 0,
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
| `duration_s`, `steps`, `steps_per_s` | how long the run went and how fast |
| `error` | the last exception line of a failed run |
| `warnings` | how many SDK warnings were recorded, so problems show without reading the log |
| `metrics.<key>`: `first`, `last`, `min`, `max`, `mean`, `count` | the shape of every scalar |
| `min_step`, `max_step`, `last_step` | where the extremes happened and how far the metric got |
| `ema_last` | the exponentially smoothed last value: `ema = 0.9 · ema + 0.1 · x`, starting at the first value |
| `nonfinite` | count of NaN and Inf values |
| `slope_last10pct` | slope over the last 10 % of steps: is the metric still moving? |
| `values` | values set explicitly (`run.card["test/acc"] = 0.931`) |

All statistics cover finite values only; `count` counts them and `nonfinite` the rest. A metric that
never had a finite value has only `count`, `nonfinite` and `last_step`. `slope_last10pct` is fitted to
the preview's bucket means (at bucket centres) of buckets starting in the last 10 % of the metric's
steps, and is `null` with fewer than two such buckets.

Proposal checks and verdicts are not part of the card, since the run doesn't know them; CLI and MCP
add them when they show a card ([layer 8](08-cli-mcp.md)).

### `_preview.json`

A downsampled copy of every metric's curve, written by the run next to the card and on the same
schedule. With card and preview, run tables and overview charts need no index.

```json
{
  "schema": 1,
  "metrics": {
    "train/loss": {
      "bucket_width": 64,
      "first_bucket": 0,
      "min": [2.31, 1.92], "max": [2.48, 2.05], "last": [2.29, 1.95],
      "mean": [2.37, 1.99], "count": [64, 64]
    }
  }
}
```

- Each metric has its own `bucket_width`, a power of two. Bucket `i` covers steps
  `[i * bucket_width, (i + 1) * bucket_width)`. When a metric would exceed 512 buckets, neighbouring
  buckets merge and its width doubles, so a long metric has between 256 and 512 buckets and a short
  one has one bucket per logged step. Edges stay fixed between rewrites, so live curves don't jitter.
- Min and max keep spikes visible; mean and count allow exact means over whole buckets. Like the card,
  buckets cover finite values only. Empty buckets of sparse metrics are `null` in every list, `count`
  included; a metric without any finite value has no preview entry.
- The size is a few hundred KB at most.

### `_artifacts.jsonl`

```json
{"name": "best.ckpt", "path": "artifacts/best.ckpt", "size": 47185920, "kind": "checkpoint"}
{"name": "final.ckpt", "uri": "/scratch/me/ckpts/run42/final.ckpt", "size": 1.2e10, "kind": "checkpoint"}
```

Small files are copied into `artifacts/`; large ones are recorded by reference (`uri`) and never
copied or pulled. Lightning's `checkpoints/` are listed by reference as well, with `monitor` and
`score`; any extra fields passed to `run.artifact` are kept.

**`origin`** is set by `beamtime cp`: a checkpoint left in place (no `--with-checkpoints`) that
lived inside the source run's `checkpoints/` keeps its `uri` and gains
`{"run": "<source id>", "path": "checkpoints/x.ckpt"}`, so the file is found by the source's id
through the index (it follows `mv`) rather than by a fixed path. A copy of a copy keeps its
`origin` as it is: it already names the true holder.

## Write protocol

| Kind | How | Durability |
|---|---|---|
| replaced (`_run.json`, `_config.json`, `_run_card.json`, `_preview.json`) | write `._<name>.tmp`, then `os.replace` | `fsync` at run end |
| appended (`_*.jsonl`, `_output.log`, `_output.rank<N>.log`) | one `write()` per line, flushed every few seconds | `fsync` at run end |
| rotated (`_output.tail.log`) | appended; renamed to `_output.tail.prev.log` when full, then started anew | none |
| created (data files, artifacts, authored files) | written under a temporary name, then renamed to a unique name | none |
| heartbeat | `os.utime` on `_run.json` every 30 s | none |

On Windows, a replace that a reader blocks is retried briefly; it never fails the run.

## Deleting and cleaning up

Files are immutable while they matter, but a project must stay manageable, and a leaked secret in a
log or a note must be removable.

- **`beamtime rm <run or group>`** moves it into `_trash/<timestamp>/` in the log dir; `beamtime gc`
  empties the trash, removes crashed runs that never logged a metric, and clears any `cp` working
  directory a crash left behind (reserved name `_cp-<id>`, never renamed into place). Both are user
  commands; agents never run them ([layer 8](08-cli-mcp.md#policy)). Removing a run doesn't block
  `beamtime cp` copies of it, but `rm` and `gc --yes` list the copies that reference its checkpoints,
  since those stay readable with `exists: false` once it is gone.
- **`beamtime note rm <id>`** moves a note, with the versions it superseded, into the trash the
  same way.
- **`beamtime mv <group> <new path>`** moves or renames a group and appends the move to
  `_moves.jsonl` in the log dir (`{schema, from, to, t}` per line). Nothing that names the old path is
  rewritten: runs keep their recorded proposal membership, notes their links and `completes`;
  readers map old paths through the moves. Moving a run (`beamtime mv <run> <group>`) needs no
  record, since runs are found by id.
- **A run's display name** can be changed after the run: `beamtime name <run> <name>` writes a new
  version in the run's `name/` folder (`{schema, name, author, user}`), which listings show instead of
  the name in `_run.json`. The run id never changes.
- **Deleting by hand** is supported too. The index notices vanished folders and forgets them
  ([layer 3](03-index.md#discovery)).

## Decisions

- The root is the user's repo; runs live in user-chosen folders under one log dir, found by
  `_run.json`. Batch jobs anchor the root at the training script's location if the working directory
  doesn't lead to it.
- Folders are the only hierarchy. Projects, sweeps and the journal are groups and their notes.
- Machine-written files start with `_`; authored files live in `proposal/`, `notes/`, `view/`,
  `memory/` and `blocks/`, versioned by new files.
- Every file carries `schema`; readers accept every version forever; there is no migration.
- Runs record their proposal membership in `_run.json`.
- The heartbeat is the modification time of `_run.json`; card and preview are rewritten every 3
  minutes and at the end.
- Resumed runs append new attempts; the newer attempt wins from its resume step on.
- Runs record data, views present it: scalars, tables, images and text; histograms are tables.
- `_output.log` is always captured, with a head and a rotating tail.
- Deleting goes through `_trash/` and `beamtime gc`, or by hand; the index copes.
- Beamtime records experiments and never runs them.
