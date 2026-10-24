"""Benchmark driver: python bench.py <build|query|ingest|oneshot> <cand> <scale>."""

from pathlib import Path
import json
import sys
import time

from common import (AGG_RUNS, AGG_WINDOW, CHART_KEY, CHART_RUNS, IDX, L1_KEYS, N_BUCKETS, N_STEPS, STEP_KEYS, VAL_KEYS,
                    ZOOM, dir_size, record, run_dirs, timeit)


class Cand:
    """Uniform handle on a candidate: build, ingest, chart and mean variants."""

    def __init__(self, *, name: str, idx: Path):
        self.name, self.idx = name, idx
        match name:
            case "A":
                import cand_a as m

                h = m.open_index(idx)
                self.build = lambda dirs: m.build(idx, dirs)
                self.ingest = lambda run: m.ingest(h, run)
                self.charts = {"levels": lambda *a: m.chart(h, *a)}
                self.means = {"levels": lambda *a: m.mean(h, *a), "jsonl-json": lambda *a: m.mean_jsonl(h, *a),
                              "jsonl-orjson": lambda *a: m.mean_jsonl(h, *a, loads=__import__("orjson").loads)}
            case "B" | "C" | "E":
                m = __import__(f"cand_{name.lower()}")
                h = m.open_index(idx)
                if name != "E":
                    self.build = lambda dirs: m.build(idx, dirs)
                    self.ingest = lambda run: m.ingest(h, run)
                self.charts = {"default": lambda *a: m.chart(h, *a)}
                self.means = {"default": lambda *a: m.mean(h, *a)}
                if name == "B":
                    self.charts["tsdownsample"] = lambda *a: m.chart_tsd(h, *a)
            case "D1" | "D2":
                import cand_d

                h = getattr(cand_d, name)(idx=idx)
                self.build = (lambda dirs: [h.ingest(r, d / "metrics.jsonl") for r, d in enumerate(dirs)]) if name == "D1" else h.build_all
                self.ingest = h.ingest
                self.charts = {"default": h.chart}
                self.means = {"default": h.mean}
            case _:
                raise ValueError(name)


def spike_misses(out: dict, runs: list[int], dirs: list[Path], lo: int, hi: int) -> tuple[int, int]:
    """Count train/loss spikes in [lo, hi] whose value is missing from the chart maxima.

    :return: (missed, total)."""
    missed = total = 0
    for r in runs:
        maxs = set(float(x) for x in out[r][2])
        for key, step, val in json.loads((dirs[r] / "spikes.json").read_text()):
            if key == CHART_KEY and lo <= step <= hi:
                total += 1
                missed += val not in maxs
    return missed, total


def query(c: Cand, scale: str) -> None:
    """Run W2/W4 (S, M) or W3 (L1) in this fresh process."""
    dirs = run_dirs(scale)
    if scale == "L1":
        windows = [(f"W3 zoom {k}", [0], lo, hi) for k, (lo, hi) in ZOOM.items()]
    else:
        windows = [("W2 chart", CHART_RUNS[scale], 0, N_STEPS - 1)]
    for wl, runs, lo, hi in windows:
        for var, fn in c.charts.items():
            out = fn(runs, CHART_KEY, lo, hi, N_BUCKETS)
            first, warm = timeit(lambda: fn(runs, CHART_KEY, lo, hi, N_BUCKETS))
            missed, total = spike_misses(out, runs, dirs, lo, hi)
            pts = sum(len(o[0]) for o in out.values())
            record(cand=c.name, scale=scale, workload=wl, variant=var, first_s=first, warm_s=warm,
                   points=pts, spikes_missed=missed, spikes_total=total)
    if scale != "L1":
        runs = AGG_RUNS[scale]
        for var, fn in c.means.items():
            first, warm = timeit(lambda: fn(runs, CHART_KEY, *AGG_WINDOW), repeat=3)
            vals = fn(runs, CHART_KEY, *AGG_WINDOW)
            record(cand=c.name, scale=scale, workload="W4 mean", variant=var, first_s=first, warm_s=warm,
                   n_runs=len(vals), checksum=round(sum(vals.values()), 6))


def ingest(c: Cand, scale: str) -> None:
    """W1b: append 1000 lines to run 0, time ingest + a chart query showing them, then restore the file."""
    path = run_dirs(scale)[0] / "metrics.jsonl"
    size = path.stat().st_size
    last = json.loads(path.read_bytes()[size - 2000:].split(b"\n")[-2])["_step"]
    keys = L1_KEYS if scale == "L1" else STEP_KEYS
    lines = []
    for s in range(last + 1, last + 1001):
        row = {"_step": s, "_t": 1.8e9 + s} | {k: 1.0 + s * 1e-9 for k in keys}
        if scale != "L1" and s % 100 == 0:
            row |= {k: 0.5 for k in VAL_KEYS}
        lines.append(json.dumps(row))
    try:
        with path.open("a") as f:
            f.write("\n".join(lines) + "\n")
        t = time.perf_counter()
        c.ingest(0)
        out = next(iter(c.charts.values()))([0], CHART_KEY, last - 9999, last + 1000, N_BUCKETS)
        dt = time.perf_counter() - t
        record(cand=c.name, scale=scale, workload="W1 incremental 1000 lines", first_s=dt, ok=len(out[0][0]) > 0)
    finally:
        with path.open("r+b") as f:
            f.truncate(size)


def main() -> None:
    """Dispatch on the phase."""
    phase, name, scale = sys.argv[1:4]
    idx = IDX / f"{'B' if name == 'E' else name}-{scale}"
    if phase == "build":
        t = time.perf_counter()
        c = Cand(name=name, idx=idx)
        c.build(run_dirs(scale))
        record(cand=name, scale=scale, workload="W1 full build", first_s=time.perf_counter() - t, index_bytes=dir_size(idx))
        return
    t = time.perf_counter()
    c = Cand(name=name, idx=idx)
    if phase == "query":
        record(cand=name, scale=scale, workload="open+imports", first_s=time.perf_counter() - t)
        query(c, scale)
    elif phase == "ingest":
        ingest(c, scale)
    elif phase == "oneshot":
        var = next(iter(c.charts.values()))
        out = var(CHART_RUNS[scale], CHART_KEY, 0, N_STEPS - 1, N_BUCKETS)
        print(sum(len(o[0]) for o in out.values()))


if __name__ == "__main__":
    main()
