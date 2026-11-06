import json
import os
import sys
from pathlib import Path

import pytest

from beamtime.format.authored import file_hash, newest, read_yaml_doc
from beamtime.format.io import read_json
from beamtime.format.run import (
    read_artifacts,
    read_card,
    read_config,
    read_data,
    read_effective_metrics,
    read_events,
    read_metrics,
    read_output,
    read_preview,
    read_run_info,
)
from beamtime.format.tree import iter_runs
from beamtime.synth.summary import card_and_preview
from tests.sdk.conftest import Script, only_run

POSIX = pytest.mark.skipif(sys.platform == "win32", reason="POSIX only")


def test_full_run(script: Script, logdir: Path, tmp_path: Path) -> None:
    """A run records metrics, data, config, events, artifacts, proposals and output."""
    group = logdir / "scaling" / "proposal"
    group.mkdir(parents=True)
    (group / "20261020-140000-q7w3.yaml").write_text("schema: 1\nstatement: g\n")
    (tmp_path / "small.ckpt").write_bytes(b"ckpt")
    proc = script(
        """
        import math, os, subprocess, sys
        import beamtime
        run = beamtime.init(dir="scaling/lr", name="n1", tags=["t"],
                            config={"lr": 3e-4, "model": {"w": 64}},
                            proposal="Warmup helps.")
        assert beamtime.current() is run
        assert os.environ["BEAMTIME_RUN_DIR"] == str(run.dir)
        print("hello stdout")
        print("hello stderr", file=sys.stderr)
        os.write(1, b"raw fd write\\n")
        subprocess.run([sys.executable, "-c", "print('from child')"])
        for s in range(100):
            run.log({"train/loss": 1 / (s + 1), "acc": s / 100}, step=s)
        run.log({"val/nan": math.nan}, step=99)
        run.log({"table": beamtime.Table({"a": [1, 2]}),
                 "img": beamtime.Image(os.path.abspath("small.ckpt"))}, step=99)
        run.card["test/acc"] = 0.9
        run.config.update({"n_params": 10})
        run.config.update(lr=1.0)
        run.event("lr decayed", factor=0.5)
        run.artifact("small.ckpt", kind="checkpoint")
        run.artifact("small.ckpt", copy=False)
        run.finish()
        run.finish()
        run.log({"after": 1})
        assert beamtime.current() is None and "BEAMTIME_RUN_DIR" not in os.environ
        """
    )
    assert proc.returncode == 0, proc.stderr.decode()
    out, err = proc.stdout.decode(), proc.stderr.decode()
    assert "hello stdout" in out and "raw fd write" in out and "from child" in out
    assert "hello stderr" in err and "config 'lr' is already" in err

    run = only_run(logdir)
    assert run.parent == logdir / "scaling" / "lr"
    info = read_run_info(run)
    assert (info.name, info.tags, info.status) == ("n1", ["t"], "finished")
    assert info.ended_at and info.exit is None and info.attempts[0].resume_step is None
    own = read_yaml_doc(newest(run / "proposal"), kind="proposal")
    assert own.meta["statement"] == "Warmup helps." and own.meta["author"]
    assert info.proposals == {".": own.id, "scaling": "20261020-140000-q7w3"}
    group = logdir / "scaling" / "proposal" / "20261020-140000-q7w3.yaml"
    assert info.proposal_hashes == {".": file_hash(own.path), "scaling": file_hash(group)}
    assert read_config(run) == {"lr": 3e-4, "model": {"w": 64}, "n_params": 10}

    rows = read_effective_metrics(run)
    assert [r["_step"] for r in rows] == list(range(100)) + [99]
    expected, preview = card_and_preview(rows, status="finished", duration_s=1.0)
    card = read_card(run)
    assert card.status == "finished" and card.values == {"test/acc": 0.9}
    assert card.warnings == 1 and card.steps == 99
    for key, m in card.metrics.items():
        exact = expected["metrics"][key]
        assert m.count == exact["count"] and m.nonfinite == exact["nonfinite"]
        assert m.max == exact.get("max")
        assert m.mean == pytest.approx(exact.get("mean"))
    assert read_preview(run).metrics.keys() == preview["metrics"].keys()

    data = {d.key: d for d in read_data(run)}
    assert data["table"].columns == {"a": [1, 2]}
    assert (run / data["img"].path).read_bytes() == b"ckpt"
    kinds = [e.kind for e in read_events(run)]
    assert kinds[:2] == ["created", "attempt_started"] and kinds[-1] == "finished"
    assert "warning" in kinds
    user = next(e for e in read_events(run) if e.kind == "user")
    assert user.message == "lr decayed" and user.data == {"factor": 0.5}
    copied, referenced = read_artifacts(run)
    assert copied.path == "artifacts/small.ckpt" and (run / copied.path).exists()
    assert referenced.uri == str((tmp_path / "small.ckpt").resolve())
    assert (run / "_env" / "packages.txt").read_text()

    log = read_output(run)
    for text in ("hello stdout", "hello stderr", "raw fd write", "from child"):
        assert text in log


