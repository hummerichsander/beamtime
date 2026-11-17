"""The benchmark's log dirs: synthetic runs without the research record and the planted answers.

On top of the synth's scale ``s`` the benchmark plants the messier data of Decision 17: a second
batch of the lr sweep that logs validation accuracy under another name and at another spacing, a
config that a later run supersedes, an out-of-memory crash, an unpaired tokenizer seed, an egnn
arm that overfits and a NaN in the middle of a validation loss."""

import json
import math
import os
import random
import shutil
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from beamtime.format.io import write_replaced
from beamtime.format.tree import is_run, iter_runs
from beamtime.synth.generate import BEST_LR, LRS, SCALES, Generator, Manifest, RunSpec

RECORD = ("proposal", "notes", "memory")
SECOND_BATCH = "scaling/lr-sweep-2"
SECOND_SEEDS = (3, 4)
RENAMED = "val/accuracy"
SECOND_VAL_EVERY = 100
SUPERSEDED = {"lr": 1e-3, "seed": 1, "final": 0.975}
OOM = {"lr": 3e-3, "seed": 4}
OOM_ERROR = (
    "torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB "
    "(GPU 0; 39.39 GiB total capacity)"
)
NAN_EGNN = {"call": 2, "step": 300}
# the egnn arms are generated small, medium, large with three seeds each; calls 7-9 are large.
OVERFIT = {"calls": (7, 8, 9), "onset": 0.6, "rise": 4.0}


