"""Candidate E: B's column files read with pure Python (mmap + memoryview, no numpy)."""

from bisect import bisect_left
from pathlib import Path
import mmap

from common import open_meta


def open_index(idx: Path):
    """Open B's index (E only queries; ingest and build are B's).

    :param idx: Index directory.
    :return: sqlite3 connection."""
    return open_meta(idx / "b.sqlite")


def col_dir(db) -> Path:
    """Return the column file directory of an index connection.

    :return: Directory path."""
    return Path(db.execute("PRAGMA database_list").fetchone()[2]).parent / "cols"


def series(db, run: int, kid: int, lo: int, hi: int) -> tuple[memoryview, memoryview]:
    """Return memoryviews of steps and values in [lo, hi].

    :return: (steps, values)."""
    p = col_dir(db) / str(run) / f"{kid}"
    views = []
    for ext, fmt in (("s", "q"), ("v", "d")):
        with open(f"{p}.{ext}", "rb") as f:
            views.append(memoryview(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)).cast(fmt))
    s, v = views
    i0, i1 = bisect_left(s, lo), bisect_left(s, hi + 1)
    return s[i0:i1], v[i0:i1]


def chart(db, runs: list[int], key: str, lo: int, hi: int, nb: int) -> dict:
    """Min/max per equal-width bucket using bisect for bucket edges.

    :return: run -> (bucket ids, mins, maxs)."""
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    span = hi - lo + 1
    out = {}
    for run in runs:
        s, v = series(db, run, kid, lo, hi)
        edges = [bisect_left(s, lo + (k * span + nb - 1) // nb) for k in range(nb + 1)]
        bs, mn, mx = [], [], []
        for k in range(nb):
            if edges[k + 1] > edges[k]:
                chunk = v[edges[k]:edges[k + 1]]
                bs.append(k)
                mn.append(min(chunk))
                mx.append(max(chunk))
        out[run] = (bs, mn, mx)
    return out


def mean(db, runs: list[int], key: str, lo: int, hi: int) -> dict:
    """Exact mean over a step window.

    :return: run -> mean."""
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    out = {}
    for run in runs:
        v = series(db, run, kid, lo, hi)[1]
        out[run] = sum(v) / len(v)
    return out
