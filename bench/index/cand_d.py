"""Candidate D: DuckDB, either over one Parquet file per ingest batch per run (D1) or a native long table (D2)."""

from pathlib import Path

import duckdb

from common import open_meta, run_state


def tail(idx: Path, path: str, offset: int) -> tuple[str, int]:
    """Return a JSONL file holding the run's complete lines after offset, and the new end offset.

    :return: (file to read, end offset)."""
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read()
    end = offset + data.rfind(b"\n") + 1
    if offset == 0 and end == len(data):
        return path, end
    out = idx / "tail.jsonl"
    out.write_bytes(data[: end - offset])
    return str(out), end


class D1:
    """DuckDB over wide Parquet files, idx/pq/<run>/part-<n>.parquet."""

    def __init__(self, *, idx: Path):
        idx.mkdir(parents=True, exist_ok=True)
        self.idx, self.db, self.con = idx, open_meta(idx / "meta.sqlite"), duckdb.connect()

    def ingest(self, run: int, path: Path | None = None) -> None:
        """Write new lines of a run as one more Parquet part.

        :param run: Run id.
        :param path: metrics.jsonl for a new run."""
        path, offset = run_state(self.db, run, path)
        src, end = tail(self.idx, path, offset)
        d = self.idx / "pq" / str(run)
        d.mkdir(parents=True, exist_ok=True)
        n = len(list(d.glob("*.parquet")))
        self.con.execute(f"COPY (SELECT * FROM read_json('{src}', format='newline_delimited')) TO '{d}/part-{n}.parquet' (FORMAT parquet)")
        self.db.execute("UPDATE runs SET offset=? WHERE run=?", (end, run))
        self.db.commit()

    def scan(self, runs: list[int], key: str) -> str:
        """Return a SQL relation of (run, step, v) for one key over the runs' Parquet files.

        :return: SQL fragment."""
        files = ", ".join(f"'{self.idx}/pq/{r}/*.parquet'" for r in runs)
        return (f"(SELECT CAST(regexp_extract(filename, '/pq/(\\d+)/', 1) AS INT) AS run, _step AS step, \"{key}\" AS v "
                f"FROM read_parquet([{files}], filename=true, union_by_name=true) WHERE \"{key}\" IS NOT NULL)")

    def chart(self, runs: list[int], key: str, lo: int, hi: int, nb: int) -> dict:
        """Min/max per equal-width bucket in DuckDB SQL.

        :return: run -> (bucket ids, mins, maxs)."""
        rows = self.con.execute(f"SELECT run, (step - {lo}) * {nb} // {hi - lo + 1} AS b, min(v), max(v) FROM {self.scan(runs, key)} "
                                f"WHERE step BETWEEN {lo} AND {hi} GROUP BY ALL ORDER BY run, b").fetchall()
        return group(rows)

    def mean(self, runs: list[int], key: str, lo: int, hi: int) -> dict:
        """Exact mean over a step window.

        :return: run -> mean."""
        return dict(self.con.execute(f"SELECT run, avg(v) FROM {self.scan(runs, key)} WHERE step BETWEEN {lo} AND {hi} GROUP BY run").fetchall())


UNPIVOT = ("SELECT {run} AS run, key, _step AS step, value FROM (UNPIVOT (SELECT * EXCLUDE (_t) FROM read_json({src}, format='newline_delimited'{extra})) "
           "ON COLUMNS(* EXCLUDE (_step{excl})) INTO NAME key VALUE value)")


class D2:
    """DuckDB native long table m(run, key, step, value)."""

    def __init__(self, *, idx: Path):
        idx.mkdir(parents=True, exist_ok=True)
        self.idx, self.db, self.con = idx, open_meta(idx / "meta.sqlite"), duckdb.connect(str(idx / "d2.duckdb"))

    def build_all(self, dirs: list[Path]) -> None:
        """Bulk-load all runs in one multi-threaded statement, sorted by (run, key, step).

        :param dirs: Run directories, position = run id."""
        files = "[" + ", ".join(f"'{d}/metrics.jsonl'" for d in dirs) + "]"
        run = "CAST(regexp_extract(filename, 'run_(\\d+)/metrics', 1) AS INT)"
        sql = UNPIVOT.format(run=run, src=files, extra=", filename=true", excl=", filename")
        self.con.execute(f"CREATE TABLE m AS {sql} ORDER BY run, key, step")
        for r, d in enumerate(dirs):
            run_state(self.db, r, d / "metrics.jsonl")
            self.db.execute("UPDATE runs SET offset=? WHERE run=?", ((d / "metrics.jsonl").stat().st_size, r))
        self.db.commit()

    def ingest(self, run: int, path: Path | None = None) -> None:
        """Insert new lines of a run.

        :param run: Run id.
        :param path: metrics.jsonl for a new run."""
        path, offset = run_state(self.db, run, path)
        src, end = tail(self.idx, path, offset)
        self.con.execute(f"INSERT INTO m {UNPIVOT.format(run=run, src=repr(src), extra='', excl='')}")
        self.db.execute("UPDATE runs SET offset=? WHERE run=?", (end, run))
        self.db.commit()

    def chart(self, runs: list[int], key: str, lo: int, hi: int, nb: int) -> dict:
        """Min/max per equal-width bucket in DuckDB SQL.

        :return: run -> (bucket ids, mins, maxs)."""
        rows = self.con.execute(f"SELECT run, (step - {lo}) * {nb} // {hi - lo + 1} AS b, min(value), max(value) FROM m "
                                f"WHERE key = ? AND run IN ({', '.join(map(str, runs))}) AND step BETWEEN {lo} AND {hi} "
                                "GROUP BY ALL ORDER BY run, b", [key]).fetchall()
        return group(rows)

    def mean(self, runs: list[int], key: str, lo: int, hi: int) -> dict:
        """Exact mean over a step window.

        :return: run -> mean."""
        return dict(self.con.execute(f"SELECT run, avg(value) FROM m WHERE key = ? AND run IN ({', '.join(map(str, runs))}) "
                                     f"AND step BETWEEN {lo} AND {hi} GROUP BY run", [key]).fetchall())


def group(rows: list[tuple]) -> dict:
    """Group (run, b, min, max) rows by run.

    :return: run -> (bucket ids, mins, maxs)."""
    out = {}
    for run, b, mn, mx in rows:
        o = out.setdefault(run, ([], [], []))
        o[0].append(b)
        o[1].append(mn)
        o[2].append(mx)
    return out
