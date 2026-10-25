# Layer 2: SDK

Status: **reviewed; v1 scope per the [overview](00-overview.md#scope)**

The SDK is what training code imports. It writes the storage format of [layer 1](01-storage.md) and
nothing else: no network, no database, no server.

## Principles

1. **Never break the training run.** Once `init` has returned, no SDK error propagates into user
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
    dir="scaling/lr-sweep",          # folder below the log dir; created if missing
    name="lr-3e-4-warmup",           # optional
    tags=["resnet18"],
    config=cfg,                      # dict, dataclass, Pydantic model, Namespace, OmegaConf
    proposal="Warmup removes the loss spike.",    # str, dict, path to a YAML file, or None
    resume=None,                     # None: new run; a run id: continue that run
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
   then the git root, then the working directory with a warning.
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
| `Table(data)` | DataFrame, dict of columns, list of row dicts | `table` |
| `Image(data, caption=None)` | NumPy array, PIL image, path | `image` |
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
- `run.artifact(path, kind=None, copy=None)` copies files below 100 MB into `artifacts/` and records
  larger ones by absolute path; `copy` overrides.

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
| `SIGTERM` (scheduler timeout, preemption, cancellation) | signal handler (POSIX) | `killed` |
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
- **Size cap** (default 10 MB): the first half goes to `_output.log`. Then output goes to
  `_output.tail.log`; when that reaches a quarter of the cap, it is renamed to
  `_output.tail.prev.log` and a new one begins. Readers show the head, a truncation marker, and the
  two tail files, so at least the last 2.5 MB survive.
- On Windows, capture uses the same pipe design.

## Heartbeat

A daemon thread wakes every 30 seconds. It updates the modification time of `_run.json`, flushes the
buffered streams, and every sixth wake writes the card and the preview. All writes share one lock
with `log()`; it is almost always uncontended.

## Resume

There are two modes:

- **New** (`resume=None`, the default): always a new run with a fresh id.
- **Continue** (`resume=<run id>`): continue that run, wherever it is below the log dir. An unknown
  id raises in `init`.

Continuing a run:

1. appends an attempt to `_run.json` and an `attempt_started` event with the resume step and the
   current byte offset of `_metrics.jsonl`;
2. sets the status back to `running`;
3. **rebuilds the card and preview** by reading `_metrics.jsonl` once, up to the resume step, so the
   statistics continue correctly;
4. continues the step counter at the resume step: the step passed to the first `log`, or the last
   logged step plus one.

Steps from the resume step on belong to the new attempt; the index drops the older attempt's points
for those steps ([layer 1](01-storage.md#_metricsjsonl)). A config that differs from the stored one
is recorded as a `config_conflict` event and not applied. The run's proposal membership is kept from
its first attempt.

## Environment capture

Written once at `init`:

- `_run.json`: host, user, Python, command line, working directory, git commit, branch, dirty flag,
  remote, and the job scheduler if one is detected.
- `_env/git.diff`: uncommitted changes to tracked files (capped at 1 MB).
- `_env/packages.txt`: installed distributions from `importlib.metadata`, without a subprocess.

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

- **Rank 0** gets a real `Run`.
- **Other ranks** get a `NullRun`, whose methods do nothing, so code needs no `if rank == 0`. Their
  output is still captured into `_output.rank<N>.log` in rank 0's run directory, because crashes
  often happen on other ranks.

A non-zero rank finds rank 0's run directory:

1. **through the inherited environment**: rank 0 sets `BEAMTIME_RUN_DIR` at `init`, and processes it
   starts later inherit it (Lightning's launcher, `mp.spawn`, fork);
2. **through the job key**, for processes started independently (torchrun, `srun`): it waits up to 2
   minutes for a running `_run.json` with the same `job_key` in the same folder.

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
- **SLURM requeue**: Lightning's `SLURMEnvironment(auto_requeue=True)` handles `SIGUSR1`; Beamtime
  records `requeue_requested`, and the following `SIGTERM` sets `killed`. The requeued job starts a
  new run unless the script passes `resume`. The handler composition is covered by the Lightning
  version matrix in the tests.

## Module layout

```
src/beamtime/
  __init__.py      # init, current, data wrappers (no other imports at module level)
  run.py           # Run, NullRun
  paths.py         # root and log dir resolution, ids
  env.py           # host, scheduler, git, packages
  capture.py       # output capture and rotation
  data.py          # Table, Image, Text, Histogram, Figure
  files.py         # atomic replace, JSONL appender
  lightning.py     # BeamtimeLogger
```

These modules use Python 3.10 syntax and never import from the CLI, index or server packages.

## Decisions

- All logging goes through the `Run` object; deep code uses `beamtime.current()`.
- Python 3.10+, standard library and PyYAML; Linux, macOS and Windows.
- `init` records proposal membership in `_run.json`; the run never writes into group folders.
- Two resume modes, new and continue; continuing rebuilds card and preview, and the newer attempt
  wins from its resume step on.
- Output capture uses a pipe and a bounded buffer and never blocks training; notebooks capture
  `sys.stdout` and must finish explicitly.
- The heartbeat is the modification time of `_run.json`; card and preview are written every 3
  minutes.
- Rank 0 writes the run; other ranks capture their output into `_output.rank<N>.log`.
- PyTorch Lightning is supported natively through `BeamtimeLogger`.
- The SDK logs data, never charts.
- Notes are written with the CLI or MCP ([layer 8](08-cli-mcp.md)), not the SDK.

## Later

- **Auto resume**: continuing a matching run without an id, e.g. after a requeue. Matching on the job
  id alone is not enough, since one job may train several models; candidates are an explicit run
  `key` or a checkpoint path inside a run directory.
- Adapters for other frameworks (Hugging Face Trainer, Accelerate).
- The uploader for the self-hosted server ([layer 6](06-server.md)).
