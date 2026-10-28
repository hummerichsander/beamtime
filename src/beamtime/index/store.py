"""The SQLite part of the index: runs, folders, events, data entries, notes and links."""

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    folder TEXT NOT NULL,
    name TEXT,
    status TEXT,
    created_at TEXT,
    ended_at TEXT,
    heartbeat REAL,
    tags TEXT,
    info TEXT,
    config TEXT,
    card TEXT,
    run_mtime REAL,
    config_mtime REAL,
    card_mtime REAL,
    notes_mtime REAL,
    events_offset INTEGER NOT NULL DEFAULT 0,
    data_offset INTEGER NOT NULL DEFAULT 0,
    metrics_size INTEGER NOT NULL DEFAULT 0,
    indexed_at REAL
);
CREATE INDEX runs_folder ON runs (folder);
CREATE TABLE folders (
    path TEXT PRIMARY KEY,
    mtime REAL,
    walked REAL,
    children TEXT,
    notes_mtime REAL
);
CREATE TABLE events (
    run_id TEXT NOT NULL, t REAL, step INTEGER, kind TEXT, message TEXT, data TEXT
);
CREATE INDEX events_run ON events (run_id);
CREATE TABLE data (
    run_id TEXT NOT NULL, step INTEGER, t REAL, key TEXT, kind TEXT, path TEXT,
    record TEXT
);
CREATE INDEX data_run ON data (run_id, key);
CREATE TABLE notes (
    path TEXT PRIMARY KEY,
    folder TEXT NOT NULL,
    run_id TEXT,
    id TEXT,
    t REAL,
    type TEXT,
    description TEXT,
    meta TEXT
);
CREATE INDEX notes_folder ON notes (folder);
CREATE TABLE links (source TEXT NOT NULL, kind TEXT, target TEXT);
CREATE INDEX links_target ON links (target);
"""


# what catch-up needs to tell whether a run changed; the JSON columns are left out.
STALE_COLUMNS = (
    "id, path, status, run_mtime, notes_mtime, config_mtime, card_mtime, "
    "metrics_size, events_offset, data_offset, indexed_at"
)


def in_scope(column: str, scope: str) -> tuple[str, list[str]]:
    """Build a condition for paths at or below a folder.

    :param column: The path column, e.g. ``folder``.
    :param scope: The folder relative to the log dir; ``.`` is everything.
    :return: The SQL condition and its parameters."""
    if scope in (".", ""):
        return "1", []
    prefix = scope.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"({column} = ? OR {column} LIKE ? ESCAPE '\\')", [scope, f"{prefix}/%"]


class Store:
    """Access to ``index.sqlite``; safe for many readers and one writer at a time."""

    def __init__(self, *, path: Path) -> None:
        """Open the database, rebuilding it if its schema is outdated.

        :param path: The database file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.use_wal()
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.rebuilt = False
        if self.version() != SCHEMA_VERSION:
            with self.transaction():
                # another process may be creating the schema right now; check again.
                if self.version() != SCHEMA_VERSION:
                    self.create()
                    self.rebuilt = True

    def use_wal(self) -> None:
        """Switch to write-ahead logging, so readers never wait for writers.

        Switching needs a lock that the busy timeout doesn't cover; when two processes
        open a new database at once, the second retries until the first is done."""
        deadline = time.monotonic() + 10
        while True:
            try:
                if self.db.execute("PRAGMA journal_mode").fetchone()[0] != "wal":
                    self.db.execute("PRAGMA journal_mode=WAL")
                return
            except sqlite3.OperationalError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.02)

    def version(self) -> int | None:
        """Read the schema version of the database.

        :return: The version, or ``None`` for a new or foreign database."""
        try:
            row = self.db.execute("SELECT value FROM meta WHERE key = 'schema'").fetchone()
        except sqlite3.OperationalError:
            return None
        return int(row[0]) if row else None

    def rebuild(self) -> None:
        """Drop every table and create the current schema, in one transaction."""
        with self.transaction():
            self.create()

    def create(self) -> None:
        """Drop every table and create the current schema; call inside a transaction."""
        tables = self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for (name,) in tables.fetchall():
            self.db.execute(f"DROP TABLE IF EXISTS {name}")
        for statement in SCHEMA.split(";"):
            if statement.strip():
                self.db.execute(statement)
        self.db.execute("INSERT INTO meta VALUES ('schema', ?)", (str(SCHEMA_VERSION),))

    def transaction(self) -> "Transaction":
        """Group writes into one transaction.

        :return: A context manager."""
        return Transaction(db=self.db)

    def run(self, run_id: str) -> sqlite3.Row | None:
        """Read one run's row.

        :param run_id: The run id.
        :return: The row, or ``None``."""
        return self.db.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()

    def runs_in(self, scope: str) -> list[sqlite3.Row]:
        """Read the staleness columns of every run at or below a folder.

        :param scope: The folder relative to the log dir.
        :return: The rows."""
        cond, params = in_scope("folder", scope)
        return self.db.execute(f"SELECT {STALE_COLUMNS} FROM runs WHERE {cond}", params).fetchall()

    def upsert_run(self, run_id: str, fields: dict[str, Any]) -> None:
        """Insert a run or update some of its fields.

        :param run_id: The run id.
        :param fields: Column to value; dicts and lists are stored as JSON."""
        values = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in fields.items()}
        if self.run(run_id) is None:
            cols = ["id", *values]
            marks = ", ".join("?" * len(cols))
            self.db.execute(
                f"INSERT INTO runs ({', '.join(cols)}) VALUES ({marks})",
                [run_id, *values.values()],
            )
        elif values:
            sets = ", ".join(f"{k} = ?" for k in values)
            self.db.execute(f"UPDATE runs SET {sets} WHERE id = ?", [*values.values(), run_id])

    def delete_run(self, run_id: str) -> None:
        """Forget a run and everything indexed from it.

        :param run_id: The run id."""
        for table, col in (("runs", "id"), ("events", "run_id"), ("data", "run_id")):
            self.db.execute(f"DELETE FROM {table} WHERE {col} = ?", (run_id,))
        self.db.execute(
            "DELETE FROM links WHERE source IN (SELECT path FROM notes WHERE run_id = ?)",
            (run_id,),
        )
        self.db.execute("DELETE FROM notes WHERE run_id = ?", (run_id,))

    def folder(self, path: str) -> sqlite3.Row | None:
        """Read a folder's walk state.

        :param path: The folder relative to the log dir.
        :return: The row, or ``None``."""
        return self.db.execute("SELECT * FROM folders WHERE path = ?", (path,)).fetchone()

    def set_folder(self, path: str, **fields: Any) -> None:
        """Insert or update a folder's walk state.

        :param path: The folder relative to the log dir.
        :param fields: Columns to set; ``children`` is a list."""
        if "children" in fields:
            fields["children"] = json.dumps(fields["children"])
        cols = ["path", *fields]
        updates = ", ".join(f"{k} = excluded.{k}" for k in fields)
        marks = ", ".join("?" * len(cols))
        self.db.execute(
            f"INSERT INTO folders ({', '.join(cols)}) VALUES ({marks}) "
            f"ON CONFLICT (path) DO UPDATE SET {updates}",
            [path, *fields.values()],
        )

    def replace_notes(self, folder: str, run_id: str | None, notes: list[dict]) -> None:
        """Replace the indexed notes of a folder or run.

        :param folder: The folder (or run path) relative to the log dir.
        :param run_id: The run id for run notes, else ``None``.
        :param notes: Rows with ``path``, ``id``, ``t``, ``type``, ``description``,
            ``meta`` and ``links``, ``(kind, target)`` pairs."""
        self.db.execute(
            "DELETE FROM links WHERE source IN (SELECT path FROM notes WHERE folder = ?)",
            (folder,),
        )
        self.db.execute("DELETE FROM notes WHERE folder = ?", (folder,))
        for n in notes:
            self.db.execute(
                "INSERT OR REPLACE INTO notes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    n["path"],
                    folder,
                    run_id,
                    n["id"],
                    n["t"],
                    n["type"],
                    n["description"],
                    json.dumps(n["meta"], default=str),
                ),
            )
            self.db.executemany(
                "INSERT INTO links VALUES (?, ?, ?)",
                [(n["path"], kind, target) for kind, target in n["links"]],
            )


class Transaction:
    """``BEGIN IMMEDIATE`` … ``COMMIT``, rolled back on errors."""

    def __init__(self, *, db: sqlite3.Connection) -> None:
        """Wrap a connection.

        :param db: The connection, in autocommit mode."""
        self.db = db

    def __enter__(self) -> sqlite3.Connection:
        """Begin.

        :return: The connection."""
        self.db.execute("BEGIN IMMEDIATE")
        return self.db

    def __exit__(self, kind: Any, *exc: Any) -> None:
        """Commit, or roll back after an exception.

        :param kind: The exception type, if any.
        :param exc: The rest of the exception information."""
        self.db.execute("COMMIT" if kind is None else "ROLLBACK")
