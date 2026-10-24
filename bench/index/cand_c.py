"""Candidate C: SQLite long table (run, key, step, value) WITHOUT ROWID, downsampling in SQL."""

from pathlib import Path

import orjson

from common import key_id, open_meta, read_jsonl, run_state


def open_index(idx: Path):
    """Open the index.

    :param idx: Index directory.
    :return: sqlite3 connection."""
    idx.mkdir(parents=True, exist_ok=True)
    db = open_meta(idx / "c.sqlite")
    db.execute("CREATE TABLE IF NOT EXISTS m(run INT, key INT, step INT, value REAL, PRIMARY KEY(run, key, step)) WITHOUT ROWID")
    return db


def ingest(db, run: int, path: Path | None = None) -> None:
    """Insert new JSONL lines of a run.

    :param run: Run id.
    :param path: metrics.jsonl for a new run."""
    path, offset = run_state(db, run, path)
    cols, end, _ = read_jsonl(Path(path), offset, orjson.loads)
    for name, (steps, vals) in cols.items():
        k = key_id(db, name)
        db.executemany("INSERT INTO m VALUES (?, ?, ?, ?)", ((run, k, s, v) for s, v in zip(steps, vals)))
    db.execute("UPDATE runs SET offset=? WHERE run=?", (end, run))
    db.commit()


def build(idx: Path, dirs: list[Path]) -> None:
    """Build the index for all runs.

    :param idx: Index directory.
    :param dirs: Run directories, position = run id."""
    db = open_index(idx)
    for run, d in enumerate(dirs):
        ingest(db, run, d / "metrics.jsonl")


def chart(db, runs: list[int], key: str, lo: int, hi: int, nb: int) -> dict:
    """Min/max per equal-width bucket with GROUP BY in SQLite.

    :return: run -> (bucket ids, mins, maxs)."""
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    out = {}
    for run in runs:
        rows = db.execute("SELECT (step - ?) * ? / ? AS b, min(value), max(value) FROM m "
                          "WHERE run=? AND key=? AND step BETWEEN ? AND ? GROUP BY b",
                          (lo, nb, hi - lo + 1, run, kid, lo, hi)).fetchall()
        out[run] = tuple(map(list, zip(*rows)))
    return out


def mean(db, runs: list[int], key: str, lo: int, hi: int) -> dict:
    """Exact mean over a step window.

    :return: run -> mean."""
    kid = db.execute("SELECT key FROM keys WHERE name=?", (key,)).fetchone()[0]
    return {run: db.execute("SELECT avg(value) FROM m WHERE run=? AND key=? AND step BETWEEN ? AND ?",
                            (run, kid, lo, hi)).fetchone()[0] for run in runs}
