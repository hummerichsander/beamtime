"""Readers for the files of a run directory."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.constants import DataKind, DerivedStatus, RunStatus
from beamtime.format.io import Chunk, read_json, read_jsonl
from beamtime.format.schema import SchemaError, schema_of

SEGMENT = re.compile(r"\[beamtime: output segment (\d+)\]")


@dataclass(kw_only=True, frozen=True)
class Attempt:
    """One start of a run; a resumed run has several."""

    started_at: str
    host: str | None = None
    resume_step: int | None = None


@dataclass(kw_only=True, frozen=True)
class RunInfo:
    """The identity, environment, status and proposal membership of a run."""

    schema: int
    id: str
    name: str
    status: RunStatus
    created_at: str
    tags: list[str] = field(default_factory=list)
    ended_at: str | None = None
    exit: dict[str, Any] | None = None
    attempts: list[Attempt] = field(default_factory=list)
    proposals: dict[str, str] = field(default_factory=dict)
    proposal_hashes: dict[str, str] = field(default_factory=dict)
    job_key: str | None = None
    host: dict[str, Any] = field(default_factory=dict)
    scheduler: dict[str, Any] | None = None
    git: dict[str, Any] | None = None
    command: list[str] = field(default_factory=list)
    cwd: str | None = None
    beamtime_version: str | None = None


def read_run_info(run_dir: Path) -> RunInfo:
    """Read ``_run.json``.

    :param run_dir: The run directory.
    :return: The run's identity and status."""
    path = run_dir / c.RUN
    d = read_json(path)
    match schema_of(d, kind="run", path=path):
        case 1:
            return RunInfo(
                schema=1,
                id=d["id"],
                name=d["name"],
                status=d["status"],
                created_at=d["created_at"],
                tags=d.get("tags") or [],
                ended_at=d.get("ended_at"),
                exit=d.get("exit"),
                attempts=[
                    Attempt(
                        started_at=a["started_at"],
                        host=a.get("host"),
                        resume_step=a.get("resume_step"),
                    )
                    for a in d.get("attempts") or []
                ],
                proposals=d.get("proposals") or {},
                proposal_hashes=d.get("proposal_hashes") or {},
                job_key=d.get("job_key"),
                host=d.get("host") or {},
                scheduler=d.get("scheduler"),
                git=d.get("git"),
                command=d.get("command") or [],
                cwd=d.get("cwd"),
                beamtime_version=d.get("beamtime_version"),
            )
        case v:
            raise SchemaError(f"{path}: no reader for run schema {v}.")


def run_status(info: RunInfo, *, heartbeat: float, now: float) -> DerivedStatus:
    """Derive the status shown for a run: a running run with a stale heartbeat is lost.

    :param info: The run's ``_run.json``.
    :param heartbeat: The modification time of ``_run.json``, in unix seconds.
    :param now: The time to judge against, e.g. a pulled snapshot's time.
    :return: The run status, or ``lost``."""
    return derived_status(info.status, heartbeat, now)


def derived_status(status: Any, heartbeat: float | None, now: float) -> Any:
    """Apply the one lost-run rule: running with a heartbeat older than ``LOST_AFTER_S`` is lost.

    :param status: The status ``_run.json`` records.
    :param heartbeat: The modification time of ``_run.json``.
    :param now: The time to judge against.
    :return: The status shown."""
    if status == "running" and heartbeat is not None and now - heartbeat > c.LOST_AFTER_S:
        return "lost"
    return status


def read_config(run_dir: Path) -> dict[str, Any]:
    """Read ``_config.json`` without its ``schema`` field.

    :param run_dir: The run directory.
    :return: The hyperparameters, nested as logged."""
    path = run_dir / c.CONFIG
    d = read_json(path)
    match schema_of(d, kind="config", path=path):
        case 1:
            return {k: v for k, v in d.items() if k != "schema"}
        case v:
            raise SchemaError(f"{path}: no reader for config schema {v}.")


@dataclass(kw_only=True, frozen=True)
class MetricSummary:
    """The shape of one scalar metric; statistics cover finite values only."""

    count: int
    nonfinite: int = 0
    first: float | None = None
    last: float | None = None
    ema_last: float | None = None
    min: float | None = None
    min_step: int | None = None
    max: float | None = None
    max_step: int | None = None
    mean: float | None = None
    last_step: int | None = None
    slope_last10pct: float | None = None


