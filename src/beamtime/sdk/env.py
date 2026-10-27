"""What a run records about its environment: host, git, packages, scheduler, rank."""

import getpass
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
RANK_VARS = ("RANK", "SLURM_PROCID", "LOCAL_RANK", "NODE_RANK")


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


def git_info(cwd: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Describe the git checkout and its uncommitted changes.

    :param cwd: A directory inside the checkout.
    :return: ``commit``, ``branch``, ``dirty`` and ``remote``, and the diff of tracked
        files (capped at 1 MB), or ``(None, None)`` outside a checkout."""
    if (commit := git(["rev-parse", "HEAD"], cwd)) is None:
        return None, None
    diff = git(["diff", "HEAD"], cwd) or ""
    if len(diff) > GIT_DIFF_CAP:
        diff = diff[:GIT_DIFF_CAP] + "\n[beamtime: diff cut at 1 MB]\n"
    info = {
        "commit": commit.strip(),
        "branch": (git(["rev-parse", "--abbrev-ref", "HEAD"], cwd) or "").strip() or None,
        "dirty": bool(diff),
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
