"""Reading a run's files into the index, continuing where the last ingest stopped."""

import json
import os
import time
from pathlib import Path
from typing import Any

import msgspec

from beamtime.format import constants as c
from beamtime.format.authored import note_links, read_markdown_doc, versions
from beamtime.format.ids import id_time
from beamtime.format.io import read_json, read_jsonl
from beamtime.format.schema import SchemaError, schema_of
from beamtime.index.columns import TIME_KEY, ColumnWriter
from beamtime.index.store import Store

CHUNK = 64 * 1024 * 1024
_decoder = msgspec.json.Decoder()


def decode(line: bytes) -> Any:
    """Parse one JSON line; Python's parser handles the NaN and Infinity literals.

    :param line: The line without its newline.
    :return: The value, or ``None`` if the line is damaged."""
    try:
        return _decoder.decode(line)
    except msgspec.DecodeError:
        try:
            return json.loads(line)
        except ValueError:
            return None


def mtime(path: Path | str) -> float | None:
    """Read a file's modification time.

    :param path: The file.
    :return: The time, or ``None`` if the file is missing."""
    try:
        return os.stat(path).st_mtime
    except OSError:
        return None


def size(path: Path | str) -> int:
    """Read a file's size.

    :param path: The file.
    :return: The size, 0 if the file is missing."""
    try:
        return os.stat(path).st_size
    except OSError:
        return 0