def test_exit_without_finish(script: Script, logdir: Path) -> None:
    """A script that ends without finish is finished at exit."""
    proc = script("import beamtime\nbeamtime.init().log({'x': 1})\n")
    assert proc.returncode == 0
    assert read_run_info(only_run(logdir)).status == "finished"


def test_exception_fails_the_run(script: Script, logdir: Path) -> None:
    """An unhandled exception marks the run failed with its traceback."""
    proc = script(
        """
        import beamtime
        run = beamtime.init()
        run.log({"x": 1})
        raise FloatingPointError("loss is nan")
        """
    )
    assert proc.returncode == 1 and b"FloatingPointError" in proc.stderr
    run = only_run(logdir)
    info, card = read_run_info(run), read_card(run)
    assert info.status == "failed" and info.exit == {"code": 1}
    assert card.error == "FloatingPointError: loss is nan"
    assert "Traceback" in read_events(run)[-1].data["traceback"]
    assert "FloatingPointError: loss is nan" in read_output(run)


def test_context_manager(script: Script, logdir: Path) -> None:
    """A with block fails the run on an exception and kills it on Ctrl-C."""
    proc = script(
        """
        import beamtime
        try:
            with beamtime.init(dir="a") as run:
                raise ValueError("bad")
        except ValueError:
            pass
        try:
            with beamtime.init(dir="b") as run:
                raise KeyboardInterrupt
        except KeyboardInterrupt:
            pass
        """
    )
    assert proc.returncode == 0, proc.stderr.decode()
    assert read_run_info(only_run(logdir / "a")).status == "failed"
    killed = only_run(logdir / "b")
    assert read_run_info(killed).status == "killed"
    assert read_events(killed)[-1].data["reason"] == "interrupted"


def test_bad_input_warns_and_continues(script: Script, logdir: Path) -> None:
    """Decreasing steps, reserved keys and unknown types are dropped with one warning each."""
    proc = script(
        """
        import beamtime
        run = beamtime.init()
        run.log({"x": 1}, step=5)
        run.log({"x": 2}, step=3)
        run.log({"x": 2}, step=2)
        run.log({"_step": 1, "y": "text", "z": [1]}, step=6)
        run.log({"x": 3})
        run.finish()
        """
    )
    assert proc.returncode == 0
    run = only_run(logdir)
    assert [r["_step"] for r in read_metrics(run).rows] == [5, 7]
    assert read_card(run).warnings == 4
    assert proc.stderr.decode().count("beamtime: warning") == 4


@pytest.mark.skipif(
    sys.platform == "win32", reason="Windows doesn't delete files a process has open"
)
def test_io_errors_never_reach_the_script(script: Script, logdir: Path) -> None:
    """Deleting the run directory mid-run produces warnings, not exceptions."""
    proc = script(
        """
        import shutil, time
        import beamtime
        run = beamtime.init()
        shutil.rmtree(run.dir)
        for s in range(10):
            run.log({"x": s})
        run.event("still here")
        run.artifact("missing.file")
        run.finish()
        print("survived")
        """
    )
    assert proc.returncode == 0, proc.stderr.decode()
    assert b"survived" in proc.stdout and b"beamtime: warning" in proc.stderr


