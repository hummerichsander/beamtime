"""What a run records about its environment: host, git, packages, scheduler, rank."""

import getpass
import hashlib
import os
import platform
import socket
import subprocess
import sys
from collections.abc import Mapping
from importlib import metadata
from pathlib import Path
from typing import Any

GIT_DIFF_CAP = 1024 * 1024
UNTRACKED_CAP = 50
RANK_VARS = ("RANK", "SLURM_PROCID", "LOCAL_RANK", "NODE_RANK")
TIME_LIMIT_WINDOW_S = 300


def user() -> str:
    """Name the local account.

    :return: The user name, or ``unknown``."""
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


def host_info() -> dict[str, Any]:
    """Describe the machine and interpreter.

    :return: ``hostname``, ``user``, ``os`` and ``python``."""
    return {
        "hostname": socket.gethostname(),
        "user": user(),
        "os": platform.system(),
        "python": platform.python_version(),
    }


def git(args: list[str], cwd: Path) -> str | None:
    """Run a git command with a short timeout.

    :param args: The arguments after ``git``.
    :param cwd: Where to run it.
    :return: Its output, or ``None`` if git is missing, fails or is too slow."""
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            timeout=2,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.decode(errors="replace") if out.returncode == 0 else None


def untracked_files(cwd: Path, logdir: Path | None = None) -> list[str]:
    """List untracked paths, so a new file counts as a change too.

    An untracked folder is one entry, as ``git status`` shows it. The log dir is left out:
    every run adds files there, which would make each run's code look different.

    :param cwd: A directory inside the checkout.
    :param logdir: The log dir, which may lie inside the checkout.
    :return: Up to :data:`UNTRACKED_CAP` paths relative to the checkout's top, sorted."""
    status = git(["status", "--porcelain", "-z"], cwd) or ""
    paths = sorted(entry[3:] for entry in status.split("\0") if entry[:3] == "?? ")
    if logdir is not None and paths and (top := git(["rev-parse", "--show-toplevel"], cwd)):
        root, skip = Path(top.strip()), logdir.resolve()
        paths = [p for p in paths if skip != (q := (root / p).resolve()) and skip not in q.parents]
    return paths[:UNTRACKED_CAP]


def git_info(cwd: Path, logdir: Path | None = None) -> tuple[dict[str, Any] | None, str | None]:
    """Describe the git checkout and its uncommitted changes.

    A new untracked file leaves no trace in ``git diff``, so it is listed and counted
    into ``dirty`` and ``diff_sha`` on its own.

    :param cwd: A directory inside the checkout.
    :param logdir: The log dir, whose files are never counted as changes.
    :return: ``commit``, ``branch``, ``dirty``, ``untracked``, ``diff_sha`` and ``remote``,
        and the diff of tracked files (capped at 1 MB), or ``(None, None)`` outside a
        checkout."""
    if (commit := git(["rev-parse", "HEAD"], cwd)) is None:
        return None, None
    diff = git(["diff", "HEAD"], cwd) or ""
    untracked = untracked_files(cwd, logdir)
    dirty = bool(diff) or bool(untracked)
    diff_sha = None
    if dirty:
        payload = diff + "\x00" + "\x00".join(untracked)
        diff_sha = hashlib.sha256(payload.encode()).hexdigest()[:8]
    if len(diff) > GIT_DIFF_CAP:
        diff = diff[:GIT_DIFF_CAP] + "\n[beamtime: diff cut at 1 MB]\n"
    info = {
        "commit": commit.strip(),
        "branch": (git(["rev-parse", "--abbrev-ref", "HEAD"], cwd) or "").strip() or None,
        "dirty": dirty,
        "untracked": untracked,
        "diff_sha": diff_sha,
        "remote": (git(["remote", "get-url", "origin"], cwd) or "").strip() or None,
    }
    return info, diff or None


def packages() -> str:
    """List the installed distributions without a subprocess.

    :return: One ``name==version`` per line, sorted."""
    names = set()
    for d in metadata.distributions():
        if name := d.metadata["Name"]:
            names.add(f"{name}=={d.version}")
    return "".join(f"{n}\n" for n in sorted(names, key=str.lower))


