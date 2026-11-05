import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

SWEEP = "scaling/lr-sweep"


class Session:
    """A ``serve --stdio`` process and a way to talk to it."""

    def __init__(self, logdir: Path, tmp: Path) -> None:
        """Start the process.

        :param logdir: The log dir it serves.
        :param tmp: Its TMPDIR, to see the temporary cache go."""
        env = os.environ | {"TMPDIR": str(tmp)}
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "beamtime.cli", "serve", "--stdio", "--logdir", str(logdir)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env,
        )  # fmt: skip
        self.next = 0
        self.events: list[dict] = []
        self.answers: dict[int, dict] = {}

    def ask(self, method: str, **params) -> dict:
        """Send a request and wait for its answer.

        :param method: The API method.
        :param params: Its parameters.
        :return: The answer line."""
        self.next += 1
        rid = self.next
        self.proc.stdin.write(json.dumps({"id": rid, "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()
        while rid not in self.answers:
            self.read()
        return self.answers.pop(rid)

    def read(self) -> None:
        """Read one line: an answer or an event."""
        line = self.proc.stdout.readline()
        assert line, "the process ended"
        message = json.loads(line)
        if "event" in message:
            self.events.append(message)
        else:
            self.answers[message["id"]] = message

    def close(self) -> int:
        """End the session by closing stdin.

        :return: The exit code."""
        self.proc.stdin.close()
        return self.proc.wait(timeout=30)


@pytest.fixture
def session(project: Path, tmp_path: Path):
    """A stdio session on the project's log dir.

    :param project: The project root.
    :param tmp_path: Pytest's temporary directory.
    :return: The session."""
    tmp = tmp_path / "remote-tmp"
    tmp.mkdir()
    s = Session(project / "beamtime", tmp)
    yield s
    if s.proc.poll() is None:
        s.close()


def test_hello_reads_and_errors(session: Session, project: Path, tmp_path: Path) -> None:
    """The remote shakes hands, answers operations like the API, and names what went wrong."""
    hello = session.ask("hello", protocol=1)["result"]
    assert hello["protocol"] == 1 and hello["logdir_exists"]
    assert "protocol 2" in session.ask("hello", protocol=2)["error"]["message"]
    runs = session.ask("runs", **{"from": SWEEP, "limit": 3})["result"]
    assert len(runs["rows"]) == 3
    assert session.ask("nope")["error"]["code"] == 4
    assert session.ask("runs", **{"from": "no/such"})["error"]["code"] == 4
    # the temporary cache it indexed into is gone with the process.
    assert any((tmp_path / "remote-tmp").iterdir())
    assert session.close() == 0
    assert not any((tmp_path / "remote-tmp").iterdir())


def test_writes_and_subscriptions(session: Session, project: Path) -> None:
    """A note written over stdio lands in the remote's files and is reported as a change."""
    session.ask("subscribe", paths=[SWEEP])
    deadline = time.monotonic() + 15
    # the first catch-up only builds the index; let it pass before writing the note to notice.
    while not session.events and time.monotonic() < deadline:
        session.read()
    session.events.clear()
    written = session.ask("note_add", group=SWEEP, type="observation", description="From afar.")
    path = project / "beamtime" / written["result"]["path"]
    assert path.is_file() and "From afar." in path.read_text()
    while not any(SWEEP in e["changed"] for e in session.events) and time.monotonic() < deadline:
        session.read()
    assert any(e["changed"].get(SWEEP) == ["authored"] for e in session.events)


def test_files_list_and_read_from_an_offset(session: Session, project: Path) -> None:
    """files lists a folder and reads a file in pieces; paths can't leave the log dir."""
    entries = session.ask("files", list=SWEEP)["result"]["entries"]
    metrics = next(e for e in entries if e["path"].endswith("_metrics.jsonl"))
    whole = (project / "beamtime" / metrics["path"]).read_bytes()
    part = session.ask("files", read=metrics["path"], offset=10, limit=20)["result"]
    assert base64.b64decode(part["data"]) == whole[10:30] and not part["eof"]
    assert part["size"] == len(whole) == metrics["size"]
    assert session.ask("files", read="../secret")["error"]["code"] == 2
