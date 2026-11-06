import argparse
import dataclasses
import os
import subprocess
from pathlib import Path

import pytest

from beamtime.sdk import env
from beamtime.sdk.paths import check_folder, find_run, locate, logdir_of
from beamtime.sdk.run import scalar, to_config, to_proposal


def git_repo(path: Path) -> Path:
    """Make a tiny git repo with one commit.

    :param path: Where to create it.
    :return: The repo's directory."""
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True)
    (path / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "a.py"], cwd=path, check=True)
    # a fixed date, so two repos made in different seconds get the same commit.
    date = {"GIT_AUTHOR_DATE": "2026-01-01T00:00:00", "GIT_COMMITTER_DATE": "2026-01-01T00:00:00"}
    subprocess.run(
        ["git", "commit", "-q", "-m", "init"], cwd=path, check=True, env=os.environ | date
    )
    return path


def test_git_info_untracked_file_counts_as_dirty(tmp_path: Path) -> None:
    """A new, never-added file makes the checkout dirty and is listed, unlike a bare diff."""
    repo = git_repo(tmp_path / "repo")
    clean, clean_diff = env.git_info(repo)
    assert clean["dirty"] is False and clean["untracked"] == [] and clean["diff_sha"] is None
    assert clean_diff is None
    (repo / "b.py").write_text("y = 2\n")
    info, diff = env.git_info(repo)
    assert info["dirty"] is True
    assert info["untracked"] == ["b.py"]
    assert info["diff_sha"] is not None
    assert diff is None  # an untracked file never shows up in `git diff`.


def test_git_info_leaves_out_the_log_dir(tmp_path: Path) -> None:
    """Runs written into an untracked log dir inside the checkout don't make it dirty."""
    repo = git_repo(tmp_path / "repo")
    (repo / "beamtime" / "exp" / "run-1").mkdir(parents=True)
    (repo / "beamtime" / "exp" / "run-1" / "_run.json").write_text("{}")
    info, _ = env.git_info(repo, repo / "beamtime")
    assert info["dirty"] is False and info["untracked"] == [] and info["diff_sha"] is None
    (repo / "new.py").write_text("y = 2\n")
    info, _ = env.git_info(repo, repo / "beamtime")
    assert info["untracked"] == ["new.py"]


def test_git_info_diff_sha_matches_across_checkouts_with_the_same_change(tmp_path: Path) -> None:
    """Two checkouts of the same commit with the same uncommitted change compare equal."""
    a, b = git_repo(tmp_path / "a"), git_repo(tmp_path / "b")
    for repo in (a, b):
        (repo / "a.py").write_text("x = 2\n")
    info_a, _ = env.git_info(a)
    info_b, _ = env.git_info(b)
    assert info_a["commit"] == info_b["commit"]
    assert info_a["diff_sha"] == info_b["diff_sha"]
    (b / "a.py").write_text("x = 3\n")
    info_c, _ = env.git_info(b)
    assert info_c["diff_sha"] != info_b["diff_sha"]


def test_beamtime_yaml_sets_the_root_and_logdir(tmp_path: Path, monkeypatch) -> None:
    """``beamtime.yaml`` above the working directory is the root; ``logdir`` is read."""
    (tmp_path / "beamtime.yaml").write_text("schema: 1\nlogdir: runs\n")
    (tmp_path / "src" / "deep").mkdir(parents=True)
    monkeypatch.chdir(tmp_path / "src" / "deep")
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    loc = locate("scaling/lr")
    assert loc.logdir == (tmp_path / "runs").resolve()
    assert loc.relative == "scaling/lr" and not loc.warnings


def test_git_root_and_default_logdir(tmp_path: Path, monkeypatch) -> None:
    """Without settings, the git root holds ``beamtime/``."""
    (tmp_path / ".git").mkdir()
    (tmp_path / "a").mkdir()
    monkeypatch.chdir(tmp_path / "a")
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    assert locate().logdir == (tmp_path / "beamtime").resolve()


def test_env_logdir_wins(tmp_path: Path, monkeypatch) -> None:
    """``BEAMTIME_LOGDIR`` overrides the root's log dir."""
    monkeypatch.setenv("BEAMTIME_LOGDIR", str(tmp_path / "scratch"))
    assert locate("x").folder == (tmp_path / "scratch" / "x").resolve()


def test_absolute_dir(tmp_path: Path, monkeypatch) -> None:
    """An absolute dir below a log dir keeps that log dir; elsewhere it is the log dir."""
    (tmp_path / "beamtime.yaml").write_text("schema: 1\n")
    monkeypatch.setenv("BEAMTIME_LOGDIR", str(tmp_path / "ignored"))
    loc = locate(tmp_path / "beamtime" / "sweep")
    assert loc.logdir == logdir_of(tmp_path) and loc.relative == "sweep"
    other = tmp_path / "elsewhere"
    assert locate(other).logdir == other.resolve()


