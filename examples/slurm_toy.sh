#!/bin/bash
# Smoke test for Beamtime under SLURM: an array job that hits its time limit and requeues itself.
#   sbatch examples/slurm_toy.sh
# SLURM never requeues a job that times out, so the batch shell does it on the warning signal;
# each attempt runs about 2 minutes, and the third one finishes the 1500 steps.
#SBATCH --job-name=beamtime-toy
#SBATCH --array=0-1
#SBATCH --time=00:03:00
#SBATCH --signal=B:USR1@60
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=beamtime-toy-%A_%a.out

export BEAMTIME_LOGDIR=${BEAMTIME_LOGDIR:-$HOME/beamtime-smoke}
trap 'echo "requeue at $(date)"; scontrol requeue "$SLURM_JOB_ID"' USR1
srun python examples/train_toy.py --dir slurm-smoke --steps 1500 --sleep 0.2 \
    --lr "$(python -c "print([1e-4, 3e-4][$SLURM_ARRAY_TASK_ID])")" &
wait  # returns as soon as USR1 arrives
wait  # then lets srun see the SIGTERM the requeue sends
