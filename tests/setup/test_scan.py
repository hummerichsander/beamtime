"""The scan on fixture trees: facts, flows and speed."""

from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import time

import pytest
import yaml

from beamtime import __version__
from beamtime.guide.rules import END, RELEASES, START, render, write_block
from beamtime.settings import Settings
from beamtime.setup.scan import PythonEnv, scan
from tests.test_budgets import timed

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


def test_flow_teammate_by_an_unregistered_agent(tmp_path, home, tools):
    """An installed agent client without Beamtime makes a teammate, however complete the project."""
    (tmp_path / "beamtime.yaml").write_text("logdir: beamtime\n")
    env = {**DESK, "PATH": tools("cursor")}
    s = run(tmp_path, home, env=env)
    assert s.flow == "teammate" and not s.agents[0].registered
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text('{"mcpServers": {"beamtime": {}}}')
    s = run(tmp_path, home, env=env)
    assert s.flow == "current" and s.agents[0].registered
    (tmp_path / ".cursor" / "mcp.json").write_text("{not json")
    assert run(tmp_path, home, env=env).flow == "teammate"


def test_flow_ignores_an_agent_that_is_not_installed(tmp_path, home):
    """A project file of a client that isn't on this machine asks nothing."""
    (tmp_path / "beamtime.yaml").write_text("logdir: beamtime\n")
    (tmp_path / ".cursor").mkdir()
    s = run(tmp_path, home)
    assert s.agents and s.flow == "current"


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
    # the fake home gets its own mount: on a runner whose /tmp is tmpfs it would fall under /tmp.
    mounts.write_text(
        f"/dev/sda1 / ext4 rw 0 0\n"
        f"tmpfs /tmp tmpfs rw 0 0\n"
        f"/dev/sda2 {home.resolve()} ext4 rw 0 0\n"
        f"server:/s {scratch.resolve()} lustre rw 0 0\n"
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
    assert env == PythonEnv("uv", project_tree / ".venv", "3.11", __version__, True)


def test_env_version_without_import(project_tree, home, monkeypatch):
    packages = project_tree / ".venv" / "lib" / "python3.11" / "site-packages"
    (packages / "beamtime").mkdir()
    (packages / "beamtime" / "__init__.py").write_text("raise RuntimeError('imported')\n")
    monkeypatch.syspath_prepend(str(packages))
    monkeypatch.delitem(sys.modules, "beamtime", raising=False)
    assert run(project_tree, home).env.beamtime_version == __version__


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


@timed
def test_scan_is_fast_on_a_large_tree(tmp_path, home):
    """Scanning a tree of over 2000 files stays under one second (a timing budget, run serially)."""
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


def touch(root: Path, *names: str) -> None:
    """Create empty files, and the folders around them.

    :param root: The folder they go below.
    :param names: Paths relative to ``root``."""
    for name in names:
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).touch()


def rules_file(path: Path, preface: str = "") -> str:
    """Write an instruction file with this release's rules block.

    :param path: The file.
    :param preface: Text before the block.
    :return: The block."""
    block = render(Settings().agent, ["setup", "serve", "settings"])
    write_block(path, block)
    path.write_text(preface + path.read_text())
    return block


def test_agents_by_project_files_and_path(tmp_path, home, tools):
    (tmp_path / ".mcp.json").write_text("{}")
    rules_file(tmp_path / "CLAUDE.md")
    found = {a.client: a for a in run(tmp_path, home, env={"PATH": tools("codex")}).agents}
    assert set(found) == {"claude-code", "codex"}
    claude, codex = found["claude-code"], found["codex"]
    assert claude.command is None and claude.files == (".mcp.json", "CLAUDE.md")
    assert (claude.rules_file, claude.has_block) == ("CLAUDE.md", True)
    assert claude.release == version("beamtime")
    assert codex.command is not None and codex.files == ()
    assert (codex.rules_file, codex.has_block, codex.release) == ("AGENTS.md", False, None)


