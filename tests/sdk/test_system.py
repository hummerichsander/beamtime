import json
import sys
from pathlib import Path

import pytest

FAKE_SMI = """#!/bin/sh
case "$1" in
  *name*) echo "Fake GPU, 81920, 550.54" ;;
  *) echo "37, 8192, 81920" ;;
esac
"""

TRAIN = """
import time
import beamtime
from beamtime.sdk import run as sdk_run
sdk_run.FLUSH_EVERY_S, sdk_run.SYSTEM_EVERY_S = 0.05, 0.1
{before}
run = beamtime.init(dir="sys", system_metrics={on})
for step in range(4):
    run.log({{"loss": 1.0 / (step + 1)}})
    time.sleep(0.4)
run.finish()
"""


def rows(logdir: Path) -> tuple[dict, list[dict]]:
    """Read the one run's ``_run.json`` and metric rows.

    :param logdir: The log dir.
    :return: The run info and the rows."""
    run_dir = next((logdir / "sys").iterdir())
    info = json.loads((run_dir / "_run.json").read_text())
    lines = (run_dir / "_metrics.jsonl").read_text().splitlines()
    return info, [json.loads(line) for line in lines]


def fake_gpu(tmp_path: Path) -> dict[str, str]:
    """Put a fake ``nvidia-smi`` first on PATH.

    :param tmp_path: Pytest's temporary directory.
    :return: The environment for the script."""
    import os

    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "nvidia-smi").write_text(FAKE_SMI)
    (bin_dir / "nvidia-smi").chmod(0o755)
    return {"PATH": f"{bin_dir}:{os.environ['PATH']}"}


# the fake nvidia-smi is a shell script, which Windows doesn't run.
FAKE_GPU = pytest.mark.skipif(sys.platform == "win32", reason="the fake nvidia-smi is a shell script")


@FAKE_GPU
def test_hardware_and_system_metrics(script, logdir: Path, tmp_path: Path) -> None:
    """The hardware is recorded at start; sys/* rows sit at logged steps, one per step."""
    done = script(TRAIN.format(before="", on=True), env=fake_gpu(tmp_path))
    assert done.returncode == 0, done.stderr
    info, metrics = rows(logdir)
    assert info["host"]["gpus"] == [{"name": "Fake GPU", "memory_gb": 80.0, "driver": "550.54"}]
    assert info["host"]["cores"] >= 1
    system = [r for r in metrics if "sys/gpu0/util" in r]
    assert system and all(r["sys/gpu0/util"] == 37.0 and r["sys/gpu0/memory"] == 10.0 for r in system)
    assert all("_t" not in r for r in system)
    steps = [r["_step"] for r in metrics]
    assert steps == sorted(steps)
    assert len({r["_step"] for r in system}) == len(system)


@FAKE_GPU
def test_system_metrics_can_be_turned_off(script, logdir: Path, tmp_path: Path) -> None:
    """system_metrics=False writes no sys/* rows; the hardware is still recorded."""
    done = script(TRAIN.format(before="", on=False), env=fake_gpu(tmp_path))
    assert done.returncode == 0, done.stderr
    info, metrics = rows(logdir)
    assert "gpus" in info["host"]
    assert not any(k.startswith("sys/") for r in metrics for k in r)


def test_a_failing_sampler_turns_itself_off(script, logdir: Path) -> None:
    """A sampler that raises warns once and stops; training goes on."""
    broken = (
        "from beamtime.sdk import system\n"
        "system.Sampler.sample = lambda self: 1 / 0\n"
    )
    done = script(TRAIN.format(before=broken, on=True))
    assert done.returncode == 0, done.stderr
    assert done.stderr.count(b"system metrics failed") == 1
    _, metrics = rows(logdir)
    assert [r["_step"] for r in metrics if "loss" in r] == [0, 1, 2, 3]
