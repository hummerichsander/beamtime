"""Generate synthetic runs: 200 unique runs, M as hardlinks, one 10M-step run and a 10k-run table."""

from multiprocessing import Pool
import json
import os
import shutil

import numpy as np
import orjson

from common import L1_DIR, L1_STEPS, N_RUNS, N_STEPS, N_UNIQUE, RUNS, STEP_KEYS, TABLE, VAL_KEYS


def curves(rng: np.random.Generator, s: np.ndarray, keys: list[str]) -> tuple[dict, list]:
    """Make noisy decaying curves for some keys; loss gets upward spikes, acc downward ones.

    :param rng: Random generator.
    :param s: Steps.
    :param keys: Keys to generate.
    :return: (key -> values, spikes as [key, step, value])."""
    n, span = len(s), s[-1] + 1
    out, spikes = {}, []
    for i, k in enumerate(keys):
        tau = span * rng.uniform(0.1, 0.5)
        if "acc" in k or k in ("val/f1", "val/auc", "val/precision", "val/recall", "gpu/util"):
            v = 1 - 0.9 * np.exp(-s / tau) + 0.02 * rng.standard_normal(n)
        elif k == "lr":
            v = 3e-4 * 0.5 * (1 + np.cos(np.pi * s / span))
        else:
            v = (rng.uniform(1, 5) * np.exp(-s / tau) + rng.uniform(0.1, 1)) * (1 + 0.05 * rng.standard_normal(n))
        v = v.astype(np.float32).astype(np.float64)  # values typically come from float32 tensors.
        if k in ("train/loss", "train/acc"):
            n_spikes = max(6, n // 100_000)
            pos = rng.choice(n, n_spikes, replace=False)
            v[pos] = v[pos] * rng.uniform(3, 10, n_spikes) if k == "train/loss" else rng.uniform(0.0, 0.1, n_spikes)
            spikes += [[k, int(s[p]), float(v[p])] for p in pos]
        out[k] = v.tolist()
    return out, spikes


def write_run(i: int) -> None:
    """Write metrics.jsonl and spikes.json of unique run i.

    :param i: Run index."""
    rng = np.random.default_rng(i)
    d = RUNS / f"run_{i:04d}"
    d.mkdir(parents=True, exist_ok=True)
    s = np.arange(N_STEPS)
    t = (1761300000.0 + i * 1e4 + np.cumsum(rng.uniform(0.2, 0.3, N_STEPS))).tolist()
    tr, sp = curves(rng, s, STEP_KEYS)
    va, sp2 = curves(rng, s[::100], VAL_KEYS)
    with (d / "metrics.jsonl").open("wb") as f:
        for j in range(N_STEPS):
            row = {"_step": j, "_t": t[j]} | {k: tr[k][j] for k in STEP_KEYS}
            if j % 100 == 0:
                row |= {k: va[k][j // 100] for k in VAL_KEYS}
            f.write(orjson.dumps(row) + b"\n")
    (d / "spikes.json").write_text(json.dumps(sp + sp2))


def write_l1() -> None:
    """Write the single 10M-step run with 3 keys in chunks."""
    rng = np.random.default_rng(12345)
    L1_DIR.mkdir(parents=True, exist_ok=True)
    s = np.arange(L1_STEPS)
    t = (1761300000.0 + np.cumsum(rng.uniform(0.2, 0.3, L1_STEPS))).tolist()
    v, spikes = curves(rng, s, ["train/loss", "lr", "train/grad_norm"])
    with (L1_DIR / "metrics.jsonl").open("wb") as f:
        for j in range(L1_STEPS):
            f.write(orjson.dumps({"_step": j, "_t": t[j], "train/loss": v["train/loss"][j], "lr": v["lr"][j],
                                  "train/grad_norm": v["train/grad_norm"][j]}) + b"\n")
    (L1_DIR / "spikes.json").write_text(json.dumps(spikes))


def write_table(n: int = 10_000) -> None:
    """Write n synthetic run folders with run.json, config.json and summary.json.

    :param n: Number of runs."""
    rng = np.random.default_rng(7)
    for i in range(n):
        d = TABLE / f"run_{i:05d}"
        d.mkdir(parents=True, exist_ok=True)
        run = {"id": f"r{i:05d}", "name": f"sweep{i // 100}-{i % 100}", "status": str(rng.choice(["finished", "running", "failed", "lost"])),
               "created": 1761300000.0 + i * 60, "folder": f"beamtime/dir{i // 500}/sweep{i // 100}", "hypothesis": "Lower lr improves val loss."}
        config = {"lr": float(rng.choice([1e-4, 3e-4, 1e-3, 3e-3])), "batch_size": int(rng.choice([32, 64, 128, 256])),
                  "optimizer": str(rng.choice(["adam", "sgd", "lion"])), "model": {"depth": int(rng.integers(2, 24)), "width": int(rng.choice([256, 512, 1024]))},
                  "seed": i, "dropout": float(rng.uniform(0, 0.3))}
        summary = {"train/loss": float(rng.uniform(0.1, 3)), "val/loss": float(rng.uniform(0.1, 3)), "val/acc": float(rng.uniform(0.5, 1)), "_step": 10_000, "_runtime": float(rng.uniform(100, 1e5))}
        for name, obj in [("run.json", run), ("config.json", config), ("summary.json", summary)]:
            (d / name).write_text(json.dumps(obj, indent=2))


def main() -> None:
    """Generate all data."""
    with Pool(8) as p:
        p.map(write_run, range(N_UNIQUE))
    for i in range(N_UNIQUE, N_RUNS["M"]):
        d = RUNS / f"run_{i:04d}"
        d.mkdir(parents=True, exist_ok=True)
        for name in ("metrics.jsonl", "spikes.json"):
            if not (d / name).exists():
                os.link(RUNS / f"run_{i % N_UNIQUE:04d}" / name, d / name)
    write_table()
    write_l1()


if __name__ == "__main__":
    shutil.rmtree(RUNS, ignore_errors=True)
    main()
