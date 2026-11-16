"""Remotes of the setup: the parallel probe, the install and the shared ssh login, on a faked ssh."""

import os
import subprocess
import time
from pathlib import Path

import pytest

from beamtime import __version__
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.setup import remotes
from beamtime.setup.apply import apply
from beamtime.setup.plan import Remote
from beamtime.setup.remotes import Probe, probe, remote_name_problem

from .test_plan import make_plan, project  # noqa: F401

FAKE_SSH = """\
#!/bin/sh
echo "$@" >> "$SSH_LOG"
case "$1" in
  -fN) exit 0 ;;
  -O) exit 1 ;;
esac
host="$5"
line="$6"
case "$line" in
  *"pip install"*)
    [ "$host" = badpip ] && { echo "ERROR: Package requires a different Python: 3.9.2" >&2; exit 1; }
    exit 0 ;;
esac
case "$host" in
  needs_code) echo "u@h: Permission denied (publickey,keyboard-interactive)." >&2; exit 255 ;;
  unknown_host) echo "Host key verification failed." >&2; exit 255 ;;
  slow) exec sleep 30 ;;
  local) exec sh -c "$line" ;;
  ok) printf 'how=path\\nversion=beamtime 0.2.2\\npython=Python 3.12.1\\nfstype=ext4\\n' ;;
  no_beamtime) printf 'how=path\\npython=Python 3.12.1\\nfstype=ext4\\n' ;;
  old_python) printf 'how=path\\npython=Python 3.9.2\\n' ;;
  *) echo "ssh: Could not resolve hostname $host" >&2; exit 255 ;;
esac
"""


@pytest.fixture
def ssh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake ``ssh`` first on ``PATH``; it logs its arguments and acts by host name.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :return: The log of the calls, one line each."""
    bin_dir = tmp_path / "fakebin"
    bin_dir.mkdir()
    (bin_dir / "ssh").write_text(FAKE_SSH)
    (bin_dir / "ssh").chmod(0o755)
    log = tmp_path / "ssh.log"
    log.touch()
    monkeypatch.setenv("SSH_LOG", str(log))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return log


def test_probe_reports_each_host(ssh: Path) -> None:
    """One ssh per host tells login, Beamtime and Python apart."""
    found = probe(["ok", "needs_code", "unknown_host", "no_beamtime", "old_python", "gone"])
    assert {h: p.status for h, p in found.items()} == {
        "ok": "ok",
        "needs_code": "needs_code",
        "unknown_host": "unknown_host",
        "no_beamtime": "no_beamtime",
        "old_python": "old_python",
        "gone": "failed",
    }
    assert found["ok"] == Probe(
        "ok", "ok", command="beamtime", version="0.2.2", python="3.12.1", fstype="ext4"
    )
    assert "older than 3.11" in found["old_python"].detail
    assert "Could not resolve" in found["gone"].detail
    assert ssh.read_text().count("BatchMode=yes") == 6


def test_probe_timeout(ssh: Path) -> None:
    """A host that doesn't answer fails alone after its timeout, the others are not held up."""
    start = time.monotonic()
    # 3 s, not less: on a loaded machine the fake ssh of a quick host can take a second to start.
    found = probe(["slow", "ok", "needs_code"], timeout=3)
    assert time.monotonic() - start < 10
    assert found["slow"].status == "failed" and "within 3 s" in found["slow"].detail
    assert found["ok"].status == "ok" and found["needs_code"].status == "needs_code"


