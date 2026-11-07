import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import pytest

from beamtime.index.index import Index
from beamtime.query import QueryError, run
from beamtime.synth import generate
from beamtime.synth.generate import SCALES, Generator


@pytest.fixture(scope="module")
def logdir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A synthetic log dir whose heartbeats are judged against the real clock.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: The log dir."""
    out = tmp_path_factory.mktemp("q") / "beamtime"
    generate(out, seed=0, now=datetime.now(timezone.utc))
    view = out / "scaling" / "view" / "data"
    view.mkdir(parents=True)
    (view / "3f9a21c0-fit.csv").write_text("lr,acc\n0.001,0.9\n0.003,0.85\n")
    (view / "aa11bb22-fit.json").write_text(json.dumps({"columns": {"a": [1, 2]}}))
    return out


@pytest.fixture(scope="module")
def roles(logdir: Path) -> dict[str, str]:
    """The generator's runs by role.

    :param logdir: The log dir.
    :return: Role to run id."""
    return json.loads((logdir / "_synth.json").read_text())["roles"]


@pytest.fixture(scope="module")
def ask(logdir: Path, tmp_path_factory: pytest.TempPathFactory):
    """Answer queries against the log dir with a shared index.

    :param logdir: The log dir.
    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: A function from query to answer."""
    index = Index(logdir=logdir, cache=tmp_path_factory.mktemp("cache"))
    index.catch_up(".", budget_s=float("inf"))

    def answer(query: dict, **kwargs) -> dict:
        return run(query, logdir=logdir, index=index, **kwargs)

    yield answer
    index.close()


def table(answer: dict) -> list[dict]:
    """Turn a columnar answer into row dicts.

    :param answer: A ``runs`` or ``groups`` answer.
    :return: One dict per row."""
    return [dict(zip(answer["columns"], row, strict=True)) for row in answer["rows"]]


def test_runs_finds_the_planted_best_lr(ask) -> None:
    """Sorting by final accuracy puts lr 3e-4 runs first; the answer is JSON-ready."""
    a = ask(
        {
            "runs": {
                "from": "scaling/lr-sweep",
                "where": {"run.status": "finished"},
                "select": ["config.lr", "metric.val/acc.last"],
                "sort": ["-metric.val/acc.last"],
                "limit": 3,
            }
        }
    )
    rows = table(a)
    assert [r["config.lr"] for r in rows] == [3e-4] * 3
    assert a["meta"]["matched"] == 15 and a["meta"]["cut"]
    assert json.loads(json.dumps(a)) == a


def test_seeds_group_runs(ask) -> None:
    """seeds merges runs that differ only in the seed: five lrs of three seeds."""
    a = ask(
        {
            "runs": {
                "from": "scaling/lr-sweep",
                "where": {"run.status": "finished"},
                "seeds": "config.seed",
                "select": ["config.lr", "metric.val/acc.last"],
                "sort": ["-metric.val/acc.last"],
            }
        }
    )
    rows = table(a)
    assert len(rows) == 5 and all(len(r["runs"]) == 3 for r in rows)
    assert rows[0]["config.lr"] == 3e-4
    assert rows[0]["metric.val/acc.last"]["n"] == 3


def test_where_operators_and_numeric_strings(ask) -> None:
    """Conditions combine; YAML-style numeric strings compare as numbers."""
    a = ask(
        {
            "runs": {
                "from": ".",
                "where": {
                    "config.lr": {"lt": "1e-3", "ge": "1e-4"},
                    "run.tags": {"has": "resnet18"},
                    "not": {"config.seed": 0},
                    "any": [{"run.status": "finished"}, {"run.status": "killed"}],
                },
                "select": ["config.lr", "config.seed", "run.status"],
                "limit": 100,
            }
        }
    )
    rows = table(a)
    assert rows and all(1e-4 <= r["config.lr"] < 1e-3 and r["config.seed"] != 0 for r in rows)
    assert {r["run.status"] for r in rows} <= {"finished", "killed"}
    # the killed run (seed 3) has no tags, so the has condition drops it.
    assert {r["config.seed"] for r in rows} == {1, 2}


def test_code_identity_fields(ask) -> None:
    """``run.code`` is the short commit, plus the diff's hash when the checkout was dirty."""
    clean = table(
        ask(
            {
                "runs": {
                    "from": "scaling/lr-sweep",
                    "where": {"run.dirty": False},
                    "select": ["run.branch", "run.dirty", "run.commit", "run.code"],
                    "limit": 1,
                }
            }
        )
    )
    (row,) = clean
    assert row["run.branch"] == "main" and row["run.dirty"] is False
    assert row["run.code"] == row["run.commit"][:7]
    dirty = ask(
        {
            "runs": {
                "from": "realistic/egnn-bench",
                "where": {"run.dirty": True},
                "select": ["run.branch", "run.code"],
                "limit": 10,
            }
        }
    )
    rows = table(dirty)
    assert rows and all(r["run.branch"] == "feature/egnn" for r in rows)
    # the generator's synth runs predate diff_sha, so an old dirty run's code is unknown.
    assert all(r["run.code"] is None for r in rows)