class BenchGenerator(Generator):
    """The synth generator with the benchmark's messier data planted on top.

    Planted runs draw from a random stream of their own, so the synth's runs keep their values."""

    def __init__(self, *, logdir: Path, seed: int, now: datetime) -> None:
        """Set up a generator at scale ``s``.

        :param logdir: The log dir to write into.
        :param seed: The random seed; equal seeds give identical metrics.
        :param now: The wall-clock time heartbeats are judged against."""
        super().__init__(logdir=logdir, seed=seed, scale=SCALES["s"], now=now)
        self.planted = random.Random(seed + 1000)
        self.lightning_calls = 0
        self.nan_pending = False

    def lr_sweep(self) -> None:
        """Write a superseded early run, the synth's sweep, then the sweep's second batch."""
        folder = self.logdir / "scaling" / "lr-sweep"
        lr, seed, final = SUPERSEDED["lr"], SUPERSEDED["seed"], SUPERSEDED["final"]
        with self.own_stream(self.clock - timedelta(days=1)):
            rows = self.curves(self.scale.steps, lr=lr, final_acc=final)
            spec = self.sweep_spec(folder, lr, seed, {}, rows, final_acc=final)
            self.manifest.roles["superseded"] = self.write_run(spec)
        super().lr_sweep()
        with self.own_stream(self.clock + timedelta(days=1)):
            self.second_batch()

    def second_batch(self) -> None:
        """Write ``scaling/lr-sweep-2``: seeds 3 and 4 per lr after a refactor that renamed
        ``val/acc`` and evaluates every 100 steps; one run crashes out of memory and is rerun."""
        folder = self.logdir / SECOND_BATCH
        for lr in LRS:
            for seed in SECOND_SEEDS:
                final = 0.93 - 0.04 * math.log10(lr / BEST_LR) ** 2 + self.rng.gauss(0, 0.003)
                config = {"lr": lr, "seed": seed, "model": "resnet18"}
                if (lr, seed) == (OOM["lr"], OOM["seed"]):
                    rows = self.renamed_curves(self.scale.steps, lr=lr, final_acc=final)
                    spec = self.spec(folder, config, rows[: self.scale.steps * 15 // 100], "failed")
                    spec.error = OOM_ERROR
                    spec.tags = ["resnet18", "cifar10"]
                    self.manifest.roles["oom"] = self.write_run(spec)
                rows = self.renamed_curves(self.scale.steps, lr=lr, final_acc=final)
                spec = self.spec(folder, config, rows)
                spec.tags = ["resnet18", "cifar10"]
                run_id = self.write_run(spec)
                if (lr, seed) == (OOM["lr"], OOM["seed"]):
                    self.manifest.roles["oom_rerun"] = run_id
                if (lr, seed) == (BEST_LR, 3):
                    self.manifest.roles["killed_rerun"] = run_id

    def renamed_curves(self, steps: int, *, lr: float, final_acc: float) -> list[dict[str, Any]]:
        """Make classifier records as the refactored script logs them.

        :param steps: Number of steps.
        :param lr: Peak learning rate.
        :param final_acc: The accuracy the run approaches.
        :return: The records, with ``val/accuracy`` every 100 steps and at the last step."""
        rows = self.curves(steps, lr=lr, final_acc=final_acc)
        for row in rows:
            if (acc := row.pop("val/acc", None)) is not None and (
                row["_step"] % SECOND_VAL_EVERY == 0 or row["_step"] == steps - 1
            ):
                row[RENAMED] = acc
        return rows

    def tokenizer(self) -> None:
        """Write the synth's tokenizer comparison, then a seed 3 whose unigram run was killed."""
        super().tokenizer()
        folder = self.logdir / "tokenizer" / "bpe-vs-unigram"
        with self.own_stream(self.clock):
            for tok in ("bpe", "unigram"):
                floor = 12.0 - (0.4 if tok == "unigram" else 0.0) + self.rng.gauss(0, 0.05)
                rows = self.ppl_curves(self.scale.steps, floor=floor)
                killed = tok == "unigram"
                status = "killed" if killed else "finished"
                cut = rows[: self.scale.steps // 2] if killed else rows
                spec = self.spec(folder, {"tokenizer": tok, "seed": 3}, cut, status)
                spec.tags = ["lm", tok]
                if killed:
                    spec.signal = "SIGTERM"
                run_id = self.write_run(spec)
                self.manifest.roles["unpaired_killed" if killed else "unpaired"] = run_id

    def lightning_curves(self, steps: int, *, lr: float, quality: float) -> list[dict[str, Any]]:
        """Make Lightning records; the egnn ``large`` arm overfits (its validation loss rises
        late in training), and one egnn run's validation loss is NaN at one evaluation.

        :param steps: Number of steps.
        :param lr: Peak learning rate.
        :param quality: Higher is better.
        :return: The metric records."""
        rows = super().lightning_curves(steps, lr=lr, quality=quality)
        self.lightning_calls += 1
        if self.lightning_calls in OVERFIT["calls"]:
            for row in rows:
                if (
                    "validation/loss" in row
                    and (late := row["_step"] / steps - OVERFIT["onset"]) > 0
                ):
                    row["validation/loss"] = round(
                        row["validation/loss"] + OVERFIT["rise"] * late**2, 6
                    )
        if self.lightning_calls == NAN_EGNN["call"]:
            row = next(r for r in rows if r["_step"] == NAN_EGNN["step"])
            row["validation/loss"] = math.nan
            self.nan_pending = True
        return rows

    def write_run(self, spec: RunSpec) -> str:
        """Write a run directory and note the run that got the NaN validation loss.

        :param spec: The run description.
        :return: The run id."""
        run_id = super().write_run(spec)
        if self.nan_pending:
            self.manifest.roles["nan_loss"] = run_id
            self.nan_pending = False
        return run_id

    @contextmanager
    def own_stream(self, start: datetime) -> Iterator[None]:
        """Write planted runs from their own random stream, starting at a given time.

        :param start: The clock of the first planted run.
        :return: A context; afterwards the synth's stream continues where it was, and the clock
            at the later of the two."""
        rng, clock = self.rng, self.clock
        self.rng, self.clock = self.planted, start
        try:
            yield
        finally:
            self.rng, self.clock = rng, max(clock, self.clock)


def make_logdir(dest: Path, *, seed: int, now: datetime) -> Manifest:
    """Generate the benchmark's log dir at ``dest/beamtime`` and strip everything that states
    answers.

    :param dest: The folder that will hold ``beamtime/``.
    :param seed: The data seed.
    :param now: The time heartbeats are judged against; equal inputs give equal metrics.
    :return: The manifest; its roles stay in memory for grading, never written into ``dest``."""
    logdir = dest / "beamtime"
    logdir.mkdir(parents=True, exist_ok=True)
    gen = BenchGenerator(logdir=logdir, seed=seed, now=now)
    gen.run()
    strip_record(logdir)
    return gen.manifest


def strip_record(logdir: Path) -> None:
    """Delete the research record and clear every run's proposals.

    :param logdir: The log dir."""
    (logdir / "_synth.json").unlink(missing_ok=True)
    remove_record(logdir)
    for run in iter_runs(logdir):
        card = run / "_run.json"
        stat = card.stat()
        data = json.loads(card.read_text())
        data["proposals"] = {}
        data["proposal_hashes"] = {}
        write_replaced(card, data)
        # the heartbeat is the file's mtime; the rewrite must not make a lost run look alive.
        os.utime(card, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def remove_record(folder: Path) -> None:
    """Delete the ``proposal``, ``notes`` and ``memory`` folders below a folder, outside of runs.

    :param folder: A log dir or a group."""
    for child in sorted(folder.iterdir()):
        if not child.is_dir() or is_run(child):
            continue
        if child.name in RECORD:
            shutil.rmtree(child)
        else:
            remove_record(child)
