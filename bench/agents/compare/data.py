"""The benchmark's log dirs: synthetic runs without the research record and the planted answers."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

from beamtime.format.io import write_replaced
from beamtime.format.tree import is_run, iter_runs
from beamtime.synth.generate import Manifest, generate

RECORD = ("proposal", "notes", "memory")


def make_logdir(dest: Path, *, seed: int, now: datetime) -> Manifest:
    """Generate a scale ``s`` log dir at ``dest/beamtime`` and strip everything that states answers.

    :param dest: The folder that will hold ``beamtime/``.
    :param seed: The data seed.
    :param now: The time heartbeats are judged against; equal inputs give equal metrics.
    :return: The manifest; its roles stay in memory for grading, never written into ``dest``."""
    manifest = generate(dest / "beamtime", seed=seed, scale="s", now=now)
    strip_record(dest / "beamtime")
    return manifest


def strip_record(logdir: Path) -> None:
    """Delete the synth manifest and the research record, and clear every run's proposals.

    :param logdir: The log dir."""
    (logdir / "_synth.json").unlink(missing_ok=True)
    remove_record(logdir)
    for run in iter_runs(logdir):
        card = run / "_run.json"
        stat = card.stat()
        data = json.loads(card.read_text())
        data["proposals"] = {}
        data["proposal_hashes"] = {}
        write_replaced(card, data)
        # the heartbeat is the file's mtime; the rewrite must not make a lost run look alive.
        os.utime(card, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def remove_record(folder: Path) -> None:
    """Delete the ``proposal``, ``notes`` and ``memory`` folders below a folder, outside of runs.

    :param folder: A log dir or a group."""
    for child in sorted(folder.iterdir()):
        if not child.is_dir() or is_run(child):
            continue
        if child.name in RECORD:
            shutil.rmtree(child)
        else:
            remove_record(child)
