# Layer 2: SDK

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

The SDK is what experiment code imports: a simulation, a training loop, a parameter scan. It writes the storage format of [layer 1](01-storage.md) and
nothing else: no network, no database, no server.

## Principles

1. **Never break the experiment.** Once `init` has returned, no SDK error propagates into user
   code and no SDK operation blocks the process. Problems become a warning on stderr, a `warning`
   event and a count in the run card; the run goes on. Only `init` may raise, and only for misuse
   (invalid arguments, an unknown `resume` id), never for I/O trouble.
2. **Cheap in the hot loop.** `log()` of a dict of scalars costs microseconds: one `json.dumps` and a
   buffered write.
3. **Light to import, broad to run.** The SDK needs Python 3.10+, the standard library and PyYAML.
   NumPy, Pillow, PyArrow and Matplotlib are imported only when a data wrapper needs them. The SDK
   modules never import CLI or server code. It runs on Linux, macOS and Windows.
4. **No network code.** Runs only ever write local files. A future uploader
   ([layer 6](06-server.md)) tails those files from outside the run.
5. **The file format is the API for everything that isn't Python.** A Julia simulation or a shell
   script can write `_run.json` and `_metrics.jsonl` itself.

## API

```python
import beamtime

run = beamtime.init(
    dir="scaling/lr-sweep",          # group below the log dir; created if missing
    name="lr-3e-4-warmup",           # optional
    tags=["resnet18"],
    config=cfg,                      # dict, dataclass, Pydantic model, Namespace, OmegaConf
    proposal="Warmup removes the loss spike.",    # str, dict, path to a YAML file, or None
    resume=None,                     # None: new run; a run id: continue that run
    key=None,                        # a name for this launch; resuming it needs no id
)

for step, batch in enumerate(loader):
    loss = train_step(batch)
    run.log({"train/loss": loss, "lr": sched.get_last_lr()[0]}, step=step)

run.log({"samples": beamtime.Image(grid, caption="epoch 3")}, step=step)
run.card["test/acc"] = 0.931
run.config.update({"n_params": model.n_params})
run.event("lr decayed")
run.artifact("best.ckpt", kind="checkpoint")
run.finish()
```

`init` returns a `Run`. It also works as a context manager (`with beamtime.init(...) as run:`), which
finishes the run on exit and records an exception as `failed`. Code deep in a library reaches the
active run through `beamtime.current()`, which returns the run or `None`. There is no module-level
`beamtime.log`.

### `init`