def test_probe_line_runs_in_a_shell(ssh: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The one line the remote shell gets finds a venv next to the log dir, expanding ``~``."""
    home = tmp_path / "remote-home"
    venv = home / "proj" / ".venv" / "bin"
    venv.mkdir(parents=True)
    (home / "proj" / "beamtime").mkdir()
    for name, text in (("beamtime", "beamtime 0.2.2"), ("python3", "Python 3.12.1")):
        tool = venv.parent.parent / name if name == "python3" else venv / name
        tool.write_text(f"#!/bin/sh\necho '{text}'\n")
        tool.chmod(0o755)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SCRATCH", str(home))
    fake = os.environ["PATH"].split(os.pathsep)[0]
    monkeypatch.setenv("PATH", f"{fake}:{venv.parent.parent}:/usr/bin:/bin")
    found = probe(["local"], {"local": "~/proj/beamtime"})["local"]
    assert found.status == "ok" and found.version == "0.2.2", found
    assert found.command == "~/proj/beamtime/../.venv/bin/beamtime"
    assert found.python == "3.12.1"
    assert found.scratch


def test_install_and_ssh_share_only_when_asked(project: Path, home: Path) -> None:  # noqa: F811
    """Without their flags the plan has no remote change."""
    changes = make_plan(project, home, "--remote", "juwels=jdoe@login:/p")
    assert not [c for c in changes if c.where == "remote"]
    assert not (home / ".ssh").exists()


def test_install_pins_version(ssh: Path, project: Path, home: Path) -> None:  # noqa: F811
    """The install is the last step and pins this release for the user's site-packages."""
    changes = make_plan(
        project, home, "--remote", "juwels=jdoe@login:/p", "--install-remote", "juwels", "--yes"
    )
    install = changes[-1]
    assert install.where == "remote" and install.label == "juwels"
    assert f"beamtime[serve]=={__version__}" in install.after
    assert ssh.read_text() == ""
    apply(changes)
    line = ssh.read_text().splitlines()[-1]
    assert line.endswith(f"jdoe@login python3 -m pip install --user 'beamtime[serve]=={__version__}'")
    assert "BatchMode=yes" in line


def test_failed_install_names_the_host(ssh: Path, project: Path, home: Path) -> None:  # noqa: F811
    """A pip failure surfaces as the host and the last line pip said."""
    changes = make_plan(project, home, "--remote", "badpip", "--install-remote", "badpip")
    with pytest.raises(Exception, match="badpip: ERROR: Package requires a different Python"):
        changes[-1].run()


def test_ssh_block_once(ssh: Path, project: Path, home: Path) -> None:  # noqa: F811
    """The block lands once, marked, below what the file had; a second plan adds none."""
    config = home / ".ssh" / "config"
    config.parent.mkdir()
    config.write_text("Host other\n  User me")
    first = make_plan(project, home, "--remote", "juwels", "--ssh-share", "juwels")
    shared = [c for c in first if c.label == "~/.ssh/config"]
    assert len(shared) == 1 and shared[0].where == "machine"
    apply(first)
    apply(make_plan(project, home, "--remote", "juwels", "--ssh-share", "juwels"))
    text = config.read_text()
    assert text.count("# beamtime: one login per session for juwels") == 1
    assert text.startswith("Host other\n  User me\n\n# beamtime:")
    assert "  ControlPath ~/.ssh/cm-%r@%h-%p\n  ControlPersist 12h\n" in text
    assert oct(config.stat().st_mode)[-3:] == "600"
    again = make_plan(project, home, "--remote", "juwels", "--ssh-share", "juwels")
    assert not [c for c in again if c.label == "~/.ssh/config"]


def test_ssh_login_runs_attached(
    ssh: Path, project: Path, home: Path, monkeypatch: pytest.MonkeyPatch  # noqa: F811
) -> None:
    """``ssh -fN`` inherits the terminal: no captured streams, so ssh can ask for the code."""
    calls = []
    real = subprocess.run

    def spy(argv, **kw):
        calls.append((argv, kw))
        return real(argv, **kw)

    monkeypatch.setattr(subprocess, "run", spy)
    changes = make_plan(project, home, "--remote", "juwels", "--ssh-share", "juwels")
    apply(changes)
    (argv, kw), = [c for c in calls if c[0][:2] == ["ssh", "-fN"]]
    assert argv == ["ssh", "-fN", "juwels"] and not kw
    assert [c.label for c in changes][-2:] == ["~/.ssh/config", "juwels"]


def test_names_must_be_known(project: Path, home: Path) -> None:  # noqa: F811
    """An install or share for a name that is no remote is refused before anything runs."""
    with pytest.raises(ValueError, match="--install-remote nowhere: no remote of that name"):
        make_plan(project, home, "--install-remote", "nowhere")
    with pytest.raises(ValueError, match="--ssh-share nowhere: no remote of that name"):
        make_plan(project, home, "--ssh-share", "nowhere")
    with pytest.raises(ValueError, match="alias of ~/.ssh/config"):
        make_plan(project, home, "--remote", "x=jdoe@login", "--ssh-share", "x")


@pytest.mark.parametrize("name", ["a@b", "a/b", "a=b", "a:b"])
def test_remote_names_follow_one_rule(name: str, ctx: Context) -> None:
    """``setup --remote`` and ``source add`` refuse the same names, with one line."""
    assert remote_name_problem(name) == "a remote name can't contain @, /, = or :"
    with pytest.raises(OpError, match="can't contain @, /, = or :"):
        call("source add", {"name": name, "remote": "h:/p", "command": "bt"}, ctx)
    if name[1] in "@/":
        with pytest.raises(ValueError, match=r"--remote 'a.b': a remote name can't contain"):
            Remote.parse(name)
    assert Remote.parse("fine-name=h:/p").name == "fine-name"


def test_ssh_share_of_one_host_twice(ssh: Path, project: Path, home: Path) -> None:  # noqa: F811
    """Two names for one host plan one block; blocks for two hosts stay a blank line apart."""
    config = home / ".ssh" / "config"
    config.parent.mkdir()
    config.write_text("Host jw\n  User me\n")
    changes = make_plan(
        project, home, "--remote", "juwels=jw", "--remote", "other",
        "--ssh-share", "juwels", "--ssh-share", "jw", "--ssh-share", "other",
    )  # fmt: skip
    assert [c.after for c in changes if c.where == "remote"] == ["ssh -fN jw", "ssh -fN other"]
    apply(changes)
    text = config.read_text()
    assert text.count("# beamtime: one login per session for jw") == 1
    assert "ControlPersist 12h\n\n# beamtime: one login per session for other\n" in text
