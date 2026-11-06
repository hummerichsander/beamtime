"""The run: ``init``, ``Run``, ``NullRun`` and ``current``."""

import argparse
import atexit
import dataclasses
import json
import os
import shutil
import signal
import sys
import threading
import time
import traceback
from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import Any, Literal

import yaml

from beamtime.format import constants as c
from beamtime.format.authored import file_hash, newest
from beamtime.format.ids import new_run_id, new_version_id
from beamtime.format.io import json_line, read_json, write_created, write_replaced
from beamtime.format.names import random_name
from beamtime.format.run import read_card, read_config, read_effective_metrics
from beamtime.format.schema import schema_of
from beamtime.format.times import iso, parse_iso
from beamtime.sdk import env
from beamtime.sdk.capture import Capture, LogFiles
from beamtime.sdk.data import Data, plain
from beamtime.sdk.paths import Location, find_run, locate
from beamtime.sdk.stats import MetricStats
from beamtime.sdk.system import Sampler, hardware

FLUSH_EVERY_S = 2.0
SYSTEM_EVERY_S = 30.0
SYSTEM_SLOW_S = 2.0
FLUSH_AT_BYTES = 1024 * 1024
PENDING_CAP = 64 * 1024 * 1024
COPY_BELOW = 100 * 1024 * 1024
RANK_WAIT_S = 120.0
RANK_RECENT_S = 600.0

_current: "Run | None" = None


def current() -> "Run | None":
    """Return the active run of this process, for code deep in a library.

    :return: The run, or ``None`` if none is active."""
    return _current


def jsonable(obj: Any) -> Any:
    """Make a value JSON-ready, turning unknown objects into strings.

    :param obj: The value.
    :return: A copy made only of JSON types."""
    return json.loads(json.dumps(obj, default=lambda o: plain(o)))


def to_config(config: Any) -> dict[str, Any]:
    """Convert a config object to a plain nested dict.

    :param config: A dict, dataclass, Pydantic model, ``argparse.Namespace`` or
        OmegaConf config, or ``None``.
    :return: The config as JSON-ready dict."""
    if config is None:
        out: Any = {}
    elif isinstance(config, Mapping) and type(config).__module__.split(".")[0] != "omegaconf":
        out = dict(config)
    elif dataclasses.is_dataclass(config) and not isinstance(config, type):
        out = dataclasses.asdict(config)
    elif hasattr(config, "model_dump"):
        out = config.model_dump()
    elif isinstance(config, argparse.Namespace):
        out = vars(config)
    elif "omegaconf" in sys.modules and type(config).__module__.startswith("omegaconf"):
        from omegaconf import OmegaConf

        out = OmegaConf.to_container(config, resolve=True)
    else:
        raise ValueError(
            "config must be a dict, dataclass, Pydantic model, argparse.Namespace or "
            f"OmegaConf config, not {type(config).__name__}"
        )
    out = jsonable({str(k): v for k, v in out.items()})
    if "schema" in out:
        raise ValueError("config key 'schema' is reserved by Beamtime; rename it")
    return out


def to_proposal(proposal: str | Path | dict[str, Any] | None) -> dict[str, Any]:
    """Read the run's own proposal from its argument or ``BEAMTIME_PROPOSAL``.

    :param proposal: A statement, a dict in the proposal shape, a path to a YAML file,
        or ``None`` for ``BEAMTIME_PROPOSAL`` or a blank proposal.
    :return: The proposal fields."""
    if proposal is None and (path := os.environ.get("BEAMTIME_PROPOSAL")):
        proposal = Path(path)
    if isinstance(proposal, str) and proposal.endswith((".yaml", ".yml")):
        if Path(proposal).is_file():
            proposal = Path(proposal)
    match proposal:
        case None:
            return {"statement": None}
        case Path():
            data = yaml.safe_load(proposal.read_text())
            if not isinstance(data, dict):
                raise ValueError(f"proposal file {proposal} must hold a mapping")
            return data
        case str():
            return {"statement": proposal}
        case dict():
            return dict(proposal)
        case _:
            raise ValueError(f"proposal must be a str, dict, path or None, not {proposal!r}")


def scalar(value: Any) -> bool | int | float | None:
    """Read a scalar from a Python number, a NumPy scalar or a 0-d tensor.

    :param value: The logged value.
    :return: The plain number, or ``None`` if it is not a scalar."""
    if isinstance(value, (bool, int, float)):
        return value
    if hasattr(value, "item") and getattr(value, "ndim", 0) == 0:
        try:
            item = value.item()
        except Exception:
            return None
        return item if isinstance(item, (bool, int, float)) else None
    return None


