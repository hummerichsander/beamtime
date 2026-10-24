"""Extra measurements: JSONL scan speed, run table (W5), interpreter start and import times."""

import json
import statistics
import subprocess
import sys
import time

import duckdb
import orjson
import pyarrow.json as pj

from common import DATA, TABLE, dir_size, read_jsonl, record, run_dirs, timeit


def scan() -> None:
    """Parse speed over 50 unique runs with several JSON readers."""
    files = [d / "metrics.jsonl" for d in run_dirs("S")[:50]]
    mb = sum(f.stat().st_size for f in files) / 1e6
    lines = 50 * 10_000
    cases = {
        "json.loads per line": lambda: [json.loads(x) for f in files for x in f.read_bytes().splitlines()],
        "orjson.loads per line": lambda: [orjson.loads(x) for f in files for x in f.read_bytes().splitlines()],
        "read_jsonl columnar (json)": lambda: [read_jsonl(f) for f in files],
        "read_jsonl columnar (orjson)": lambda: [read_jsonl(f, loads=orjson.loads) for f in files],
        "pyarrow.json.read_json": lambda: [pj.read_json(f) for f in files],
        "duckdb read_json (all files, 1 query)": lambda: duckdb.sql(
            "SELECT count(*), avg(\"train/loss\") FROM read_json([" + ", ".join(f"'{f}'" for f in files) + "])").fetchall(),
    }
    for name, fn in cases.items():
        t = time.perf_counter()
        fn()
        dt = time.perf_counter() - t
        record(workload="JSONL scan", variant=name, first_s=dt, mb_per_s=mb / dt, lines_per_s=lines / dt, mb=mb)


def table() -> None:
    """W5: filter 10k runs by config.optimizer and sort by summary val/acc."""
    dirs = sorted(TABLE.iterdir())

    def from_files():
        rows = []
        for d in dirs:
            cfg = json.loads((d / "config.json").read_bytes())
            if cfg["optimizer"] == "adam":
                rows.append((json.loads((d / "summary.json").read_bytes())["val/acc"], json.loads((d / "run.json").read_bytes()), cfg))
        return sorted(rows, key=lambda r: -r[0])[:100]

    first, warm = timeit(from_files, repeat=3)
    record(workload="W5 run table", variant="scan 30k json files, no index", first_s=first, warm_s=warm)

    import sqlite3

    p = DATA / "w5.sqlite"
    p.unlink(missing_ok=True)
    t = time.perf_counter()
    db = sqlite3.connect(p)
    db.execute("CREATE TABLE runs(id TEXT PRIMARY KEY, name TEXT, status TEXT, created REAL, folder TEXT, config TEXT, summary TEXT)")
    rows = []
    for d in dirs:
        r = json.loads((d / "run.json").read_bytes())
        rows.append((r["id"], r["name"], r["status"], r["created"], r["folder"], (d / "config.json").read_text(), (d / "summary.json").read_text()))
    db.executemany("INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    db.commit()
    record(workload="W5 build", variant="sqlite json columns", first_s=time.perf_counter() - t, index_bytes=dir_size(p))
    q = ("SELECT id, name, status, config, summary FROM runs WHERE config ->> '$.optimizer' = 'adam' "
         "ORDER BY summary ->> '$.\"val/acc\"' DESC LIMIT 100")
    first, warm = timeit(lambda: db.execute(q).fetchall())
    record(workload="W5 run table", variant="sqlite json_extract", first_s=first, warm_s=warm)

    def in_python():
        rs = [(json.loads(c), json.loads(s), i) for i, c, s in db.execute("SELECT id, config, summary FROM runs")]
        return sorted((r for r in rs if r[0]["optimizer"] == "adam"), key=lambda r: -r[1]["val/acc"])[:100]

    first, warm = timeit(in_python)
    record(workload="W5 run table", variant="sqlite load all + filter in Python", first_s=first, warm_s=warm)
    db.close()
    cmd = ("import sqlite3; db = sqlite3.connect(%r); db.execute(%r).fetchall()" % (str(p), q))
    ts = [timed([sys.executable, "-c", cmd]) for _ in range(7)]
    record(workload="W5 run table", variant="sqlite one-shot fresh process", first_s=ts[0], warm_s=statistics.median(ts))

    con = duckdb.connect()
    t = time.perf_counter()
    con.execute(f"CREATE TABLE runs AS SELECT r.*, c AS config, s AS summary FROM read_json('{TABLE}/*/run.json', filename=true) r "
                f"JOIN read_json('{TABLE}/*/config.json', filename=true, records=false) c ON parse_dirpath(r.filename) = parse_dirpath(c.filename) "
                f"JOIN read_json('{TABLE}/*/summary.json', filename=true, records=false) s ON parse_dirpath(r.filename) = parse_dirpath(s.filename)")
    record(workload="W5 build", variant="duckdb read_json over 30k files", first_s=time.perf_counter() - t)
    q = "SELECT id, name, status, config, summary FROM runs WHERE config.json.optimizer = 'adam' ORDER BY summary.json.\"val/acc\" DESC LIMIT 100"
    first, warm = timeit(lambda: con.execute(q).fetchall())
    record(workload="W5 run table", variant="duckdb in-memory table", first_s=first, warm_s=warm)
    p.unlink()


def timed(cmd: list[str]) -> float:
    """Wall time of a subprocess.

    :return: Seconds."""
    t = time.perf_counter()
    subprocess.run(cmd, check=True, capture_output=True)
    return time.perf_counter() - t


def imports() -> None:
    """Fresh-interpreter wall time for bare start and single imports (median of 10)."""
    for mod in ["", "json", "sqlite3", "orjson", "numpy", "pyarrow", "duckdb", "tsdownsample", "numpy, duckdb, pyarrow"]:
        code = f"import {mod}" if mod else "pass"
        ts = [timed([sys.executable, "-c", code]) for _ in range(10)]
        record(workload="W6 import", variant=code, first_s=ts[0], warm_s=statistics.median(ts))
    ts = [timed([sys.executable, "-I", "-S", "-c", "pass"]) for _ in range(10)]
    record(workload="W6 import", variant="python -I -S -c pass", first_s=ts[0], warm_s=statistics.median(ts))


if __name__ == "__main__":
    {"scan": scan, "table": table, "imports": imports}[sys.argv[1]]()