def test_resume_explicit_step(script: Script, logdir: Path) -> None:
    """A resumed run appends an attempt; the new attempt wins from its resume step."""
    first = script(
        """
        import beamtime
        run = beamtime.init(config={"lr": 1})
        for s in range(10):
            run.log({"x": float(s)}, step=s)
        run.card["v"] = 1
        print(run.id)
        """
    )
    run_id = first.stdout.decode().strip()
    run = only_run(logdir)
    with (run / "_metrics.jsonl").open("ab") as f:
        f.write(b'{"_step":10,"_t":17')
    second = script(
        f"""
        import beamtime
        run = beamtime.init(resume="{run_id}", config={{"lr": 2}})
        assert run.config["lr"] == 1
        for s in range(5, 13):
            run.log({{"x": 100.0 + s}}, step=s)
        run.finish()
        """
    )
    assert second.returncode == 0, second.stderr.decode()
    info = read_run_info(run)
    assert [a.resume_step for a in info.attempts] == [None, 5] and info.status == "finished"
    rows = read_effective_metrics(run)
    assert [r["_step"] for r in rows] == list(range(13))
    assert rows[4]["x"] == 4.0 and rows[5]["x"] == 105.0
    assert read_metrics(run).bad == 1
    card = read_card(run)
    assert card.metrics["x"].count == 13 and card.metrics["x"].first == 0.0
    assert card.values == {"v": 1}
    conflict = next(e for e in read_events(run) if e.kind == "config_conflict")
    assert conflict.data["diff"] == {"lr": [1, 2]}
    assert read_config(run) == {"lr": 1}


def test_resume_implicit_step_and_unknown_id(script: Script, logdir: Path) -> None:
    """Without explicit steps a resumed run continues at the last step plus one."""
    run_id = (
        script(
            "import beamtime\nr = beamtime.init()\nr.log({'x': 1})\nr.log({'x': 2})\nprint(r.id)\n"
        )
        .stdout.decode()
        .strip()
    )
    proc = script(
        f"""
        import beamtime
        try:
            beamtime.init(resume="20200101-000000-00000000")
        except LookupError as e:
            print("lookup", e)
        run = beamtime.init(resume="{run_id}")
        run.log({{"x": 3}})
        """
    )
    assert b"lookup" in proc.stdout, proc.stderr.decode()
    run = only_run(logdir)
    assert [r["_step"] for r in read_effective_metrics(run)] == [0, 1, 2]
    assert read_run_info(run).attempts[-1].resume_step == 2


def test_resume_by_key(script: Script, logdir: Path) -> None:
    """A killed run is continued by its key, with no id named, and finishing it ends that."""
    first = script(
        """
        import beamtime
        run = beamtime.init(key="demo")
        run.log({"x": 1}, step=0)
        run.end("killed", exit={"signal": "SIGTERM"})
        print(run.id)
        """
    )
    run_id = first.stdout.decode().strip()
    second = script(
        """
        import beamtime
        run = beamtime.init(key="demo")
        run.log({"x": 2}, step=1)
        run.finish()
        """
    )
    assert second.returncode == 0, second.stderr.decode()
    run = only_run(logdir)
    assert run.name == run_id
    info = read_run_info(run)
    assert info.status == "finished" and [a.resume_step for a in info.attempts] == [None, 1]


def test_resume_by_key_across_job_ids(script: Script, logdir: Path) -> None:
    """A key resumes a run regardless of a different job id the second time."""
    script(
        'import beamtime\nr = beamtime.init(key="k")\nr.log({"x": 1})\n'
        'r.end("killed", exit={"signal": "SIGTERM"})\n',
        env={"SLURM_JOB_ID": "1"},
    )
    proc = script(
        'import beamtime\nr = beamtime.init(key="k")\nr.log({"x": 2})\nr.finish()\n',
        env={"SLURM_JOB_ID": "2"},
    )
    assert proc.returncode == 0, proc.stderr.decode()
    run = only_run(logdir)
    assert [a.resume_step for a in read_run_info(run).attempts] == [None, 1]


