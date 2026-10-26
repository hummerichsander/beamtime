#!/bin/bash
# Smoke test for Beamtime under SLURM: an array job that is preempted and requeued.
#   sbatch examples/slurm_toy.sh
#   scontrol requeue <jobid>_<task>     # or wait for the signal below
#SBATCH --job-name=beamtime-toy
#SBATCH --array=0-1
#SBATCH --time=00:10:00
#SBATCH --signal=B:USR1@60
#SBATCH --requeue
#SBATCH --output=beamtime-toy-%A_%a.out

export BEAMTIME_LOGDIR=${BEAMTIME_LOGDIR:-$HOME/beamtime-smoke}
srun python examples/train_toy.py --dir slurm-smoke --steps 3000 --sleep 0.2 \
    --lr "$(python -c "print([1e-4, 3e-4][$SLURM_ARRAY_TASK_ID])")"
