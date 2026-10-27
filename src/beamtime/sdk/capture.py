"""Output capture: stdout and stderr go to the terminal and, never blocking, to logs."""

import os
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Any, BinaryIO, Literal

from beamtime.format import constants as c

BUFFER_CAP = 4 * 1024 * 1024
JOIN_TIMEOUT_S = 2.0


def segment_header(n: int) -> bytes:
    """Make the first line of a tail segment.

    :param n: The segment number, from 1.
    :return: The header line."""
    return f"[beamtime: output segment {n}]\n".encode()


class LogFiles:
    """Writes captured output into a head file and two rotating tail files."""

    def __init__(self, *, run_dir: Path, rank: int = 0, cap: int = c.OUTPUT_CAP) -> None:
        """Open a rank's log files, continuing existing ones after a resume.

        :param run_dir: The run directory.
        :param rank: The rank; 0 is the main process.
        :param cap: The size cap; the head gets half, each tail segment a quarter."""
        head, tail, prev = (run_dir / n for n in c.output_names(rank))
        self.tail_path, self.prev_path = tail, prev
        self.head_cap, self.tail_cap = cap // 2, cap // 4
        self.head_size = head.stat().st_size if head.exists() else 0
        self.head: BinaryIO | None = head.open("ab", buffering=0)
        self.tail: BinaryIO | None = None
        self.tail_size = 0
        self.segment = 0
        if tail.exists():
            with tail.open("rb") as f:
                first = f.readline()
            prefix = b"[beamtime: output segment "
            header = len(first) if first.startswith(prefix) else 0
            if header:
                self.segment = int(first[len(prefix) :].split(b"]")[0])
            self.tail = tail.open("ab", buffering=0)
            self.tail_size = tail.stat().st_size - header

    def write(self, data: bytes) -> None:
        """Append captured bytes, moving on to the tail and rotating it when full.

        :param data: The bytes."""
        if self.head is not None and self.head_size < self.head_cap:
            part = data[: self.head_cap - self.head_size]
            self.head.write(part)
            self.head_size += len(part)
            data = data[len(part) :]
        while data:
            if self.tail is None or self.tail_size >= self.tail_cap:
                self.rotate()
            part = data[: self.tail_cap - self.tail_size]
            self.tail.write(part)
            self.tail_size += len(part)
            data = data[len(part) :]

    def rotate(self) -> None:
        """Start a new tail segment, keeping the current one as the previous tail."""
        if self.tail is not None:
            self.tail.close()
            os.replace(self.tail_path, self.prev_path)
        self.segment += 1
        self.tail = self.tail_path.open("ab", buffering=0)
        # headers don't count towards the segment size, so every segment makes progress.
        self.tail.write(segment_header(self.segment))
        self.tail_size = 0

    def close(self) -> None:
        """Close the files, syncing them to disk."""
        for f in (self.head, self.tail):
            if f is not None:
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
                f.close()
        self.head = self.tail = None


class Buffer:
    """A bounded byte buffer between the readers and the file writer."""

    def __init__(self, *, cap: int = BUFFER_CAP) -> None:
        """Create an empty buffer.

        :param cap: The most bytes held before new output is dropped from the log."""
        self.cap = cap
        self.chunks: deque[bytes] = deque()
        self.size = 0
        self.dropped = 0
        self.closed = False
        self.cond = threading.Condition()

    def put(self, data: bytes) -> None:
        """Queue bytes for the log, or drop them if the buffer is full.

        :param data: The bytes."""
        with self.cond:
            if self.size + len(data) > self.cap:
                self.dropped += len(data)
                return
            if self.dropped:
                marker = f"\n[beamtime: {self.dropped:,} bytes dropped]\n".encode()
                self.chunks.append(marker)
                self.size += len(marker)
                self.dropped = 0
            self.chunks.append(data)
            self.size += len(data)
            self.cond.notify()

    def take(self, timeout: float) -> bytes | None:
        """Wait for queued bytes and take all of them.

        :param timeout: How long to wait.
        :return: The bytes, empty if none arrived, ``None`` once closed and drained."""
        with self.cond:
            if not self.chunks and not self.closed:
                self.cond.wait(timeout)
            if not self.chunks:
                if not self.closed:
                    return b""
                if not self.dropped:
                    return None
                self.chunks.append(f"\n[beamtime: {self.dropped:,} bytes dropped]\n".encode())
                self.dropped = 0
            data = b"".join(self.chunks)
            self.chunks.clear()
            self.size = 0
            return data

    def close(self) -> None:
        """Stop accepting waits; the writer drains what is left and ends."""
        with self.cond:
            self.closed = True
            self.cond.notify_all()