def test_cwd_fallback_warns(tmp_path: Path, monkeypatch) -> None:
    """Without settings or git, the working directory is the root, with a warning."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    monkeypatch.setattr("beamtime.sdk.paths.find_up", lambda start, name: None)
    assert locate().warnings


@pytest.mark.parametrize("bad", ["../x", "a/notes", "_trash", "a/20261024-101532-k3m9xq2a"])
def test_bad_folders(bad: str) -> None:
    """Folders may not escape the log dir or use reserved names or run ids."""
    with pytest.raises(ValueError):
        check_folder(bad)


def test_find_run(golden: Path) -> None:
    """Runs are found by id anywhere below the log dir."""
    assert find_run(golden, "20261024-111500-r3s4m5d6").name == "20261024-111500-r3s4m5d6"
    assert find_run(golden, "20261024-111500-zzzzzzzz") is None


def test_rank_rule() -> None:
    """A process is rank 0 iff every rank variable is 0 or unset."""
    assert env.rank({}) == 0
    assert env.rank({"RANK": "0", "LOCAL_RANK": "0"}) == 0
    assert env.rank({"RANK": "3"}) == 3
    assert env.rank({"SLURM_PROCID": "2"}) == 2
    assert env.rank({"LOCAL_RANK": "1", "NODE_RANK": "1", "LOCAL_WORLD_SIZE": "4"}) == 5
    assert env.rank({"LOCAL_RANK": "0", "NODE_RANK": "2"}) == 2000


def test_scheduler_and_job_key() -> None:
    """SLURM array jobs map to common fields and an array job key."""
    e = {
        "SLURM_JOB_ID": "8812345",
        "SLURM_ARRAY_JOB_ID": "8812300",
        "SLURM_ARRAY_TASK_ID": "45",
        "SLURM_JOB_PARTITION": "gpu",
    }
    assert env.scheduler(e) == {
        "kind": "slurm",
        "job_id": "8812345",
        "array_job_id": "8812300",
        "array_task_id": "45",
        "partition": "gpu",
    }
    assert env.job_key(e) == "slurm:8812300:45"
    assert env.job_key({"TORCHELASTIC_RUN_ID": "abc"}) == "torchrun:abc"
    assert env.scheduler({}) is None and env.job_key({}) is None
    assert env.scheduler({"PBS_JOBID": "1.pbs"})["kind"] == "pbs"


def test_packages_and_host() -> None:
    """Installed packages are listed without a subprocess; the host is described."""
    assert "pyyaml==" in env.packages().lower()
    assert set(env.host_info()) == {"hostname", "user", "os", "python"}


def test_config_conversion() -> None:
    """Dicts, dataclasses, Namespaces and objects with model_dump become plain dicts."""

    @dataclasses.dataclass
    class Cfg:
        lr: float = 3e-4
        path: Path = Path("/data")

    class Model:
        def model_dump(self) -> dict:
            return {"width": 64}

    # paths keep the platform's own form: \\data on Windows.
    assert to_config(Cfg()) == {"lr": 3e-4, "path": str(Path("/data"))}
    assert to_config(argparse.Namespace(a=1)) == {"a": 1}
    assert to_config(Model()) == {"width": 64}
    assert to_config(None) == {}
    with pytest.raises(ValueError):
        to_config(42)
    with pytest.raises(ValueError, match="reserved"):
        to_config({"schema": 2})


def test_proposal_argument(tmp_path: Path, monkeypatch) -> None:
    """Proposals come from a statement, a dict, a YAML file or BEAMTIME_PROPOSAL."""
    monkeypatch.delenv("BEAMTIME_PROPOSAL", raising=False)
    assert to_proposal("Warmup helps.") == {"statement": "Warmup helps."}
    assert to_proposal({"statement": "x", "confidence": 0.5})["confidence"] == 0.5
    f = tmp_path / "p.yaml"
    f.write_text("statement: from file\n")
    assert to_proposal(str(f)) == {"statement": "from file"}
    assert to_proposal(None) == {"statement": None}
    monkeypatch.setenv("BEAMTIME_PROPOSAL", str(f))
    assert to_proposal(None) == {"statement": "from file"}


def test_scalars() -> None:
    """Numbers and 0-d objects with ``item`` are scalars; other values are not."""

    class ZeroD:
        ndim = 0

        def item(self) -> float:
            return 1.5

    assert scalar(2) == 2 and scalar(True) is True and scalar(ZeroD()) == 1.5
    assert scalar("x") is None and scalar([1.0]) is None
