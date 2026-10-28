import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from beamtime.format.authored import read_markdown_doc
from beamtime.ops import call
from beamtime.ops.context import Context

TRAIN = """
import math, random, sys
import beamtime

lr, seed = float(sys.argv[1]), int(sys.argv[2])
rng = random.Random(seed)
with beamtime.init(dir="toy/sweep", config={"lr": lr, "seed": seed}) as run:
    for step in range(30):
        run.log({"acc": 1 - 0.9 * math.exp(-lr * step) + rng.gauss(0, 0.005)}, step=step)
"""

PROPOSAL = {
    "statement": "A learning rate of 0.5 reaches 0.95 accuracy and beats 0.05.",
    "confidence": 0.8,
    "plan": {"grid": {"config.lr": [0.05, 0.5], "config.seed": [0, 1, 2]}},
    "predictions": [
        {
            "name": "reaches",
            "where": {"config.lr": 0.5},
            "reduce": {"metric": "acc", "stat": "last"},
            "seeds": "config.seed",
            "op": ">",
            "value": 0.95,
        },
        {
            "name": "fast-beats-slow",
            "reduce": {"metric": "acc", "stat": "mean", "steps": [10, 29]},
            "test": "compare",
            "a": {"config.lr": 0.5},
            "b": {"config.lr": 0.05},
            "pair_by": ["config.seed"],
            "op": ">",
            "margin": 0.1,
        },
    ],
}


def train(project: Path, lr: float, seed: int) -> None:
    """Run the toy training script with the SDK, as a user would.

    :param project: The project root.
    :param lr: The learning rate.
    :param seed: The seed."""
    script = project / "train.py"
    script.write_text(textwrap.dedent(TRAIN))
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BEAMTIME_", "SLURM_"))}
    done = subprocess.run(
        [sys.executable, str(script), str(lr), str(seed)],
        cwd=project,
        env=env,
        capture_output=True,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr.decode()


def test_proposal_sweep_check_verdict_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A proposal written before a sweep is checked as the sweep runs; then a verdict and
    a memory update close the loop."""
    project = tmp_path / "proj"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    monkeypatch.chdir(project)
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    (project / "beamtime").mkdir()
    ctx = Context.make(caller="mcp")

    saved = call("proposal set", {"group": "toy/sweep", "proposal": PROPOSAL, "author": "m"}, ctx)
    version = saved["version"]
    assert call("groups", {"from": "toy"}, ctx)["rows"][-1][2] == "proposed"

    for seed in range(3):
        train(project, 0.5, seed)
    early = call("check", {"group": "toy/sweep"}, ctx)
    assert early["provisional"] and early["progress"]["text"] == "3 of 6 grid points"
    assert [p["result"] for p in early["predictions"]] == ["pass", "pending"]
    assert call("groups", {"from": "toy"}, ctx)["rows"][-1][2] == "running"

    for seed in range(3):
        train(project, 0.05, seed)
    final = call("check", {"group": "toy/sweep"}, ctx)
    assert final["result"] == "pass" and not final["provisional"]
    assert final["predictions"][1]["n"] == {"pairs": 3}
    assert call("groups", {"from": "toy"}, ctx)["rows"][-1][2:4] == ["evaluable", "pass"]

    verdict = call(
        "note add",
        {
            "group": "toy/sweep",
            "type": "verdict",
            "description": "lr 0.5 reaches 0.95 and beats 0.05 in every seed.",
            "proposal": version,
            "verdict": {"reaches": "confirmed", "fast-beats-slow": "confirmed"},
            "overall": "confirmed",
            "evidence": ["toy/sweep#reaches"],
            "body": "Both hold; see [[toy/sweep#fast-beats-slow]].",
            "author": "m",
        },
        ctx,
    )
    doc = read_markdown_doc(ctx.logdir / verdict["path"], kind="note")
    assert doc.meta["check"]["reaches"]["result"] == "pass"
    assert call("groups", {"from": "toy"}, ctx)["rows"][-1][2] == "concluded"

    assert call("memory show", {"group": "toy/sweep"}, ctx)["meta"]["hints"]
    call(
        "memory update",
        {"group": "toy", "body": f"## Current understanding\n- lr 0.5 is best [[{doc.id}]]\n"},
        ctx,
    )
    chain = call("memory show", {"group": "toy/sweep"}, ctx)["chain"]
    assert chain[-1]["group"] == "toy" and chain[-1]["notes_since"] == 0

    run = next((ctx.logdir / "toy" / "sweep").glob("2*"))
    card = call("card", {"run": run.name}, ctx)
    assert card["proposals"] == [
        {
            "group": "toy/sweep",
            "version": version,
            "statement": PROPOSAL["statement"],
            "current": True,
            "check": "pass",
            "provisional": False,
            "verdict": "confirmed",
        }
    ]


def test_own_proposal_of_a_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A run's own proposal is evaluable once the run has finished."""
    project = tmp_path / "proj"
    project.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    monkeypatch.chdir(project)
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    script = project / "single.py"
    script.write_text(
        "import beamtime\n"
        "with beamtime.init(dir='single', proposal='Loss falls.') as run:\n"
        "    run.log({'loss': 1.0}, step=0)\n"
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith(("BEAMTIME_", "SLURM_"))}
    subprocess.run([sys.executable, str(script)], cwd=project, env=env, check=True, timeout=60)
    ctx = Context.make()
    rows = call("runs", {"select": ["proposal.status", "proposal.progress"]}, ctx)["rows"]
    assert [r[1:] for r in rows] == [["evaluable", 1.0]]
    card = call("card", {"run": rows[0][0]}, ctx)
    assert card["proposals"][0]["group"] == "." and card["proposals"][0]["check"] is None
