import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from beamtime.format.run import (
    read_events,
    read_metrics,
    read_output,
    read_run_info,
    run_status,
)
from beamtime.sdk.capture import Buffer, LogFiles
from tests.sdk.conftest import Script, only_run

POSIX = pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")


def test_log_files_rotate(tmp_path: Path) -> None:
    """Head, then tail segments with headers; the previous tail is kept."""
    files = LogFiles(run_dir=tmp_path, cap=400)
    for i in range(30):
        files.write(f"line {i:02d} padding\n".encode())
    files.close()
    head = (tmp_path / "_output.log").read_bytes()
    assert len(head) == 200 and head.startswith(b"line 00")
    prev = (tmp_path / "_output.tail.prev.log").read_text()
    tail = (tmp_path / "_output.tail.log").read_text()
    assert prev.startswith("[beamtime: output segment ") and tail.endswith("line 29 padding\n")
    text = read_output(tmp_path)
    assert "not kept" in text and text.endswith("line 29 padding\n")


def test_log_files_continue_after_resume(tmp_path: Path) -> None:
    """Reopened log files continue the segment count."""
    files = LogFiles(run_dir=tmp_path, cap=40)
    files.write(b"x" * 60)
    files.close()
    seg = files.segment
    again = LogFiles(run_dir=tmp_path, cap=40)
    assert again.segment == seg and again.head_size == 20
    again.write(b"y" * 30)
    again.close()
    assert again.segment > seg


def test_buffer_drops_with_a_marker() -> None:
    """A full buffer drops bytes from the log and says how many."""
    buf = Buffer(cap=10)
    buf.put(b"12345678")
    buf.put(b"abcdef")
    assert buf.take(0) == b"12345678"
    buf.put(b"ok")
    assert buf.take(0) == b"\n[beamtime: 6 bytes dropped]\nok"
    buf.put(b"0123456789x")
    buf.close()
    assert b"11 bytes dropped" in buf.take(0) and buf.take(0) is None


def test_fast_output_rotates_and_reaches_the_terminal(script: Script, logdir: Path) -> None:
    """Very fast output rotates through the tail; the terminal copy is complete."""
    proc = script(
        """
        import beamtime
        from beamtime.sdk.capture import LogFiles
        LogFiles.__init__.__kwdefaults__["cap"] = 40_000
        run = beamtime.init()
        for i in range(5000):
            print(f"line {i:05d}")
        """
    )
    assert proc.returncode == 0
    lines = proc.stdout.decode().splitlines()
    assert lines == [f"line {i:05d}" for i in range(5000)]
    log = read_output(only_run(logdir))
    assert log.startswith("line 00000") and log.endswith("line 04999\n")
    assert "not kept" in log


