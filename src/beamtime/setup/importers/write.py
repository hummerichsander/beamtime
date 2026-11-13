"""The one writer of imported runs."""

import os
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.ids import new_run_id
from beamtime.format.io import json_line, read_json, write_bytes_replaced, write_replaced
from beamtime.format.times import iso
from beamtime.setup.importers import Imported
from beamtime.synth.summary import card_and_preview

IMPORTED = "imported"


def write_run(logdir: Path, dest: str, imported: Imported, provenance: dict[str, str]) -> Path:
    """Write an imported run as a run folder; a run imported before is left as it is.

    ``_run.json`` goes last, so a crash leaves a folder no reader sees.

    :param logdir: The log dir.
    :param dest: The group the run goes into, relative to the log dir, e.g. ``imported/mnist``.
    :param imported: The run.
    :param provenance: The source's ``kind`` and the absolute ``path`` of the original.
    :return: The run folder."""
    if (found := find_imported(logdir, provenance["path"], imported.source_id)) is not None:
        return found
    rows = sorted(
        (
            {"_step": r["_step"], "_t": r.get("_t", imported.created_at)}
            | {k: v for k, v in r.items() if k not in ("_step", "_t")}
            for r in imported.rows
        ),
        key=lambda r: r["_step"],
    )
    end = imported.ended_at
    card, preview = card_and_preview(
        rows,
        status=imported.status,
        duration_s=end - imported.created_at if end is not None else 0.0,
    )
    run_id = new_run_id(now=datetime.fromtimestamp(imported.created_at, timezone.utc))
    d = logdir / dest / run_id
    d.mkdir(parents=True)
    host = socket.gethostname()
    source = {"id": imported.source_id} if imported.source_id else {}
    info = {
        "schema": 1,
        "id": run_id,
        "name": imported.name,
        "tags": [],
        "status": imported.status,
        "created_at": iso(imported.created_at),
        "ended_at": iso(end) if end is not None else None,
        "attempts": [{"started_at": iso(imported.created_at), "host": None, "resume_step": None}],
        "proposals": {},
        "proposal_hashes": {},
        "host": imported.host or {},
        "git": imported.git,
        "command": imported.command or [],
        "imported_from": provenance | source | {"host": host, "at": iso(time.time())},
    }
    write_replaced(d / c.CONFIG, {"schema": 1, **imported.config})
    write_bytes_replaced(d / c.METRICS, b"".join(json_line(r) for r in rows))
    write_replaced(d / c.CARD, card)
    write_replaced(d / c.PREVIEW, preview)
    write_replaced(d / c.RUN, info)
    return d


def find_imported(logdir: Path, path: str, source_id: str | None) -> Path | None:
    """Look for a run imported from the same original, below ``imported/`` only.

    :param logdir: The log dir.
    :param path: The absolute path of the original.
    :param source_id: The source's own run id, if it has one.
    :return: The run folder, or ``None``."""
    for folder, _, names in os.walk(logdir / IMPORTED):
        if c.RUN not in names:
            continue
        try:
            origin: Any = read_json(Path(folder) / c.RUN).get("imported_from")
        except (OSError, ValueError):
            continue
        if origin and origin.get("path") == path and origin.get("id") == source_id:
            return Path(folder)
    return None
