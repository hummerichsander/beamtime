"""M2 benchmark: the implemented index and query layer against the layer-3 targets.

Usage: uv run python bench/index/m2.py <work dir>
Builds a scale-m log dir with the generator, a 10k-run table (card-only copies) and one
run with 10M steps, then times the workloads of docs/design/03-index.md."""

import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

from beamtime.format.io import json_line
from beamtime.index.daemon import Daemon
from beamtime.index.index import Index
from beamtime.query import run
from beamtime.synth import generate


def timed(fn, repeat: int = 5) -> tuple[float, float]:
    """Time the first call and the median of the following ones.

    :return: (first, median) in seconds."""
    t = time.perf_counter()
    fn()
    first = time.perf_counter() - t
    rest = []
    for _ in range(repeat):
        t = time.perf_counter()
        fn()
        rest.append(time.perf_counter() - t)
    return first, statistics.median(rest)


def one_shot(code: str, env: dict) -> float:
    """Time a fresh process running some code, best of five.

    :return: Seconds."""
    best = float("inf")
    for _ in range(5):
        t = time.perf_counter()
        subprocess.run([sys.executable, "-c", code], env=env, check=True)
        best = min(best, time.perf_counter() - t)
    return best


def table_logdir(src: Path, dst: Path, n: int) -> None:
    """Make n card-only runs from the generator's runs, for run tables.

    :param src: A generated log dir.
    :param dst: The new log dir.
    :param n: Number of runs."""
    runs = [p for p in src.rglob("_run.json")]
    for i in range(n):
        base = runs[i % len(runs)].parent
        run_id = f"20261101-{i // 3600:02d}{i // 60 % 60:02d}{i % 60:02d}-{i:08d}"
        d = dst / f"group{i % 20}" / run_id
        d.mkdir(parents=True)
        info = json.loads((base / "_run.json").read_text()) | {"id": run_id}
        (d / "_run.json").write_text(json.dumps(info))
        config = json.loads((base / "_config.json").read_text()) | {"i": i}
        (d / "_config.json").write_text(json.dumps(config))
        shutil.copy(base / "_run_card.json", d / "_run_card.json")


def long_run(logdir: Path, steps: int) -> Path:
    """Write one finished run with a long train/loss curve.

    :param logdir: The log dir.
    :param steps: Number of steps.
    :return: The run directory."""
    d = logdir / "long" / "20261101-000000-longrun0"
    d.mkdir(parents=True)
    (d / "_run.json").write_text(json.dumps({
        "schema": 1, "id": d.name, "name": "long", "status": "finished",
        "created_at": "2026-11-01T00:00:00.000Z", "attempts": [],
    }))  # fmt: skip
    (d / "_config.json").write_text('{"schema": 1}')
    with (d / "_metrics.jsonl").open("wb") as f:
        buf = []
        for s in range(steps):
            buf.append(json_line({"_step": s, "_t": 1.7e9 + s * 0.01, "train/loss": 1 / (1 + s)}))
            if len(buf) == 100_000:
                f.write(b"".join(buf))
                buf = []
        f.write(b"".join(buf))
    return d


