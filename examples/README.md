# Examples

`train_toy.py` logs like a training script without training anything; `slurm_toy.sh` runs it as a
SLURM array job. `train_lightning.py` and `slurm_lightning.sh` do the same with Lightning.

## Local checks

```sh
uv run python examples/train_toy.py                    # finished
uv run python examples/train_toy.py --crash-at 500     # failed, traceback in _events.jsonl
uv run python examples/train_toy.py --sleep 0.05 &     # then: kill -TERM %1  → killed
uv run python examples/train_toy.py --sleep 0.05 &     # then: kill -KILL %1  → lost after 5 min
uv run python examples/train_toy.py --resume <run id> --start-step 1500  # a second attempt
uv run python examples/train_toy.py --key demo --sleep 0.05 &          # then: kill -TERM %1 → killed
uv run python examples/train_toy.py --key demo                         # continues it, no id needed
```

## On a cluster

```sh
export BEAMTIME_LOGDIR=$SCRATCH/beamtime-smoke
sbatch examples/slurm_toy.sh
```

Each attempt gets `USR1` 60 s before its limit; the batch shell asks for a requeue, SLURM ends
the attempt with `SIGTERM` and starts it again with `SLURM_RESTART_COUNT` raised. Check in each run
directory: `_run.json` has the `scheduler` block and `job_key`, `_output.log` holds the step lines,
and there is **one run per task, not one per attempt**: three `attempt_started` events (the later
ones `resumed from step ...`), and before each requeue a `killed` event with `reason: time_limit`.
No `--resume` is needed, since a requeued job keeps its `job_key` and `init` finds the one
unfinished run from it. `beamtime resume <run>` prints the recorded command, cwd and last step of a
run that didn't auto-resume (e.g. one killed by `SIGKILL` or an out-of-memory node), for an `sbatch`
call by hand.

A Lightning job resumes the same way, with Lightning doing the requeue: `slurm_lightning.sh` runs
`train_lightning.py` (needs `lightning` and `torch`) with `--signal=USR1@120`. Lightning's handler
saves a checkpoint and calls `scontrol requeue`; the requeued job's `BeamtimeLogger` continues the
same run, and `fit(ckpt_path="last")` restores `<run>/checkpoints/last.ckpt`. Expect one run in
`slurm-lightning/` with several `attempt_started` events, a `killed` (`reason: time_limit`) before
each requeue, `Restoring states from the checkpoint` in the job's output, and status `finished`.