def test_resume_by_key_after_it_finished(script: Script, logdir: Path) -> None:
    """A key whose run already ended starts a new run, with a warning."""
    first = script('import beamtime\nr = beamtime.init(key="done")\nr.finish()\nprint(r.id)\n')
    first_id = first.stdout.decode().strip()
    proc = script('import beamtime\nr = beamtime.init(key="done")\nr.finish()\nprint(r.id)\n')
    assert proc.returncode == 0, proc.stderr.decode()
    second_id = proc.stdout.decode().strip()
    assert second_id != first_id
    runs = {d.name: d for d in iter_runs(logdir)}
    assert runs.keys() == {first_id, second_id}
    warning = next(e for e in read_events(runs[second_id]) if e.kind == "warning")
    assert "already finished" in warning.message


def test_requeue_resumes_the_one_unfinished_run(script: Script, logdir: Path) -> None:
    """A SLURM requeue continues the one unfinished run of the same job, with no id or key."""
    env = {"SLURM_JOB_ID": "500"}
    first = script(
        'import beamtime\nr = beamtime.init()\nr.log({"x": 1})\n'
        'r.end("killed", exit={"signal": "SIGTERM"}, reason="time_limit")\nprint(r.id)\n',
        env=env,
    )
    run_id = first.stdout.decode().strip()
    proc = script(
        'import beamtime\nr = beamtime.init()\nr.log({"x": 2})\nr.finish()\n',
        env=env | {"SLURM_RESTART_COUNT": "1"},
    )
    assert proc.returncode == 0, proc.stderr.decode()
    run = only_run(logdir)
    assert run.name == run_id
    info = read_run_info(run)
    assert info.status == "finished" and [a.resume_step for a in info.attempts] == [None, 1]


def test_requeue_ambiguous_candidates_start_a_new_run(script: Script, logdir: Path) -> None:
    """Two unfinished runs of the same job can't be told apart without a key."""
    env = {"SLURM_JOB_ID": "501"}
    for _ in range(2):
        script(
            'import beamtime\nr = beamtime.init()\nr.log({"x": 1})\n'
            'r.end("killed", exit={"signal": "SIGTERM"})\n',
            env=env,
        )
    proc = script(
        'import beamtime\nr = beamtime.init()\nr.log({"x": 2})\nr.finish()\n',
        env=env | {"SLURM_RESTART_COUNT": "1"},
    )
    assert proc.returncode == 0, proc.stderr.decode()
    runs = list(iter_runs(logdir))
    assert len(runs) == 3
    new = max(runs, key=lambda d: d.name)
    warning = next(e for e in read_events(new) if e.kind == "warning")
    assert "unfinished runs match this job" in warning.message
    assert read_run_info(new).attempts[0].resume_step is None


def test_broken_run_json_does_not_stop_resolution(script: Script, logdir: Path) -> None:
    """A damaged ``_run.json`` next to the group doesn't keep a new run from starting."""
    garbage = logdir / "toy" / "garbage"
    garbage.mkdir(parents=True)
    (garbage / "_run.json").write_text("{not json")
    proc = script(
        'import beamtime\nr = beamtime.init(dir="toy", key="k")\nr.finish()\nprint(r.id)\n'
    )
    assert proc.returncode == 0, proc.stderr.decode()


@POSIX
def test_sigterm_near_time_limit_records_the_reason(script: Script, logdir: Path) -> None:
    """SIGTERM within 300 s of SLURM_JOB_END_TIME is recorded as reason time_limit."""
    proc = script(
        """
        import os, signal, time
        os.environ["SLURM_JOB_END_TIME"] = str(int(time.time()) + 100)
        import beamtime
        run = beamtime.init()
        run.log({"x": 1})
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(2)
        """
    )
    run = only_run(logdir)
    killed = next(e for e in read_events(run) if e.kind == "killed")
    assert killed.data.get("reason") == "time_limit"
    assert proc.returncode != 0


