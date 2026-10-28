"""Write a synthetic log dir with planted effects, driven by a seed."""

import math
import os
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import yaml

from beamtime.format import constants as c
from beamtime.format.authored import file_hash
from beamtime.format.ids import new_run_id, new_version_id
from beamtime.format.io import json_line, write_created, write_replaced
from beamtime.format.names import random_name
from beamtime.format.png import encode_png
from beamtime.format.run import merge_attempts
from beamtime.synth.summary import card_and_preview

BASE_TIME = datetime(2026, 10, 20, 8, 0, 0, tzinfo=timezone.utc)
LRS = (3e-5, 1e-4, 3e-4, 1e-3, 3e-3)
BEST_LR = 3e-4
TOKENIZER_PPL_GAP = 0.4


@dataclass(kw_only=True, frozen=True)
class Scale:
    """How large a generated log dir is."""

    name: str
    seeds: int
    steps: int
    val_every: int


SCALES = {
    "s": Scale(name="s", seeds=3, steps=2000, val_every=50),
    "m": Scale(name="m", seeds=70, steps=20000, val_every=200),
}


@dataclass(kw_only=True)
class Manifest:
    """What was generated: the runs by role and the planted effects."""

    seed: int
    scale: str
    runs: int = 0
    roles: dict[str, str] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    effects: list[dict[str, Any]] = field(default_factory=list)


@dataclass(kw_only=True)
class Attempt:
    """One attempt of a synthetic run: its resume step and metric records."""

    resume_step: int | None
    rows: list[dict[str, Any]]


@dataclass(kw_only=True)
class RunSpec:
    """Everything needed to write one synthetic run."""

    folder: Path
    config: dict[str, Any]
    attempts: list[Attempt]
    status: c.RunStatus
    start: datetime
    tags: list[str] = field(default_factory=list)
    proposals: dict[str, str] = field(default_factory=dict)
    error: str | None = None
    signal: str | None = None
    data: list[dict[str, Any]] = field(default_factory=list)
    files: dict[str, bytes] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)
    heartbeat_age_s: float = 0.0


def iso(t: datetime) -> str:
    """Format a time as ISO 8601 UTC with milliseconds.

    :param t: The time.
    :return: E.g. ``2026-10-24T10:15:32.104Z``."""
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def png(rng: random.Random, size: int = 16) -> bytes:
    """Make a small random grayscale PNG.

    :param rng: The random source.
    :param size: Width and height in pixels.
    :return: The PNG file."""
    return encode_png(size, size, 1, bytes(rng.randrange(256) for _ in range(size**2)))


