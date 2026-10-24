"""Candidate B: SQLite metadata + raw int64/float64 column files per (run, key), downsampled on the fly with numpy."""

from pathlib import Path

import numpy as np
import orjson

from common import key_id, open_meta, read_jsonl, run_state


def open_index(idx: Path):
    """Open the index.

    :param idx: Index directory.
    :return: sqlite3 connection with an extra attribute-free layout: files under idx/cols."""
    idx.mkdir(parents=True, exist_ok=True)
    return open_meta(idx / "b.sqlite")


def col_dir(db) -> Path:
    """Return the column file directory of an index connection.

    :return: Directory path."""
    return Path(db.execute("PRAGMA database_list").fetchone()[2]).parent / "cols"


def ingest(db, run: int, path: Path | None = None) -> None:
    """Append new JSONL lines of a run to its column files.

    :param run: Run id.
    :param path: metrics.jsonl for a new run."""
    path, offset = run_state(db, run, path)
    cols, end, _ = read_jsonl(Path(path), offset, orjson.loads)
    d = col_dir(db) / str(run)
    d.mkdir(parents=True, exist_ok=True)
    for name, (steps, vals) in cols.items():
        k = key_id(db, name)
        with open(d / f"{k}.s", "ab") as f:
            f.write(steps.tobytes())
        with open(d / f"{k}.v", "ab") as f:
            f.write(vals.tobytes())
    db.execute("UPDATE runs SET offset=? WHERE run=?", (end, run))
    db.commit()


def build(idx: Path, dirs: list[Path]) -> None:
    """Build the index for all runs.

    :param idx: Index directory.
    :param dirs: Run directories, position = run id."""
    db = open_index(idx)
    for run, d in enumerate(dirs):
        ingest(db, run, d / "metrics.jsonl")


def series(db, run: int, key: str, lo: int, hi: int, kid: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Return steps and values of a key in [lo, hi]; large files are memory-mapped.

    :return: (steps, values)."""
    if kid is None:
        kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    p = col_dir(db) / str(run) / f"{kid}"
    sp, vp = Path(f"{p}.s"), Path(f"{p}.v")
    read = np.memmap if sp.stat().st_size > 1 << 20 else np.fromfile
    s = read(sp, dtype=np.int64)
    v = read(vp, dtype=np.float64)
    i0, i1 = np.searchsorted(s, [lo, hi + 1])
    return s[i0:i1], v[i0:i1]


def chart(db, runs: list[int], key: str, lo: int, hi: int, nb: int) -> dict:
    """Min/max per equal-width bucket with np.minimum/maximum.reduceat.

    :return: run -> (bucket ids, mins, maxs)."""
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    out = {}
    for run in runs:
        s, v = series(db, run, key, lo, hi, kid)
        b = (s - lo) * nb // (hi - lo + 1)
        starts = np.flatnonzero(np.r_[True, b[1:] != b[:-1]])
        out[run] = (b[starts], np.minimum.reduceat(v, starts), np.maximum.reduceat(v, starts))
    return out


def chart_tsd(db, runs: list[int], key: str, lo: int, hi: int, nb: int) -> dict:
    """Min/max per bucket via tsdownsample (returns indices of the chosen points).

    :return: run -> (steps, values, values)."""
    from tsdownsample import MinMaxDownsampler

    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    ds = MinMaxDownsampler()
    out = {}
    for run in runs:
        s, v = series(db, run, key, lo, hi, kid)
        i = ds.downsample(s, v, n_out=2 * nb)
        out[run] = (s[i], v[i], v[i])
    return out


def mean(db, runs: list[int], key: str, lo: int, hi: int) -> dict:
    """Exact mean over a step window.

    :return: run -> mean."""
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    return {run: float(series(db, run, key, lo, hi, kid)[1].mean()) for run in runs}