def test_code_fields_read_a_real_run_without_them(golden: Path) -> None:
    """A real-format ``_run.json`` written before ``diff_sha`` and ``untracked`` still reads."""
    a = run(
        {
            "runs": {
                "from": "scaling/lr-sweep/20261024-101532-k3m9xq2a",
                "select": ["run.branch", "run.dirty", "run.code"],
            }
        },
        logdir=golden,
    )
    (row,) = table(a)
    assert row["run.branch"] == "master" and row["run.dirty"] is True and row["run.code"] is None


def test_derived_lost_status_and_globs(ask, roles) -> None:
    """A running run with a stale heartbeat is lost; glob matches names."""
    lost = ask({"runs": {"from": ".", "where": {"run.status": "lost"}, "select": ["run.id"]}})
    assert [r["run.id"] for r in table(lost)] == [roles["lost"]]
    some = ask({"runs": {"from": ".", "where": {"run.path": {"glob": "tokenizer/*"}}}})
    assert some["meta"]["matched"] == 6


def test_windowed_statistics(ask, roles) -> None:
    """Windowed fields come from the columns and match a brute-force mean."""
    a = ask(
        {
            "runs": {
                "from": roles["resumed"],
                "select": ["metric.train/loss.mean[0:999]", "metric.train/loss.count[1000:]"],
            }
        }
    )
    ((_, m, n),) = a["rows"]
    assert n == 1000 and 0 < m < 3


def test_keys(ask) -> None:
    """keys lists metrics, config keys, data keys, tags and statuses."""
    a = ask({"keys": {"from": "."}})
    metrics = {r[0]: r for r in a["metrics"]["rows"]}
    assert metrics["train/loss"][1] == 26 and metrics["val/ppl"][1] == 6
    config = {r[0]: r for r in a["config"]["rows"]}
    assert config["config.tokenizer"][2] == ["bpe", "unigram"]
    assert {r[0] for r in a["data"]["rows"]} == {
        "val/per_class",
        "grads/layer3",
        "samples",
        "samples/text",
    }
    assert a["tags"]["resnet18"] == 15 and a["status"]["lost"] == 1


def test_series_raw_downsampled_and_from_preview(ask, roles) -> None:
    """Finished runs answer overview curves from previews; zooms use the columns."""
    overview = ask({"series": {"from": "scaling/lr-sweep", "y": ["train/loss"], "points": 50}})
    assert overview["meta"]["downsampled"]
    assert overview["meta"]["from_preview"] == overview["meta"]["curves"]
    zoom = ask({"series": {"from": roles["killed"], "y": ["train/loss"], "steps": [100, 119]}})
    (curve,) = zoom["curves"]
    assert curve["raw"] and curve["x"] == list(range(100, 120)) and curve["source"] == "columns"


