"""The scan on fixture trees: facts, flows and speed."""

from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest
import yaml

from beamtime.setup.scan import PythonEnv, scan

DESK = {"DISPLAY": ":0", "PATH": ""}
NO_MOUNTS = Path("/nonexistent/mounts")


def run(root: Path, home: Path, **kw):
    """Scan with the fixture home, no mounts file and a desk environment unless told otherwise.

    :param root: The project root.
    :param home: The fake home.
    :return: The scan."""
    kw.setdefault("env", DESK)
    kw.setdefault("mounts", NO_MOUNTS)
    return scan(root, home=home, **kw)


def write_record(logdir: Path) -> None:
    """Write one group with a proposal, a run with a note, and a memory.

    :param logdir: The log dir."""
    for d in ("g/proposal", "g/r1/notes", "memory"):
        (logdir / d).mkdir(parents=True)
    (logdir / "g" / "r1" / "_run.json").write_text("{}")
    (logdir / "g" / "proposal" / "p1.yaml").write_text("x: 1")
    (logdir / "g" / "r1" / "notes" / "n1.md").write_text("x")
    (logdir / "memory" / "m1.md").write_text("x")


def test_flow_first(tmp_path, home):
    s = run(tmp_path, home)
    assert s.flow == "first"
    assert not s.project.settings and not s.project.has_logdir
    assert s.env is None and s.git.root is None


def test_flow_logdir_only(tmp_path, home):
    write_record(tmp_path / "beamtime")
    s = run(tmp_path, home)
    assert s.flow == "update"
    assert not s.project.settings


def test_project_counts(tmp_path, home):
    (tmp_path / "beamtime.yaml").write_text("logdir: runs\n")
    write_record(tmp_path / "runs")
    p = run(tmp_path, home).project
    assert (p.settings, p.has_logdir) == (True, True)
    assert (p.runs, p.notes, p.proposals, p.memories) == (1, 1, 1, 1)
    assert p.logdir == (tmp_path / "runs").resolve()


def test_flow_current_and_teammate(tmp_path, home):
    (tmp_path / "beamtime.yaml").write_text(yaml.safe_dump({"remotes": {"juwels": {"path": "/p"}}}))
    assert run(tmp_path, home).flow == "teammate"

    settings = home / ".config" / "beamtime" / "settings.yaml"
    settings.parent.mkdir(parents=True)
    settings.write_text(yaml.safe_dump({"remotes": {"juwels": {"host": "juwels"}}}))
    assert run(tmp_path, home).flow == "current"

    settings.write_text(yaml.safe_dump({"remotes": {"juwels": {"enabled": False}}}))
    assert run(tmp_path, home).flow == "current"


def test_flow_cluster_by_scheduler(tmp_path, home):
    bin = tmp_path / "bin"
    bin.mkdir()
    sbatch = bin / "sbatch"
    sbatch.write_text("#!/bin/sh\n")
    sbatch.chmod(0o755)
    s = run(tmp_path, home, env={**DESK, "PATH": str(bin)})
    assert (s.scheduler, s.flow) == ("slurm", "cluster")