class RunConfig(Mapping):
    """The run's config: readable like a dict, extended with ``update``."""

    def __init__(self, *, run: "Run", values: dict[str, Any]) -> None:
        """Wrap the stored config.

        :param run: The run that owns it.
        :param values: The config values."""
        self.run = run
        self.values = values

    def __getitem__(self, key: str) -> Any:
        """Read a config value.

        :param key: The key.
        :return: The value."""
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over the keys.

        :return: The key iterator."""
        return iter(self.values)

    def __len__(self) -> int:
        """Count the keys.

        :return: The number of keys."""
        return len(self.values)

    def update(self, values: Any = None, **kwargs: Any) -> None:
        """Add keys; a different value for an existing key warns and is ignored.

        :param values: A dict or another config object.
        :param kwargs: More keys."""
        self.run.guard("config", self.run.update_config, values, kwargs)


class Run:
    """A run being recorded; every method is safe to call and never raises."""

    def __init__(
        self,
        *,
        dir: Path,
        info: dict[str, Any],
        config: dict[str, Any],
        capture: Capture | None,
        resume_last_step: int | None = None,
        resuming: bool = False,
    ) -> None:
        """Set up the in-memory state of a run whose files exist; ``init`` creates it.

        :param dir: The run directory.
        :param info: The content of ``_run.json``.
        :param config: The stored config.
        :param capture: The output capture, or ``None``.
        :param resume_last_step: The last effective step of a resumed run.
        :param resuming: Whether the new attempt's resume step is still open."""
        self.dir = dir
        self.info = info
        self.config = RunConfig(run=self, values=config)
        self.capture = capture
        self.card: dict[str, Any] = {}
        self.lock = threading.RLock()
        self.io_lock = threading.Lock()
        self.pending: dict[str, list[bytes]] = {}
        self.pending_size = 0
        self.jobs: list[Callable[[], None]] = []
        self.stats: dict[str, MetricStats] = {}
        self.step: int | None = None
        self.warned: set[str] = set()
        self.warnings = 0
        self.error: str | None = None
        self.data_names: set[str] = set()
        self.config_dirty = False
        self.ended = False
        self.inert = False
        self.resuming = resuming
        self.resume_last_step = resume_last_step
        self.started = time.time()
        self.created = parse_iso(info["created_at"])
        self.wake = threading.Event()
        self.stopping = False
        self.pump = threading.Thread(target=self.pump_loop, name="beamtime-pump", daemon=True)
        # system metrics: set by init unless turned off; the last step they were written at.
        self.sampler: Sampler | None = None
        self.sampled_step: int | None = None

    @property
    def id(self) -> str:
        """The run id."""
        return self.info["id"]

    @property
    def name(self) -> str:
        """The run name."""
        return self.info["name"]

    def __enter__(self) -> "Run":
        """Use the run as a context manager.

        :return: The run."""
        return self

    def __exit__(self, kind: Any, error: Any, tb: Any) -> Literal[False]:
        """Finish the run, as failed or killed if the block raised.

        :param kind: The exception type, if any.
        :param error: The exception, if any.
        :param tb: The traceback, if any.
        :return: ``False``, so exceptions propagate."""
        if kind is None:
            self.finish()
        elif issubclass(kind, KeyboardInterrupt):
            self.end("killed", exit={"signal": "SIGINT"}, reason="interrupted")
        else:
            self.end_failed(kind, error, tb)
        return False

    def guard(self, what: str, fn: Callable[..., Any], *args: Any) -> Any:
        """Call an SDK operation; an error becomes a warning, never an exception.

        :param what: The operation, for the warning.
        :param fn: The function.
        :param args: Its arguments.
        :return: The function's result, or ``None`` after an error."""
        if self.inert or self.ended:
            return None
        try:
            return fn(*args)
        except Exception as e:
            self.warn(f"{what}:{type(e).__name__}", f"{what} failed: {e!r}")
            return None

    def warn(self, key: str, message: str) -> None:
        """Report an absorbed problem once per key: stderr, an event and the card count.

        :param key: Deduplication key.
        :param message: What happened."""
        with self.lock:
            if key in self.warned:
                return
            self.warned.add(key)
            self.warnings += 1
            self.queue(c.EVENTS, {"_t": time.time(), "kind": "warning", "message": message})
        try:
            sys.stderr.write(f"beamtime: warning: {message}\n")
        except Exception:
            pass

    def queue(self, name: str, record: dict[str, Any]) -> None:
        """Queue a JSON line for one of the run's streams; the pump writes it.

        :param name: The stream file name.
        :param record: The record."""
        line = json_line(record)
        with self.lock:
            if self.pending_size + len(line) > PENDING_CAP:
                if "pending-full" not in self.warned:
                    self.warned.add("pending-full")
                    self.warnings += 1
                return
            self.pending.setdefault(name, []).append(line)
            self.pending_size += len(line)
        if self.pending_size > FLUSH_AT_BYTES:
            self.wake.set()

    def log(self, values: dict[str, Any], step: int | None = None) -> None:
        """Log scalars and data at a step.

        :param values: Key to a number, a 0-d array or tensor, or a data wrapper.
        :param step: The step; by default one more than the last."""
        self.guard("log", self.log_values, values, step)

    def log_values(self, values: dict[str, Any], step: int | None) -> None:
        """Log values; the unguarded body of ``log``.

        :param values: Key to value.
        :param step: The step, or ``None``."""
        with self.lock:
            if self.resuming:
                self.settle(step)
            if step is None:
                step = 0 if self.step is None else self.step + 1
            else:
                step = int(step)
                if self.step is not None and step < self.step:
                    for key in values:
                        self.warn(
                            f"decreasing:{key}",
                            f"step {step} of {key!r} is below the last step "
                            f"{self.step}; dropped (and silently from now on)",
                        )
                    return
            self.step = step
            t = round(time.time(), 3)
            row: dict[str, Any] = {"_step": step, "_t": t}
            for key, value in values.items():
                if not isinstance(key, str) or not key or key.startswith("_"):
                    self.warn(f"key:{key}", f"key {key!r} is reserved or invalid; dropped")
                elif isinstance(value, Data):
                    self.log_data(key, step, t, value)
                elif (x := scalar(value)) is not None:
                    row[key] = x
                    self.stats.setdefault(key, MetricStats()).add(step, float(x))
                else:
                    self.warn(
                        f"type:{key}",
                        f"{key!r} is a {type(value).__name__}, not a scalar or a "
                        "data wrapper; dropped",
                    )
            if len(row) > 2:
                self.queue(c.METRICS, row)

    def log_data(self, key: str, step: int, t: float, value: Data) -> None:
        """Encode a data wrapper and queue its record and file.

        :param key: The key.
        :param step: The step.
        :param t: The time.
        :param value: The wrapper."""
        try:
            enc = value.encode()
        except Exception as e:
            self.warn(f"data:{key}", f"could not encode {key!r}: {e!r}; dropped")
            return
        record = {"_step": step, "_t": t, "key": key} | enc.fields
        if enc.content is not None:
            base = f"{c.DATA_DIR}/{c.key_to_path(key)}/{step}"
            path, n = f"{base}.{enc.ext}", 1
            while path in self.data_names or (self.dir / path).exists():
                path, n = f"{base}-{n}.{enc.ext}", n + 1
            self.data_names.add(path)
            target, content = self.dir / path, enc.content
            self.jobs.append(lambda: write_created(target, content))
            record["path"] = path
        self.queue(c.DATA, record)

    def event(self, message: str, **data: Any) -> None:
        """Record a user event in ``_events.jsonl``.

        :param message: What happened.
        :param data: Extra fields."""
        record = {
            "_t": time.time(),
            "_step": self.step,
            "kind": "user",
            "message": message,
        }
        self.guard("event", self.queue, c.EVENTS, record | jsonable(data))

    def artifact(
        self,
        path: str | Path,
        kind: str | None = None,
        copy: bool | None = None,
        **data: Any,
    ) -> None:
        """Record a file the run produced, copying small ones into ``artifacts/``.

        :param path: The file.
        :param kind: E.g. ``checkpoint``.
        :param copy: Copy or reference; by default files below 100 MB are copied.
        :param data: Extra fields, e.g. the monitored score of a checkpoint."""
        self.guard("artifact", self.add_artifact, Path(path), kind, copy, data)

    def add_artifact(
        self, path: Path, kind: str | None, copy: bool | None, data: dict[str, Any]
    ) -> None:
        """Record an artifact; the unguarded body of ``artifact``.

        :param path: The file.
        :param kind: Its kind.
        :param copy: Whether to copy it.
        :param data: Extra fields."""
        size = path.stat().st_size
        record: dict[str, Any] = {"name": path.name, "size": size, "kind": kind}
        record |= jsonable(data)
        if path.is_file() and (copy if copy is not None else size < COPY_BELOW):
            with self.lock:
                rel, n = f"artifacts/{path.name}", 1
                while rel in self.data_names or (self.dir / rel).exists():
                    rel, n = f"artifacts/{path.stem}-{n}{path.suffix}", n + 1
                self.data_names.add(rel)
                target, source = self.dir / rel, path.resolve()

                def copy_file() -> None:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)

                self.jobs.append(copy_file)
            record["path"] = rel
        else:
            record["uri"] = str(path.resolve())
        self.queue(c.ARTIFACTS, record)

    def update_config(self, values: Any, kwargs: dict[str, Any]) -> None:
        """Add config keys; the unguarded body of ``config.update``.

        :param values: A config object, or ``None``.
        :param kwargs: More keys."""
        new = to_config(values) | jsonable(kwargs)
        with self.lock:
            for key, value in new.items():
                if key not in self.config.values:
                    self.config.values[key] = value
                    self.config_dirty = True
                elif self.config.values[key] != value:
                    self.warn(
                        f"config:{key}",
                        f"config {key!r} is already {self.config.values[key]!r}; "
                        f"the new value {value!r} is ignored",
                    )

    def settle(self, step: int | None) -> None:
        """Start the new attempt of a resumed run once its resume step is known.

        :param step: The first step logged in this attempt, or ``None`` for last + 1."""
        last = self.resume_last_step
        resume = step if step is not None else (0 if last is None else last + 1)
        rows = read_effective_metrics(self.dir)
        for row in rows:
            if row["_step"] >= resume:
                break
            for key, value in row.items():
                if not key.startswith("_") and isinstance(value, (int, float)):
                    self.stats.setdefault(key, MetricStats()).add(row["_step"], float(value))
        metrics = self.dir / c.METRICS
        offset = metrics.stat().st_size if metrics.exists() else 0
        self.info["attempts"].append(
            {
                "started_at": iso(self.started, ms=True),
                "host": self.info["host"].get("hostname"),
                "resume_step": resume,
            }
        )
        self.queue(
            c.EVENTS,
            {
                "_t": round(self.started, 3),
                "kind": "attempt_started",
                "resume_step": resume,
                "metrics_offset": offset,
            },
        )
        # the attempt continues at its resume step, also with implicit steps.
        self.step = resume - 1 if resume > 0 else None
        self.resuming = False
        self.write_info()

    def pump_loop(self) -> None:
        """Write queued lines, beat the heart, and rewrite card and preview."""
        beat = card = system = time.monotonic()
        while True:
            self.wake.wait(FLUSH_EVERY_S)
            self.wake.clear()
            if self.stopping:
                return
            try:
                self.flush()
                now = time.monotonic()
                if now - beat >= c.HEARTBEAT_S:
                    beat = now
                    os.utime(self.dir / c.RUN)
                if now - card >= c.CARD_EVERY_S and not self.resuming:
                    card = now
                    self.write_card()
                if now - system >= SYSTEM_EVERY_S and self.sampler is not None:
                    system = now
                    self.sample_system()
            except Exception as e:
                self.warn(f"pump:{type(e).__name__}", f"writing run files failed: {e!r}")

    def sample_system(self) -> None:
        """Write a sample of system metrics at the current step, at most one per step.

        Samples carry no time of their own and never move the step: they sit next to what
        training logged. A sampler that fails or is slow turns itself off with one warning."""
        sampler = self.sampler
        if sampler is None or self.step is None or self.step == self.sampled_step:
            return
        started = time.monotonic()
        try:
            values = sampler.sample()
        except Exception as e:
            self.sampler = None
            self.warn("system", f"system metrics failed ({e!r}); turned off")
            return
        if time.monotonic() - started > SYSTEM_SLOW_S:
            self.sampler = None
            self.warn("system", "sampling system metrics was slow; turned off")
        with self.lock:
            # the step at queueing time: rows in _metrics.jsonl never go back in step.
            if not values or self.step is None or self.resuming or self.step == self.sampled_step:
                return
            for key, value in values.items():
                self.stats.setdefault(key, MetricStats()).add(self.step, value)
            self.queue(c.METRICS, {"_step": self.step, **values})
            self.sampled_step = self.step

    def flush(self, *, sync: bool = False) -> None:
        """Write queued lines, files and config changes.

        :param sync: Whether to fsync the streams, as at the end of the run."""
        with self.lock:
            pending, self.pending, self.pending_size = self.pending, {}, 0
            jobs, self.jobs = self.jobs, []
            config = dict(self.config.values) if self.config_dirty else None
            self.config_dirty = False
        with self.io_lock:
            for job in jobs:
                job()
            for name, lines in pending.items():
                with (self.dir / name).open("ab") as f:
                    f.write(b"".join(lines))
                    if sync:
                        f.flush()
                        os.fsync(f.fileno())
            if config is not None:
                write_replaced(self.dir / c.CONFIG, {"schema": 1, **config})

    def build_card(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Assemble the run card and the preview from the running statistics.

        :return: ``_run_card.json`` and ``_preview.json``."""
        with self.lock:
            duration = time.time() - self.created
            steps = self.step or 0
            card = {
                "schema": 1,
                "status": self.info["status"],
                "duration_s": round(duration, 3),
                "steps": steps,
                "steps_per_s": round(steps / duration, 3) if duration > 0 else None,
                "error": self.error,
                "warnings": self.warnings,
                "metrics": {k: s.card() for k, s in self.stats.items()},
                "values": jsonable(self.card),
            }
            previews = {k: p for k, s in self.stats.items() if (p := s.preview())}
        return card, {"schema": 1, "metrics": previews}

    def write_card(self, *, sync: bool = False) -> None:
        """Rewrite ``_run_card.json`` and ``_preview.json``.

        :param sync: Whether to fsync, as at the end of the run."""
        card, preview = self.build_card()
        with self.io_lock:
            write_replaced(self.dir / c.CARD, card, sync=sync)
            write_replaced(self.dir / c.PREVIEW, preview, sync=sync)

    def write_info(self, *, sync: bool = False) -> None:
        """Rewrite ``_run.json``.

        :param sync: Whether to fsync, as at the end of the run."""
        with self.lock:
            info = jsonable(self.info)
        with self.io_lock:
            write_replaced(self.dir / c.RUN, info, sync=sync)

    def start(self) -> None:
        """Start the pump thread."""
        self.pump.start()

    def finish(self, status: Literal["finished", "failed"] = "finished") -> None:
        """Finish the run: final card, preview and status, synced; twice is a no-op.

        :param status: ``finished`` or ``failed``."""
        if status not in ("finished", "failed"):
            self.warn("finish-status", f"finish status {status!r} is not allowed; finished")
            status = "finished"
        self.end(status)

    def end_failed(self, kind: Any, error: Any, tb: Any) -> None:
        """End the run as failed with the traceback of an exception.

        :param kind: The exception type.
        :param error: The exception.
        :param tb: The traceback."""
        text = "".join(traceback.format_exception(kind, error, tb))
        last = traceback.format_exception_only(kind, error)[-1].strip()
        self.end("failed", traceback_text=text, error=last, exit={"code": 1})

    def end(
        self,
        status: c.RunStatus,
        *,
        exit: dict[str, Any] | None = None,
        error: str | None = None,
        traceback_text: str | None = None,
        reason: str | None = None,
    ) -> None:
        """End the run with a status; the shared path of ``finish``, hooks and signals.

        :param status: The final status.
        :param exit: How the process ended, e.g. ``{"signal": "SIGTERM"}``.
        :param error: The last exception line.
        :param traceback_text: The full traceback of a failure.
        :param reason: Why the run was killed, e.g. ``interrupted``."""
        global _current
        with self.lock:
            if self.ended or self.inert:
                return
            self.ended = True
        try:
            with self.lock:
                if self.resuming:
                    self.settle(None)
                self.error = error
                event: dict[str, Any] = {
                    "_t": time.time(),
                    "_step": self.step,
                    "kind": status,
                }
                if traceback_text:
                    event["traceback"] = traceback_text
                if exit and "signal" in exit:
                    event["signal"] = exit["signal"]
                if reason:
                    event["reason"] = reason
                self.queue(c.EVENTS, event)
                self.info.update(status=status, ended_at=iso(time.time(), ms=True), exit=exit)
            self.stopping = True
            self.wake.set()
            if self.pump.is_alive():
                self.pump.join(5.0)
            self.flush(sync=True)
            self.write_card(sync=True)
            self.write_info(sync=True)
        except Exception as e:
            try:
                sys.stderr.write(f"beamtime: warning: finishing the run failed: {e!r}\n")
            except Exception:
                pass
        finally:
            if self.capture is not None:
                self.capture.stop()
            if _current is self:
                _current = None
            os.environ.pop("BEAMTIME_RUN_DIR", None)


class NullConfig(dict):
    """The config of a ``NullRun``: updates are ignored."""

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Ignore updates.

        :param args: Ignored.
        :param kwargs: Ignored."""


class NullRun:
    """The run on ranks other than 0: every method does nothing."""

    def __init__(self, *, rank: int, capture: Capture | None = None) -> None:
        """Create a run that records nothing.

        :param rank: This process's rank.
        :param capture: The rank's output capture, if any."""
        self.rank = rank
        self.capture = capture
        self.card: dict[str, Any] = {}
        self.config = NullConfig()
        self.dir: Path | None = None
        self.id: str | None = None
        self.name: str | None = None

    def log(self, values: dict[str, Any], step: int | None = None) -> None:
        """Do nothing.

        :param values: Ignored.
        :param step: Ignored."""

    def event(self, message: str, **data: Any) -> None:
        """Do nothing.

        :param message: Ignored.
        :param data: Ignored."""

    def artifact(
        self, path: Any, kind: str | None = None, copy: bool | None = None, **data: Any
    ) -> None:
        """Do nothing.

        :param path: Ignored.
        :param kind: Ignored.
        :param copy: Ignored.
        :param data: Ignored."""

    def finish(self, status: str = "finished") -> None:
        """Stop the rank's output capture.

        :param status: Ignored."""
        if self.capture is not None:
            self.capture.stop()

    def __enter__(self) -> "NullRun":
        """Use as a context manager.

        :return: The null run."""
        return self

    def __exit__(self, *exc: Any) -> Literal[False]:
        """Stop capture at the end of the block.

        :param exc: The exception information, ignored.
        :return: ``False``."""
        self.finish()
        return False


_hooks_installed = False


def install_hooks() -> None:
    """Install the exit, exception, signal and fork hooks once per process."""
    global _hooks_installed
    if _hooks_installed:
        return
    _hooks_installed = True
    atexit.register(on_exit)
    previous_hook = sys.excepthook

    def excepthook(kind: Any, error: Any, tb: Any) -> None:
        # print first, so the traceback is captured before capture stops.
        previous_hook(kind, error, tb)
        if (run := _current) is not None:
            if issubclass(kind, KeyboardInterrupt):
                run.end("killed", exit={"signal": "SIGINT"}, reason="interrupted")
            else:
                run.end_failed(kind, error, tb)

    sys.excepthook = excepthook
    if hasattr(os, "register_at_fork"):
        os.register_at_fork(after_in_child=on_fork)
    if threading.current_thread() is threading.main_thread() and hasattr(signal, "SIGUSR1"):
        for sig in (signal.SIGTERM, signal.SIGUSR1):
            chain_signal(sig)


def on_exit() -> None:
    """Finish the active run when the interpreter exits."""
    if (run := _current) is not None:
        run.end("finished")


def on_fork() -> None:
    """Make the active run inert in a forked child, so workers never write run files."""
    global _current
    if (run := _current) is not None:
        run.inert = True
    _current = None


def chain_signal(sig: signal.Signals) -> None:
    """Handle a signal and then pass it on to the handler that was installed before.

    :param sig: ``SIGTERM`` (the run is killed) or ``SIGUSR1`` (a requeue request)."""
    previous = signal.getsignal(sig)
    handling = False

    def handler(signum: int, frame: Any) -> None:
        nonlocal handling
        # a shell and a launcher (uv, srun) often both deliver the signal; a repeat that
        # arrives while the run is being ended must not cut that short.
        if handling:
            return
        handling = True
        run = _current
        name = signal.Signals(signum).name
        if run is not None and signum == signal.SIGUSR1:
            run.guard("signal", run.queue, c.EVENTS, {
                "_t": time.time(), "_step": run.step, "kind": "requeue_requested",
                "signal": name,
            })  # fmt: skip
        if run is not None and (signum == signal.SIGTERM or previous == signal.SIG_DFL):
            near_end = signum == signal.SIGTERM and env.near_time_limit(os.environ, time.time())
            run.end("killed", exit={"signal": name}, reason="time_limit" if near_end else None)
        try:
            if callable(previous):
                previous(signum, frame)
            elif previous == signal.SIG_DFL:
                signal.signal(signum, signal.SIG_DFL)
                os.kill(os.getpid(), signum)
        finally:
            handling = False

    signal.signal(sig, handler)


def in_notebook() -> bool:
    """Tell whether the process is a Jupyter kernel.

    :return: Whether ``ipykernel`` is loaded."""
    return "ipykernel" in sys.modules


def rank_capture(rank: int, folder: Path, job_key: str | None) -> Capture:
    """Capture a non-zero rank's output into rank 0's run directory once it is found.

    :param rank: The rank.
    :param folder: The folder rank 0 creates its run in.
    :param job_key: The launch's job key.
    :return: The started capture."""
    files = None
    if (env_dir := os.environ.get("BEAMTIME_RUN_DIR")) and Path(env_dir).is_dir():
        files = LogFiles(run_dir=Path(env_dir), rank=rank)
    capture = Capture(files=files, mode="stream" if in_notebook() else "fd")
    capture.start()
    atexit.register(capture.stop)
    if files is not None:
        return capture

    def find() -> None:
        deadline = time.monotonic() + RANK_WAIT_S
        while time.monotonic() < deadline:
            if job_key is not None and (run_dir := find_by_job_key(folder, job_key)):
                capture.set_files(LogFiles(run_dir=run_dir, rank=rank))
                return
            time.sleep(1.0)
        try:
            sys.__stderr__.write(f"beamtime: warning: rank {rank} found no run; not captured\n")
        except Exception:
            pass

    threading.Thread(target=find, name="beamtime-rank", daemon=True).start()
    return capture


def scan_runs(folder: Path) -> list[tuple[Path, dict[str, Any]]]:
    """List a folder's run directories with their parsed ``_run.json``.

    :param folder: The folder rank 0 creates its runs in.
    :return: Directory and info pairs; unreadable or missing files are skipped."""
    if not folder.is_dir():
        return []
    out = []
    for d in folder.iterdir():
        try:
            out.append((d, read_json(d / c.RUN)))
        except (OSError, ValueError):
            continue
    return out


def find_by_job_key(folder: Path, job_key: str) -> Path | None:
    """Find a recently created running run of the same launch in a folder.

    :param folder: The folder rank 0 creates its run in.
    :param job_key: The launch's job key.
    :return: The newest matching run directory, or ``None``."""
    found = [
        d
        for d, info in scan_runs(folder)
        if info.get("job_key") == job_key
        and info.get("status") == "running"
        and time.time() - parse_iso(info["created_at"]) < RANK_RECENT_S
    ]
    return max(found, default=None, key=lambda d: d.name)


UNFINISHED = ("running", "killed")


def resume_by_key(folder: Path, key: str) -> tuple[str, str] | None:
    """Find the newest run in a folder recorded under a given key.

    :param folder: The folder rank 0 creates its runs in.
    :param key: The key.
    :return: Its id and status, or ``None`` if no run carries this key."""
    matches = [(d, info) for d, info in scan_runs(folder) if info.get("key") == key]
    if not matches:
        return None
    d, info = max(matches, key=lambda m: m[0].name)
    return info.get("id", d.name), info.get("status", "finished")


def resume_candidates(folder: Path, job_key: str | None, name: str | None) -> list[str]:
    """Find a folder's unfinished runs from the same job launch.

    :param folder: The folder rank 0 creates its runs in.
    :param job_key: The current launch's job key.
    :param name: The run name this call asked for, or ``None`` to not filter by it.
    :return: Their ids."""
    if job_key is None:
        return []
    return [
        info.get("id", d.name)
        for d, info in scan_runs(folder)
        if info.get("job_key") == job_key
        and info.get("status") in UNFINISHED
        and (name is None or info.get("name") == name)
    ]


def resolve_resume(
    location: Location,
    environ: dict[str, str],
    explicit: str | None,
    key: str | None,
    name: str | None,
) -> tuple[str | None, str | None]:
    """Find an existing run to continue, or none for a new run.

    Tried in order: an explicit ``resume`` id (unchanged: an unknown id raises); a matching
    ``key``; a SLURM requeue of the same job. Anything that goes wrong while looking falls
    back to a new run with a warning, since this must never keep training from starting.

    :param location: Where the run goes.
    :param environ: The process environment.
    :param explicit: The ``resume`` argument.
    :param key: The ``key`` argument or ``BEAMTIME_RUN_KEY``.
    :param name: The ``name`` argument, to tell several models of one job apart.
    :return: A run id to continue (or ``None`` for a new run), and a warning, if any."""
    if explicit is not None:
        return explicit, None
    try:
        if key is not None:
            found = resume_by_key(location.folder, key)
            if found is None:
                return None, None
            run_id, status = found
            if status in UNFINISHED:
                return run_id, None
            return None, f"the run for key {key!r} already finished; starting a new run"
        if env.requeued(environ):
            candidates = resume_candidates(location.folder, env.job_key(environ), name)
            if not candidates:
                return None, None
            if len(candidates) > 1:
                return None, (
                    f"{len(candidates)} unfinished runs match this job; pass key= to tell them "
                    "apart; starting a new run"
                )
            return candidates[0], None
    except Exception:
        return None, "could not resolve resume; starting a new run"
    return None, None


def proposals_of(logdir: Path, run_dir: Path, own: str) -> tuple[dict[str, str], dict[str, str]]:
    """Record the newest proposal version of every ancestor group and the run's own.

    :param logdir: The log dir.
    :param run_dir: The new run's directory, holding its own proposal.
    :param own: The version id of the run's own proposal.
    :return: Path relative to the log dir (``.`` for the run) to version id, and the
        same keys to the hash of each recorded file."""
    files = {".": run_dir / c.PROPOSAL / f"{own}.yaml"}
    parts = run_dir.parent.relative_to(logdir).parts
    for i in range(1, len(parts) + 1):
        rel = "/".join(parts[:i])
        if (path := newest(logdir / rel / c.PROPOSAL)) is not None:
            files[rel] = path
    return {k: p.stem for k, p in files.items()}, {k: file_hash(p) for k, p in files.items()}


def init(
    dir: str | Path | None = None,
    name: str | None = None,
    tags: list[str] | None = None,
    config: Any = None,
    proposal: str | Path | dict[str, Any] | None = None,
    resume: str | None = None,
    key: str | None = None,
    system_metrics: bool = True,
) -> Run | NullRun:
    """Start recording a run, or continue one.

    :param dir: The folder below the log dir, created if missing, or an absolute path.
    :param name: A readable name; generated if missing.
    :param tags: Tags.
    :param config: The hyperparameters: a dict, dataclass, Pydantic model, Namespace or
        OmegaConf config.
    :param proposal: The run's own proposal: a statement, a dict, a path to a YAML
        file, or ``None`` (``BEAMTIME_PROPOSAL`` if set, else blank).
    :param resume: A run id to continue; ``None`` starts a new run, unless ``key`` or a
        SLURM requeue resolves one ([Resume](../docs/design/02-sdk.md#resume)).
    :param key: A name for this launch, stored in ``_run.json``; resuming it without an id
        continues the newest unfinished run recorded under it. Defaults to
        ``BEAMTIME_RUN_KEY``.
    :param system_metrics: Sample CPU, memory and GPUs every 30 s as ``sys/*`` metrics.
    :return: The run; a ``NullRun`` on ranks other than 0."""
    global _current
    location = locate(dir)
    environ = dict(os.environ)
    if (rank := env.rank(environ)) != 0:
        capture = rank_capture(rank, location.folder, env.job_key(environ))
        return NullRun(rank=rank, capture=capture)
    if tags is not None and not all(isinstance(t, str) for t in tags):
        raise ValueError("tags must be a list of strings")
    cfg = to_config(config)
    key = key or environ.get("BEAMTIME_RUN_KEY")
    resolved, warning = resolve_resume(location, environ, resume, key, name)
    if (previous := _current) is not None:
        previous.warn("init-again", "init() called again; finishing the previous run")
        previous.finish()
    install_hooks()
    if resolved is not None:
        run = continue_run(location.logdir, resolved, cfg)
    else:
        run = new_run(location, name, tags or [], cfg, to_proposal(proposal), key)
    notebook = in_notebook()
    run.capture = Capture(files=LogFiles(run_dir=run.dir), mode="stream" if notebook else "fd")
    run.capture.start()
    if warning:
        run.warn("resume", warning)
    for message in location.warnings:
        run.warn("root", message)
    if notebook:
        run.warn("notebook", "in a notebook, end the run with run.finish() or a with block")
    os.environ["BEAMTIME_RUN_DIR"] = str(run.dir)
    if system_metrics:
        run.sampler = Sampler()
    _current = run
    run.start()
    return run


def new_run(
    location: Location,
    name: str | None,
    tags: list[str],
    cfg: dict[str, Any],
    proposal: dict[str, Any],
    key: str | None = None,
) -> Run:
    """Create the directory and first files of a new run.

    :param location: Where the run goes.
    :param name: Its name, or ``None``.
    :param tags: Its tags.
    :param cfg: Its config.
    :param proposal: Its own proposal's fields.
    :param key: A name for this launch, so a later call can resume it by key.
    :return: The run, not yet started."""
    location.folder.mkdir(parents=True, exist_ok=True)
    for _ in range(10):
        run_id = new_run_id()
        try:
            (run_dir := location.folder / run_id).mkdir()
            break
        except FileExistsError:
            continue
    else:
        raise RuntimeError(f"could not create a unique run directory in {location.folder}")
    now = time.time()
    user = env.user()
    own = new_version_id()
    doc = {"schema": 1} | {k: v for k, v in proposal.items() if k != "schema"}
    doc.setdefault("author", user)
    doc.setdefault("user", user)
    write_created(
        run_dir / c.PROPOSAL / f"{own}.yaml",
        yaml.safe_dump(jsonable(doc), sort_keys=False).encode(),
    )
    proposals, hashes = proposals_of(location.logdir, run_dir, own)
    try:
        host = env.host_info() | hardware()
    except Exception:
        # describing the hardware must never keep a run from starting.
        host = env.host_info()
    git, diff = env.git_info(Path.cwd())
    environ = dict(os.environ)
    info: dict[str, Any] = {
        "schema": 1,
        "id": run_id,
        "name": name or random_name(),
        "tags": tags,
        "status": "running",
        "created_at": iso(now, ms=True),
        "ended_at": None,
        "exit": None,
        "attempts": [
            {"started_at": iso(now, ms=True), "host": host["hostname"], "resume_step": None}
        ],
        "proposals": proposals,
        "proposal_hashes": hashes,
        "job_key": env.job_key(environ),
        "host": host,
    }
    if (scheduler := env.scheduler(environ)) is not None:
        info["scheduler"] = scheduler
    if key is not None:
        info["key"] = key
    info |= {
        "git": git,
        "command": env.command(),
        "cwd": env.cwd(),
        "beamtime_version": beamtime_version(),
    }
    write_replaced(run_dir / c.RUN, info)
    write_replaced(run_dir / c.CONFIG, {"schema": 1, **cfg})
    write_created(run_dir / c.ENV_DIR / "packages.txt", env.packages().encode())
    if diff:
        write_created(run_dir / c.ENV_DIR / "git.diff", diff.encode())
    t = round(now, 3)
    with (run_dir / c.EVENTS).open("ab") as f:
        f.write(json_line({"_t": t, "kind": "created"}))
        f.write(
            json_line(
                {
                    "_t": t,
                    "kind": "attempt_started",
                    "resume_step": None,
                    "metrics_offset": 0,
                }
            )
        )
    return Run(dir=run_dir, info=info, config=cfg, capture=None)


def continue_run(logdir: Path, run_id: str, cfg: dict[str, Any]) -> Run:
    """Reopen a run for a new attempt.

    :param logdir: The log dir.
    :param run_id: The run to continue.
    :param cfg: The config the new attempt brings.
    :return: The run, not yet started; its resume step is settled at the first log."""
    if (run_dir := find_run(logdir, run_id)) is None:
        raise LookupError(f"resume: no run {run_id!r} below {logdir}")
    info = read_json(run_dir / c.RUN)
    schema_of(info, kind="run", path=run_dir / c.RUN)
    metrics = run_dir / c.METRICS
    if metrics.exists() and metrics.stat().st_size:
        with metrics.open("rb+") as f:
            f.seek(-1, os.SEEK_END)
            # end a partial line left by a killed writer, so it can't merge with ours.
            if f.read(1) != b"\n":
                f.write(b"\n")
    stored = read_config(run_dir) if (run_dir / c.CONFIG).exists() else {}
    rows = read_effective_metrics(run_dir)
    run = Run(
        dir=run_dir,
        info=info,
        config=stored,
        capture=None,
        resume_last_step=rows[-1]["_step"] if rows else None,
        resuming=True,
    )
    if (run_dir / c.CARD).exists():
        old = read_card(run_dir)
        run.card.update(old.values)
        run.warnings = old.warnings
    if cfg and cfg != stored:
        diff = {
            k: [stored.get(k), cfg.get(k)]
            for k in sorted(stored.keys() | cfg.keys())
            if stored.get(k) != cfg.get(k)
        }
        run.queue(c.EVENTS, {"_t": time.time(), "kind": "config_conflict", "diff": diff})
    info.update(status="running", ended_at=None, exit=None)
    write_replaced(run_dir / c.RUN, info)
    return run


def beamtime_version() -> str | None:
    """Read the installed Beamtime version.

    :return: The version, or ``None`` if not installed."""
    try:
        from importlib.metadata import version

        return version("beamtime")
    except Exception:
        return None
