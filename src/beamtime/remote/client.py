"""One connection to a remote: ``beamtime serve --stdio`` started over ssh (or as a plain command),
with requests matched to answers by id, events passed on, and reconnects after a pause."""

import json
import shlex
import subprocess
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib.metadata import version
from typing import Any, Literal

from beamtime.ops.context import OpError

TIMEOUT_S = 120.0
HELLO_S = 60.0
BACKOFF_S = (5.0, 15.0, 60.0)
PROTOCOL = 1


class Unreachable(OpError):
    """A remote that can't answer now; a snapshot may answer for it."""


@dataclass(kw_only=True)
class Spec:
    """How to reach a remote: from the settings, or named on the command line."""

    name: str
    path: str
    host: str | None = None
    command: str = "beamtime"
    cache: str | None = None
    # ssh, or a command run here (for tests and for log dirs on mounted disks).
    transport: Literal["ssh", "command"] = "ssh"
    # the group a source is narrowed to (`serve cluster:scaling`), "." for all of it.
    scope: str = "."

    def argv(self) -> list[str]:
        """Build the command that starts the remote end.

        :return: The arguments."""
        args = [
            "serve",
            "--stdio",
            "--logdir",
            self.path,
            *(["--cache", self.cache] if self.cache else []),
        ]
        match self.transport:
            case "command":
                return [*shlex.split(self.command), *args]
            case "ssh":
                # no prompts: a login with a second factor goes through a ControlMaster set up
                # beforehand (`ssh -fNM <host>`); keepalives notice a dropped network.
                options = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]
                options += ["-o", "ServerAliveInterval=30", "-T"]
                # the command is the remote shell's (~, a venv, `uv run`); the paths are quoted,
                # and the remote end expands ~, ${VAR} and {user} in them itself.
                line = f"{self.command} {shlex.join(args)}"
                return ["ssh", *options, self.host or self.name, line]
            case other:
                raise ValueError(f"no transport {other!r}")


@dataclass(kw_only=True)
class Pending:
    """A request waiting for its answer."""

    done: threading.Event = field(default_factory=threading.Event)
    answer: dict[str, Any] | None = None