class Generator:
    """Writes the synthetic log dir; one instance per call of ``generate``."""

    def __init__(self, *, logdir: Path, seed: int, scale: Scale, now: datetime) -> None:
        """Set up a generator.

        :param logdir: The log dir to write into.
        :param seed: The random seed; equal seeds give identical files.
        :param scale: The size of the log dir.
        :param now: The wall-clock time heartbeats are judged against."""
        self.logdir = logdir
        self.scale = scale
        self.now = now
        self.rng = random.Random(seed)
        self.clock = BASE_TIME
        self.host = 0
        self.hashes: dict[str, str] = {}
        self.manifest = Manifest(seed=seed, scale=scale.name)

    def run(self) -> None:
        """Write every group, run and authored file."""
        self.lr_sweep()
        self.long_context()
        self.tokenizer()
        self.record()
        self.write_md(
            self.logdir / c.MEMORY,
            {"covers_until": iso(self.clock), "author": "synth", "user": "synth"},
            "# Project memory\n\n- lr 3e-4 is best for the resnet sweep.\n"
            "- unigram beats bpe on validation perplexity.\n",
        )

    def lr_sweep(self) -> None:
        """Write ``scaling/lr-sweep``: a best lr, a diverging and a killed run."""
        folder = self.logdir / "scaling" / "lr-sweep"
        proposal = self.write_yaml(
            folder / c.PROPOSAL,
            {
                "statement": f"lr {BEST_LR:g} gives the best final val/acc.",
                "rationale": "Low rates underfit; high ones are unstable.",
                "confidence": 0.6,
                "plan": {"grid": {"config.lr": list(LRS), "config.seed": list(range(3))}},
                "predictions": [
                    {
                        "name": "converges",
                        "where": {"config.lr": BEST_LR},
                        "reduce": {"metric": "val/acc", "stat": "last"},
                        "seeds": "config.seed",
                        "op": ">",
                        "value": 0.9,
                    },
                    {
                        "name": "mid-beats-high",
                        "reduce": {"metric": "val/acc", "stat": "last"},
                        "seeds": "config.seed",
                        "test": "compare",
                        "a": {"config.lr": BEST_LR},
                        "b": {"config.lr": 3e-3},
                        "op": ">",
                        "margin": 0.01,
                    },
                ],
                "author": "synth",
                "user": "synth",
            },
        )
        member = {"scaling/lr-sweep": proposal}
        for lr in LRS:
            for seed in range(self.scale.seeds):
                final = 0.93 - 0.04 * math.log10(lr / BEST_LR) ** 2
                final += self.rng.gauss(0, 0.003)
                rows = self.curves(self.scale.steps, lr=lr, final_acc=final)
                self.write_run(self.sweep_spec(folder, lr, seed, member, rows, final_acc=final))
        self.manifest.roles["diverging"] = self.write_run(self.diverging(folder, member))
        self.manifest.roles["killed"] = self.write_run(self.killed(folder, member))
        diverging = self.manifest.roles["diverging"]
        self.write_md(
            folder / c.NOTES,
            {
                "type": "observation",
                "description": "lr 1e-2 diverges after about 30 % of training.",
                "evidence": [diverging],
                "author": "synth",
                "user": "synth",
            },
            f"The loss of [[{diverging}]] grows, then turns NaN.\n",
        )

    def record(self) -> None:
        """Write the research record after the runs: a verdict, a question with its
        answer, and a decision that completes the plan-less long-context proposal."""
        sweep = self.logdir / "scaling" / "lr-sweep"
        version = (sweep / c.PROPOSAL).iterdir().__next__().stem
        killed = self.manifest.roles["killed"]
        self.manifest.notes["verdict"] = self.write_md(
            sweep / c.NOTES,
            {
                "description": f"lr {BEST_LR:g} is best; high rates lose about 4 points.",
                "type": "verdict",
                "proposal": version,
                "verdicts": {"converges": "confirmed", "mid-beats-high": "confirmed"},
                "overall": "confirmed",
                "check": {
                    "converges": {
                        "result": "pass",
                        "effect": 0.029,
                        "ci": [0.012, 0.045],
                        "points": 1,
                    },
                    "mid-beats-high": {
                        "result": "pass",
                        "effect": 0.04,
                        "ci": [0.025, 0.054],
                        "points": 6,
                    },
                },  # fmt: skip
                "evidence": [{"prediction": "scaling/lr-sweep#mid-beats-high"}],
                "author": "synth",
                "user": "synth",
            },
            "Both predictions hold; see [[scaling/lr-sweep#converges]]. The killed run "
            f"[[{killed}]] is not counted.\n",
        )
        tok = self.logdir / "tokenizer" / "bpe-vs-unigram"
        question = self.write_md(
            tok / c.NOTES,
            {
                "description": "Does the unigram gain hold with a larger vocabulary?",
                "type": "question",
                "author": "synth",
                "user": "synth",
            },
            "The sweep used one vocabulary size.\n",
        )
        self.manifest.notes["question"] = question
        self.manifest.notes["open_question"] = self.write_md(
            tok / c.NOTES,
            {
                "description": "Is the gain the same for code?",
                "type": "question",
                "author": "synth",
                "user": "synth",
            },
            "",
        )
        self.manifest.notes["answer"] = self.write_md(
            tok / c.NOTES,
            {
                "description": "A 64k vocabulary keeps the gain within noise.",
                "type": "observation",
                "resolves": [question],
                "author": "synth",
                "user": "synth",
            },
            f"Answers [[{question}]].\n",
        )
        self.manifest.notes["decision"] = self.write_md(
            self.logdir / "scaling" / "long-context" / c.NOTES,
            {
                "description": "Long context is explored enough; resume support works.",
                "type": "decision",
                "completes": ["scaling/long-context"],
                "author": "synth",
                "user": "synth",
            },
            "",
        )

    def long_context(self) -> None:
        """Write ``scaling/long-context``: a resumed, a lost and a running run."""
        folder = self.logdir / "scaling" / "long-context"
        proposal = self.write_yaml(
            folder / c.PROPOSAL,
            {
                "statement": "Resumed runs continue where they stopped.",
                "author": "synth",
                "user": "synth",
            },
        )
        member = {"scaling/long-context": proposal}
        steps = self.scale.steps
        rows = self.curves(steps, lr=BEST_LR, final_acc=0.91)
        cut, resume = int(steps * 0.6), int(steps * 0.5)
        first = Attempt(resume_step=None, rows=rows[: cut + 1])
        redo = self.curves(steps, lr=BEST_LR, final_acc=0.91)[resume:]
        # the requeued job starts two minutes after the first attempt ends.
        shift = first.rows[-1]["_t"] + 120.0 - redo[0]["_t"]
        for row in redo:
            row["_t"] = round(row["_t"] + shift, 3)
        second = Attempt(resume_step=resume, rows=redo)
        spec = self.spec(folder, {"lr": BEST_LR, "context": 4096}, [first, second])
        spec.signal = "SIGUSR1"
        spec.proposals = member
        self.manifest.roles["resumed"] = self.write_run(spec)

        rows = self.curves(steps, lr=BEST_LR, final_acc=0.9)[: steps // 3]
        spec = self.spec(folder, {"lr": BEST_LR, "context": 8192}, rows, "running")
        spec.heartbeat_age_s = 3600.0
        spec.proposals = member
        self.manifest.roles["lost"] = self.write_run(spec)

        rows = self.curves(steps, lr=BEST_LR, final_acc=0.9)[: steps // 2]
        spec = self.spec(folder, {"lr": BEST_LR, "context": 16384}, rows, "running")
        spec.proposals = member
        self.manifest.roles["running"] = self.write_run(spec)

    def tokenizer(self) -> None:
        """Write ``tokenizer/bpe-vs-unigram`` with unigram's planted perplexity gain."""
        folder = self.logdir / "tokenizer" / "bpe-vs-unigram"
        proposal = self.write_yaml(
            folder / c.PROPOSAL,
            {
                "statement": "Unigram lowers validation perplexity compared with BPE.",
                "plan": {
                    "grid": {
                        "config.tokenizer": ["bpe", "unigram"],
                        "config.seed": list(range(3)),
                    }
                },
                "predictions": [
                    {
                        "name": "unigram-wins",
                        "reduce": {"metric": "val/ppl", "stat": "last"},
                        "seeds": "config.seed",
                        "test": "compare",
                        "a": {"config.tokenizer": "unigram"},
                        "b": {"config.tokenizer": "bpe"},
                        "op": "<",
                        "margin": 0.1,
                    }
                ],
                "author": "synth",
                "user": "synth",
            },
        )
        for tok in ("bpe", "unigram"):
            for seed in range(self.scale.seeds):
                floor = 12.0 - (TOKENIZER_PPL_GAP if tok == "unigram" else 0.0)
                floor += self.rng.gauss(0, 0.05)
                rows = self.ppl_curves(self.scale.steps, floor=floor)
                spec = self.spec(folder, {"tokenizer": tok, "seed": seed}, rows)
                spec.proposals = {"tokenizer/bpe-vs-unigram": proposal}
                spec.tags = ["lm", tok]
                spec.data = [self.text_entry(rows[-1]["_step"], tok)]
                self.write_run(spec)

    def curves(self, steps: int, *, lr: float, final_acc: float) -> list[dict[str, Any]]:
        """Make classifier records: train/loss and lr every step, val/acc periodically.

        :param steps: Number of steps.
        :param lr: Peak learning rate; lower rates converge slower.
        :param final_acc: The accuracy the run approaches.
        :return: The metric records."""
        tau = steps * 0.15 * (BEST_LR / lr) ** 0.3
        floor = 0.2 + 2.0 * (1 - final_acc)
        t = self.clock.timestamp()
        rows = []
        for s in range(steps):
            t += 0.2 + 0.1 * self.rng.random()
            decay = math.exp(-s / tau)
            row: dict[str, Any] = {
                "_step": s,
                "_t": round(t, 3),
                "train/loss": round(
                    ((2.3 - floor) * decay + floor) * (1 + 0.03 * self.rng.gauss(0, 1)),
                    6,
                ),
                "lr": round(lr * 0.5 * (1 + math.cos(math.pi * s / steps)), 9),
            }
            if s % self.scale.val_every == 0 or s == steps - 1:
                acc = final_acc - (final_acc - 0.1) * decay + self.rng.gauss(0, 0.003)
                row["val/acc"] = round(acc, 6)
            rows.append(row)
        return rows

    def ppl_curves(self, steps: int, *, floor: float) -> list[dict[str, Any]]:
        """Make language-model records: train/loss every step, val/ppl periodically.

        :param steps: Number of steps.
        :param floor: The perplexity the run approaches.
        :return: The metric records."""
        t = self.clock.timestamp()
        rows = []
        for s in range(steps):
            t += 0.3 + 0.1 * self.rng.random()
            decay = math.exp(-s / (steps * 0.2))
            ppl = floor + 40.0 * decay
            row: dict[str, Any] = {
                "_step": s,
                "_t": round(t, 3),
                "train/loss": round(math.log(ppl) + 0.02 * self.rng.gauss(0, 1), 6),
            }
            if s % self.scale.val_every == 0 or s == steps - 1:
                row["val/ppl"] = round(ppl + 0.05 * self.rng.gauss(0, 1), 6)
            rows.append(row)
        return rows

    def sweep_spec(
        self,
        folder: Path,
        lr: float,
        seed: int,
        member: dict[str, str],
        rows: list[dict[str, Any]],
        *,
        final_acc: float,
    ) -> RunSpec:
        """Describe a finished sweep run with tables, images, text and an artifact.

        :param folder: The sweep folder.
        :param lr: The run's learning rate.
        :param seed: The run's seed.
        :param member: The proposal versions the run records.
        :param rows: The metric records.
        :param final_acc: The planted final accuracy, for the per-class table.
        :return: The run description."""
        last = rows[-1]["_step"]
        spec = self.spec(folder, {"lr": lr, "seed": seed, "model": "resnet18"}, rows)
        spec.proposals = member
        spec.tags = ["resnet18", "cifar10"]
        spec.values = {"test/acc": round(final_acc - 0.002, 4)}
        classes = [f"class{i}" for i in range(10)]
        spec.data = [
            {
                "_step": last,
                "key": "val/per_class",
                "kind": "table",
                "columns": {
                    "class": classes,
                    "acc": [
                        round(min(1.0, final_acc + self.rng.gauss(0, 0.02)), 4) for _ in classes
                    ],
                },
            },
            *(self.histogram(step) for step in (0, last)),
            *(self.image(spec, step) for step in (0, last)),
            self.text_entry(last, "resnet"),
        ]
        spec.files["artifacts/model-summary.txt"] = b"resnet18: 11.2M parameters\n"
        return spec

    def diverging(self, folder: Path, member: dict[str, str]) -> RunSpec:
        """Describe a run whose loss blows up to NaN and Infinity, then fails.

        :param folder: The sweep folder.
        :param member: The proposal versions the run records.
        :return: The run description."""
        steps = self.scale.steps
        rows = self.curves(steps, lr=1e-2, final_acc=0.8)
        start = int(steps * 0.3)
        rows = rows[: start + 60]
        for i, row in enumerate(rows[start:]):
            row["train/loss"] = round(row["train/loss"] * math.exp(i / 8), 6)
            if i >= 50:
                row["train/loss"] = math.nan if i < 59 else math.inf
        spec = self.spec(folder, {"lr": 1e-2, "seed": 0, "model": "resnet18"}, rows, "failed")
        spec.proposals = member
        spec.error = "FloatingPointError: train/loss is inf"
        return spec

    def killed(self, folder: Path, member: dict[str, str]) -> RunSpec:
        """Describe a run killed by the scheduler at 40 % of training.

        :param folder: The sweep folder.
        :param member: The proposal versions the run records.
        :return: The run description."""
        rows = self.curves(self.scale.steps, lr=BEST_LR, final_acc=0.93)
        rows = rows[: int(self.scale.steps * 0.4)]
        spec = self.spec(folder, {"lr": BEST_LR, "seed": 3, "model": "resnet18"}, rows, "killed")
        spec.proposals = member
        spec.signal = "SIGTERM"
        return spec

    def spec(
        self,
        folder: Path,
        config: dict[str, Any],
        rows: list[dict[str, Any]] | list[Attempt],
        status: c.RunStatus = "finished",
    ) -> RunSpec:
        """Start a run description at the generator's clock.

        :param folder: The folder the run goes into.
        :param config: The run's hyperparameters.
        :param rows: The metric records, or the attempts of a resumed run.
        :param status: The run status.
        :return: The run description."""
        attempts = (
            rows
            if rows and isinstance(rows[0], Attempt)
            else [Attempt(resume_step=None, rows=rows)]
        )
        return RunSpec(
            folder=folder,
            config=config,
            attempts=attempts,
            status=status,
            start=self.clock,
        )

    def histogram(self, step: int) -> dict[str, Any]:
        """Make a histogram entry: a table with bin edges and counts.

        :param step: The step it is logged at.
        :return: The ``_data.jsonl`` record."""
        edges = [round(-1 + 0.25 * i, 2) for i in range(9)]
        counts = [int(abs(self.rng.gauss(0, 1)) * 100) for _ in range(8)]
        return {
            "_step": step,
            "key": "grads/layer3",
            "kind": "table",
            "columns": {"bin_start": edges[:-1], "bin_end": edges[1:], "count": counts},
        }

    def image(self, spec: RunSpec, step: int) -> dict[str, Any]:
        """Make an image entry and queue its PNG file.

        :param spec: The run description that receives the file.
        :param step: The step it is logged at.
        :return: The ``_data.jsonl`` record."""
        path = f"{c.DATA_DIR}/{c.key_to_path('samples')}/{step}.png"
        spec.files[path] = png(self.rng)
        return {"_step": step, "key": "samples", "kind": "image", "path": path}

    def text_entry(self, step: int, model: str) -> dict[str, Any]:
        """Make a text entry with a generated sample.

        :param step: The step it is logged at.
        :param model: Which model wrote it.
        :return: The ``_data.jsonl`` record."""
        words = ("the", "beam", "collides", "at", "high", "energy", "and", "decays")
        text = " ".join(self.rng.choice(words) for _ in range(12))
        return {
            "_step": step,
            "key": "samples/text",
            "kind": "text",
            "text": f"{model}: {text}",
        }

    def attempt_records(
        self, spec: RunSpec, host: str
    ) -> tuple[list[dict[str, Any]], bytes, list[dict[str, Any]]]:
        """Make the events, metric lines and ``_run.json`` attempts of every attempt.

        :param spec: The run description.
        :param host: The run's host name.
        :return: The events so far, the ``_metrics.jsonl`` bytes and the attempts."""
        events: list[dict[str, Any]] = []
        metrics = bytearray()
        attempts = []
        for a in spec.attempts:
            begin = spec.start.timestamp() if not events else a.rows[0]["_t"] - 1.0
            started = datetime.fromtimestamp(begin, timezone.utc)
            attempts.append(
                {"started_at": iso(started), "host": host, "resume_step": a.resume_step}
            )
            if not events:
                events.append({"_t": round(begin, 3), "kind": "created"})
            events.append(
                {
                    "_t": round(begin, 3),
                    "kind": "attempt_started",
                    "resume_step": a.resume_step,
                    "metrics_offset": len(metrics),
                }
            )
            metrics += b"".join(json_line(r) for r in a.rows)
            if a is not spec.attempts[-1]:
                events.append(
                    {
                        "_t": a.rows[-1]["_t"],
                        "_step": a.rows[-1]["_step"],
                        "kind": "requeue_requested",
                        "signal": spec.signal,
                    }
                )
        return events, bytes(metrics), attempts

    def ending(
        self, spec: RunSpec, end_t: float, last_step: int | None
    ) -> tuple[dict[str, Any] | None, str]:
        """Make the final event and the last output lines for the run's status.

        :param spec: The run description.
        :param end_t: When the run ended.
        :param last_step: The last logged step.
        :return: The final event (none while running) and the output it printed."""
        end = {"_t": end_t, "_step": last_step, "kind": spec.status}
        match spec.status:
            case "finished":
                return end, "done\n"
            case "failed":
                tb = (
                    "Traceback (most recent call last):\n"
                    '  File "train.py", line 88, in <module>\n'
                    "    check_finite(loss)\n"
                    f"{spec.error}\n"
                )
                return end | {"traceback": tb}, tb
            case "killed":
                cancelled = f"slurmstepd: *** JOB CANCELLED ({spec.signal}) ***\n"
                return end | {"signal": spec.signal}, cancelled
            case "running":
                return None, ""
            case _:
                raise ValueError(f"unknown status {spec.status!r}")

    def artifacts(self, spec: RunSpec, run_id: str) -> list[dict[str, Any]]:
        """List the run's copied artifacts and, for finished runs, a referenced one.

        :param spec: The run description.
        :param run_id: The run id.
        :return: The ``_artifacts.jsonl`` records."""
        records = [
            {"name": Path(rel).name, "path": rel, "size": len(data), "kind": "summary"}
            for rel, data in spec.files.items()
            if rel.startswith("artifacts/")
        ]
        if spec.status == "finished":
            records.append(
                {
                    "name": "final.ckpt",
                    "uri": f"/scratch/synth/ckpt/{run_id}/final.ckpt",
                    "size": 47185920,
                    "kind": "checkpoint",
                }
            )
        return records

    def write_run(self, spec: RunSpec) -> str:
        """Write a run directory with every machine-written file.

        :param spec: The run description.
        :return: The run id."""
        run_id = new_run_id(now=spec.start, rng=self.rng)
        d = spec.folder / run_id
        d.mkdir(parents=True)
        self.host += 1
        host = f"gpu{self.host % 64:03d}"
        job = f"88123{self.host:02d}"
        t0 = spec.start.timestamp()

        events, metrics, attempts = self.attempt_records(spec, host)
        last = spec.attempts[-1].rows
        end_t = last[-1]["_t"] + 1.0 if last else t0
        end, last_output = self.ending(spec, end_t, last[-1]["_step"] if last else None)
        if end is not None:
            events.append(end)
        output = [f"[{host}] starting {spec.config}\n"]
        output += [
            f"step {r['_step']} loss {r['train/loss']}\n" for r in last[:: max(1, len(last) // 20)]
        ]
        output.append(last_output)

        info = {
            "schema": 1,
            "id": run_id,
            "name": random_name(self.rng),
            "tags": spec.tags,
            "status": spec.status,
            "created_at": iso(spec.start),
            "ended_at": iso(datetime.fromtimestamp(end_t, timezone.utc))
            if end is not None
            else None,
            "exit": {"failed": {"code": 1}, "killed": {"signal": spec.signal}}.get(spec.status),
            "attempts": attempts,
            "proposals": spec.proposals,
            "proposal_hashes": {k: self.hashes[v] for k, v in spec.proposals.items()},
            "job_key": f"slurm:{job}",
            "host": {
                "hostname": host,
                "user": "synth",
                "os": "Linux",
                "python": "3.11",
            },
            "scheduler": {
                "kind": "slurm",
                "job_id": job,
                "partition": "gpu",
                "nodes": host,
            },
            "git": {"commit": "57878f1", "branch": "main", "dirty": False},
            "command": ["python", "train.py"] + [f"--{k}={v}" for k, v in spec.config.items()],
            "cwd": "/home/synth/proj",
            "beamtime_version": "synth",
        }
        effective = merge_attempts([(a.resume_step, a.rows) for a in spec.attempts])
        card, preview = card_and_preview(
            effective,
            status=spec.status,
            duration_s=end_t - t0,
            error=spec.error,
            values=spec.values,
        )
        data = [
            {"_step": e["_step"], "_t": round(t0 + e["_step"] * 0.25, 3)} | e for e in spec.data
        ]

        write_replaced(d / c.RUN, info)
        write_replaced(d / c.CONFIG, {"schema": 1, **spec.config})
        write_replaced(d / c.CARD, card)
        write_replaced(d / c.PREVIEW, preview)
        (d / c.METRICS).write_bytes(metrics)
        (d / c.EVENTS).write_bytes(b"".join(json_line(e) for e in events))
        (d / c.OUTPUT).write_bytes("".join(output).encode())
        if data:
            (d / c.DATA).write_bytes(b"".join(json_line(e) for e in data))
        for rel, content in spec.files.items():
            write_created(d / rel, content)
        if artifacts := self.artifacts(spec, run_id):
            (d / c.ARTIFACTS).write_bytes(b"".join(json_line(a) for a in artifacts))
        write_created(d / c.ENV_DIR / "packages.txt", b"torch==2.9.0\n")
        heartbeat = self.now.timestamp() - spec.heartbeat_age_s
        os.utime(d / c.RUN, (heartbeat, heartbeat))
        self.clock += timedelta(minutes=7)
        self.manifest.runs += 1
        return run_id

    def write_yaml(self, folder: Path, fields: dict[str, Any]) -> str:
        """Write a new version of a YAML authored file.

        :param folder: The authored folder, e.g. ``<group>/proposal``.
        :param fields: The fields after ``schema``.
        :return: The version id."""
        vid = new_version_id(now=self.clock, rng=self.rng)
        text = yaml.safe_dump({"schema": 1, **fields}, sort_keys=False)
        write_created(folder / f"{vid}.yaml", text.encode())
        self.hashes[vid] = file_hash(folder / f"{vid}.yaml")
        self.clock += timedelta(minutes=3)
        return vid

    def write_md(self, folder: Path, fields: dict[str, Any], body: str) -> str:
        """Write a new version of a Markdown authored file with frontmatter.

        :param folder: The authored folder, e.g. ``<group>/notes``.
        :param fields: The frontmatter fields after ``schema``.
        :param body: The Markdown body.
        :return: The version id."""
        vid = new_version_id(now=self.clock, rng=self.rng)
        front = yaml.safe_dump({"schema": 1, **fields}, sort_keys=False)
        write_created(folder / f"{vid}.md", f"---\n{front}---\n{body}".encode())
        self.clock += timedelta(minutes=3)
        return vid


def generate(
    logdir: Path,
    *,
    seed: int = 0,
    scale: Literal["s", "m"] = "s",
    now: datetime | None = None,
) -> Manifest:
    """Write a synthetic log dir with planted effects.

    :param logdir: The log dir; created if missing, and expected to be empty.
    :param seed: The random seed; equal seeds give byte-identical files.
    :param scale: ``s`` for tests (about 25 runs), ``m`` for benchmarks (about 500).
    :param now: The time heartbeats are judged against; defaults to the current time.
    :return: The manifest, also written to ``_synth.json``."""
    logdir.mkdir(parents=True, exist_ok=True)
    gen = Generator(
        logdir=logdir,
        seed=seed,
        scale=SCALES[scale],
        now=now or datetime.now(timezone.utc),
    )
    gen.run()
    gen.manifest.effects = [
        {
            "folder": "scaling/lr-sweep",
            "metric": "val/acc",
            "stat": "last",
            "best": {"config.lr": BEST_LR},
        },
        {
            "folder": "tokenizer/bpe-vs-unigram",
            "metric": "val/ppl",
            "stat": "last",
            "lower": {"config.tokenizer": "unigram"},
            "gap": TOKENIZER_PPL_GAP,
        },
    ]
    write_replaced(logdir / "_synth.json", {"schema": 1, **asdict(gen.manifest)})
    return gen.manifest