def test_flow_cluster_by_display(tmp_path, home, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    s = run(tmp_path, home, env={"PATH": ""})
    assert (s.display, s.flow) == (False, "cluster")
    assert run(tmp_path, home, env={"WAYLAND_DISPLAY": "wayland-0"}).flow == "first"


def test_flow_cluster_by_network_home(tmp_path, home):
    mounts = tmp_path / "mounts"
    mounts.write_text(f"/dev/sda1 / ext4 rw 0 0\nserver:/h {home.resolve()} nfs4 rw 0 0\n")
    s = run(tmp_path, home, mounts=mounts)
    assert s.flow == "cluster"


def test_cluster_wins_over_teammate(tmp_path, home, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    (tmp_path / "beamtime.yaml").write_text(yaml.safe_dump({"remotes": {"a": {}}}))
    assert run(tmp_path, home, env={"PATH": ""}).flow == "cluster"


def test_disks(tmp_path, home):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    mounts = tmp_path / "mounts"
    mounts.write_text(
        f"/dev/sda1 / ext4 rw 0 0\n"
        f"server:/s {scratch.resolve()} lustre rw 0 0\n"
        f"tmpfs /tmp tmpfs rw 0 0\n"
    )
    disks = {
        d.label: d
        for d in run(tmp_path, home, mounts=mounts, env={**DESK, "SCRATCH": str(scratch)}).disks
    }
    assert disks["home"].fstype == "ext4" and not disks["home"].network
    assert disks["SCRATCH"].fstype == "lustre" and disks["SCRATCH"].network
    assert disks["cache"].path == home / ".cache"
    assert set(disks) == {"home", "cache", "SCRATCH", "tmp"}


def test_env_uv(project_tree, home):
    env = run(project_tree, home).env
    assert env == PythonEnv("uv", project_tree / ".venv", "3.11", "0.2.0", True)


def test_env_version_without_import(project_tree, home, monkeypatch):
    packages = project_tree / ".venv" / "lib" / "python3.11" / "site-packages"
    (packages / "beamtime").mkdir()
    (packages / "beamtime" / "__init__.py").write_text("raise RuntimeError('imported')\n")
    monkeypatch.syspath_prepend(str(packages))
    monkeypatch.delitem(sys.modules, "beamtime", raising=False)
    assert run(project_tree, home).env.beamtime_version == "0.2.0"


def test_env_without_serve(project_tree, home):
    shutil.rmtree(next((project_tree / ".venv").rglob("uvicorn-*.dist-info")))
    assert run(project_tree, home).env.has_serve is False


def test_env_pip(tmp_path, home):
    packages = tmp_path / ".venv" / "lib" / "python3.12" / "site-packages"
    packages.mkdir(parents=True)
    env = run(tmp_path, home).env
    assert (env.tool, env.python, env.beamtime_version, env.has_serve) == (
        "pip",
        "3.12",
        None,
        False,
    )


def test_env_conda(tmp_path, home):
    prefix = tmp_path / "conda" / "envs" / "demo"
    packages = prefix / "lib" / "python3.10" / "site-packages"
    (packages / "beamtime-0.1.1.dist-info").mkdir(parents=True)
    env = run(tmp_path, home, env={**DESK, "CONDA_PREFIX": str(prefix)}).env
    assert (env.tool, env.path, env.python, env.beamtime_version) == (
        "conda",
        prefix,
        "3.10",
        "0.1.1",
    )


def test_env_none_and_requirements_only(tmp_path, home):
    assert run(tmp_path, home).env is None
    (tmp_path / "requirements.txt").write_text("numpy\n")
    env = run(tmp_path, home).env
    assert (env.tool, env.path, env.python) == ("pip", None, None)


def test_framework_and_job_scripts(project_tree, home):
    ssh = home / ".ssh"
    ssh.mkdir()
    (ssh / "config").write_text(
        "Host juwels\n  HostName juwels.fz-juelich.de\n  User me\nHost other\n"
    )
    s = run(project_tree, home)
    assert s.framework == "lightning"
    [job] = s.job_scripts
    assert (job.path, job.scheduler, job.hosts) == ("jobs/train.sbatch", "slurm", ("juwels",))


def test_framework_none_and_deep_files_ignored(tmp_path, home):
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (deep / "train.py").write_text("import pytorch_lightning\n")
    (deep / "x.sbatch").write_text("#SBATCH -n 1\n")
    s = run(tmp_path, home)
    assert s.framework is None and s.job_scripts == ()
    (tmp_path / "a" / "train.py").write_text("from pytorch_lightning import Trainer\n")
    assert run(tmp_path, home).framework == "lightning"


def test_job_script_in_shell_file(tmp_path, home):
    (tmp_path / "run.sh").write_text("#!/bin/bash\n#PBS -l nodes=1\n")
    (tmp_path / "plain.sh").write_text("#!/bin/bash\necho hi\n")
    assert [(j.path, j.scheduler) for j in run(tmp_path, home).job_scripts] == [("run.sh", "pbs")]


def test_ssh_wildcards(tmp_path, home):
    (home / ".ssh").mkdir()
    (home / ".ssh" / "config").write_text(
        "Host *\n  ForwardAgent yes\n"
        "Host juwels jw-*\n  HostName jwlogin.example.org\n  User me\n"
        "Host !bad ok?\n"
        "Host=eq\n  hostname=eq.example.org\n"
    )
    hosts = run(tmp_path, home).ssh_hosts
    assert [(h.name, h.hostname, h.user) for h in hosts] == [
        ("juwels", "jwlogin.example.org", "me"),
        ("eq", "eq.example.org", None),
    ]


def test_ssh_include(tmp_path, home):
    ssh = home / ".ssh"
    (ssh / "config.d").mkdir(parents=True)
    (ssh / "config").write_text("Include config.d/*\nInclude ~/.ssh/loop\nHost main\n")
    (ssh / "config.d" / "a").write_text("Host alpha\n  User x\n")
    (ssh / "config.d" / "b").write_text("Host beta\n")
    (ssh / "loop").write_text(f"Include {ssh / 'config'}\nHost looped\n")
    assert [h.name for h in run(tmp_path, home).ssh_hosts] == ["alpha", "beta", "looped", "main"]


def test_ssh_missing_config(tmp_path, home):
    assert run(tmp_path, home).ssh_hosts == ()


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_git(tmp_path, home):
    def git(*args):
        subprocess.run(
            ["git", "-C", str(tmp_path), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            check=True,
            capture_output=True,
        )

    git("init", "-b", "work")
    (tmp_path / ".gitignore").write_text("beamtime/\n")
    git("add", ".")
    git("commit", "-m", "x")
    s = run(tmp_path, home)
    assert (s.git.branch, s.git.clean, s.git.logdir_ignored) == ("work", True, True)
    assert s.git.root == tmp_path
    (tmp_path / "new.py").write_text("x = 1\n")
    assert run(tmp_path, home).git.clean is False


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git")
def test_git_without_commits_and_no_ignore(tmp_path, home):
    subprocess.run(
        ["git", "-C", str(tmp_path), "init", "-b", "fresh"], check=True, capture_output=True
    )
    git = run(tmp_path, home).git
    assert (git.branch, git.clean, git.logdir_ignored) == ("fresh", True, False)


def test_scan_is_fast_on_a_large_tree(tmp_path, home):
    for i in range(40):
        d = tmp_path / f"d{i}" / "sub"
        d.mkdir(parents=True)
        for j in range(25):
            (d / f"f{j}.py").write_text("import numpy\n" * 20)
            (tmp_path / f"d{i}" / f"g{j}.txt").write_text("x")
    write_record(tmp_path / "beamtime")
    assert sum(1 for _ in tmp_path.rglob("*") if _.is_file()) >= 2000
    start = time.perf_counter()
    run(tmp_path, home)
    assert time.perf_counter() - start < 1.0
