import argparse
import dataclasses
from pathlib import Path

import pytest

from beamtime.sdk import env
from beamtime.sdk.paths import check_folder, find_run, locate, logdir_of
from beamtime.sdk.run import scalar, to_config, to_proposal


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

    assert to_config(Cfg()) == {"lr": 3e-4, "path": "/data"}
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