def test_series_x_axes_and_smoothing(ask, roles) -> None:
    """x by wall time, elapsed time or another metric; EMA smoothing narrows the band."""
    base = {"from": roles["resumed"], "y": ["train/loss"], "points": 10}
    elapsed = ask({"series": base | {"x": "_elapsed"}})["curves"][0]
    assert elapsed["x"][0] == 0.0 and elapsed["x"] == sorted(elapsed["x"])
    # active time: the queue wait between the two attempts must not show as a jump.
    diffs = [b - a for a, b in zip(elapsed["x"][:-1], elapsed["x"][1:], strict=True)]
    assert max(diffs) < 2 * min(diffs)
    raw = ask({"series": base})["curves"][0]
    smooth = ask({"series": base | {"smooth": {"ema": 0.99}}})["curves"][0]
    spread = lambda c: mean(b - a for a, b in zip(c["min"], c["max"]))  # noqa: E731
    assert spread(smooth) < spread(raw)
    by_lr = ask({"series": {"from": "scaling/lr-sweep", "y": ["val/acc"], "x": "lr", "points": 5}})
    assert all(x is None or x <= 0.01 for c in by_lr["curves"] for x in c["x"])


def test_grouped_series_show_the_tokenizer_gap(ask) -> None:
    """Grouped curves average seeds per bucket; unigram ends lower than BPE."""
    a = ask(
        {
            "series": {
                "from": "tokenizer",
                "y": ["val/ppl"],
                "by": ["config.tokenizer"],
                "band": "stderr",
                "points": 8,
            }
        }
    )
    final = {c["by"]["config.tokenizer"]: c["mean"][-1] for c in a["curves"]}
    assert 0.2 < final["bpe"] - final["unigram"] < 0.6
    assert all(n == 3 for c in a["curves"] for n in c["n"])
    seeded = ask({"series": {"from": "tokenizer", "y": ["val/ppl"], "seeds": "config.seed"}})
    assert len(seeded["curves"]) == 2


def test_point_budget_shrinks_points_per_curve(ask) -> None:
    """Many curves share a chart budget of about 30k points."""
    a = ask({"series": {"from": ".", "y": ["train/loss"], "points": 5000}}, caller="view")
    assert a["meta"]["points"] * a["meta"]["curves"] <= 30_000 + a["meta"]["curves"]


def test_data_kinds(ask) -> None:
    """Tables come as columns, images and text as references and inline text."""
    a = ask({"data": {"from": "scaling/lr-sweep", "key": "val/per_class", "limit": 100}})
    assert len(a["entries"]) == 15 and len(a["entries"][0]["columns"]["acc"]) == 10
    images = ask({"data": {"from": "scaling/lr-sweep", "key": "samples", "step": "all"}})
    assert all(Path(e["file"]).is_file() for e in images["entries"])
    text = ask({"data": {"from": "tokenizer", "key": "samples/text"}})
    assert all(e["text"] for e in text["entries"])
    window = ask({"data": {"from": "scaling", "key": "grads/layer3", "step": [0, 0], "limit": 100}})
    assert {e["step"] for e in window["entries"]} == {0}


def test_timeline(ask, roles) -> None:
    """Notes and events in time order, filtered by type; bodies on request."""
    a = ask(
        {"timeline": {"from": "scaling/lr-sweep", "types": ["failed", "observation"], "full": True}}
    )
    kinds = [(e["kind"], e["type"]) for e in a["entries"]]
    assert ("event", "failed") in kinds and ("note", "observation") in kinds
    note = next(e for e in a["entries"] if e["kind"] == "note")
    assert roles["diverging"] in note["body"]
    failed = next(e for e in a["entries"] if e["type"] == "failed")
    assert failed["description"].startswith("failed: FloatingPointError")
    times = [e["t"] for e in a["entries"]]
    assert times == sorted(times)
    later = ask({"timeline": {"from": ".", "since": "2030-01-01"}})
    assert later["entries"] == []


