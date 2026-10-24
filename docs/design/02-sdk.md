# Layer 2: SDK

Status: **draft, under discussion**

The SDK is what training code imports. It writes the storage format from
[layer 1](01-storage.md) and nothing else: no network, no database, no server.

## Principles

1. **Never break the training run.** Once `init` has returned, no SDK error propagates into user
   code. Problems become a warning on stderr and an event in `events.jsonl`; the run goes on.
   Only `init` may raise, and only for misuse (invalid arguments), never for I/O trouble.
2. **Cheap in the hot loop.** `log()` of a dict of scalars costs microseconds: one `json.dumps` and
   a buffered write. No threads hand-off, no queue.
3. **Light to import.** The SDK depends only on the standard library and PyYAML. NumPy, Pillow,
   PyArrow and Matplotlib are imported lazily, only when a media type needs them. Server, UI and MCP
   dependencies live in extras (`beamtime[serve]`).
4. **The file format is the API for everything that isn't Python.** A Julia simulation or a shell
   script can write `run.json` and `metrics.jsonl` itself. The SDK is a convenience, not a gate.

## API

```python
import beamtime

run = beamtime.init(
    dir="scaling/lr-sweep",          # folder below the log dir; created if missing
    name="lr-3e-4-warmup",           # optional
    tags=["resnet18"],
    config=cfg,                      # dict, dataclass, Pydantic model, Namespace, OmegaConf
    hypothesis="Warmup removes the loss spike.",  # str, dict, path to a YAML file, or None
    resume="auto",                   # "auto" | "never" | a run id
)

for step, batch in enumerate(loader):
    loss = train_step(batch)
    run.log({"train/loss": loss, "lr": sched.get_last_lr()[0]}, step=step)

run.log({"samples": beamtime.Image(grid, caption="epoch 3")}, step=step)
run.summary["test/acc"] = 0.931
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
2. Resume an existing run or create a new run directory with a fresh id (see
   [Resume](#resume)).
3. Write `run.json`, `config.json`, `hypothesis.yaml` and the `env/` files.
4. Freeze every unfrozen group hypothesis between the run folder and the log dir by creating its
   `hypothesis.frozen.json`.
5. Start output capture and the heartbeat thread, install exit and signal hooks.

The `hypothesis` argument accepts a plain string (taken as the statement), a dict in the
`hypothesis.yaml` shape, or a path to such a YAML file, which lets an agent write the hypothesis
before launching a job. `BEAMTIME_HYPOTHESIS` can point to that file as well, for jobs launched by
scripts. `None` writes a blank hypothesis.

### `log`

```python
run.log(values: dict[str, Any], step: int | None = None) -> None
```

- Scalars (`int`, `float`, `bool`, NumPy scalars, 0-d tensors via `.item()`) go to
  `metrics.jsonl`. Media wrappers go to `media.jsonl` and `media/`.
- Without `step`, the step increments by one per call. With `step`, it must not decrease within an
  attempt; a decreasing step is dropped with a warning (once per key).
- The first `log` call freezes the run's hypothesis.
- Anything that is neither a scalar nor a media wrapper is dropped with a warning.

`.item()` on a GPU tensor forces a device sync. That is the user's cost and the docs say so; the SDK
does not try to be clever about it.

### Media wrappers

| Wrapper | Accepts | Stored as |
|---|---|---|
| `Image(data, caption=None)` | NumPy array, PIL image, path | PNG |
| `Histogram(values, bins=64)` or `Histogram(bins=, counts=)` | array-like | inline in `media.jsonl` |
| `Table(data)` | DataFrame, dict of columns, list of rows | Parquet |
| `Figure(fig)` | Matplotlib figure, Vega-Lite dict | PDF + PNG, or JSON |
| `Text(text)` | str | `.txt` |

### `summary`, `config`, `event`, `artifact`

- `run.summary` is a dict-like. The SDK keeps last, min and max of every scalar in memory and
  writes them, merged with explicit values, to `summary.json` every 60 s and at the end.
- `run.config.update()` adds keys; overwriting an existing key with a different value warns and is
  ignored, so the config never silently changes meaning mid-run.
- `run.event(message, **data)` appends to `events.jsonl`.
- `run.artifact(path, kind=None, copy=None)` copies files below 100 MB into `artifacts/` and
  references larger ones by absolute path. `copy=True/False` overrides.

### `finish`

```python
run.finish(status: Literal["finished", "failed"] = "finished") -> None
```

Flushes and fsyncs all streams, writes the final `summary.json`, sets `status` and `ended_at`,
stops capture and the heartbeat. Calling it twice is a no-op.

## Lifecycle and exit handling

| What happens | How the SDK sees it | Status |
|---|---|---|
| `finish()` or context manager exits cleanly | direct call | `finished` |
| Script ends without `finish()` | `atexit` | `finished` |
| Unhandled exception | `sys.excepthook` chain, or context manager | `failed`, traceback in `events.jsonl` |
| `SIGTERM` (SLURM timeout, preemption, `scancel`) | signal handler | `killed` |
| `Ctrl-C` | `KeyboardInterrupt` | `killed`, reason `interrupted` |
| `SIGKILL`, OOM kill, node crash | nothing, the process is gone | `lost`, derived from the stale heartbeat |

Signal handlers are installed only in the main thread and **chain** to any previous handler, so
frameworks that install their own (e.g. Lightning's SLURM auto-requeue) keep working.

## Output capture

Always on. The SDK captures at the **file-descriptor** level, not by replacing `sys.stdout`, so
output from C extensions, CUDA, NCCL and subprocesses is caught too.

- File descriptors 1 and 2 are redirected into a pipe; a reader thread copies everything both to
  the original destination and to the log. Nothing disappears from the terminal or the SLURM output
  file.
- When the original stream is a terminal, a pseudo-terminal is used instead of a pipe, so
  `isatty()` stays true and progress bars keep rendering.
- Bytes are stored as written, including `\r` from progress bars; readers collapse them.

Size cap (default 10 MB): the first half goes to `output.log`. After that, output goes to
`output.tail.log`; when it reaches a quarter of the cap, it is renamed to `output.tail.prev.log`
and a new one begins. Readers show `output.log`, a truncation marker, then the two tail files.
The head and at least the last 2.5 MB always survive.

## Heartbeat

A daemon thread wakes every 30 s. It replaces `heartbeat` with the current time, flushes the
buffered streams, and every second wake writes `summary.json`. All writes share one lock with
`log()`; the lock is uncontended almost always, so the hot loop doesn't notice.

## Resume

A run resumes instead of starting fresh when:

- `resume=<run id>`: that run, wherever it is below the log dir.
- `resume="auto"` (default): a run in the same folder with the same `SLURM_JOB_ID` and
  `SLURM_ARRAY_TASK_ID` exists. This covers SLURM requeue, which keeps the job id. Outside SLURM,
  `"auto"` never resumes.
- `resume="never"`: always a new run.

Resuming appends an attempt to `run.json`, sets status back to `running`, and continues the step
counter after the last logged step unless `step` is passed. A config that differs from the stored
one is logged as an event with the diff and not applied.

## Environment capture

Written once at `init`:

- `run.json`: host, user, Python, command line, working directory, SLURM variables, git commit,
  branch, dirty flag, remote.
- `env/git.diff`: uncommitted changes to tracked files (capped at 1 MB).
- `env/packages.txt`: installed distributions from `importlib.metadata`, no subprocess.

## Distributed training

In distributed training every GPU runs its own process with a number, its rank. `init` reads it
from `RANK` (torchrun, Accelerate) or `SLURM_PROCID`.

- **Rank 0** gets a real `Run` and writes everything, as for a single process.
- **Other ranks** get a `NullRun`: `log`, `summary`, `event` and the rest do nothing, so code doesn't
  need `if rank == 0` around every call. Their output is still captured, into
  `output.rank<N>.log` in rank 0's run directory, because a crash often happens on another rank.
  Each file has exactly one writer, its rank.

The SDK has no channel between processes, so a non-zero rank finds rank 0's run through a shared
job key: `SLURM_JOB_ID` plus `SLURM_ARRAY_TASK_ID` under SLURM, `TORCHELASTIC_RUN_ID` under
torchrun. It waits up to 2 minutes for a running `run.json` with that key in the same folder, then
starts capturing. Without a job key, or if the wait times out, the rank prints a warning and is not
captured. Per-rank files use the same size cap and rotation as `output.log`.

## Module layout

```
src/beamtime/
  __init__.py      # init, current, media wrappers
  run.py           # Run, NullRun
  paths.py         # root and log dir resolution, ids
  env.py           # host, SLURM, git, packages
  capture.py       # output tee and rotation
  media.py         # Image, Histogram, Table, Figure, Text
  files.py         # atomic replace, JSONL appender
```

## Out of scope for v1

- Framework integrations (Lightning logger, Hugging Face callback). They are thin adapters on top
  of `log` and come later.
- Writing notes from the SDK. That belongs to the annotation API, which is designed
  together with hypotheses.

## Decisions

- All logging goes through the `Run` object. There is no module-level `beamtime.log`; deep code
  uses `beamtime.current()`.
- `resume="auto"` is the default, so a requeued SLURM job continues its run.
- Rank 0 writes the run; other ranks capture their output into `output.rank<N>.log`.
