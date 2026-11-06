#!/bin/bash
# A Lightning job that hits its time limit and requeues itself (needs lightning and torch).
#   sbatch examples/slurm_lightning.sh
# Lightning catches USR1, saves a checkpoint and calls scontrol requeue; the requeued job's
# BeamtimeLogger continues the same run, and fit(ckpt_path="last") resumes from its checkpoint.
#SBATCH --job-name=beamtime-lightning
#SBATCH --time=00:05:00
#SBATCH --signal=USR1@120
#SBATCH --requeue
#SBATCH --open-mode=append
#SBATCH --output=beamtime-lightning-%j.out

export BEAMTIME_LOGDIR=${BEAMTIME_LOGDIR:-$HOME/beamtime-smoke}
srun python examples/train_lightning.py --epochs 40 --sleep 0.02