def main() -> None:
    """Run every workload and print a results table."""
    work = Path(sys.argv[1]).resolve()
    shutil.rmtree(work, ignore_errors=True)
    os.environ["BEAMTIME_CACHE"] = str(work / "cache")
    env = dict(os.environ)
    results = []

    m = work / "m" / "beamtime"
    t = time.perf_counter()
    generate(m, seed=0, scale="m")
    print(f"generated scale m in {time.perf_counter() - t:.0f} s", flush=True)
    lines = sum(1 for p in m.rglob("_metrics.jsonl") for _ in p.open("rb"))
    index = Index(logdir=m)
    t = time.perf_counter()
    index.catch_up(".", budget_s=float("inf"))
    build = time.perf_counter() - t
    results.append(("Full build, scale m", f"{lines / 1e6:.1f}M lines, 495 runs", f"{build:.1f} s", "~1 min per 1e8 points"))

    q = {"series": {"from": "scaling/lr-sweep", "where": {"config.seed": {"lt": 10}},
                    "y": ["train/loss"], "points": 500}}  # fmt: skip
    first, warm = timed(lambda: run(q, logdir=m, index=index, caller="view"))
    n = run(q, logdir=m, index=index, caller="view")["meta"]
    results.append(("Chart from previews", f"{n['curves']} runs × 1 metric", f"{first * 1e3:.0f} / {warm * 1e3:.0f} ms", "< 100 ms"))
    qc = {"series": q["series"] | {"steps": [0, 10**9]}}
    first, warm = timed(lambda: run(qc, logdir=m, index=index, caller="view"))
    results.append(("Chart from columns", f"{n['curves']} runs × 1 metric, 20k steps each", f"{first * 1e3:.0f} / {warm * 1e3:.0f} ms", "< 100 ms"))

    agg = {"runs": {"from": ".", "select": ["metric.train/loss.mean[2000:7999]"], "limit": 1000}}
    first, warm = timed(lambda: run(agg, logdir=m, index=index), repeat=3)
    results.append(("Exact windowed mean", "495 runs, 6000-step window", f"{first:.2f} / {warm:.2f} s", "< 1 s"))

    roles = json.loads((m / "_synth.json").read_text())["roles"]
    live = next(p for p in m.rglob(roles["running"]) if p.is_dir())
    last = index.store.run(live.name)
    with (live / "_metrics.jsonl").open("ab") as f:
        f.write(b"".join(json_line({"_step": 10**6 + i, "_t": 1.0, "train/loss": 0.5}) for i in range(1000)))
    t = time.perf_counter()
    run({"series": {"from": live.name, "y": ["train/loss"], "steps": [10**6, 10**6 + 999]}},
        logdir=m, index=index)  # fmt: skip
    results.append(("Live: 1000 new lines queryable", "running run", f"{(time.perf_counter() - t) * 1e3:.0f} ms", "< 1 s"))
    assert last is not None

    tab = work / "table" / "beamtime"
    table_logdir(m, tab, 10_000)
    tindex = Index(logdir=tab)
    t = time.perf_counter()
    tindex.catch_up(".", budget_s=float("inf"))
    tb = time.perf_counter() - t
    rq = {"runs": {"where": {"config.lr": {"lt": "1e-3"}, "run.status": "finished"},
                   "select": ["run.name", "config.lr", "metric.val/acc.max"],
                   "sort": ["-metric.val/acc.max"], "limit": 20}}  # fmt: skip
    first, warm = timed(lambda: run(rq, logdir=tab, index=tindex))
    results.append(("Run table, no daemon (query + freshness check)", f"10k runs (first index: {tb:.1f} s)", f"{first * 1e3:.0f} / {warm * 1e3:.0f} ms", "< 50 ms"))
    tindex.close()
    daemon = Daemon(logdir=tab)
    daemon.start()
    time.sleep(3)
    tindex = Index(logdir=tab)
    first, warm = timed(lambda: run(rq, logdir=tab, index=tindex))
    results.append(("Run table, daemon running", "10k runs", f"{first * 1e3:.0f} / {warm * 1e3:.0f} ms", "< 50 ms"))
    daemon.stop()
    code = (
        "from pathlib import Path; from beamtime.query import run; "
        f"run({rq!r}, logdir=Path({str(tab)!r}))"
    )
    results.append(("Run table, one-shot process", "10k runs", f"{one_shot(code, env) * 1e3:.0f} ms", "as low as possible"))

    lg = work / "long" / "beamtime"
    t = time.perf_counter()
    long_run(lg, 10_000_000)
    print(f"wrote the 10M-step run in {time.perf_counter() - t:.0f} s", flush=True)
    lindex = Index(logdir=lg)
    t = time.perf_counter()
    lindex.catch_up(".", budget_s=float("inf"))
    results.append(("Ingest one 10M-step run", "10M lines", f"{time.perf_counter() - t:.1f} s", ""))
    zoom = {"series": {"from": "long", "y": ["train/loss"], "steps": [5_000_000, 5_099_999], "points": 1000}}
    first, warm = timed(lambda: run(zoom, logdir=lg, index=lindex, caller="view"))
    results.append(("Zoom 1 % of 10M steps", "100k points → 1000 buckets", f"{first * 1e3:.0f} / {warm * 1e3:.0f} ms", "< 100 ms"))
    full = {"series": {"from": "long", "y": ["train/loss"], "steps": [0, 10**8], "points": 1000}}
    first, warm = timed(lambda: run(full, logdir=lg, index=lindex, caller="view"), repeat=2)
    results.append(("Full range of 10M steps from columns", "10M points → 1000 buckets", f"{first * 1e3:.0f} / {warm * 1e3:.0f} ms", ""))
    code = (
        "from pathlib import Path; from beamtime.query import run; "
        f"run({zoom!r}, logdir=Path({str(lg)!r}))"
    )
    results.append(("Zoom, one-shot process", "", f"{one_shot(code, env) * 1e3:.0f} ms", ""))

    print("\n| Workload | Size | Measured (first / warm) | Target |\n|---|---|---|---|")
    for row in results:
        print("| " + " | ".join(row) + " |")


if __name__ == "__main__":
    main()