def test_groups(ask) -> None:
    """Groups carry proposal statements and run counts by status."""
    rows = {r["path"]: r for r in table(ask({"groups": {"from": "."}}))}
    sweep = rows["scaling/lr-sweep"]
    assert sweep["proposal"].startswith("lr 0.0003") and sweep["runs"] == 17
    assert sweep["failed"] == 1 and sweep["killed"] == 1
    assert rows["."]["runs"] == 47 and rows["scaling"]["direct"] == 0
    shallow = ask({"groups": {"from": ".", "depth": 1}})
    assert {r[0] for r in shallow["rows"]} == {".", "realistic", "scaling", "tokenizer"}


def test_research_fields(ask) -> None:
    """Groups carry their research status; proposal.* fields filter groups and runs."""
    rows = {r["path"]: r for r in table(ask({"groups": {"from": "."}}))}
    assert rows["tokenizer/bpe-vs-unigram"]["status"] == "evaluable"
    assert rows["tokenizer/bpe-vs-unigram"]["check"] == "pass"
    assert rows["tokenizer/bpe-vs-unigram"]["progress"] == "6 of 6 grid points"
    assert rows["scaling"]["status"] == "open" and rows["scaling"]["check"] is None
    done = ask({"groups": {"where": {"proposal.status": {"in": ["evaluable", "concluded"]}}}})
    assert {r[0] for r in done["rows"]} == {
        "scaling/lr-sweep",
        "scaling/long-context",
        "tokenizer/bpe-vs-unigram",
    }
    assert rows["scaling/lr-sweep"]["status"] == "concluded"
    assert rows["scaling/lr-sweep"]["verdict"] == "confirmed"
    # no plan: complete once a decision note says so; nothing to check.
    assert rows["scaling/long-context"]["status"] == "evaluable"
    runs = ask({"runs": {"from": "tokenizer", "select": ["proposal.status", "proposal.check"]}})
    # runs started without a proposal of their own have a blank one.
    assert {tuple(r[1:]) for r in runs["rows"]} == {("open", None)}


def test_file(ask) -> None:
    """View data files come back as tables."""
    a = ask({"file": {"path": "data/3f9a21c0-fit.csv", "view": "scaling"}})
    assert a["columns"] == ["lr", "acc"] and a["rows"][1] == [0.003, 0.85]
    b = ask({"file": {"path": "data/aa11bb22-fit.json", "view": "scaling"}})
    assert b["rows"] == [[1], [2]]
    with pytest.raises(QueryError):
        ask({"file": {"path": "../../_synth.json", "view": "scaling"}})


@pytest.mark.parametrize(
    "query, code, text",
    [
        ({"runs": {"from": "scalng"}}, "not_found", "Did you mean 'scaling'"),
        ({"runs": {"select": ["metric.val/accc.max"]}}, "not_found", "'val/acc'"),
        ({"runs": {"select": ["config.lrr"]}}, "not_found", "'lr'"),
        ({"data": {"from": ".", "key": "sample"}}, "not_found", "'samples'"),
        ({"runs": {"from": "@cluster/x"}}, "invalid", "no remote source"),
        ({"runs": {"where": {"proposal.chek": "pass"}}}, "invalid", "proposal.check"),
        ({"groups": {"where": {"config.lr": 1}}}, "invalid", "proposal.*"),
        ({"importance": {"target": "metric.val/acc.max"}}, "invalid", "v1.1"),
        ({"runs": {"from": "../.."}}, "invalid", "leaves the log dir"),
        ({"runs": {"where": {"config.lr": {"less": 1}}}}, "invalid", "operators"),
        ({"series": {"y": ["train/loss"], "steps": [1]}}, "invalid", "steps"),
    ],
)
def test_helpful_errors(ask, query: dict, code: str, text: str) -> None:
    """Errors say what is wrong, suggest the closest names and carry an exit code."""
    with pytest.raises(QueryError) as e:
        ask(query)
    assert e.value.code == code and text in str(e.value)