def scheduler(env: Mapping[str, str]) -> dict[str, Any] | None:
    """Detect the job scheduler and map what it exposes to common names.

    :param env: The environment variables.
    :return: The ``scheduler`` field of ``_run.json``, or ``None``."""

    def pick(**names: str) -> dict[str, str]:
        return {k: env[v] for k, v in names.items() if env.get(v)}

    if env.get("SLURM_JOB_ID"):
        return {"kind": "slurm"} | pick(
            job_id="SLURM_JOB_ID",
            array_job_id="SLURM_ARRAY_JOB_ID",
            array_task_id="SLURM_ARRAY_TASK_ID",
            partition="SLURM_JOB_PARTITION",
            nodes="SLURM_JOB_NODELIST",
        )
    if env.get("PBS_JOBID"):
        return {"kind": "pbs"} | pick(
            job_id="PBS_JOBID",
            array_index="PBS_ARRAY_INDEX",
            queue="PBS_QUEUE",
            nodes="PBS_NODEFILE",
        )
    if env.get("LSB_JOBID"):
        return {"kind": "lsf"} | pick(
            job_id="LSB_JOBID",
            array_index="LSB_JOBINDEX",
            queue="LSB_QUEUE",
            nodes="LSB_HOSTS",
        )
    if env.get("KUBERNETES_SERVICE_HOST"):
        return {"kind": "kubernetes"} | pick(pod="HOSTNAME", namespace="POD_NAMESPACE")
    return None


def requeued(env: Mapping[str, str]) -> bool:
    """Tell whether this process is a SLURM requeue of a killed job.

    :param env: The environment variables.
    :return: Whether ``SLURM_RESTART_COUNT`` is set and above zero."""
    try:
        return int(env.get("SLURM_RESTART_COUNT") or 0) > 0
    except ValueError:
        return False


def near_time_limit(env: Mapping[str, str], now: float) -> bool:
    """Tell whether the job's wall-time limit has ended this process, or is about to.

    :param env: The environment variables.
    :param now: The current time, unix seconds.
    :return: Whether ``now`` is past ``SLURM_JOB_END_TIME`` minus ``TIME_LIMIT_WINDOW_S``."""
    try:
        end = float(env["SLURM_JOB_END_TIME"])
    except (KeyError, ValueError):
        return False
    # the limit itself signals at or after the end time; a requeue on the warning, minutes before.
    return end - now <= TIME_LIMIT_WINDOW_S


def job_key(env: Mapping[str, str]) -> str | None:
    """Identify the launch, so other ranks of the same job find the run.

    :param env: The environment variables.
    :return: E.g. ``slurm:8812300:45`` or ``torchrun:<id>``, or ``None``."""
    if job := env.get("SLURM_ARRAY_JOB_ID") or env.get("SLURM_JOB_ID"):
        task = env.get("SLURM_ARRAY_TASK_ID")
        return f"slurm:{job}:{task}" if task else f"slurm:{job}"
    if run_id := env.get("TORCHELASTIC_RUN_ID"):
        return f"torchrun:{run_id}"
    for kind, var in (("pbs", "PBS_JOBID"), ("lsf", "LSB_JOBID")):
        if job := env.get(var):
            return f"{kind}:{job}"
    return None


def rank(env: Mapping[str, str]) -> int:
    """Find this process's rank; it is 0 iff every rank variable it sees is 0 or unset.

    :param env: The environment variables.
    :return: The global rank, or a stand-in when only local and node ranks are known."""

    def value(name: str) -> int:
        try:
            return int(env.get(name) or 0)
        except ValueError:
            return 0

    if all(value(v) == 0 for v in RANK_VARS):
        return 0
    for name in ("RANK", "SLURM_PROCID"):
        if env.get(name):
            return value(name)
    if size := value("LOCAL_WORLD_SIZE"):
        return value("NODE_RANK") * size + value("LOCAL_RANK")
    return value("LOCAL_RANK") or 1000 * value("NODE_RANK")


def command() -> list[str]:
    """Reconstruct the command line.

    :return: The interpreter's ``argv``, starting with ``python``."""
    return ["python", *sys.orig_argv[1:]] if hasattr(sys, "orig_argv") else sys.argv


def cwd() -> str:
    """Name the working directory.

    :return: The absolute working directory."""
    return os.getcwd()
