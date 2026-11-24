"""Remote hosts: the parallel probe, the install and the shared ssh login."""

import re
import shlex
import subprocess
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from beamtime.setup.plan import Change

SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]
NAME_FORBIDDEN = "@/=:"
MIN_PYTHON = (3, 11)
SSH_MARK = "# beamtime: one login per session for"
SSH_BLOCK = """{mark} {host}
Host {host}
  ControlMaster auto
  ControlPath ~/.ssh/cm-%r@%h-%p
  ControlPersist 12h
"""
# the first beamtime that answers wins: a venv in or above the log dir (the project's own), the
# PATH, the user's bin, then venvs and conda envs a level or two below home or scratch.
PROBE = """\
p={path}
c=; v=; n=0
try() {{
  [ -z "$c" ] && [ -x "$1" ] && [ "$n" -lt 8 ] || return 0
  n=$((n + 1))
  v=$("$1" --version 2>/dev/null) && [ -n "$v" ] && c=$1
  return 0
}}
if [ -n "$p" ]; then
  d=$p
  while [ -z "$c" ]; do
    for e in .venv venv env .env; do try "$d/$e/bin/beamtime"; done
    case "$d" in /|.) break ;; esac
    d=$(dirname "$d")
  done
fi
try "$(command -v beamtime 2>/dev/null)"
[ -n "$c" ] && [ "$c" = "$(command -v beamtime 2>/dev/null)" ] && c=beamtime
s=${{SCRATCH:-/nonexistent}}
for f in "$HOME"/.local/bin/beamtime "$HOME"/*/.venv/bin/beamtime "$HOME"/*/venv/bin/beamtime \
  "$HOME"/*/*/.venv/bin/beamtime "$HOME"/*/*/venv/bin/beamtime "$s"/*/.venv/bin/beamtime \
  "$s"/*/venv/bin/beamtime "$HOME"/.conda/envs/*/bin/beamtime "$HOME"/*conda*/envs/*/bin/beamtime \
  "$HOME"/*forge*/envs/*/bin/beamtime "$HOME"/*conda*/bin/beamtime "$HOME"/*forge*/bin/beamtime; do
  try "$f"
done
case "$c" in "$HOME"/*) c="~${{c#"$HOME"}}" ;; esac
[ -n "$c" ] && echo "command=$c" && echo "version=$v"
echo "python=$(python3 --version 2>&1)"
echo "scratch=${{SCRATCH:+yes}}"
if [ -n "$p" ]; then
  d=$(dirname "$p"); while [ ! -d "$d" ] && [ "$d" != / ]; do d=$(dirname "$d"); done
  echo "fstype=$(df -PT "$d" 2>/dev/null | awk 'NR==2 {{print $2}}')"
fi
exit 0
"""


@dataclass(frozen=True)
class Probe:
    """What one ssh to a host found out."""

    host: str
    status: Literal["ok", "needs_code", "unknown_host", "no_beamtime", "old_python", "failed"]
    command: str | None = None
    version: str | None = None
    python: str | None = None
    fstype: str | None = None
    detail: str = ""
    scratch: bool = False


def remote_name_problem(name: str) -> str | None:
    """Check a remote's name, the rule ``source add`` and ``setup --remote`` share.

    :param name: The name.
    :return: A one-line reason, or ``None`` when the name is fine."""
    if not name:
        return "a remote needs a name"
    if any(c in name for c in NAME_FORBIDDEN):
        return "a remote name can't contain @, /, = or :"
    return None


def ssh_run(host: str, line: str, timeout: float) -> subprocess.CompletedProcess:
    """Run one line on a host without ever asking for a password.

    :param host: The ssh host.
    :param line: The line the remote shell runs.
    :param timeout: Seconds before the attempt is given up.
    :return: The finished process.
    :raises subprocess.TimeoutExpired: The host did not answer in time."""
    return subprocess.run([*SSH, host, line], capture_output=True, text=True, timeout=timeout)


def remote_path(path: str) -> str:
    """Quote a log dir path for the remote shell, which expands ``~``, ``${VAR}`` and ``{user}``.

    :param path: The path as written in the settings.
    :return: A double-quoted shell word."""
    path = path.replace("{user}", "${USER}")
    if path.startswith("~"):
        path = "${HOME}" + path[1:]
    return '"' + re.sub(r'(["\\`])', r"\\\1", path) + '"'


def probe(
    hosts: list[str], paths: dict[str, str | None] | None = None, *, timeout: float = 30
) -> dict[str, Probe]:
    """Ask every host in one ssh each, all at once, what login, Beamtime, Python and disk it has.

    :param hosts: The ssh hosts.
    :param paths: The log dir per host; a host without one skips the venv and disk checks.
    :param timeout: Seconds one host may take; a slow host fails alone.
    :return: One probe per host, in the order given."""
    names = list(dict.fromkeys(hosts))
    if not names:
        return {}
    paths = paths or {}
    with ThreadPoolExecutor(max_workers=len(names)) as pool:
        found = pool.map(lambda h: probe_host(h, paths.get(h), timeout), names)
        return dict(zip(names, found, strict=True))