def test_agents_user_wide_config_and_shared_rules_file(tmp_path, home):
    touch(home, ".codex/config.toml")
    rules_file(tmp_path / "AGENTS.md")
    (agent,) = run(tmp_path, home).agents
    assert (agent.client, agent.files) == ("codex", ("~/.codex/config.toml",))
    assert (agent.has_block, agent.release) == (True, version("beamtime"))


def test_agents_old_and_edited_blocks(tmp_path, home):
    old = (files("beamtime.guide") / "rules" / "history" / "0.1.0.md").read_text()
    write_block(tmp_path / "GEMINI.md", old.strip())
    write_block(tmp_path / "CLAUDE.md", "Written by hand.")
    found = {a.client: a for a in run(tmp_path, home).agents}
    assert found["gemini"].release == RELEASES["0.1.0.md"]
    assert (found["claude-code"].has_block, found["claude-code"].release) == (True, None)


def test_no_agents(tmp_path, home):
    (tmp_path / "AGENTS.md").write_text("notes\n")
    assert run(tmp_path, home).agents == ()


def test_conflicts(tmp_path, home):
    (tmp_path / "CLAUDE.md").write_text(
        "# Rules\nKeep results in NOTES.md.\nBe kind.\nThe Experiment Log is in docs/\n"
    )
    (tmp_path / "AGENTS.md").write_text("Our results go in a spreadsheet.\nLab notebook: wiki\n")
    assert run(tmp_path, home).conflicts == (
        ("CLAUDE.md", 2, "Keep results in NOTES.md."),
        ("CLAUDE.md", 4, "The Experiment Log is in docs/"),
        ("AGENTS.md", 1, "Our results go in a spreadsheet."),
        ("AGENTS.md", 2, "Lab notebook: wiki"),
    )


def test_conflict_outside_block(tmp_path, home):
    block = START + "\nExperiment log lines belong in Beamtime. Keep results in Beamtime.\n" + END
    (tmp_path / "CLAUDE.md").write_text(f"top: keep notes in a diary\n{block}\nlab notebook\n")
    lines = [(c.line, c.text) for c in run(tmp_path, home).conflicts]
    assert lines == [(1, "top: keep notes in a diary"), (5, "lab notebook")]


def test_past_work_by_source(tmp_path, home):
    touch(tmp_path, "tb_logs/model/version_0/events.out.tfevents.1.h.1")
    touch(tmp_path, "tb_logs/model/version_1/events.out.tfevents.2.h.1")
    touch(tmp_path, "wandb/offline-run-20240101_000000-a/run-a.wandb")
    touch(tmp_path, "mlruns/0/abc/meta.yaml", "mlruns/0/abc/metrics/loss")
    touch(tmp_path, "old/r1/_run.json")
    touch(tmp_path, "data/table.csv", "deep/a/b/c/events.out.tfevents.1.h.1")
    past = {p.found.kind: p for p in run(tmp_path, home).past}
    assert set(past) == {"tensorboard", "wandb", "mlflow", "beamtime"}
    assert all(not p.other for p in past.values())
    assert past["tensorboard"].found.path == tmp_path / "tb_logs" / "model"
    assert past["tensorboard"].found.n == 2
    assert past["wandb"].found.path == tmp_path / "wandb"
    assert past["mlflow"].found.path == tmp_path / "mlruns"
    assert past["beamtime"].found.path == tmp_path / "old" / "r1"


def test_past_work_skips_environments_and_hidden(tmp_path, home):
    touch(tmp_path, ".venv/x/events.out.tfevents.1", ".hidden/events.out.tfevents.1")
    touch(tmp_path, "node_modules/x/mlflow.db")
    assert run(tmp_path, home).past == ()


