"""Run all phases per candidate in fresh processes; dump partial results to RESULTS.md after each candidate."""

import json
import shutil
import statistics
import subprocess
import sys
import time

from common import IDX, RESULTS, ROOT, record


def run(*args: str) -> str:
    """Run bench.py in a fresh interpreter.

    :return: stdout."""
    return subprocess.run([sys.executable, "bench.py", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def oneshot(cand: str, scale: str, n: int = 7) -> None:
    """W6: wall time of a fresh process answering W2, median of n."""
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        run("oneshot", cand, scale)
        ts.append(time.perf_counter() - t)
    record(cand=cand, scale=scale, workload="W6 one-shot CLI (W2)", first_s=ts[0], warm_s=statistics.median(ts))


def dump() -> None:
    """Write all results so far as a raw table to RESULTS.md."""
    rows = [json.loads(line) for line in RESULTS.read_text().splitlines()]
    cols = ["cand", "scale", "workload", "variant", "first_s", "warm_s", "index_bytes", "points", "spikes_missed", "spikes_total", "checksum"]
    lines = ["# Metric index benchmark (partial, raw)", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(f"{r[c]:.4g}" if isinstance(r.get(c), float) else str(r.get(c, "")) for c in cols) + " |")
    (ROOT / "RESULTS.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    """Benchmark the candidates given on the command line (default all)."""
    for cand in sys.argv[1:] or ["B", "D2", "D1", "A", "C"]:
        for scale in ["S", "M", "L1"]:
            shutil.rmtree(IDX / f"{cand}-{scale}", ignore_errors=True)
            run("build", cand, scale)
            run("query", cand, scale)
            if cand == "B":
                run("query", "E", scale)
            if scale != "L1":
                oneshot(cand, scale)
                if cand == "B":
                    oneshot("E", scale)
            run("ingest", cand, scale)
            shutil.rmtree(IDX / f"{cand}-{scale}")
        dump()


if __name__ == "__main__":
    main()
