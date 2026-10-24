"""Candidate A: pure stdlib. SQLite holds multi-resolution min/max/sum/count/last buckets; exact data from JSONL."""

from array import array
from bisect import bisect_right
from pathlib import Path
import json
import math

from common import key_id, open_meta, read_jsonl, run_state

WIDTHS = [16, 64, 256, 1024, 4096]
CHUNK = 1024
INF = math.inf


def open_index(idx: Path, loads=json.loads):
    """Open the index.

    :param idx: Index directory.
    :param loads: JSON parser used for ingest and exact reads.
    :return: sqlite3 connection."""
    idx.mkdir(parents=True, exist_ok=True)
    db = open_meta(idx / "a.sqlite")
    db.execute("CREATE TABLE IF NOT EXISTS levels(run INT, key INT, width INT, chunk INT, data BLOB, "
               "PRIMARY KEY(run, key, width, chunk)) WITHOUT ROWID")
    return db


class Level:
    """Buckets of one width, starting at bucket index base."""

    def __init__(self, *, base: int, data: list[array]):
        self.base = base
        self.mn, self.mx, self.sm, self.ct, self.last = (list(a) for a in data) if data else ([], [], [], [], [])

    def grow(self, n: int) -> None:
        """Extend to n buckets with empty buckets.

        :param n: Target length."""
        k = n - len(self.mn)
        if k > 0:
            self.mn += [INF] * k
            self.mx += [-INF] * k
            self.sm += [0.0] * k
            self.ct += [0.0] * k
            self.last += [math.nan] * k


def load(db, run: int, key: int, w: int, c0: int) -> Level:
    """Load all chunks >= c0 of one level.

    :return: Level starting at bucket c0 * CHUNK."""
    parts = [[], [], [], [], []]
    for (blob,) in db.execute("SELECT data FROM levels WHERE run=? AND key=? AND width=? AND chunk>=? ORDER BY chunk",
                              (run, key, w, c0)):
        a = array("d", blob)
        n = len(a) // 5
        for i in range(5):
            parts[i] += a[i * n:(i + 1) * n]
    return Level(base=c0 * CHUNK, data=parts if parts[0] else [])