@dataclass(kw_only=True, frozen=True)
class Card:
    """The compact summary of a run that run tables are built from."""

    schema: int
    status: RunStatus
    duration_s: float | None = None
    steps: int | None = None
    steps_per_s: float | None = None
    error: str | None = None
    warnings: int = 0
    metrics: dict[str, MetricSummary] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)


def read_card(run_dir: Path) -> Card:
    """Read ``_run_card.json``.

    :param run_dir: The run directory.
    :return: The run card."""
    path = run_dir / c.CARD
    d = read_json(path)
    match schema_of(d, kind="card", path=path):
        case 1:
            fields = MetricSummary.__dataclass_fields__
            return Card(
                schema=1,
                status=d["status"],
                duration_s=d.get("duration_s"),
                steps=d.get("steps"),
                steps_per_s=d.get("steps_per_s"),
                error=d.get("error"),
                warnings=d.get("warnings", 0),
                metrics={
                    k: MetricSummary(**{f: v for f, v in m.items() if f in fields})
                    for k, m in (d.get("metrics") or {}).items()
                },
                values=d.get("values") or {},
            )
        case v:
            raise SchemaError(f"{path}: no reader for card schema {v}.")


@dataclass(kw_only=True, frozen=True)
class MetricPreview:
    """A metric's downsampled curve; bucket ``i`` covers steps from
    ``(first_bucket + i) * bucket_width``, and empty buckets are ``None``."""

    bucket_width: int
    first_bucket: int
    min: list[float | None]
    max: list[float | None]
    last: list[float | None]
    mean: list[float | None]
    count: list[int | None]


@dataclass(kw_only=True, frozen=True)
class Preview:
    """Downsampled curves of every metric of a run."""

    schema: int
    metrics: dict[str, MetricPreview] = field(default_factory=dict)


def read_preview(run_dir: Path) -> Preview:
    """Read ``_preview.json``.

    :param run_dir: The run directory.
    :return: The preview."""
    path = run_dir / c.PREVIEW
    d = read_json(path)
    match schema_of(d, kind="preview", path=path):
        case 1:
            return Preview(
                schema=1,
                metrics={
                    k: MetricPreview(
                        bucket_width=m["bucket_width"],
                        first_bucket=m["first_bucket"],
                        min=m["min"],
                        max=m["max"],
                        last=m["last"],
                        mean=m["mean"],
                        count=m["count"],
                    )
                    for k, m in (d.get("metrics") or {}).items()
                },
            )
        case v:
            raise SchemaError(f"{path}: no reader for preview schema {v}.")


def _stream(path: Path, offset: int, schema: int, kind: str) -> Chunk:
    """Read a JSON Lines stream of a run, whose schema is the run's.

    :param path: The stream.
    :param offset: The byte offset to start from.
    :param schema: The schema of the run's ``_run.json``.
    :param kind: The stream kind, for errors.
    :return: The complete records from ``offset`` on."""
    match schema:
        case 1:
            if not path.exists():
                return Chunk(end=offset)
            return read_jsonl(path, offset)
        case v:
            raise SchemaError(f"{path}: no reader for {kind} schema {v}.")


def read_metrics(run_dir: Path, offset: int = 0, *, schema: int = 1) -> Chunk:
    """Read ``_metrics.jsonl``: one sparse record per ``log()`` call.

    :param run_dir: The run directory.
    :param offset: The byte offset to continue from.
    :param schema: The schema of the run's ``_run.json``.
    :return: The records and the offset to continue from."""
    return _stream(run_dir / c.METRICS, offset, schema, "metrics")


@dataclass(kw_only=True, frozen=True)
class Event:
    """A lifecycle, diagnostic or user event of a run."""

    t: float
    kind: str
    step: int | None = None
    message: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


def read_events(run_dir: Path, *, schema: int = 1) -> list[Event]:
    """Read ``_events.jsonl``.

    :param run_dir: The run directory.
    :param schema: The schema of the run's ``_run.json``.
    :return: The events in the order they were written."""
    rows = _stream(run_dir / c.EVENTS, 0, schema, "events").rows
    own = {"_t", "_step", "kind", "message"}
    return [
        Event(
            t=r["_t"],
            kind=r["kind"],
            step=r.get("_step"),
            message=r.get("message"),
            data={k: v for k, v in r.items() if k not in own},
        )
        for r in rows
    ]