def probe_host(host: str, path: str | None, timeout: float) -> Probe:
    """Probe one host.

    :param host: The ssh host.
    :param path: The log dir there, or ``None``.
    :param timeout: Seconds the ssh may take.
    :return: The probe."""
    line = "sh -c " + shlex.quote(PROBE.format(path=remote_path(path) if path else '""'))
    try:
        done = ssh_run(host, line, timeout)
    except subprocess.TimeoutExpired:
        return Probe(host, "failed", detail=f"no answer within {timeout:g} s")
    except OSError as e:
        return Probe(host, "failed", detail=f"ssh didn't start: {e}")
    if done.returncode != 0:
        return login_failure(host, done.stderr)
    facts = dict(row.partition("=")[::2] for row in done.stdout.splitlines() if "=" in row)
    found = re.search(r"(\d+)\.(\d+)", facts.get("python", ""))
    python = facts["python"].removeprefix("Python ").strip() if found else None
    version = (facts.get("version") or "").split()[-1:] or None
    command = (facts.get("command") or None) if version else None
    fstype = facts.get("fstype") or None
    kept = dict(
        command=command,
        version=version[0] if version else None,
        python=python,
        fstype=fstype,
        scratch=facts.get("scratch") == "yes",
    )
    if command is not None:
        return Probe(host, "ok", **kept)
    if found is None:
        return Probe(host, "old_python", detail="no python3 there", **kept)
    if (int(found[1]), int(found[2])) < MIN_PYTHON:
        return Probe(host, "old_python", detail=f"Python {python} is older than 3.11", **kept)
    return Probe(host, "no_beamtime", **kept)


def login_failure(host: str, stderr: str) -> Probe:
    """Name why a login failed under ``BatchMode``.

    :param host: The ssh host.
    :param stderr: What ssh said.
    :return: A probe that is ``needs_code``, ``unknown_host`` or ``failed``."""
    text = stderr.strip()
    if "Host key verification failed" in text:
        return Probe(host, "unknown_host", detail=text)
    if "Permission denied" in text and re.search(r"keyboard-interactive|password", text):
        return Probe(host, "needs_code", detail=text)
    return Probe(host, "failed", detail=text.splitlines()[-1] if text else "login failed")


def install_change(host: str, name: str, version: str, *, python: str = "python3") -> "Change":
    """Plan installing this version of Beamtime on a host, to run after the review.

    :param host: The ssh host.
    :param name: The remote's name, for the review.
    :param version: The version to pin, this one.
    :param python: The interpreter on the host that runs pip.
    :return: The change."""
    from beamtime.setup.plan import Change

    spec = f"beamtime[serve]=={version}"

    def run() -> str:
        done = ssh_run(host, f"{python} -m pip install --user {shlex.quote(spec)}", timeout=600)
        if done.returncode != 0:
            last = (done.stderr.strip() or "install failed").splitlines()[-1]
            raise RuntimeError(f"{host}: {last}")
        return f"installed {spec}"

    return Change(
        where="remote",
        label=name,
        before=None,
        after=f"{python} -m pip install --user {spec}",
        run=run,
    )


def ssh_share_changes(host: str, config: Path, label: str) -> list["Change"]:
    """Plan one login per session for a host: the marked ``ControlMaster`` block, then the login.

    :param host: An alias of the ssh config.
    :param config: The ssh config file.
    :param label: How the review names the file.
    :return: The block (left out when the file has it) and ``ssh -fN`` for the login."""
    from beamtime.setup.plan import Change

    block = SSH_BLOCK.format(mark=SSH_MARK, host=host)
    mark = block.splitlines()[0]
    out = []
    if mark not in read_lines(config):

        def append() -> str:
            # read again: an earlier change of the same apply may have appended a block.
            old = config.read_text(encoding="utf-8") if config.is_file() else ""
            if mark in old.splitlines():
                return "already there"
            config.parent.mkdir(mode=0o700, exist_ok=True)
            gap = "" if not old or old.endswith("\n\n") else "\n" if old.endswith("\n") else "\n\n"
            with config.open("a", encoding="utf-8") as f:
                f.write(gap + block)
            config.chmod(0o600)
            return "appended"

        out.append(
            Change(where="machine", label=label, before=None, after=block.rstrip(), run=append)
        )

    def login() -> str:
        if subprocess.run(["ssh", "-O", "check", host], capture_output=True).returncode == 0:
            return "already open"
        # attached to the terminal, so ssh asks for the password and the code itself.
        if subprocess.run(["ssh", "-fN", host]).returncode != 0:
            raise RuntimeError(f"{host}: ssh -fN failed")
        return "open"

    out.append(Change(where="remote", label=host, before=None, after=f"ssh -fN {host}", run=login))
    return out


def read_lines(path: Path) -> list[str]:
    """Read a file's lines, none when it is missing.

    :param path: The file.
    :return: Its lines."""
    return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