def test_past_work_mlflow_db_at_the_root(tmp_path, home):
    mlflow = tmp_path / "mlflow.db"
    con = sqlite3.connect(mlflow)
    con.executescript(
        "CREATE TABLE experiments (experiment_id, lifecycle_stage);"
        "CREATE TABLE runs (run_uuid, experiment_id, lifecycle_stage);"
    )
    con.close()
    assert [p.found.path for p in run(tmp_path, home).past] == [mlflow]


def test_own_logdir_not_offered(tmp_path, home):
    touch(tmp_path, "beamtime/g/r1/_run.json", "runs/g/r1/_run.json")
    (tmp_path / "beamtime.yaml").write_text("logdir: runs\n")
    touch(tmp_path, "beamtime/g/r2/_run.json")
    kinds = [(p.found.kind, p.found.path) for p in run(tmp_path, home).past]
    assert kinds == []


def test_own_nested_logdir_not_offered(tmp_path, home):
    touch(tmp_path, "exp/tb/events.out.tfevents.1", "exp/beamtime/g/_run.json")
    (tmp_path / "beamtime.yaml").write_text("logdir: exp/beamtime\n")
    assert [p.found.path for p in run(tmp_path, home).past] == [tmp_path / "exp" / "tb"]


def known(tmp_path: Path, monkeypatch, *logdirs: Path) -> None:
    """Give the index cache a database for each log dir, as an opened index leaves it.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :param logdirs: The log dirs the cache knows."""
    for n, logdir in enumerate(logdirs):
        (tmp_path / "cache" / f"c{n}").mkdir(parents=True)
        con = sqlite3.connect(tmp_path / "cache" / f"c{n}" / "index.sqlite")
        con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        con.execute("INSERT INTO meta VALUES ('logdir', ?)", (str(logdir),))
        con.commit()
        con.close()
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))


def test_past_work_from_other_logdirs(tmp_path, home, monkeypatch):
    other, root = tmp_path / "elsewhere", tmp_path / "project"
    touch(other, "g/r1/_run.json", "g/r2/_run.json")
    touch(root, "mine/g/r1/_run.json")
    (root / "beamtime.yaml").write_text("logdir: mine\n")
    known(tmp_path, monkeypatch, other, root / "mine")
    (past,) = run(root, home).past
    assert past.other and (past.found.kind, past.found.n) == ("beamtime", 2)
    assert past.found.path == other.resolve()


def test_notes_and_claude_memory(tmp_path, home):
    root = tmp_path / "my.project"
    touch(root, "NOTES.md", "notebook/a.md", "notebook/b.md", "docs/notes/c.md", "notes/.hidden")
    escaped = re.sub(r"[^A-Za-z0-9-]", "-", str(root.resolve()))
    memory = home / ".claude" / "projects" / escaped / "memory"
    touch(memory, "MEMORY.md", "style.md")
    found = [
        (n.kind, n.path.relative_to(root if n.kind == "notes" else home), n.n)
        for n in run(root, home).notes
    ]
    assert found == [
        ("notes", Path("NOTES.md"), 1),
        ("notes", Path("notebook"), 2),
        ("notes", Path("docs/notes"), 1),
        ("memory", memory.relative_to(home), 2),
    ]


def test_claude_memory_folder_name(tmp_path, home):
    root = tmp_path / "a b" / ".c_d"
    root.mkdir(parents=True)
    expected = str(root.resolve()).replace("/", "-").replace(".", "-").replace(" ", "-")
    expected = expected.replace("_", "-")
    touch(home / ".claude" / "projects" / expected / "memory", "m.md")
    assert [n.kind for n in run(root, home).notes] == ["memory"]


def test_logdir_notes_are_not_offered(tmp_path, home):
    touch(tmp_path, "beamtime/notes/n.md", "beamtime/memory/m.md")
    assert run(tmp_path, home).notes == ()


def test_stale_is_empty_here(tmp_path, home):
    assert run(tmp_path, home).stale == ()