@dataclass(kw_only=True, frozen=True)
class DataEntry:
    """A logged table, image or text; inline or stored below ``_data/``."""

    step: int
    t: float
    key: str
    kind: DataKind
    path: str | None = None
    columns: dict[str, list[Any]] | None = None
    text: str | None = None


def read_data(run_dir: Path, *, schema: int = 1) -> list[DataEntry]:
    """Read ``_data.jsonl``.

    :param run_dir: The run directory.
    :param schema: The schema of the run's ``_run.json``.
    :return: The logged data entries; file contents are not loaded."""
    rows = _stream(run_dir / c.DATA, 0, schema, "data").rows
    return [
        DataEntry(
            step=r["_step"],
            t=r["_t"],
            key=r["key"],
            kind=r["kind"],
            path=r.get("path"),
            columns=r.get("columns"),
            text=r.get("text"),
        )
        for r in rows
    ]


@dataclass(kw_only=True, frozen=True)
class Artifact:
    """A file a run produced, copied into ``artifacts/`` or recorded by ``uri``."""

    name: str
    size: float | None = None
    path: str | None = None
    uri: str | None = None
    kind: str | None = None


def read_artifacts(run_dir: Path, *, schema: int = 1) -> list[Artifact]:
    """Read ``_artifacts.jsonl``.

    :param run_dir: The run directory.
    :param schema: The schema of the run's ``_run.json``.
    :return: The recorded artifacts."""
    rows = _stream(run_dir / c.ARTIFACTS, 0, schema, "artifacts").rows
    return [
        Artifact(
            name=r["name"],
            size=r.get("size"),
            path=r.get("path"),
            uri=r.get("uri"),
            kind=r.get("kind"),
        )
        for r in rows
    ]


def read_output(run_dir: Path, *, rank: int = 0) -> str:
    """Read a rank's captured output: the head, then the previous and current tail.

    Tail segments start with ``[beamtime: output segment N]``; if the first kept segment
    is not the first one, a marker says which segments were not kept. Where the writer
    dropped output, it wrote a marker line itself.

    :param run_dir: The run directory.
    :param rank: The rank; 0 is the main process.
    :return: The output text."""
    head, tail, prev = (run_dir / n for n in c.output_names(rank))
    text = head.read_text(errors="replace") if head.exists() else ""
    tails = [p.read_text(errors="replace") for p in (prev, tail) if p.exists()]
    if tails and (m := SEGMENT.match(tails[0])) and (n := int(m[1])) > 1:
        gap = "1" if n == 2 else f"1–{n - 1}"
        text += f"[… beamtime: output segments {gap} not kept …]\n"
    return text + "".join(tails)


def merge_attempts(
    segments: list[tuple[int | None, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """Combine the metric records of a run's attempts: the newer attempt wins.

    :param segments: Per attempt, oldest first, its resume step and its records.
    :return: The effective records, sorted by step."""
    rows: list[dict[str, Any]] = []
    for resume_step, segment in segments:
        if resume_step is not None:
            rows = [r for r in rows if r["_step"] < resume_step]
        rows.extend(segment)
    return sorted(rows, key=lambda r: r["_step"])


def read_effective_metrics(run_dir: Path, *, schema: int = 1) -> list[dict[str, Any]]:
    """Read ``_metrics.jsonl`` with attempts resolved from ``attempt_started`` events.

    :param run_dir: The run directory.
    :param schema: The schema of the run's ``_run.json``.
    :return: The effective records, sorted by step."""
    starts = [
        (e.data.get("metrics_offset", 0), e.data.get("resume_step"))
        for e in read_events(run_dir, schema=schema)
        if e.kind == "attempt_started"
    ] or [(0, None)]
    chunks = [read_metrics(run_dir, offset, schema=schema) for offset, _ in starts]
    segments = []
    for i, ((_, resume_step), chunk) in enumerate(zip(starts, chunks, strict=True)):
        later = len(chunks[i + 1].rows) if i + 1 < len(chunks) else 0
        segments.append((resume_step, chunk.rows[: len(chunk.rows) - later]))
    return merge_attempts(segments)
