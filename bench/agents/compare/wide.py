"""The benchmark's second log dir, ``wide``: many runs and long series.

Twenty groups of fifteen sweep runs under ``sweeps/``, whose final validation loss follows a known
recipe with a few failed and killed runs that look better than the leaders, and two groups of
100k-step runs under ``long/``: one with divergences and a spike, one that overfits at a distinct
step per run."""

import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any

from beamtime.synth.generate import Generator, Manifest, Scale

SCALE = Scale(name="wide", seeds=2, steps=1000, val_every=50)

SWEEP_GROUPS = 20
SWEEP_RUNS = 15
GRID: dict[str, tuple[Any, ...]] = {
    "lr": (1e-4, 3e-4, 1e-3, 3e-3),
    "batch_size": (64, 128, 256),
    "weight_decay": (0, 1e-4, 1e-3, 1e-2),
    "dropout": (0, 0.1, 0.3),
    "model": ("resnet18", "resnet34"),
}
EFFECTS: dict[str, dict[Any, float]] = {
    "weight_decay": {0: 0.30, 1e-4: 0.15, 1e-3: 0.0, 1e-2: 0.10},
    "lr": {1e-4: 0.06, 3e-4: 0.0, 1e-3: 0.02, 3e-3: 0.08},
    "batch_size": {64: 0.01, 128: 0.0, 256: 0.02},
    "dropout": {0: 0.02, 0.1: 0.0, 0.3: 0.01},
    "model": {"resnet18": 0.0, "resnet34": 0.01},
}
BASE_LOSS = 0.5
NOISE_SD = 0.02
FAILED = 24
KILLED = 6
TRAPS = 3
LEADERS = 5
LEADER_GAP = 0.002
ERRORS = (
    "torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB",
    "RuntimeError: CUDA error: an illegal memory access was encountered",
    "RuntimeError: DataLoader worker (pid 4021) exited unexpectedly",
)

LONG_STEPS = 100_000
LONG_VAL_EVERY = 500
STABILITY_LRS = (1e-3, 2e-3, 3e-3, 5e-3)
SCHEDULES = ("cosine", "linear", "step", "constant")
DIVERGENCES = 3
DIVERGE_E_FOLD = 500
DIVERGE_NAN_AFTER = 1500
DIVERGE_STOP_AFTER = 1800
SPIKE_LENGTH = 200
SPIKE_HEIGHT = 6.0
MINIMA_RANGE = (30_000, 70_000)
OVERFIT_RISE = 0.4


def expected_loss(config: dict[str, Any]) -> float:
    """Give the final validation loss a sweep config is planted to reach, without noise.

    :param config: A sweep run's config.
    :return: The base loss plus the effect of every key."""
    return BASE_LOSS + sum(effects[config[key]] for key, effects in EFFECTS.items())


@dataclass(kw_only=True)
class SweepRun:
    """What a sweep run will do: its config, its final validation loss and how it ends."""

    group: int
    config: dict[str, Any]
    target: float
    status: str = "finished"
    stop: int = 0
    trap: bool = False