1. **Find the root and log dir** as in [layer 1](01-storage.md#root-and-log-dir): an absolute `dir`,
   `BEAMTIME_LOGDIR`, `beamtime.yaml` above the working directory, then above the training script,
   then the git root, then the working directory with a warning. An absolute `dir` below a log dir
   keeps that log dir; anywhere else it becomes the log dir itself. A relative `dir` may not contain
   `..`, reserved names or run ids.
2. **Create the run directory** with a fresh id, or continue the run given by `resume`
   ([Resume](#resume)).
3. **Write** `_run.json` (including `proposals`, the current proposal version of the run and of every
   ancestor group, and `job_key`), `_config.json`, the run's own proposal version in `proposal/`, and
   the `_env/` files.
4. **Start** output capture and the heartbeat thread, and install exit and signal hooks.

Recording `proposals` in `_run.json` is all freezing needs: a proposal version is frozen once a run
references it ([the research record](09-research-record.md#versions)). The run never writes into
group folders.

The `proposal` argument accepts a plain string (taken as the statement), a dict in the proposal
shape, or a path to such a YAML file, so an agent can write the proposal before a job is launched.
`BEAMTIME_PROPOSAL` can point to that file for jobs launched by scripts. `None` writes a blank
proposal. A run's own proposal is frozen from the start, since the run references it at `init`.

The config's top-level key `schema` is reserved (it marks `_config.json`'s version); `init` refuses
it. Config values that aren't JSON types are stored as strings.

### `log`

```python
run.log(values: dict[str, Any], step: int | None = None) -> None
```

- Scalars (`int`, `float`, `bool`, NumPy scalars, 0-d tensors via `.item()`) go to
  `_metrics.jsonl`; data wrappers go to `_data.jsonl` and `_data/`. Anything else is dropped with a
  warning.
- Without `step`, the step increments by one per call. With `step`, it must not decrease within an
  attempt; a decreasing step is dropped with a warning (once per key). Equal steps are allowed.
- `.item()` on a GPU tensor forces a device sync; that is the caller's cost.

### Data wrappers

| Wrapper | Accepts | Kind ([layer 1](01-storage.md#_datajsonl-and-_data)) |
|---|---|---|
| `Table(data)` | DataFrame, dict of columns, list of row dicts | `table`; above 1000 cells a Parquet file, or a JSON file without PyArrow |
| `Image(data, caption=None)` | NumPy array or tensor (H×W, H×W×C, C×H×W), PIL image, path | `image`; arrays are encoded to PNG without Pillow |
| `Text(text)` | str | `text` |
| `Histogram(values, bins=64)` or `Histogram(bins=, counts=)` | array-like | a `table` with `bin_start`, `bin_end`, `count` |
| `Figure(fig)` | a Matplotlib figure | an `image` |

There is no way to log a chart spec; presentation belongs to views.

### `card`, `config`, `event`, `artifact`

- **Card and preview.** The SDK keeps the run card and the preview buckets in memory with constant
  memory per metric: first and last, min and max with their steps, sum and count, a non-finite
  counter, an exponential moving average, and per bucket min, max, last, sum and count (at most 512
  buckets per metric, merged pairwise as the run grows). `slope_last10pct` is a line fitted to the
  bucket means of the last 10 % of steps. Both files are written every 3 minutes and at the end.
- `run.card` is a dict-like for explicit values (`run.card["test/acc"] = 0.931`).
- `run.config.update()` adds keys; overwriting a key with a different value warns and is ignored.
- `run.event(message, **data)` appends to `_events.jsonl`.
- `run.artifact(path, kind=None, copy=None, **data)` copies files below 100 MB into `artifacts/` and
  records larger ones by absolute path; `copy` overrides; `data` adds fields such as a checkpoint's
  monitored score.

### `finish`

```python
run.finish(status: Literal["finished", "failed"] = "finished") -> None
```

Flushes and fsyncs the streams, writes the final card and preview, sets `status` and `ended_at`, and
stops capture and the heartbeat. Calling it twice is a no-op.

## Lifecycle and exit handling

| What happens | How the SDK sees it | Status |
|---|---|---|
| `finish()`, or the context manager exits cleanly | direct call | `finished` |
| the script ends without `finish()` | `atexit` | `finished` |
| an unhandled exception | `sys.excepthook` chain, or the context manager | `failed`, traceback in `_events.jsonl`, last line in the card's `error` |
| `SIGTERM` (scheduler timeout, preemption, cancellation) | signal handler (POSIX) | `killed`, reason `time_limit` from 300 s before `SLURM_JOB_END_TIME` on |
| `Ctrl-C` | `KeyboardInterrupt` | `killed`, reason `interrupted` |
| `SIGKILL`, out of memory, node crash | nothing; the process is gone | `lost`, derived from the stale heartbeat |

Signal handlers are installed only in the main thread, only on POSIX, and **chain** to any previous
handler, so frameworks with their own (e.g. Lightning's requeue on SLURM) keep working.

## Notebooks

In Jupyter and IPython there is no process exit per experiment, and file-descriptor capture would
catch kernel noise instead of cell output. When `init` detects a notebook:

- it captures `sys.stdout` and `sys.stderr` instead of file descriptors;
- it warns that the run must end with `run.finish()` or a `with` block, since `atexit` won't fire;
- a run left open shows as `lost` once the heartbeat stops, which is accurate.

## Output capture

Always on. In scripts the SDK captures at the **file-descriptor** level, so output from C extensions,
CUDA, NCCL and subprocesses is caught too.

- File descriptors 1 and 2 are redirected into a **pipe**. A reader thread copies everything to the
  original destination and, through a **bounded in-memory buffer**, to the log file. Nothing
  disappears from the terminal or the scheduler's output file.
- **The training process never waits for the log file.** If writing to it stalls (a slow cluster
  filesystem), the buffer fills and further output is dropped from the log only, with a marker
  ("… 12,431 bytes dropped …"); the terminal copy is unaffected. If the reader thread dies, capture
  restores the original file descriptors.
- **At exit**, joining the reader has a timeout, since child processes (e.g. data loader workers) may
  still hold the pipe open.
- `isatty()` is false while capturing; progress bars such as tqdm degrade to line output.
- Bytes are stored as written, including `\r`; readers collapse carriage returns.
- The buffer holds 4 MB. One reader thread per stream copies to the terminal and the buffer; one
  writer thread empties the buffer into the files.
- **Size cap** (default 10 MB): the first half goes to `_output.log`. Then output goes to
  `_output.tail.log`, in segments that start with a `[beamtime: output segment N]` line; when a
  segment reaches a quarter of the cap (headers not counted), it is renamed to
  `_output.tail.prev.log` and a new one begins. Readers show the head, a marker naming the segments
  that were not kept, and the two tail files, so at least the last 2.5 MB survive.
- On Windows, capture uses the same pipe design.

## Heartbeat

`log()`, `event()` and the data wrappers only queue lines in memory; the training thread never
touches a file after `init`. One daemon thread, the pump, wakes every 2 seconds (or once 1 MB is
queued) and writes the queued lines, data files and artifact copies. Every 30 seconds it updates the
modification time of `_run.json`, every 3 minutes it writes the card and the preview. A stalled
filesystem stalls only the pump; beyond 64 MB queued, new lines are dropped with a warning. The queue
shares one lock with `log()`; it is almost always uncontended. `finish()` writes and syncs
everything on the calling thread.

## Resume

`init` resolves which run to continue, in order, before anything else runs; every mode past the
first can never raise, since starting the experiment must never be at the mercy of a lookup:

1. **Explicit** (`resume=<run id>`, or `BEAMTIME_RESUME`): continue that run, wherever it is below
   the log dir. An unknown id raises in `init`, as misuse (unchanged).
2. **By key** (`key=...`, or `BEAMTIME_RUN_KEY`): the key is stored in `_run.json`. The newest run in
   this folder recorded under it: `running` or `killed` → continue; `finished` or `failed` → a new
   run, with a warning. For a job submitted again by hand, or several models in one job
   (`beamtime.init(dir=..., key=f"{job}-{model}")`). A run whose heartbeat is still fresh (not yet
   `lost`) is another process writing it, so it gets a new run with a warning instead: one writer per
   run. The exception is a requeue of that run's own job, which may find its killed attempt still
   marked `running`.
3. **Requeue** (automatic): `SLURM_RESTART_COUNT > 0` and **exactly one** run in this folder, of
   any status, shares the launch's `job_key` and this call's `name` (name only filters when given),
   and it is `running` or `killed` → continue. Counting finished runs too matters: a job that
   trained model A to the end and was killed in model B would otherwise hand B's run to the
   requeue's first `init`, which is A's. Several runs → a new run, with a warning naming `key` or
   `name` as the way to tell them apart. `find_by_job_key` (how other ranks find rank 0's run)
   keeps its own recency window, on the heartbeat rather than `created_at`, since a requeued rank 0
   continues a run created hours before.
4. **New** (nothing above matched): a fresh id.

A broken `_run.json` elsewhere in the folder, a run found by key or requeue that can't be reopened
(say, a newer schema), or any other error while looking, is swallowed with a warning and falls back
to a new run.

Continuing a run:

1. appends an attempt to `_run.json` and an `attempt_started` event with the resume step and the
   current byte offset of `_metrics.jsonl`;
2. sets the status back to `running`;
3. **rebuilds the card and preview** by reading `_metrics.jsonl` once, up to the resume step, so the
   statistics continue correctly;
4. continues the step counter at the resume step: the step passed to the first `log`, or the last
   logged step plus one.

Since the resume step is only known at the first `log`, steps 1 and 3 and the attempt's entry in
`_run.json` happen then (or at `finish`, if nothing is logged). A partial last line in
`_metrics.jsonl`, left by a killed writer, is ended with a newline first, so it can't merge with the
new attempt's lines; readers count it as one damaged line.

Steps from the resume step on belong to the new attempt; the index drops the older attempt's points
for those steps ([layer 1](01-storage.md#_metricsjsonl)). A config that differs from the stored one
is recorded as a `config_conflict` event and not applied. The run's proposal membership is kept from
its first attempt.

**`_elapsed` counts active time, not wall-clock time.** The queue wait between two attempts (minutes
to hours on a busy cluster) would otherwise show up as a jump in the elapsed-time axis. At ingest,
when an attempt boundary is applied, the gap between the new attempt's start and the previous
attempt's last logged time is computed once (from `attempt_started`'s own timestamp, since nothing
else records where the previous attempt's writing ended) and cached next to the resume step in the
index. A point belongs to the latest attempt whose resume step is at or below it, and `_elapsed`
subtracts the gaps of that attempt and every earlier one (`beamtime.query.read.elapsed_values`), so
an attempt that resumed from an older checkpoint still counts right. `_t` (wall clock) and `_step` are unaffected.

**`beamtime resume <run>`** (also over MCP) answers what's needed to continue a killed or failed run
by hand: the recorded command and working directory, the last step, the newest checkpoint (from
`_artifacts.jsonl`), the scheduler, and the environment variable (`BEAMTIME_RESUME=<id>`) that
continues it. It is read-only and runs nothing itself, so an agent can write the `sbatch` call.

**Time limits.** When a scheduler sends `SIGTERM` after `SLURM_JOB_END_TIME` or within 300 seconds
before it (SLURM signals at the limit or tens of seconds later; Lightning's requeue on `SIGUSR1`
ends it about 2 minutes early), the `killed` event and `exit` carry `reason: "time_limit"`, shown as "killed · time limit" wherever event
descriptions are rendered. Ctrl-C's `reason: "interrupted"` is shown the same way.

## Environment capture

Written once at `init`:

- `_run.json`: host, user, Python, command line, working directory, git commit, branch, dirty flag,
  untracked paths (up to 50, as `git status` lists them: an untracked folder is one entry; the log
  dir is left out, since every run adds files there), `diff_sha` (the first 8 hex of the sha256 of
  the diff plus the untracked list, so the same changes compare equal; `None` on a clean checkout),
  remote, and the job scheduler if one is detected. An untracked file counts as dirty too, since
  `git diff` never shows it.
- `_env/git.diff`: uncommitted changes to tracked files (capped at 1 MB).
- `_env/packages.txt`: installed distributions from `importlib.metadata`, without a subprocess.
- The hardware in `host`: CPU model and logical cores, total memory, GPUs (name, memory, driver)
  from `nvidia-smi` where it exists (with a timeout), and `CUDA_VISIBLE_DEVICES`.

**System metrics** are sampled by default every 30 seconds by the SDK's background thread and
logged as `sys/cpu`, `sys/memory` (percent of the machine), `sys/proc_rss` (the process, in MB) and
`sys/gpu<i>/util` and `sys/gpu<i>/memory` (percent). `init(system_metrics=False)` turns them off; a
sampler that fails or takes longer than two seconds turns itself off with one warning. Standard
library only, plus `nvidia-smi` as a subprocess where present. A sample sits at the run's current
step (at most one per step, none before the first `log`) and carries no time of its own, so it
never moves the step counter; what a platform can't tell (memory on macOS) is left out. The default
view shows system metrics in a collapsed "System" section, never as headline charts.

Scheduler detection fills the `scheduler` field; nothing else depends on it:

| `kind` | Detected by | Common fields |
|---|---|---|
| `slurm` | `SLURM_JOB_ID` | `job_id`, `array_job_id`, `array_task_id`, `partition`, `nodes` |
| `pbs` | `PBS_JOBID` | `job_id`, `array_index`, `queue`, `nodes` |
| `lsf` | `LSB_JOBID` | `job_id`, `array_index`, `queue`, `nodes` |
| `kubernetes` | `KUBERNETES_SERVICE_HOST` | `pod`, `namespace` |

## Distributed training

Every GPU runs its own process with a rank. Launchers expose it as `RANK` (torchrun, Accelerate),
`SLURM_PROCID` (srun), or `LOCAL_RANK` plus `NODE_RANK` (Lightning's launcher). **A process is rank 0
if and only if every one of these variables it can see is `0` or unset.** This works before any
process group exists.

- **The rank** is `RANK`, else `SLURM_PROCID`, else `NODE_RANK × LOCAL_WORLD_SIZE + LOCAL_RANK`
  (without `LOCAL_WORLD_SIZE`: `LOCAL_RANK`, or `1000 × NODE_RANK` for a node's first process).
- **Rank 0** gets a real `Run`.
- **Other ranks** get a `NullRun`, whose methods do nothing, so code needs no `if rank == 0`. Their
  output is still captured into `_output.rank<N>.log` in rank 0's run directory, because crashes
  often happen on other ranks.

A non-zero rank finds rank 0's run directory:

1. **through the inherited environment**: rank 0 sets `BEAMTIME_RUN_DIR` at `init`, and processes it
   starts later inherit it (Lightning's launcher, `mp.spawn`, fork);
2. **through the job key**, for processes started independently (torchrun, `srun`): it waits up to 2
   minutes for a running `_run.json` with the same `job_key`, created in the last 10 minutes, in the
   same folder. Output starts in the capture buffer meanwhile, so `init` doesn't wait.

If neither works, the rank warns and is not captured.

## PyTorch Lightning

`beamtime.lightning.BeamtimeLogger` is a regular Lightning `Logger`. It imports `lightning.pytorch`,
falling back to `pytorch_lightning`; Lightning is not a dependency of Beamtime.

```python
from beamtime.lightning import BeamtimeLogger

logger = BeamtimeLogger(dir="scaling/lr-sweep", proposal="proposals/warmup.yaml")
trainer = Trainer(logger=logger, callbacks=[LearningRateMonitor()])
trainer.fit(model, datamodule)
trainer.test(model, datamodule)
logger.experiment.log({"samples": beamtime.Image(grid)})   # the Run, for non-scalar data
```

`BeamtimeLogger` takes the arguments of `beamtime.init` and calls it in its constructor, on every
rank; the rank rule makes that safe, and output before `fit` is captured too.

| Lightning hook | Beamtime |
|---|---|
| `experiment` | the `Run` (a `NullRun` on other ranks) |
| `log_metrics(metrics, step)` | `run.log(metrics, step=step)`, with `trainer.global_step` |
| `log_hyperparams(params)` | `run.config.update(params)` |
| `after_save_checkpoint(cb)` | checkpoint paths and the monitored score go to `_artifacts.jsonl` |
| `finalize(status)` | flush only; a `failed` status is recorded as an event |
| `save_dir`, `name`, `version` | point at the run directory, so checkpoints land in `<run>/checkpoints/` |

- **`finalize` does not finish the run**: Lightning calls it after every `fit`, `validate` and
  `test`. The exit hooks finish the run.
- **Validation and training share steps**: equal steps are allowed.
- **Checkpointing follows Lightning's rules**: without a `dirpath`, checkpoints go to
  `<run>/checkpoints/`; an explicit `dirpath` wins.
- **SLURM requeue**: Lightning's `SLURMEnvironment(auto_requeue=True)` handles `SIGUSR1`: it saves
  an HPC checkpoint and calls `scontrol requeue`. Lightning installs that handler only where
  `SIGUSR1` has none, so `BeamtimeLogger` gives `SIGUSR1` back to its earlier handler right after
  `init`; Lightning's requeue therefore records no `requeue_requested`. The `SIGTERM` the requeue
  sends sets `killed` (reason `time_limit` when it arrives near the job's end time). The requeued job continues the same run automatically
  ([Resume](#resume)); pass `key=` to tell several models of one job apart. Lightning resumes
  training itself from `ckpt_path="last"`; Beamtime only needs to find the same run, not the
  checkpoint. The handler composition is covered by the Lightning tests (`SIGUSR1` under a faked
  SLURM environment).

## Module layout

```
src/beamtime/
  __init__.py      # init, current, data wrappers, loaded on first use
  lightning.py     # BeamtimeLogger
  sdk/
    run.py         # init, Run, NullRun, current, the pump, exit and signal hooks, resume
    paths.py       # root and log dir resolution, finding runs
    env.py         # host, scheduler, rank, job key, git, packages
    capture.py     # output capture and rotation
    stats.py       # card statistics and preview buckets in constant memory
    data.py        # Table, Image, Text, Histogram, Figure
  format/          # ids, the write protocol and the readers, shared with the index
```

These modules use Python 3.10 syntax and import only `sdk/` and `format/` at module level; optional
libraries are imported inside the functions that need them.

## Decisions

- All logging goes through the `Run` object; deep code uses `beamtime.current()`.
- Python 3.10+, standard library and PyYAML; Linux, macOS and Windows.
- `init` records proposal membership in `_run.json`; the run never writes into group folders.
- Four ways to resolve a run at `init`: explicit id, key, automatic SLURM requeue, or new; continuing
  rebuilds card and preview, and the newer attempt wins from its resume step on. Only the explicit id
  can raise; the others fall back to a new run with a warning.
- `_elapsed` is active time: the queue wait between attempts is computed once at ingest and
  subtracted, so a resumed run's curve doesn't jump.
- Output capture uses a pipe and a bounded buffer and never blocks training; notebooks capture
  `sys.stdout` and must finish explicitly.
- The heartbeat is the modification time of `_run.json`; card and preview are written every 3
  minutes.
- Rank 0 writes the run; other ranks capture their output into `_output.rank<N>.log`.
- PyTorch Lightning is supported natively through `BeamtimeLogger`.
- The SDK logs data, never charts.
- Notes are written with the CLI or MCP ([layer 8](08-cli-mcp.md)), not the SDK.
- An untracked file counts as dirty too; `diff_sha` hashes the diff and the untracked list, so
  `run.code` ([layer 3](03-index.md#fields)) is one comparable identity across runs and checkouts.

## Later

- Adapters for other frameworks (Hugging Face Trainer, Accelerate).
- The uploader for the self-hosted server ([layer 6](06-server.md)).
