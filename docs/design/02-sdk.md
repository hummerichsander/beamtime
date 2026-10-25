# Layer 2: SDK

Status: **draft, under discussion**

The SDK is what training code imports. It writes the storage format from
[layer 1](01-storage.md) and nothing else: no network, no database, no server.

## Principles

1. **Never break the training run.** Once `init` has returned, no SDK error propagates into user
   code. Problems become a warning on stderr and an event in `_events.jsonl`; the run goes on.
   Only `init` may raise, and only for misuse (invalid arguments), never for I/O trouble.
2. **Cheap in the hot loop.** `log()` of a dict of scalars costs microseconds: one `json.dumps` and
   a buffered write. No threads hand-off, no queue.
3. **Light to import.** The SDK depends only on the standard library and PyYAML. NumPy, Pillow,
   PyArrow and Matplotlib are imported lazily, only when a data wrapper needs them. Server, UI and MCP
   dependencies live in extras (`beamtime[serve]`).
4. **No network code.** Runs only ever write local files. Uploading to a self-hosted server
   ([layer 6](06-server.md)) is a separate component that tails those files, so a run never
   depends on the network.
5. **The file format is the API for everything that isn't Python.** A Julia simulation or a shell
   script can write `_run.json` and `_metrics.jsonl` itself. The SDK is a convenience, not a gate.

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

`init` returns a `Run`. It also works as a context manager (`with beamtime.init(...) as run:`),
which finishes the run on exit and records an exception as `failed`.

Code deep in a library can reach the active run through `beamtime.current()`, which returns the
run or `None`.

### `init`

1. Resolve the log dir (`BEAMTIME_LOGDIR`, else `logdirs[0]` from `beamtime.yaml`, else
   `<root>/beamtime`) and the run folder `dir` below it. An absolute `dir` is used as is.