def test_stalled_log_file_never_blocks(script: Script, logdir: Path) -> None:
    """A stalled log writer drops output from the log but never slows the script."""
    proc = script(
        """
        import time
        import beamtime
        from beamtime.sdk import capture
        slow_write = capture.LogFiles.write
        stalls = [1.5]
        def stalled(self, data):
            if stalls:
                time.sleep(stalls.pop())
            slow_write(self, data)
        capture.LogFiles.write = stalled
        run = beamtime.init()
        chunk = "x" * 1023 + "\\n"
        t = time.perf_counter()
        for _ in range(8 * 1024):
            print(chunk, end="")
        print("elapsed", time.perf_counter() - t, flush=True)
        """,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr.decode()
    elapsed = float(proc.stdout.decode().splitlines()[-1].split()[1])
    assert elapsed < 0.9
    assert "bytes dropped" in read_output(only_run(logdir))


@POSIX
def test_sigterm_kills_the_run(script: Script, logdir: Path, tmp_path: Path) -> None:
    """SIGTERM marks the run killed and the process still dies of the signal."""
    code = """
        import time, beamtime
        run = beamtime.init()
        run.log({"x": 1})
        print("ready", flush=True)
        time.sleep(30)
    """
    proc = start(script, code, tmp_path, logdir)
    wait_for(proc, b"ready")
    proc.send_signal(signal.SIGTERM)
    assert proc.wait(30) == -signal.SIGTERM
    run = only_run(logdir)
    info = read_run_info(run)
    assert info.status == "killed" and info.exit == {"signal": "SIGTERM"}
    assert read_events(run)[-1].data["signal"] == "SIGTERM"
    assert "ready" in read_output(run)


@POSIX
def test_sigterm_chains_to_the_previous_handler(
    script: Script, logdir: Path, tmp_path: Path
) -> None:
    """A handler installed before init still runs after the run is marked killed."""
    code = """
        import signal, sys, time, beamtime
        signal.signal(signal.SIGTERM, lambda *a: (print("user handler"), sys.exit(3)))
        run = beamtime.init()
        print("ready", flush=True)
        time.sleep(30)
    """
    proc = start(script, code, tmp_path, logdir)
    wait_for(proc, b"ready")
    proc.send_signal(signal.SIGTERM)
    assert proc.wait(30) == 3
    assert b"user handler" in proc.stdout.read()
    assert read_run_info(only_run(logdir)).status == "killed"


@POSIX
def test_sigusr1_records_a_requeue_request(
    script: Script, logdir: Path, tmp_path: Path
) -> None:
    """SIGUSR1 with a framework handler records the request and lets the run go on."""
    code = """
        import signal, time, beamtime
        signal.signal(signal.SIGUSR1, lambda *a: print("framework requeues", flush=True))
        run = beamtime.init()
        print("ready", flush=True)
        time.sleep(1.5)
        run.log({"x": 1})
    """
    proc = start(script, code, tmp_path, logdir)
    wait_for(proc, b"ready")
    proc.send_signal(signal.SIGUSR1)
    assert proc.wait(30) == 0
    run = only_run(logdir)
    kinds = [e.kind for e in read_events(run)]
    assert "requeue_requested" in kinds and kinds[-1] == "finished"


@POSIX
def test_sigkill_leaves_a_readable_lost_run(
    script: Script, logdir: Path, tmp_path: Path
) -> None:
    """After SIGKILL the files are readable and the run shows as lost once stale."""
    code = """
        import time, beamtime
        run = beamtime.init()
        for s in range(1000):
            run.log({"x": s})
        print("ready", flush=True)
        time.sleep(30)
    """
    proc = start(script, code, tmp_path, logdir)
    wait_for(proc, b"ready")
    time.sleep(2.5)
    proc.kill()
    proc.wait(30)
    run = only_run(logdir)
    info = read_run_info(run)
    assert info.status == "running"
    assert len(read_metrics(run).rows) == 1000
    beat = (run / "_run.json").stat().st_mtime
    assert run_status(info, heartbeat=beat, now=beat + 10) == "running"
    assert run_status(info, heartbeat=beat, now=beat + 400) == "lost"


def start(script: Script, code: str, tmp_path: Path, logdir: Path) -> subprocess.Popen:
    """Start a training script without waiting for it.

    :param script: The script fixture, used for its environment conventions.
    :param code: The script's code.
    :param tmp_path: Where to write it.
    :param logdir: The log dir.
    :return: The running process with piped stdout."""
    import textwrap

    path = tmp_path / "train.py"
    path.write_text(textwrap.dedent(code))
    environ = {k: v for k, v in os.environ.items() if not k.startswith("BEAMTIME_")}
    environ |= {"BEAMTIME_LOGDIR": str(logdir), "PYTHONUNBUFFERED": "1"}
    return subprocess.Popen(
        [sys.executable, str(path)], cwd=tmp_path, env=environ, stdout=subprocess.PIPE
    )


def wait_for(proc: subprocess.Popen, text: bytes) -> None:
    """Read the process's stdout until a line contains ``text``.

    :param proc: The process.
    :param text: The expected text."""
    while text not in proc.stdout.readline():
        assert proc.poll() is None, "the script ended early"


@POSIX
def test_killed_mid_resume_can_resume_again(script: Script, logdir: Path) -> None:
    """A resume killed before its first log leaves a run that resumes cleanly later."""
    run_id = script(
        "import beamtime\nr = beamtime.init()\nfor s in range(5): r.log({'x': s})\n"
        "print(r.id)\n"
    ).stdout.decode().strip()
    killed = script(
        f"import os, signal, beamtime\nbeamtime.init(resume='{run_id}')\n"
        "os.kill(os.getpid(), signal.SIGKILL)\n"
    )
    assert killed.returncode == -signal.SIGKILL
    run = only_run(logdir)
    assert read_run_info(run).status == "running"
    again = script(
        f"import beamtime\nr = beamtime.init(resume='{run_id}')\nr.log({{'x': 50}}, step=3)\n"
    )
    assert again.returncode == 0
    info = read_run_info(run)
    assert info.status == "finished" and [a.resume_step for a in info.attempts] == [None, 3]
    from beamtime.format.run import read_effective_metrics

    assert [r["x"] for r in read_effective_metrics(run)] == [0, 1, 2, 50]


def test_leftover_temp_files_are_ignored(script: Script, logdir: Path) -> None:
    """A writer killed mid-replace leaves a temp file next to the intact original."""
    script("import beamtime\nbeamtime.init().log({'x': 1})\n")
    run = only_run(logdir)
    (run / "._run.json.tmp").write_text('{"schema": 1, "id": "half')
    (run / "._run_card.json.tmp").write_text("")
    from beamtime.format.run import read_card

    assert read_run_info(run).status == "finished" and read_card(run).metrics["x"].count == 1


@POSIX
def test_repeated_sigterm_still_records_the_kill(
    script: Script, logdir: Path, tmp_path: Path
) -> None:
    """A second SIGTERM during the first one's handling (shell plus launcher) is ignored."""
    code = """
        import os, signal, time, beamtime
        from beamtime.sdk import run as sdk_run
        run = beamtime.init()
        run.log({"x": 1})
        end = sdk_run.Run.end
        def slow_end(self, *args, **kwargs):
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.2)
            end(self, *args, **kwargs)
        sdk_run.Run.end = slow_end
        print("ready", flush=True)
        time.sleep(30)
    """
    proc = start(script, code, tmp_path, logdir)
    wait_for(proc, b"ready")
    proc.send_signal(signal.SIGTERM)
    assert proc.wait(30) == -signal.SIGTERM
    run = only_run(logdir)
    assert read_run_info(run).status == "killed"
    assert read_events(run)[-1].kind == "killed"