def save(db, run: int, key: int, w: int, lv: Level) -> None:
    """Write all chunks of a level from its base on."""
    rows = []
    for off in range(0, len(lv.mn), CHUNK):
        sl = slice(off, off + CHUNK)
        a = array("d", lv.mn[sl] + lv.mx[sl] + lv.sm[sl] + lv.ct[sl] + lv.last[sl])
        rows.append((run, key, w, (lv.base + off) // CHUNK, a.tobytes()))
    db.executemany("INSERT OR REPLACE INTO levels VALUES (?, ?, ?, ?, ?)", rows)


def update(db, run: int, key: int, steps: array, vals: array) -> None:
    """Fold new points into the finest level and recompute the touched tail of coarser levels.

    :param steps: New steps (ascending, after all indexed steps).
    :param vals: New values."""
    s0, fine = steps[0], None
    for w in WIDTHS:
        lv = load(db, run, key, w, max(0, s0 // w - 4) // CHUNK)
        if fine is None:
            lv.grow(steps[-1] // w - lv.base + 1)
            mn, mx, sm, ct, last, base = lv.mn, lv.mx, lv.sm, lv.ct, lv.last, lv.base
            for s, v in zip(steps, vals):
                b = s // w - base
                if v < mn[b]:
                    mn[b] = v
                if v > mx[b]:
                    mx[b] = v
                sm[b] += v
                ct[b] += 1
                last[b] = v
        else:
            n = (fine.base + len(fine.mn) - 1) // 4 + 1 - lv.base
            lv.grow(n)
            for b in range(s0 // w - lv.base, n):
                i = 4 * (b + lv.base) - fine.base
                lv.mn[b] = min(fine.mn[i:i + 4])
                lv.mx[b] = max(fine.mx[i:i + 4])
                lv.sm[b] = sum(fine.sm[i:i + 4])
                lv.ct[b] = sum(fine.ct[i:i + 4])
                lv.last[b] = next((x for x, c in zip(fine.last[i:i + 4][::-1], fine.ct[i:i + 4][::-1]) if c), math.nan)
        save(db, run, key, w, lv)
        fine = lv


def ingest(db, run: int, path: Path | None = None, loads=json.loads) -> None:
    """Index new lines of a run's metrics.jsonl.

    :param run: Run id.
    :param path: metrics.jsonl for a new run.
    :param loads: JSON parser."""
    path, offset = run_state(db, run, path)
    cols, end, marks = read_jsonl(Path(path), offset, loads)
    for name, (steps, vals) in cols.items():
        update(db, run, key_id(db, name), steps, vals)
    ms, mo = db.execute("SELECT marks_step, marks_off FROM runs WHERE run=?", (run,)).fetchone()
    ms, mo = array("q", ms or b""), array("q", mo or b"")
    ms.extend(m[0] for m in marks)
    mo.extend(m[1] for m in marks)
    db.execute("UPDATE runs SET offset=?, marks_step=?, marks_off=? WHERE run=?", (end, ms.tobytes(), mo.tobytes(), run))
    db.commit()


def build(idx: Path, dirs: list[Path], loads=json.loads) -> None:
    """Build the index for all runs.

    :param idx: Index directory.
    :param dirs: Run directories, position = run id."""
    db = open_index(idx)
    for run, d in enumerate(dirs):
        ingest(db, run, d / "metrics.jsonl", loads)


def read_window(db, run: int, key: str, lo: int, hi: int, loads=json.loads) -> tuple[list, list]:
    """Read exact points of a key in [lo, hi] from the JSONL via the sparse byte-offset marks.

    :return: (steps, values)."""
    path, ms, mo = db.execute("SELECT path, marks_step, marks_off FROM runs WHERE run=?", (run,)).fetchone()
    ms, mo = array("q", ms), array("q", mo)
    off = mo[max(0, bisect_right(ms, lo) - 1)]
    steps, vals = [], []
    with open(path, "rb") as f:
        f.seek(off)
        for line in f:
            row = loads(line)
            if (s := row["_step"]) > hi:
                break
            if s >= lo and (v := row.get(key)) is not None:
                steps.append(s)
                vals.append(v)
    return steps, vals


def chart(db, runs: list[int], key: str, lo: int, hi: int, nb: int) -> dict:
    """Min/max per bucket from the finest level with at most 2 * nb buckets; raw points for tiny windows.

    :return: run -> (bucket start steps, mins, maxs)."""
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    out = {}
    for run in runs:
        w = next((w for w in WIDTHS if hi // w - lo // w + 1 <= 2 * nb), WIDTHS[-1])
        if w == WIDTHS[0] and hi - lo + 1 <= 2 * nb:
            s, v = read_window(db, run, key, lo, hi)
            out[run] = (s, v, v)
            continue
        b0, b1 = lo // w, hi // w
        base, mn, mx, ct = None, [], [], []
        for c, blob in db.execute("SELECT chunk, data FROM levels WHERE run=? AND key=? AND width=? AND chunk BETWEEN ? AND ? "
                                  "ORDER BY chunk", (run, kid, w, b0 // CHUNK, b1 // CHUNK)):
            a = array("d", blob)
            n = len(a) // 5
            base = c * CHUNK if base is None else base
            mn += a[:n]
            mx += a[n:2 * n]
            ct += a[3 * n:4 * n]
        keep = [i for i in range(b0 - base, min(b1 - base + 1, len(ct))) if ct[i]]
        out[run] = ([(base + i) * w for i in keep], [mn[i] for i in keep], [mx[i] for i in keep])
    return out


def mean(db, runs: list[int], key: str, lo: int, hi: int) -> dict:
    """Exact mean from finest-level sums; requires a window aligned to the finest width.

    :return: run -> mean."""
    w = WIDTHS[0]
    assert lo % w == 0 and (hi + 1) % w == 0
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    b0, b1 = lo // w, hi // w
    out = {}
    for run in runs:
        sm = ct = 0.0
        for c, blob in db.execute("SELECT chunk, data FROM levels WHERE run=? AND key=? AND width=? AND chunk BETWEEN ? AND ?",
                                  (run, kid, w, b0 // CHUNK, b1 // CHUNK)):
            a = array("d", blob)
            n = len(a) // 5
            i0, i1 = max(b0 - c * CHUNK, 0), min(b1 - c * CHUNK + 1, n)
            if i1 > i0:
                sm += sum(a[2 * n + i0:2 * n + i1])
                ct += sum(a[3 * n + i0:3 * n + i1])
        out[run] = sm / ct
    return out


def mean_jsonl(db, runs: list[int], key: str, lo: int, hi: int, loads=json.loads) -> dict:
    """Exact mean by scanning the JSONL window (works for any window).

    :return: run -> mean."""
    out = {}
    for run in runs:
        _, v = read_window(db, run, key, lo, hi, loads)
        out[run] = sum(v) / len(v)
    return out