class WideGenerator(Generator):
    """The synth generator writing only the wide groups."""

    def __init__(self, *, logdir: Path, seed: int, now: datetime) -> None:
        """Set up a generator at the wide scale.

        :param logdir: The log dir to write into.
        :param seed: The random seed; equal seeds give identical metrics.
        :param now: The wall-clock time heartbeats are judged against."""
        super().__init__(logdir=logdir, seed=seed, scale=SCALE, now=now)

    def run(self) -> None:
        """Write the sweeps and the long series."""
        self.sweeps()
        self.long_series()

    def sweeps(self) -> None:
        """Write ``sweeps/s01`` to ``s20``: fifteen runs each, a few failed or killed, three of
        which last logged a validation loss below the fifth best finished run."""
        runs = [self.draw_sweep_run(g) for g in range(SWEEP_GROUPS) for _ in range(SWEEP_RUNS)]
        ended = self.rng.sample(runs, FAILED + KILLED)
        for i, run in enumerate(ended):
            run.status = "failed" if i < FAILED else "killed"
            run.stop = int(self.scale.steps * self.rng.uniform(0.3, 0.9))
        finished = sorted((r for r in runs if r.status == "finished"), key=lambda r: r.target)
        for i in range(1, LEADERS + 1):
            if (deficit := LEADER_GAP - (finished[i].target - finished[i - 1].target)) > 0:
                for run in finished[i:]:
                    run.target += deficit
        fifth = finished[LEADERS - 1].target
        traps = self.rng.sample(ended, TRAPS)
        for i, run in enumerate(traps):
            run.trap = True
            run.stop = self.rng.randrange(800, 901)
            run.target = fifth - 0.01 * (i + 1)
        for run in ended:
            if not run.trap:
                run.target = max(run.target, fifth + 0.03)

        ids = {}
        for run in runs:
            folder = self.logdir / "sweeps" / f"s{run.group + 1:02d}"
            ids[id(run)] = self.write_sweep_run(folder, run)
        self.manifest.roles["leaders"] = ",".join(ids[id(r)] for r in finished[:LEADERS])
        self.manifest.roles["traps"] = ",".join(ids[id(r)] for r in traps)

    def draw_sweep_run(self, group: int) -> SweepRun:
        """Draw a sweep run's config and the final validation loss it reaches.

        :param group: The index of its group.
        :return: The run, finished for now."""
        config = {key: self.rng.choice(values) for key, values in GRID.items()}
        config["seed"] = self.rng.randrange(1000)
        target = expected_loss(config) + self.rng.gauss(0, NOISE_SD)
        return SweepRun(group=group, config=config, target=target, stop=self.scale.steps)

    def write_sweep_run(self, folder: Path, run: SweepRun) -> str:
        """Write one sweep run.

        :param folder: The group folder.
        :param run: The run.
        :return: The run id."""
        rows = self.sweep_rows(run)
        spec = self.spec(folder, run.config, rows, run.status)
        match run.status:
            case "failed":
                spec.error = self.rng.choice(ERRORS)
            case "killed":
                spec.signal = "SIGTERM"
        return self.write_run(spec)

    def sweep_rows(self, run: SweepRun) -> list[dict[str, Any]]:
        """Make a sweep run's records: train/loss every 10 steps, val/loss every 50 steps and at
        the last step, which equals the run's target exactly.

        :param run: The run.
        :return: The metric records up to the run's stop."""
        last, tau = self.scale.steps - 1, self.scale.steps * 0.2
        end = math.exp(-last / tau)
        t0 = self.clock.timestamp()
        rows = []
        for s in range(run.stop):
            fall = (math.exp(-s / tau) - end) / (1 - end)
            row: dict[str, Any] = {"_step": s, "_t": round(t0 + 0.25 * s, 3)}
            if s % 10 == 0:
                floor = run.target - 0.1
                noise = 1 + 0.03 * self.rng.gauss(0, 1)
                row["train/loss"] = round((floor + (2.3 - floor) * fall) * noise, 6)
            if s % self.scale.val_every == 0 or s == last:
                noise = 0.0 if s == last else 0.004 * self.rng.gauss(0, 1)
                row["val/loss"] = round(run.target + (2.3 - run.target) * fall + noise, 6)
            if len(row) > 2:
                rows.append(row)
        if run.trap:
            rows[max(i for i, r in enumerate(rows) if "val/loss" in r)]["val/loss"] = round(
                run.target, 6
            )
        return rows

    def long_series(self) -> None:
        """Write ``long/stability`` and ``long/schedules``."""
        self.stability()
        self.schedules()

    def stability(self) -> None:
        """Write ``long/stability``: eight runs, three diverge at distinct steps, one spikes."""
        folder = self.logdir / "long" / "stability"
        configs = [
            {"optimizer": "adamw", "lr": lr, "seed": seed}
            for lr in STABILITY_LRS
            for seed in (0, 1)
        ]
        self.rng.shuffle(configs)
        onsets = self.rng.sample(range(20_000, 80_001, 500), DIVERGENCES)
        spike = self.rng.randrange(30_000, 70_001, 500)
        diverged = {}
        for role, config in enumerate(configs):
            floor = 0.3 + 0.02 * config["lr"] / 1e-3
            if role < DIVERGENCES:
                d = onsets[role]
                rows = self.long_rows(floor=floor, tau=20_000, stop=d + DIVERGE_STOP_AFTER)
                self.diverge(rows, d)
                spec = self.spec(folder, config, rows, "failed")
                spec.error = "FloatingPointError: train/loss is inf"
                diverged[d] = self.write_run(spec)
                continue
            rows = self.long_rows(floor=floor, tau=20_000)
            if role == DIVERGENCES:
                self.spike_rows(rows, spike)
            run_id = self.write_run(self.spec(folder, config, rows))
            if role == DIVERGENCES:
                self.manifest.roles["spike"] = run_id
        self.manifest.roles["diverged"] = ",".join(diverged[d] for d in sorted(diverged))

    def schedules(self) -> None:
        """Write ``long/schedules``: eight runs whose validation loss falls, then rises, with its
        minimum at a distinct evaluation step per run."""
        folder = self.logdir / "long" / "schedules"
        configs = [
            {"optimizer": "adamw", "lr": 1e-3, "schedule": schedule, "seed": seed}
            for schedule in SCHEDULES
            for seed in (0, 1)
        ]
        minima = self.rng.sample(range(*MINIMA_RANGE, LONG_VAL_EVERY), len(configs))
        for config, m in zip(configs, minima, strict=True):
            floor = 0.3 + 0.03 * SCHEDULES.index(config["schedule"])
            vmin = 0.6 + 0.05 * SCHEDULES.index(config["schedule"]) + 0.02 * config["seed"]
            rows = self.long_rows(
                floor=floor, tau=20_000, val=partial(self.overfit, vmin=vmin, m=m)
            )
            self.write_run(self.spec(folder, config, rows))

    def long_rows(
        self,
        *,
        floor: float,
        tau: float,
        stop: int = LONG_STEPS,
        val: Callable[[int], float] | None = None,
    ) -> list[dict[str, Any]]:
        """Make long-series records: train/loss every step, val/loss every 500 steps and at the
        last step, nothing else.

        :param floor: The loss train/loss settles at.
        :param tau: The decay of train/loss in steps.
        :param stop: The step the run ends at.
        :param val: The validation loss by step; defaults to a bit above the training loss.
        :return: The metric records."""
        t0 = self.clock.timestamp()
        rows = []
        for s in range(stop):
            decay = math.exp(-s / tau)
            noise = 1 + 0.03 * self.rng.gauss(0, 1)
            row: dict[str, Any] = {
                "_step": s,
                "_t": round(t0 + 0.25 * s, 3),
                "train/loss": round((floor + (2.3 - floor) * decay) * noise, 6),
            }
            if s % LONG_VAL_EVERY == 0 or s == LONG_STEPS - 1:
                value = val(s) if val else floor + 0.05 + (2.3 - floor) * decay
                row["val/loss"] = round(value + 0.0004 * self.rng.gauss(0, 1), 6)
            rows.append(row)
        return rows

    def diverge(self, rows: list[dict[str, Any]], onset: int) -> None:
        """Let both losses grow by a factor of e every 500 steps from an onset, then NaN, then inf.

        :param rows: The records, ending 300 steps after the first NaN.
        :param onset: The step the growth starts at."""
        for row in rows[onset:]:
            after = row["_step"] - onset
            if after < DIVERGE_NAN_AFTER:
                factor = math.exp(after / DIVERGE_E_FOLD)
            else:
                factor = math.nan if after < DIVERGE_NAN_AFTER + 150 else math.inf
            for key in ("train/loss", "val/loss"):
                if key in row:
                    row[key] = round(row[key] * factor, 6)

    def spike_rows(self, rows: list[dict[str, Any]], start: int) -> None:
        """Lift both losses by a half sine that peaks at about 6 times the loss for 200 steps.

        :param rows: The records.
        :param start: The step the spike starts at."""
        for row in rows[start : start + SPIKE_LENGTH]:
            phase = math.sin(math.pi * (row["_step"] - start) / SPIKE_LENGTH)
            for key in ("train/loss", "val/loss"):
                if key in row:
                    row[key] = round(row[key] * (1 + (SPIKE_HEIGHT - 1) * phase), 6)

    @staticmethod
    def overfit(s: int, vmin: float, m: int) -> float:
        """Give a validation loss that falls to ``vmin`` at step ``m``, then rises.

        :param s: The step.
        :param vmin: The minimum.
        :param m: The step of the minimum.
        :return: The loss without noise."""
        if s > m:
            return vmin + OVERFIT_RISE * (s - m) / (LONG_STEPS - 1 - m)
        tau = m / 1.5
        fall = (math.exp(-s / tau) - math.exp(-m / tau)) / (1 - math.exp(-m / tau))
        return vmin + (2.3 - vmin) * fall


def make_wide_logdir(dest: Path, *, seed: int, now: datetime) -> Manifest:
    """Generate the wide log dir at ``dest/beamtime``.

    :param dest: The folder that will hold ``beamtime/``.
    :param seed: The data seed.
    :param now: The time heartbeats are judged against; equal inputs give equal metrics.
    :return: The manifest; its roles stay in memory for grading, never written into ``dest``."""
    logdir = dest / "beamtime"
    logdir.mkdir(parents=True, exist_ok=True)
    gen = WideGenerator(logdir=logdir, seed=seed, now=now)
    gen.run()
    return gen.manifest
