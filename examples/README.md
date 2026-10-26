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
```

## On a cluster

```sh
export BEAMTIME_LOGDIR=$SCRATCH/beamtime-smoke
sbatch examples/slurm_toy.sh
```

Check in each run directory: `_run.json` has the `scheduler` block and `job_key`, `_output.log`
holds the step lines, and a run that hit its time limit is `killed` with a `requeue_requested`
event before it. Requeued tasks start new runs unless the script passes `--resume`.