class Ingester:
    """Brings the index up to date with one run's files."""

    def __init__(self, *, store: Store, logdir: Path, series: Path) -> None:
        """Set up ingest for a log dir.

        :param store: The SQLite store.
        :param logdir: The log dir.
        :param series: The cache directory holding the column files."""
        self.store = store
        self.logdir = logdir
        self.series = series

    def stale(self, rel: str, run_mtime: float, row: Any) -> tuple[bool, bool]:
        """Tell what of a run changed since it was last indexed, with few stats.

        :param rel: The run directory relative to the log dir.
        :param run_mtime: The modification time of its ``_run.json``.
        :param row: Its row in the index, or ``None`` if it is new.
        :return: Whether its small files changed, and whether its streams grew."""
        if row is None:
            return True, True
        d = os.path.join(str(self.logdir), rel)
        meta = (
            row["path"] != rel
            or run_mtime != row["run_mtime"]
            or mtime(os.path.join(d, c.NOTES)) != row["notes_mtime"]
        )
        if row["status"] != "running" and not meta:
            return False, False
        meta = (
            meta
            or mtime(os.path.join(d, c.CONFIG)) != row["config_mtime"]
            or mtime(os.path.join(d, c.CARD)) != row["card_mtime"]
        )
        streams = (
            size(os.path.join(d, c.METRICS)) != row["metrics_size"]
            or size(os.path.join(d, c.EVENTS)) != row["events_offset"]
            or size(os.path.join(d, c.DATA)) != row["data_offset"]
        )
        return meta, streams

    def ingest_meta(self, run_dir: Path) -> None:
        """Index a run's ``_run.json``, config, card and notes.

        :param run_dir: The run directory."""
        run_id = run_dir.name
        rel = run_dir.relative_to(self.logdir)
        info = read_json(run_dir / c.RUN)
        schema_of(info, kind="run", path=run_dir / c.RUN)
        fields: dict[str, Any] = {
            "path": rel.as_posix(),
            "folder": rel.parent.as_posix(),
            "name": info.get("name"),
            "status": info.get("status"),
            "created_at": info.get("created_at"),
            "ended_at": info.get("ended_at"),
            "tags": info.get("tags") or [],
            "info": info,
            "heartbeat": mtime(run_dir / c.RUN),
            "run_mtime": mtime(run_dir / c.RUN),
        }
        if (t := mtime(run_dir / c.CONFIG)) is not None:
            config = read_json(run_dir / c.CONFIG)
            fields["config"] = {k: v for k, v in config.items() if k != "schema"}
            fields["config_mtime"] = t
        if (t := mtime(run_dir / c.CARD)) is not None:
            fields["card"] = read_json(run_dir / c.CARD)
            fields["card_mtime"] = t
        notes_mtime = mtime(run_dir / c.NOTES)
        fields["notes_mtime"] = notes_mtime
        with self.store.transaction():
            self.store.upsert_run(run_id, fields)
            if notes_mtime is not None:
                self.store.replace_notes(
                    rel.as_posix(), run_id, read_notes(run_dir / c.NOTES, self.logdir)
                )

    def ingest_streams(self, run_dir: Path) -> None:
        """Index new events, data entries and metric lines of a run.

        :param run_dir: The run directory."""
        run_id = run_dir.name
        if (row := self.store.run(run_id)) is None:
            return
        events = (
            read_jsonl(run_dir / c.EVENTS, row["events_offset"])
            if (run_dir / c.EVENTS).exists()
            else None
        )
        data = (
            read_jsonl(run_dir / c.DATA, row["data_offset"])
            if (run_dir / c.DATA).exists()
            else None
        )
        with self.store.transaction() as db:
            if events is not None:
                own = {"_t", "_step", "kind", "message"}
                db.executemany(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        (
                            run_id,
                            e.get("_t"),
                            e.get("_step"),
                            e.get("kind"),
                            e.get("message"),
                            json.dumps({k: v for k, v in e.items() if k not in own}),
                        )
                        for e in events.rows
                    ],
                )
            if data is not None:
                db.executemany(
                    "INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        (
                            run_id,
                            d.get("_step"),
                            d.get("_t"),
                            d.get("key"),
                            d.get("kind"),
                            d.get("path"),
                            json.dumps(d),
                        )
                        for d in data.rows
                    ],
                )
            self.store.upsert_run(
                run_id,
                {
                    "events_offset": events.end if events else 0,
                    "data_offset": data.end if data else 0,
                },
            )
        attempts = []
        for (raw,) in self.store.db.execute(
            "SELECT data FROM events WHERE run_id = ? AND kind = 'attempt_started'",
            (run_id,),
        ):
            if (d := json.loads(raw)).get("resume_step") is not None:
                attempts.append((d.get("metrics_offset", 0), d["resume_step"]))
        consumed = self.ingest_metrics(run_dir, row["status"], sorted(attempts))
        self.store.upsert_run(run_id, {"metrics_size": consumed, "indexed_at": time.time()})

    def ingest_metrics(self, run_dir: Path, status: str, attempts: list[tuple[int, int]]) -> int:
        """Append new metric lines to the run's columns, applying resumed attempts.

        :param run_dir: The run directory.
        :param status: The run status from ``_run.json``.
        :param attempts: ``(metrics offset, resume step)`` of every resumed attempt.
        :return: The byte offset up to which the file is consumed."""
        writer = ColumnWriter(dir=self.series / run_dir.name)
        manifest = writer.manifest
        done = {tuple(a) for a in manifest.attempts}
        pending = [a for a in attempts if a not in done and a[0] >= manifest.source_offset]
        path = run_dir / c.METRICS
        pos = manifest.source_offset
        last = manifest.last_step
        if not path.exists():
            return 0
        with path.open("rb") as f:
            while True:
                f.seek(pos)
                chunk = f.read(CHUNK)
                if (cut := chunk.rfind(b"\n")) < 0:
                    break
                start = 0
                stop = False
                while start <= cut:
                    end = chunk.index(b"\n", start)
                    here = pos + start
                    while pending and pending[0][0] <= here:
                        offset, resume = pending.pop(0)
                        writer.truncate_from(resume)
                        manifest.attempts.append([offset, resume])
                        last = None if resume == 0 else resume - 1
                    row = decode(chunk[start:end]) if end > start else None
                    if isinstance(row, dict) and isinstance(step := row.get("_step"), int):
                        if last is not None and step < last:
                            if status == "running":
                                # its attempt_started event is still on the way; wait.
                                stop = True
                                break
                            writer.truncate_from(step)
                            manifest.attempts.append([here, step])
                        last = step
                        appended = False
                        for key, value in row.items():
                            if key[:1] != "_" and isinstance(value, (int, float)):
                                writer.append(key, step, float(value))
                                appended = True
                        if appended and isinstance(t := row.get("_t"), (int, float)):
                            writer.append(TIME_KEY, step, float(t))
                    start = end + 1
                pos += start
                if stop or len(chunk) < CHUNK:
                    break
        writer.commit(pos)
        return pos


def read_notes(folder: Path, logdir: Path) -> list[dict[str, Any]]:
    """Read every note version in a ``notes/`` folder for the timeline.

    :param folder: The ``notes/`` folder.
    :param logdir: The log dir, for relative paths.
    :return: Rows for ``Store.replace_notes``; damaged notes are skipped."""
    out = []
    for path in versions(folder):
        try:
            doc = read_markdown_doc(path, kind="note")
        except (SchemaError, ValueError, OSError):
            continue
        out.append(
            {
                "path": path.relative_to(logdir).as_posix(),
                "id": doc.id,
                "t": id_time(doc.id).timestamp(),
                "type": doc.meta.get("type"),
                "description": doc.meta.get("description"),
                "meta": doc.meta,
                "links": note_links(doc.meta, doc.body),
            }
        )
    return out