def test_null_run_on_other_ranks(script: Script, logdir: Path) -> None:
    """Other ranks get a NullRun and capture their output into rank 0's run."""
    proc = script(
        """
        import os, subprocess, sys
        import beamtime
        run = beamtime.init()
        child = '''
        import beamtime
        r = beamtime.init()
        assert type(r).__name__ == "NullRun" and r.dir is None
        r.log({"x": 1}); r.config.update({"a": 1}); r.card["v"] = 2
        print("rank one speaks")
        r.finish()
        '''
        env = dict(os.environ, RANK="1")
        subprocess.run([sys.executable, "-c", child.replace("\\n        ", "\\n")], env=env)
        run.log({"x": 1})
        """
    )
    assert proc.returncode == 0, proc.stderr.decode()
    run = only_run(logdir)
    assert "rank one speaks" in read_output(run, rank=1)
    assert [r["_step"] for r in read_metrics(run).rows] == [0]


def test_rank_finds_run_by_job_key(script: Script, logdir: Path, tmp_path: Path) -> None:
    """A rank started independently finds rank 0's run through the job key."""
    import subprocess

    env = {"SLURM_JOB_ID": "77", "BEAMTIME_LOGDIR": str(logdir), "PYTHONUNBUFFERED": "1"}
    worker = tmp_path / "worker.py"
    worker.write_text(
        "import time, beamtime\nr = beamtime.init(dir='job')\n"
        "time.sleep(2.5)\nprint('worker output')\nr.finish()\n"
    )
    environ = {k: v for k, v in os.environ.items() if not k.startswith("BEAMTIME_")}
    rank1 = subprocess.Popen(
        [sys.executable, str(worker)], env=environ | env | {"SLURM_PROCID": "1"}
    )
    proc = script("import time, beamtime\nr = beamtime.init(dir='job')\ntime.sleep(4)\n", env=env)
    rank1.wait(30)
    assert proc.returncode == 0
    run = only_run(logdir)
    assert read_run_info(run).job_key == "slurm:77"
    assert "worker output" in read_output(run, rank=1)


@POSIX
def test_forked_workers_stay_inert(script: Script, logdir: Path) -> None:
    """Forked workers write output into the parent's log but no run files."""
    proc = script(
        """
        import os
        import beamtime
        run = beamtime.init()
        run.log({"x": 1})
        pid = os.fork()
        if pid == 0:
            beamtime.current() is None or os._exit(3)
            run.log({"x": 99})
            run.finish()
            print("worker says hi", flush=True)
            os._exit(0)
        _, status = os.waitpid(pid, 0)
        assert os.waitstatus_to_exitcode(status) == 0
        run.log({"x": 2})
        """
    )
    assert proc.returncode == 0, proc.stderr.decode()
    run = only_run(logdir)
    assert [r["x"] for r in read_metrics(run).rows] == [1, 2]
    assert read_run_info(run).status == "finished"
    assert "worker says hi" in read_output(run)


def test_notebook_mode_captures_streams(script: Script, logdir: Path) -> None:
    """In a notebook kernel, sys.stdout is captured instead of file descriptors."""
    proc = script(
        """
        import sys, types
        sys.modules["ipykernel"] = types.ModuleType("ipykernel")
        import beamtime
        run = beamtime.init()
        print("cell output")
        run.finish()
        print("after finish")
        """
    )
    assert proc.returncode == 0, proc.stderr.decode()
    assert b"must" not in proc.stdout and b"run.finish()" in proc.stderr
    log = read_output(only_run(logdir))
    assert "cell output" in log and "after finish" not in log


def test_log_is_cheap(script: Script) -> None:
    """Logging three scalars costs microseconds, not milliseconds."""
    proc = script(
        """
        import time, beamtime
        run = beamtime.init()
        times = []
        for s in range(20000):
            t = time.perf_counter()
            run.log({"a": 1.0, "b": 2.0, "c": s})
            times.append(time.perf_counter() - t)
        times.sort()
        print(times[len(times) // 2])
        """
    )
    assert proc.returncode == 0, proc.stderr.decode()
    assert float(proc.stdout.decode().split()[-1]) < 50e-6


def test_run_json_heartbeat_file_is_valid_json(script: Script, logdir: Path) -> None:
    """``_run.json`` stays valid JSON with the documented fields."""
    script("import beamtime\nbeamtime.init().finish()\n")
    info = read_json(only_run(logdir) / "_run.json")
    for key in ("schema", "id", "name", "status", "created_at", "attempts", "proposals"):
        assert key in info
    assert json.dumps(info)