def test_caller_defaults(ask) -> None:
    """MCP answers default to 50 rows; views get up to 1000."""
    assert ask({"runs": {}}, caller="mcp")["meta"]["shown"] == 47
    assert ask({"runs": {"limit": 2}}, caller="view")["meta"]["shown"] == 2


def test_nonfinite_values_are_json_safe(ask, roles) -> None:
    """Raw curves turn NaN and Infinity into null, so answers stay valid JSON."""
    a = ask({"series": {"from": roles["diverging"], "y": ["train/loss"], "steps": [640, 700]}})
    ys = a["curves"][0]["y"]
    assert None in ys and all(y is None or math.isfinite(y) for y in ys)
    json.dumps(a, allow_nan=False)


@pytest.mark.parametrize(
    "where",
    [
        {"config.lr": {"lt": "1e-3"}},
        {"config.lr": {"ge": 1e-4, "le": 1e-3}},
        {"config.lr": "3e-4"},
        {"config.tokenizer": "bpe"},
        {"config.tokenizer": {"lt": "c"}},
        {"config.tokenizer": {"gt": "1e-3"}},
        {"config.model": {"gt": 5}},
        {"config.seed": {"gt": "0"}, "run.status": "finished"},
        {"run.status": "lost"},
        {"run.status": {"eq": "running"}},
        {"metric.val/acc.last": {"gt": 0.9}},
        {"value.test/acc": {"ge": "0.92"}},
    ],
)
def test_sql_prefilter_never_changes_answers(ask, monkeypatch, where: dict) -> None:
    """The SQL prefilter returns exactly what the Python evaluator alone returns."""
    query = {"runs": {"where": where, "select": ["run.id"], "limit": 1000}}
    with_sql = {r[0] for r in ask(query)["rows"]}
    monkeypatch.setattr("beamtime.query.select.prefilter", lambda where, exprs: ("", []))
    assert {r[0] for r in ask(query)["rows"]} == with_sql


def test_keys_of_running_runs_come_from_their_columns(tmp_path: Path) -> None:
    """A running run's new metrics are listed before its card is rewritten."""
    from beamtime.format.io import json_line

    logdir = tmp_path / "beamtime"
    roles = generate(logdir, seed=0, now=datetime.now(timezone.utc)).roles
    run_dir = next(logdir.glob(f"**/{roles['running']}"))
    with (run_dir / "_metrics.jsonl").open("ab") as f:
        f.write(json_line({"_step": 5000, "_t": 1.0, "live/new": 1.0}))
    index = Index(logdir=logdir, cache=tmp_path / "cache")
    try:
        index.catch_up(".", budget_s=float("inf"))
        a = run({"keys": {"from": "."}}, logdir=logdir, index=index)
    finally:
        index.close()
    metrics = {r[0]: r for r in a["metrics"]["rows"]}
    assert metrics["live/new"][:4] == ["live/new", 1, 5000, False]
    assert metrics["train/loss"][1] == 26