class RemoteClient:
    """A long-lived connection to one remote."""

    def __init__(self, *, spec: Spec, on_event: Callable[[dict[str, Any]], None] | None = None):
        """Prepare a client; it connects on the first request.

        :param spec: How to reach the remote.
        :param on_event: Called from the reader thread with each event (``changed``)."""
        self.spec = spec
        self.on_event = on_event
        self.state: Literal["idle", "connected", "unreachable"] = "idle"
        self.since = time.time()
        self.error: str | None = None
        self.info: dict[str, Any] = {}
        self.proc: subprocess.Popen | None = None
        self.pending: dict[int, Pending] = {}
        self.next_id = 0
        self.failures = 0
        self.lock = threading.Lock()
        self.connecting = threading.Lock()
        self.stderr: deque[str] = deque(maxlen=20)
        self.subscribed: list[str] = []
        # whether the current process can still answer; cleared when its output ends.
        self.alive = False

    @property
    def name(self) -> str:
        """The source's name, e.g. ``cluster``."""
        return self.spec.name

    def describe(self) -> dict[str, Any]:
        """Describe the connection for ``status`` and the web UI.

        :return: Name, state, since when, the last error and the remote's version."""
        return {
            "name": f"@{self.name}",
            "state": self.state,
            "since": self.since,
            "error": self.error,
            "version": self.info.get("version"),
            "host": self.spec.host or self.name if self.spec.transport == "ssh" else None,
            "path": self.spec.path,
        }

    def request(
        self,
        method: str,
        params: dict[str, Any],
        *,
        caller: str = "cli",
        timeout: float = TIMEOUT_S,
    ) -> dict[str, Any]:
        """Send a request and wait for its answer.

        :param method: The API method (an operation's MCP name, or a page method).
        :param params: Its parameters.
        :param caller: Whose defaults the remote applies (``cli``, ``mcp``, ``view``).
        :param timeout: Seconds to wait.
        :return: The result.
        :raises OpError: With the remote's message, or why it can't be reached."""
        self.connect()
        return self.send(method, params, caller, timeout)

    def send(self, method: str, params: dict[str, Any], caller: str, timeout: float) -> Any:
        """Write one request on the open connection and wait for its answer.

        :param method: The API method.
        :param params: Its parameters.
        :param caller: Whose defaults apply.
        :param timeout: Seconds to wait.
        :return: The result."""
        with self.lock:
            proc = self.proc
            if proc is None or proc.stdin is None or not self.alive:
                raise self.unreachable()
            self.next_id += 1
            rid = self.next_id
            waiting = self.pending[rid] = Pending()
            line = json.dumps({"id": rid, "method": method, "params": params, "caller": caller})
            try:
                proc.stdin.write(line + "\n")
                proc.stdin.flush()
                broken = False
            except OSError:
                self.pending.pop(rid, None)
                broken = True
        if broken:
            self.lost("the connection closed")
            raise self.unreachable()
        if not waiting.done.wait(timeout):
            with self.lock:
                self.pending.pop(rid, None)
            raise OpError(f"@{self.name} didn't answer {method} within {timeout:.0f} s", code=1)
        answer = waiting.answer or {}
        if (error := answer.get("error")) is not None:
            raise OpError(f"@{self.name}: {error.get('message')}", code=int(error.get("code", 1)))
        if answer.get("lost"):
            raise self.unreachable()
        return answer.get("result")

    def connect(self) -> None:
        """Start the remote end and shake hands, unless connected or waiting before a retry.

        :raises OpError: If the remote can't be reached."""
        with self.connecting:
            if self.state == "connected" and self.proc is not None and self.proc.poll() is None:
                return
            wait = BACKOFF_S[min(self.failures, len(BACKOFF_S)) - 1] if self.failures else 0.0
            if self.state == "unreachable" and time.time() - self.since < wait:
                raise self.unreachable()
            try:
                self.proc = subprocess.Popen(
                    self.spec.argv(),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )
            except OSError as e:
                self.fail(str(e))
                raise self.unreachable() from None
            self.alive = True
            threading.Thread(target=self.read, args=(self.proc,), daemon=True).start()
            threading.Thread(target=self.read_errors, args=(self.proc,), daemon=True).start()
            hello = {"protocol": PROTOCOL, "version": version("beamtime")}
            try:
                self.info = self.send("hello", hello, "cli", HELLO_S)
            except OpError as e:
                self.close()
                if self.state != "unreachable":
                    self.fail(str(e).removeprefix(f"@{self.name}: "))
                raise self.unreachable() from None
            self.state, self.since, self.error, self.failures = "connected", time.time(), None, 0
            if self.subscribed:
                self.send("subscribe", {"paths": self.subscribed}, "cli", HELLO_S)

    def subscribe(self, paths: list[str]) -> None:
        """Ask for change events about some scopes; kept across reconnects.

        :param paths: Scopes relative to the remote's log dir."""
        self.subscribed = sorted(set(paths))
        if self.state == "connected":
            try:
                self.send("subscribe", {"paths": self.subscribed}, "cli", HELLO_S)
            except OpError:
                pass

    def read(self, proc: subprocess.Popen) -> None:
        """Hand each line from the remote to its request or to the event callback.

        :param proc: The process whose output to read."""
        assert proc.stdout is not None
        for line in proc.stdout:
            try:
                message = json.loads(line)
            except ValueError:
                # something on the remote printed to stdout: not ours, not fatal.
                continue
            if "event" in message:
                if self.on_event is not None:
                    self.on_event(message)
                continue
            with self.lock:
                waiting = self.pending.pop(message.get("id"), None)
            if waiting is not None:
                waiting.answer = message
                waiting.done.set()
        if proc is self.proc:
            self.lost(self.last_error() or "the connection closed")

    def read_errors(self, proc: subprocess.Popen) -> None:
        """Keep the last lines the remote end wrote to stderr, for error messages.

        :param proc: The process whose errors to read."""
        assert proc.stderr is not None
        for line in proc.stderr:
            if line.strip():
                self.stderr.append(line.rstrip())

    def lost(self, reason: str) -> None:
        """Mark the connection lost and fail every waiting request.

        :param reason: What happened."""
        with self.lock:
            waiting, self.pending = list(self.pending.values()), {}
            self.alive = False
        for w in waiting:
            w.answer = {"lost": True}
            w.done.set()
        if self.state != "unreachable":
            self.fail(reason)

    def fail(self, reason: str) -> None:
        """Record a failed connection.

        :param reason: Why."""
        self.state, self.since, self.error = "unreachable", time.time(), reason
        self.failures += 1

    def last_error(self) -> str | None:
        """Name the remote end's last error output.

        :return: Its last lines, or ``None``."""
        time.sleep(0.05)
        return " / ".join(list(self.stderr)[-3:]) or None

    def unreachable(self) -> Unreachable:
        """Describe why the remote can't answer.

        :return: The error to raise."""
        when = time.strftime("%H:%M", time.localtime(self.since))
        hint = (
            f"; check `ssh {self.spec.host or self.name}` and `beamtime doctor`"
            if self.spec.transport == "ssh"
            else ""
        )
        return Unreachable(f"@{self.name} is unreachable since {when}: {self.error}{hint}", code=1)

    def close(self) -> None:
        """End the connection; the remote end exits when its stdin closes."""
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            if proc.stdin is not None:
                proc.stdin.close()
            proc.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
        if self.state == "connected":
            self.state, self.since = "idle", time.time()
