# Examples

`train_toy.py` logs like a training script without training anything; `slurm_toy.sh` runs it as a
SLURM array job.

## Local checks

```sh
uv run python examples/train_toy.py                    # finished
uv run python examples/train_toy.py --crash-at 500     # failed, traceback in _events.jsonl
uv run python examples/train_toy.py --sleep 0.05 &     # then: kill -TERM %1  → killed
uv run python examples/train_toy.py --sleep 0.05 &     # then: kill -KILL %1  → lost after 5 min
uv run python examples/train_toy.py --resume <run id> --start-step 1500  # a second attempt
uv run python examples/train_toy.py --key demo --sleep 0.05 &          # then: kill -TERM %1 → killed
uv run python examples/train_toy.py --key demo --start-step <last+1>   # continues it, no id needed
```

## On a cluster

```sh
export BEAMTIME_LOGDIR=$SCRATCH/beamtime-smoke
sbatch examples/slurm_toy.sh
```

Check in each run directory: `_run.json` has the `scheduler` block and `job_key`, `_output.log`
holds the step lines, and a run that hit its time limit is `killed` with a `requeue_requested`
event before it and `reason: time_limit` on the `killed` event. A requeued task **continues the
same run automatically**: no `--resume` is needed, since a `SLURM_RESTART_COUNT > 0` job reuses its
`job_key` and `init` finds the one unfinished run from it. `beamtime resume <run>` prints the
recorded command, cwd and last step of a run that didn't auto-resume (e.g. one killed by `SIGKILL`
or an out-of-memory node), for an `sbatch` call by hand.

Checking the real requeue path (pending until the next cluster session, see the `pending-cluster
-check` memory): submit `examples/slurm_toy.sh` with a short `--time`, let it hit the limit and
requeue (`scontrol requeue <jobid>_<task>` also forces it), and confirm each task's run has exactly
one `killed` (`reason: time_limit`) and one `attempt_started` (`resumed from step ...`) event, not a
second run directory.

A Lightning job resumes the same way: `BeamtimeLogger(key=...)` is passed on to `init`, and
`Trainer.fit(ckpt_path="last")` picks the checkpoint back up once the requeued task reuses the run.