class Tee:
    """A text stream that writes to the original stream and into the capture buffer."""

    def __init__(self, *, stream: Any, buffer: Buffer) -> None:
        """Wrap a stream.

        :param stream: The original ``sys.stdout`` or ``sys.stderr``.
        :param buffer: The capture buffer."""
        self.stream = stream
        self.buffer = buffer

    def write(self, text: str) -> int:
        """Write text to the original stream and the log.

        :param text: The text.
        :return: The number of characters written."""
        n = self.stream.write(text)
        self.buffer.put(text.encode(errors="replace"))
        return n

    def __getattr__(self, name: str) -> Any:
        """Delegate everything else to the original stream.

        :param name: The attribute.
        :return: The original stream's attribute."""
        return getattr(self.stream, name)


class Capture:
    """Captures stdout and stderr of the process into a rank's log files."""

    def __init__(
        self,
        *,
        files: LogFiles | None,
        mode: Literal["fd", "stream"] = "fd",
        buffer_cap: int = BUFFER_CAP,
    ) -> None:
        """Prepare capture; nothing is redirected before ``start``.

        :param files: The log files, or ``None`` until ``set_files`` provides them.
        :param mode: ``fd`` redirects file descriptors 1 and 2 (scripts); ``stream``
            wraps ``sys.stdout`` and ``sys.stderr`` (notebooks).
        :param buffer_cap: The size of the bounded buffer."""
        self.files = files
        self.mode = mode
        self.buffer = Buffer(cap=buffer_cap)
        self.files_ready = threading.Event()
        if files is not None:
            self.files_ready.set()
        self.saved: dict[int, int] = {}
        self.streams: dict[str, Any] = {}
        self.readers: list[threading.Thread] = []
        self.writer = threading.Thread(target=self.write_loop, name="beamtime-output", daemon=True)
        self.lock = threading.Lock()
        self.active = False

    def start(self) -> None:
        """Redirect the output and start the threads."""
        self.writer.start()
        match self.mode:
            case "fd":
                self.start_fds()
            case "stream":
                self.streams = {"stdout": sys.stdout, "stderr": sys.stderr}
                sys.stdout = Tee(stream=sys.stdout, buffer=self.buffer)
                sys.stderr = Tee(stream=sys.stderr, buffer=self.buffer)
            case _:
                raise ValueError(f"unknown capture mode {self.mode!r}")
        self.active = True

    def start_fds(self) -> None:
        """Point file descriptors 1 and 2 at pipes read by one thread each."""
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except Exception:
                pass
        for fd in (1, 2):
            saved = os.dup(fd)
            r, w = os.pipe()
            os.dup2(w, fd)
            os.close(w)
            self.saved[fd] = saved
            reader = threading.Thread(
                target=self.read_loop,
                args=(r, saved),
                name=f"beamtime-fd{fd}",
                daemon=True,
            )
            reader.start()
            self.readers.append(reader)
        if os.isatty(self.saved[1]) and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(line_buffering=True)

    def read_loop(self, r: int, original: int) -> None:
        """Copy a pipe to the original destination and into the buffer.

        :param r: The pipe's read end.
        :param original: The saved original file descriptor."""
        try:
            while data := os.read(r, 65536):
                view = memoryview(data)
                try:
                    while view:
                        view = view[os.write(original, view) :]
                except OSError:
                    pass
                self.buffer.put(data)
        except Exception:
            self.restore()
        finally:
            os.close(r)

    def write_loop(self) -> None:
        """Move buffered output into the log files until capture stops."""
        self.files_ready.wait()
        while (data := self.buffer.take(0.5)) is not None:
            if data:
                try:
                    self.files.write(data)
                except OSError:
                    pass
        try:
            self.files.close()
        except OSError:
            pass

    def set_files(self, files: LogFiles) -> None:
        """Provide the log files once they are known (other ranks find the run later).

        :param files: The log files."""
        self.files = files
        self.files_ready.set()

    def restore(self) -> None:
        """Put the original file descriptors or streams back."""
        with self.lock:
            for fd, saved in self.saved.items():
                try:
                    os.dup2(saved, fd)
                except OSError:
                    pass
            if self.streams:
                sys.stdout, sys.stderr = self.streams["stdout"], self.streams["stderr"]
                self.streams = {}

    def stop(self) -> None:
        """Restore the output, then let readers and writer finish within a timeout."""
        if not self.active:
            return
        self.active = False
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.flush()
            except Exception:
                pass
        self.restore()
        for reader, saved in zip(self.readers, self.saved.values(), strict=True):
            # forked children may hold the pipe open, so EOF may never come.
            reader.join(JOIN_TIMEOUT_S)
            if not reader.is_alive():
                os.close(saved)
        self.buffer.close()
        if self.files_ready.is_set():
            self.writer.join(JOIN_TIMEOUT_S)