2. Create a new run directory with a fresh id, or continue the run given by `resume` (see
   [Resume](#resume)).
3. Write `_run.json`, `_config.json`, the run's first proposal version (`proposal/<ts>.yaml`) and
   the `_env/` files.
4. Freeze the newest unfrozen proposal version of every group between the run folder and the log dir
   by creating `_frozen/<version>.json` (exclusive create; see
   [the research record](09-research-record.md#versions)).
5. Start output capture and the heartbeat thread, install exit and signal hooks.

The `proposal` argument accepts a plain string (taken as the statement), a dict in the proposal
shape, or a path to such a YAML file, which lets an agent write the proposal before
launching a job. `BEAMTIME_PROPOSAL` can point to that file as well, for jobs launched by scripts.
`None` writes a blank proposal.

### `log`

```python
run.log(values: dict[str, Any], step: int | None = None) -> None
```

- Scalars (`int`, `float`, `bool`, NumPy scalars, 0-d tensors via `.item()`) go to
  `_metrics.jsonl`. Data wrappers go to `_data.jsonl` and `_data/`.
- Without `step`, the step increments by one per call. With `step`, it must not decrease within an
  attempt; a decreasing step is dropped with a warning (once per key).
- The first `log` call freezes the run's proposal version (`_frozen/<version>.json`).
- Anything that is neither a scalar nor a data wrapper is dropped with a warning.

`.item()` on a GPU tensor forces a device sync. That is the user's cost and the docs say so; the SDK
does not try to be clever about it.

### Data wrappers

Three wrappers map to the three non-scalar kinds of [layer 1](01-storage.md#datajsonl-and-data):

| Wrapper | Accepts | Kind |
|---|---|---|
| `Table(data)` | DataFrame, dict of columns, list of row dicts | `table` |
| `Image(data, caption=None)` | NumPy array, PIL image, path | `image` |
| `Text(text)` | str | `text` |

Two conveniences convert at log time and add no kind of their own:

| Convenience | Becomes |
|---|---|
| `Histogram(values, bins=64)` or `Histogram(bins=, counts=)` | a `table` with `bin_start`, `bin_end`, `count` |
| `Figure(fig)` | an `image` rendered from a Matplotlib figure |

There is no way to log a chart spec. Presentation belongs to views.

### `card`, `config`, `event`, `artifact`

- The SDK maintains the run card ([layer 1](01-storage.md#_run_cardjson)) in memory and writes
  `_run_card.json` every 60 s and at the end. All statistics are streaming with constant memory per
  metric: first, last, min, max with their steps, sum and count for the mean, a non-finite counter
  and an exponential moving average.
- In the same pass it maintains the preview buckets of `_preview.json` (min, max, last, sum and
  count per bucket; at most 512 buckets per metric, merged pairwise as the run grows) and writes
  them together with the card. `slope_last10pct` is a line fitted to the preview's bucket means in
  the last 10% of steps, so no extra buffer is needed.
- `run.card` is a dict-like for explicit values (`run.card["test/acc"] = 0.931`), stored under
  `values`.
- `run.config.update()` adds keys; overwriting an existing key with a different value warns and is
  ignored, so the config never silently changes meaning mid-run.
- `run.event(message, **data)` appends to `_events.jsonl`.
- `run.artifact(path, kind=None, copy=None)` copies files below 100 MB into `artifacts/` and
  references larger ones by absolute path. `copy=True/False` overrides.

### `finish`

```python
run.finish(status: Literal["finished", "failed"] = "finished") -> None
```

Flushes and fsyncs all streams, writes the final `_run_card.json` and `_preview.json`, sets `status` and `ended_at`,
stops capture and the heartbeat. Calling it twice is a no-op.

## Lifecycle and exit handling

| What happens | How the SDK sees it | Status |
|---|---|---|
| `finish()` or context manager exits cleanly | direct call | `finished` |
| Script ends without `finish()` | `atexit` | `finished` |
| Unhandled exception | `sys.excepthook` chain, or context manager | `failed`, traceback in `_events.jsonl`, last line in the card's `error` |
| `SIGTERM` (scheduler timeout, preemption, job cancelled) | signal handler | `killed` |
| `Ctrl-C` | `KeyboardInterrupt` | `killed`, reason `interrupted` |
| `SIGKILL`, OOM kill, node crash | nothing, the process is gone | `lost`, derived from the stale heartbeat |

Signal handlers are installed only in the main thread and **chain** to any previous handler, so
frameworks that install their own (e.g. Lightning's auto-requeue on SLURM) keep working.

## Output capture

Always on. The SDK captures at the **file-descriptor** level, not by replacing `sys.stdout`, so
output from C extensions, CUDA, NCCL and subprocesses is caught too.

- File descriptors 1 and 2 are redirected into a pipe; a reader thread copies everything both to
  the original destination and to the log. Nothing disappears from the terminal or the scheduler's output
  file.
- When the original stream is a terminal, a pseudo-terminal is used instead of a pipe, so
  `isatty()` stays true and progress bars keep rendering.
- Bytes are stored as written, including `\r` from progress bars; readers collapse them.

Size cap (default 10 MB): the first half goes to `_output.log`. After that, output goes to
`_output.tail.log`; when it reaches a quarter of the cap, it is renamed to `_output.tail.prev.log`
and a new one begins. Readers show `_output.log`, a truncation marker, then the two tail files.
The head and at least the last 2.5 MB always survive.

## Heartbeat

A daemon thread wakes every 30 s. It replaces `_heartbeat` with the current time, flushes the
buffered streams, and every second wake writes `_run_card.json` and `_preview.json`. All writes share one lock with
`log()`; the lock is uncontended almost always, so the hot loop doesn't notice.

## Resume

There are two modes:

- **New** (`resume=None`, the default): always a new run with a fresh id.
- **Continue** (`resume=<run id>`): continue that run, wherever it is below the log dir. An unknown
  id raises in `init`, since that is misuse, not I/O trouble.

Resuming appends an attempt to `_run.json`, sets status back to `running`, and continues the step
counter after the last logged step unless `step` is passed. A config that differs from the stored
one is logged as an event with the diff and not applied.

## Environment capture

Written once at `init`:

- `_run.json`: host, user, Python, command line, working directory, git commit, branch, dirty
  flag, remote, and the job scheduler if one is detected.
- `_env/git.diff`: uncommitted changes to tracked files (capped at 1 MB).
- `_env/packages.txt`: installed distributions from `importlib.metadata`, no subprocess.

Scheduler detection checks a few environment variables and fills the `scheduler` field of
`_run.json` with `kind` plus whatever the scheduler exposes. Nothing else in the SDK depends on it.

| `kind` | Detected by | Common fields |
|---|---|---|
| `slurm` | `SLURM_JOB_ID` | `job_id`, `array_job_id`, `array_task_id`, `partition`, `nodes` |
| `pbs` | `PBS_JOBID` | `job_id`, `array_index`, `queue`, `nodes` |
| `lsf` | `LSB_JOBID` | `job_id`, `array_index`, `queue`, `nodes` |
| `kubernetes` | `KUBERNETES_SERVICE_HOST` | `pod`, `namespace` |

Adding a scheduler means adding one row and its variable mapping.

## Distributed training

In distributed training every GPU runs its own process with a number, its rank. Launchers expose
it through different variables: `RANK` (torchrun, Accelerate), `SLURM_PROCID` (srun), and
`LOCAL_RANK` plus `NODE_RANK` (Lightning's subprocess launcher). A process is rank 0 if and only if
every one of these variables it can see is `0` or unset. This works before any process group exists,
so `init` can decide at once.

- **Rank 0** gets a real `Run` and writes everything, as for a single process.
- **Other ranks** get a `NullRun`: `log`, `card`, `event` and the rest do nothing, so code doesn't
  need `if rank == 0` around every call. Their output is still captured, into
  `_output.rank<N>.log` in rank 0's run directory, because a crash often happens on another rank.
  Each file has exactly one writer, its rank.

A non-zero rank finds rank 0's run directory in one of two ways:

1. **Inherited environment.** Rank 0 sets `BEAMTIME_RUN_DIR` in its own environment at `init`.
   Processes it starts afterwards inherit it: Lightning's subprocess launcher, `mp.spawn`, fork.
2. **Shared job key**, for processes started independently (torchrun, a scheduler's launcher such
   as `srun`): `TORCHELASTIC_RUN_ID` under torchrun, otherwise the scheduler's job id and array
   index. The rank waits up to 2 minutes for a running `_run.json` with that key in the same
   folder.

If neither works, the rank prints a warning and is not captured. Per-rank files use the same size
cap and rotation as `_output.log`.

## PyTorch Lightning

Lightning is supported natively through `beamtime.lightning.BeamtimeLogger`, a regular Lightning
`Logger`. It imports `lightning.pytorch`, falling back to `pytorch_lightning`; Lightning is not a
dependency of Beamtime.

```python
from beamtime.lightning import BeamtimeLogger

logger = BeamtimeLogger(dir="scaling/lr-sweep", proposal="proposals/warmup.yaml")
trainer = Trainer(logger=logger, callbacks=[LearningRateMonitor()])
trainer.fit(model, datamodule)
trainer.test(model, datamodule)

logger.experiment.log({"samples": beamtime.Image(grid)})   # the Run, for non-scalar data
```

`BeamtimeLogger` takes the same arguments as `beamtime.init` and calls it in its constructor.
Thanks to the rank rule above, this is safe on every rank: rank 0 creates the run, other ranks get
a `NullRun` and start capturing their output. Creating the run eagerly, not on first use, means
output from model setup and data loading before `fit` is captured too.

| Lightning hook | Beamtime |
|---|---|
| `experiment` | the `Run` (a `NullRun` on other ranks) |
| `log_metrics(metrics, step)` | `run.log(metrics, step=step)`; `step` is `trainer.global_step` |
| `log_hyperparams(params)` | `run.config.update(params)`, including `save_hyperparameters()` |
| `after_save_checkpoint(cb)` | checkpoint paths and the monitored score go to `_artifacts.jsonl` |
| `finalize(status)` | flush only; a `failed` status is recorded as an event |
| `save_dir`, `name`, `version` | point at the run directory, so checkpoints land in `<run>/checkpoints/` |

Details that matter:

- **`finalize` does not finish the run.** Lightning calls it at the end of every `fit`, `validate`
  and `test`, and code often calls `test` after `fit`. The run is finished by the exit hooks, as
  for plain scripts.
- **Validation and training metrics share steps.** Lightning logs validation at the current
  `global_step`; equal steps are allowed, only decreasing ones are dropped.
- **Checkpointing follows Lightning's rules.** Without a `dirpath`, `ModelCheckpoint` saves to
  `<run>/checkpoints/`, as with Lightning's own loggers; an explicit `dirpath` wins. Either way the
  checkpoints are listed by reference in `_artifacts.jsonl` and excluded from pulls.
- **SLURM requeue keeps working on Lightning's side.** `SLURMEnvironment(auto_requeue=True)`
  handles `SIGUSR1`, saves an HPC checkpoint and requeues the job. Lightning composes its signal
  handlers with existing ones, so Beamtime's handlers stay active: `SIGUSR1` is recorded as a
  `requeue_requested` event and the following `SIGTERM` sets `killed`. Without an auto mode, the
  requeued job starts a new run (see [Later](#later)). (Verify the handler composition against the
  Lightning version we target before implementing.)
- **Tables, images and text** go through `logger.experiment.log(...)`, since Lightning's logger
  interface only knows scalars.

## Module layout

```
src/beamtime/
  __init__.py      # init, current, data wrappers
  run.py           # Run, NullRun
  paths.py         # root and log dir resolution, ids
  env.py           # host, scheduler, git, packages
  capture.py       # output tee and rotation
  data.py          # Table, Image, Text, Histogram, Figure
  files.py         # atomic replace, JSONL appender
  lightning.py     # BeamtimeLogger
```

## Out of scope for v1

- Integrations with other frameworks (Hugging Face Trainer, Accelerate tracker). They are thin
  adapters like the Lightning logger and come later.
- Writing notes from the SDK. That belongs to the annotation API, which is designed
  together with proposals.

## Decisions

- All logging goes through the `Run` object. There is no module-level `beamtime.log`; deep code
  uses `beamtime.current()`.
- Two resume modes: new (default) and continue (`resume=<run id>`).
- Rank 0 writes the run; other ranks capture their output into `_output.rank<N>.log`.
- PyTorch Lightning is supported natively through `BeamtimeLogger`.
- The SDK logs data, never charts: `Histogram` and `Figure` convert to a table and an image.


## Later

- **Auto resume.** A third mode that continues a matching run by itself, so that a requeued
  scheduler job or a Lightning restart from a checkpoint continues its run without passing an id.
  Matching on the job id alone is not enough: one job may train several models one after another.
  Candidates are an explicit run `key`, or a checkpoint path inside a run directory.
