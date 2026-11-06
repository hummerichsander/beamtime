"""A toy training loop for checking Beamtime by hand, locally or under SLURM."""

import argparse
import math
import os
import random
import sys
import time

import beamtime


def main() -> None:
    """Train nothing, but log like a real script: scalars, data, output, a crash."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="toy")
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--sleep", type=float, default=0.0, help="seconds per step")
    parser.add_argument("--crash-at", type=int, default=None)
    parser.add_argument("--resume", default=os.environ.get("BEAMTIME_RESUME"))
    parser.add_argument("--key", default=None, help="resume by key instead of an id")
    parser.add_argument("--start-step", type=int, default=0, help="checkpoint step")
    args = parser.parse_args()

    run = beamtime.init(
        dir=args.dir,
        config=vars(args),
        proposal="The toy loss decays exponentially.",
        resume=args.resume,
        key=args.key,
    )
    print(f"run {run.id} in {run.dir}", flush=True)
    rng = random.Random(0)
    for step in range(args.start_step, args.steps):
        loss = 2.3 * math.exp(-step * args.lr * 10) + 0.05 * rng.random()
        run.log({"train/loss": loss, "lr": args.lr}, step=step)
        if step % 100 == 0:
            print(f"step {step} loss {loss:.4f}", flush=True)
            run.log({"samples": beamtime.Text(f"sample at {step}")}, step=step)
        if step == args.crash_at:
            raise RuntimeError(f"planned crash at step {step}")
        time.sleep(args.sleep)
    run.card["final/loss"] = loss
    print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
