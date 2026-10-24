"""Shared constants and helpers for the metric index benchmark (stdlib only)."""

from pathlib import Path
import json
import statistics
import time

ROOT = Path(__file__).parent
DATA = ROOT / "data"
RUNS = DATA / "runs"
L1_DIR = DATA / "l1" / "run_0000"
TABLE = DATA / "table"
IDX = DATA / "idx"
RESULTS = ROOT / "results.jsonl"

STEP_KEYS = [
    "train/loss", "train/acc", "train/grad_norm", "lr", "train/loss_ce", "train/loss_aux",
    "train/tokens_per_s", "train/ppl", "train/weight_norm", "train/step_time", "gpu/mem", "gpu/util",
]
VAL_KEYS = ["val/loss", "val/acc", "val/ppl", "val/bleu", "val/f1", "val/precision", "val/recall", "val/auc"]
L1_KEYS = ["train/loss", "lr", "train/grad_norm"]
N_STEPS = 10_000
L1_STEPS = 10_000_000
N_UNIQUE = 200
N_RUNS = {"T": 8, "S": 200, "M": 1000, "L1": 1}

N_BUCKETS = 500
CHART_KEY = "train/loss"
CHART_RUNS = {"T": list(range(8)), "S": list(range(0, 200, 4)), "M": list(range(0, 1000, 20))}
AGG_RUNS = {"T": list(range(8)), "S": list(range(200)), "M": list(range(0, 1000, 2))}
AGG_WINDOW = (2000, 7999)
ZOOM = {"1%": (5_000_000, 5_099_999), "0.01%": (5_000_000, 5_000_999)}


def run_dirs(scale: str) -> list[Path]:
    """Return the run directories of a scale, index = run id.

    :param scale: One of S, M, L1.
    :return: List of run directories."""
    if scale == "L1":
        return [L1_DIR]
    return [RUNS / f"run_{i:04d}" for i in range(N_RUNS[scale])]


def bucket_of(step: int, lo: int, hi: int, nb: int) -> int:
    """Return the equal-width bucket of a step in [lo, hi].

    :param step: Step.
    :param lo: First step of the range.
    :param hi: Last step of the range (inclusive).
    :param nb: Number of buckets.
    :return: Bucket index."""
    return (step - lo) * nb // (hi - lo + 1)


def timeit(fn, repeat: int = 5) -> tuple[float, float]:
    """Time the first call and the median of further calls.

    :param fn: Zero-argument callable.
    :param repeat: Number of warm repetitions.
    :return: (first, warm median) in seconds."""
    t = time.perf_counter()
    fn()
    first = time.perf_counter() - t
    warm = []
    for _ in range(repeat):
        t = time.perf_counter()
        fn()
        warm.append(time.perf_counter() - t)
    return first, statistics.median(warm)


def dir_size(path: Path) -> int:
    """Return the total size of all files below a path in bytes.

    :param path: File or directory.
    :return: Size in bytes."""
    if path.is_file():
        return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def record(**fields) -> None:
    """Append one result row to the results file.

    :param fields: Result fields."""
    print(fields, flush=True)
    with RESULTS.open("a") as f:
        f.write(json.dumps(fields) + "\n")


def read_jsonl(path: Path, offset: int = 0, loads=json.loads, mark_every: int = 1024) -> tuple[dict, int, list]:
    """Parse complete lines of a metrics.jsonl from a byte offset into per-key columns.

    :param path: File to read.
    :param offset: Byte offset to start at.
    :param loads: JSON parser (json.loads or orjson.loads).
    :param mark_every: Record (step, byte offset) every this many lines.
    :return: (key -> (array('q') steps, array('d') values), end offset, marks)."""
    from array import array

    cols, marks, n = {}, [], 0
    with open(path, "rb") as f:
        f.seek(offset)
        pos = offset
        while chunk := f.read(1 << 24):
            end = chunk.rfind(b"\n") + 1
            if end == 0:
                break
            f.seek(pos + end)
            for line in chunk[:end].split(b"\n")[:-1]:
                row = loads(line)
                s = row["_step"]
                if n % mark_every == 0:
                    marks.append((s, pos))
                n += 1
                pos += len(line) + 1
                for k, v in row.items():
                    if k[0] != "_":
                        if (c := cols.get(k)) is None:
                            c = cols[k] = (array("q"), array("d"))
                        c[0].append(s)
                        c[1].append(v)
    return cols, pos, marks


def open_meta(db_path: Path):
    """Open (and create) an SQLite db with the shared runs/keys metadata tables.

    :param db_path: Database file.
    :return: sqlite3 connection."""
    import sqlite3

    db = sqlite3.connect(db_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("CREATE TABLE IF NOT EXISTS runs(run INTEGER PRIMARY KEY, path TEXT, offset INT, marks_step BLOB, marks_off BLOB)")
    db.execute("CREATE TABLE IF NOT EXISTS keys(key INTEGER PRIMARY KEY, name TEXT UNIQUE)")
    return db


def key_id(db, name: str) -> int:
    """Return the integer id of a key name, creating it if needed.

    :param db: sqlite3 connection.
    :param name: Key name.
    :return: Key id."""
    if (row := db.execute("SELECT key FROM keys WHERE name=?", (name,)).fetchone()) is not None:
        return row[0]
    return db.execute("INSERT INTO keys(name) VALUES (?)", (name,)).lastrowid


def run_state(db, run: int, path: Path | None = None) -> tuple[str, int]:
    """Return (path, byte offset) of a run, registering it at offset 0 if new.

    :param db: sqlite3 connection.
    :param run: Run id.
    :param path: metrics.jsonl path for a new run.
    :return: (path, offset)."""
    if (row := db.execute("SELECT path, offset FROM runs WHERE run=?", (run,)).fetchone()) is not None:
        return row
    db.execute("INSERT INTO runs(run, path, offset) VALUES (?, ?, 0)", (run, str(path)))
    return str(path), 0