@pytest.fixture(scope="module")
def clocked(tmp_path_factory: pytest.TempPathFactory):
    """Answer queries on two runs with known times: A at 0.5 s per step, B at 1 s per step.

    A also logs 50 steps past its last ``epoch``; ``epoch`` steps up every 100 steps, ``wiggle`` is
    not monotone and ``const`` never changes.

    :param tmp_path_factory: Pytest's temporary directory factory.
    :return: A function from query to answer."""
    logdir = tmp_path_factory.mktemp("clocked") / "beamtime"
    gen = Generator(logdir=logdir, seed=0, scale=SCALES["s"], now=datetime.now(timezone.utc))
    for seed, (end, per_step) in enumerate([(350, 0.5), (300, 1.0)]):
        rows = []
        for s in range(0, end + 1, 50):
            row = {
                "_step": s,
                "_t": 1000.0 + per_step * s,
                "m": float(s),
                "const": 5.0,
                "loss": 1.0,
            }
            row["wiggle"] = float([0, 2, 1, 3, 4, 6, 5, 7][s // 50])
            if s <= 300:
                row["epoch"] = float(s // 100)
            rows.append(row)
        gen.write_run(gen.spec(logdir / "x", {"arm": "a", "seed": seed}, rows))
    index = Index(logdir=logdir, cache=tmp_path_factory.mktemp("clocked-cache"))
    index.catch_up(".", budget_s=float("inf"))

    def answer(query: dict) -> dict:
        return run(query, logdir=logdir, index=index)

    yield answer
    index.close()


def test_series_epoch_axis_is_the_logged_stair(clocked) -> None:
    """An epoch logged as a stair stays one, also past its last point."""
    curves = clocked({"series": {"from": "x", "y": ["m"], "x": "epoch", "points": 100}})["curves"]
    a, b = sorted(curves, key=lambda c: -len(c["x"]))
    assert a["x"] == [0.0, 0.0, 1.0, 1.0, 2.0, 2.0, 3.0, 3.0] and a["monotone"]
    assert b["x"] == [0.0, 0.0, 1.0, 1.0, 2.0, 2.0, 3.0] and b["monotone"]


def test_series_elapsed_axis_stays_in_seconds(clocked) -> None:
    """Elapsed time is measured from each run's first point."""
    q = {"from": "x", "y": ["m"], "x": "_elapsed", "points": 100}
    a, b = sorted(clocked({"series": q})["curves"], key=lambda c: -len(c["x"]))
    assert a["x"] == [0.0, 25.0, 50.0, 75.0, 100.0, 125.0, 150.0, 175.0]
    assert b["x"] == [0.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0]


def test_grouped_series_buckets_by_the_x_axis(clocked) -> None:
    """Group means are taken per run per bucket of x; the last x lands in the last bucket."""
    q = {"from": "x", "y": ["m"], "by": ["config.arm"], "x": "_elapsed", "points": 3}
    (curve,) = clocked({"series": q})["curves"]
    # A: buckets of 100 s hold steps {0..150}, {200..350}; B: {0, 50}, {100, 150}, {200..300}.
    assert curve["x"] == [50.0, 150.0, 250.0]
    assert curve["mean"] == [50.0, 200.0, 250.0] and curve["n"] == [2, 2, 1]


def test_series_with_a_non_monotone_x(clocked) -> None:
    """Curves flag it and keep the steps their points were logged at; aggregating is an error."""
    a, _ = clocked({"series": {"from": "x", "y": ["m"], "x": "wiggle", "points": 100}})["curves"]
    assert not a["monotone"] and len(a["step"]) == len(a["x"])
    q = {"from": "x", "y": ["m"], "by": ["config.arm"], "x": "wiggle", "points": 3}
    with pytest.raises(QueryError, match="monotone"):
        clocked({"series": q})


def test_grouped_series_with_a_constant_x_is_one_bucket(clocked) -> None:
    """No width to divide by: every point lands in one bucket at the constant."""
    q = {"from": "x", "y": ["m"], "by": ["config.arm"], "x": "const", "points": 5}
    (curve,) = clocked({"series": q})["curves"]
    assert curve["x"] == [5.0] and curve["n"] == [2]
    assert curve["mean"] == [(175.0 + 150.0) / 2]


def test_grouped_series_of_single_point_runs_is_one_bucket(clocked) -> None:
    """Runs cut to their first step all sit at elapsed 0."""
    q = {"from": "x", "y": ["m"], "by": ["config.arm"], "x": "_elapsed", "steps": [0, 0]}
    (curve,) = clocked({"series": q | {"points": 5}})["curves"]
    assert curve["x"] == [0.0] and curve["n"] == [2] and curve["mean"] == [0.0]
