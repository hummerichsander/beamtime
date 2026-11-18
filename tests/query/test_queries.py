import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

import pytest

from beamtime.index.index import Index
from beamtime.query import QueryError, run
from beamtime.query.files import read_table
from beamtime.query.fields import parse_field
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


def brute_series(logdir: Path, run_id: str, key: str) -> list[tuple[int, float]]:
    """Read a run's metric from its metrics file.

    :param logdir: The log dir.
    :param run_id: The run id.
    :param key: The metric key.
    :return: ``(step, value)`` in file order."""
    (path,) = logdir.glob(f"**/{run_id}/_metrics.jsonl")
    rows = (json.loads(line) for line in path.read_text().splitlines())
    return [(r["_step"], r[key]) for r in rows if key in r]


def test_step_fields_match_a_brute_force_scan(ask, logdir, roles) -> None:
    """nonfinite_step and rise_step give each run's planted steps; None where nothing happens."""
    fields = [
        "metric.train/loss.nonfinite_step",
        "metric.train/loss.rise_step:10",
        "metric.train/loss.rise_step",
        "metric.train/loss.rise_step:1.5",
    ]
    rows = table(ask({"runs": {"from": "scaling/lr-sweep", "select": ["run.id", *fields]}}))
    assert rows
    for row in rows:
        series = brute_series(logdir, row["run.id"], "train/loss")
        nonfinite = next((s for s, v in series if not math.isfinite(v)), None)
        assert row[fields[0]] == nonfinite
        for field, k in zip(fields[1:], (10, 10, 1.5), strict=True):
            lowest, want = math.inf, None
            for s, v in series:
                if not math.isfinite(v) or v > k * lowest:
                    want = s
                    break
                lowest = min(lowest, v)
            assert row[field] == want, field
    by_id = {r["run.id"]: r for r in rows}
    assert by_id[roles["diverging"]][fields[0]] is not None
    assert by_id[roles["diverging"]][fields[1]] <= by_id[roles["diverging"]][fields[0]]
    assert by_id[roles["killed"]][fields[0]] is None


def test_step_fields_work_in_where_and_sort(ask, roles) -> None:
    """The fields filter and sort like any other; a missing step never matches a comparison."""
    f = "metric.train/loss.nonfinite_step"
    hit = table(ask({"runs": {"from": "scaling/lr-sweep", "where": {f: {"exists": True}}}}))
    assert roles["diverging"] in {r["run.id"] for r in hit}
    assert roles["killed"] not in {r["run.id"] for r in hit}
    late = table(ask({"runs": {"from": "scaling/lr-sweep", "where": {f: {"gt": 0}}}}))
    assert {r["run.id"] for r in late} == {r["run.id"] for r in hit}
    first = ask({"runs": {"from": "scaling/lr-sweep", "select": ["run.id", f], "sort": [f]}})
    assert first["rows"][0][0] == roles["diverging"]


@pytest.mark.parametrize(
    "bad", ["rise_step:0", "rise_step:x", "rise_step:-3", "rise_step:", "rise_step:inf"]
)
def test_rise_step_needs_a_positive_number(bad: str) -> None:
    """A bad factor is an error that names the form."""
    with pytest.raises(QueryError, match=r"rise_step:<k> takes a positive number"):
        parse_field(f"metric.train/loss.{bad}")


def test_rise_step_parses_decimals_and_refuses_windows() -> None:
    """A decimal factor is not read as a dotted key; a window is refused."""
    f = parse_field("metric.a.b.rise_step:2.5")
    assert (f.key, f.stat, f.arg) == ("a.b", "rise_step", 2.5)
    assert parse_field("metric.loss.rise_step").arg == 10
    assert parse_field("metric.loss.nonfinite_step").stat == "nonfinite_step"
    with pytest.raises(QueryError, match="windowed statistics"):
        parse_field("metric.loss.rise_step:3[0:10]")


def last_at(series: list[tuple[int, float]], step: int | None) -> float | None:
    """Brute force: the value logged at a step, or the last one before it.

    :param series: ``(step, value)`` in file order.
    :param step: The step.
    :return: The value, or ``None``."""
    before = [v for s, v in series if step is not None and s <= step]
    return before[-1] if before else None


def test_ref_reads_a_metric_at_a_step_of_another(ask, logdir) -> None:
    """metric.a[b.min_step] is a's value at b's best step; a bare step stat shows the step."""
    best = "metric.val/acc.max_step"
    ref = "metric.train/loss[val/acc.max_step]"
    rows = table(ask({"runs": {"from": "scaling/lr-sweep", "select": ["run.id", best, ref]}}))
    assert rows
    for row in rows:
        train = brute_series(logdir, row["run.id"], "train/loss")
        acc = brute_series(logdir, row["run.id"], "val/acc")
        step = max(acc, key=lambda p: p[1])[0]
        assert row[best] == step
        assert row[ref] == dict(train)[step]
    only = table(ask({"runs": {"from": "scaling/lr-sweep", "select": ["run.id", ref]}}))
    assert {r["run.id"]: r[ref] for r in only} == {r["run.id"]: r[ref] for r in rows}


def test_ref_between_points(ask, logdir) -> None:
    """val/acc is logged every 50 steps; at another step the last point before it counts."""
    ref = "metric.val/acc[train/loss.min_step]"
    rows = table(ask({"runs": {"from": "scaling/lr-sweep", "select": ["run.id", ref]}}))
    assert rows
    off_grid = 0
    for row in rows:
        loss = brute_series(logdir, row["run.id"], "train/loss")
        acc = brute_series(logdir, row["run.id"], "val/acc")
        step = min(loss, key=lambda p: p[1])[0]
        off_grid += step not in dict(acc)
        assert row[ref] == last_at(acc, step)
    assert off_grid


def test_ref_to_the_series_steps(ask, logdir) -> None:
    """A reference may be nonfinite_step or rise_step:<k>, computed from the columns."""
    fields = [
        "metric.train/loss[train/loss.nonfinite_step]",
        "metric.val/acc[train/loss.rise_step:10]",
    ]
    rows = table(ask({"runs": {"from": "scaling/lr-sweep", "select": ["run.id", *fields]}}))
    for row in rows:
        loss = brute_series(logdir, row["run.id"], "train/loss")
        acc = brute_series(logdir, row["run.id"], "val/acc")
        bad = next((s for s, v in loss if not math.isfinite(v)), None)
        got = row[fields[0]]
        want = last_at(loss, bad)
        assert got == (want if want is None or math.isfinite(want) else None)
        lowest, rise = math.inf, None
        for s, v in loss:
            if not math.isfinite(v) or v > 10 * lowest:
                rise = s
                break
            lowest = min(lowest, v)
        assert row[fields[1]] == last_at(acc, rise)


def test_ref_missing_metric(ask, logdir) -> None:
    """A run without the referenced metric, or without a, gets None."""
    ref = "metric.train/loss[val/ppl.min_step]"
    back = "metric.val/ppl[train/loss.min_step]"
    rows = table(ask({"runs": {"from": ".", "select": ["run.id", ref, back]}}))
    with_ppl = {r["run.id"] for r in rows if r[back] is not None}
    assert with_ppl and len(with_ppl) < len(rows)
    for row in rows:
        assert (row[ref] is not None) == (row["run.id"] in with_ppl)


def test_ref_in_where_and_sort_leaves_no_hidden_column(ask, logdir) -> None:
    """The window filters and sorts like any field; the step it reads is not an extra column."""
    ref = "metric.val/acc[train/loss.min_step]"
    a = ask(
        {
            "runs": {
                "from": "scaling/lr-sweep",
                "select": ["run.id", ref],
                "where": {ref: {"gt": 0}},
                "sort": [f"-{ref}"],
            }
        }
    )
    values = [r[ref] for r in table(a)]
    assert values and values == sorted(values, reverse=True)
    assert a["columns"] == ["run.id", ref]


@pytest.mark.parametrize("bad", ["val/acc.max", "val/acc", "val/acc.max_step:3"])
def test_ref_needs_a_step_stat(bad: str) -> None:
    """A reference to a statistic that is not a step is an error naming the step stats."""
    with pytest.raises(QueryError, match=r"min_step, max_step, last_step, nonfinite_step"):
        parse_field(f"metric.train/loss[{bad}]")


def test_ref_parses_and_takes_no_statistic() -> None:
    """The window keeps the metric as key, the step as ref; numeric windows are unchanged."""
    f = parse_field("metric.train/loss[val/acc.rise_step:2.5]")
    assert (f.key, f.stat, f.window) == ("train/loss", "last", None)
    assert (f.ref.key, f.ref.stat, f.ref.arg) == ("val/acc", "rise_step", 2.5)
    assert parse_field("metric.a.b.last[a.b.min_step]").key == "a.b"
    with pytest.raises(QueryError, match="takes no statistic"):
        parse_field("metric.train/loss.mean[val/acc.min_step]")
    g = parse_field("metric.train/loss.mean[10:20]")
    assert (g.window, g.ref) == ((10, 20), None)


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


def finite_triples(curve: dict) -> list[tuple[float, float, float]]:
    """Return the ``(lo, y, hi)`` triples of a curve where all three are numbers.

    :param curve: A series curve with the envelope.
    :return: The triples."""
    triples = zip(curve["lo"], curve["y"], curve["hi"], strict=True)
    return [t for t in triples if None not in t]


def test_raw_envelope(ask, roles) -> None:
    """A raw curve is its own envelope: ``y`` and no band."""
    zoom = ask({"series": {"from": roles["killed"], "y": ["train/loss"], "steps": [100, 119]}})
    (curve,) = zoom["curves"]
    assert curve["raw"] and len(curve["y"]) == len(curve["x"]) == 20
    assert not {"lo", "hi", "n"} & curve.keys()


def test_downsampled_envelope(ask, roles) -> None:
    """A downsampled curve answers ``y`` as last, ``lo`` as min, ``hi`` as max, ``n`` as count."""
    q = {"from": roles["killed"], "y": ["train/loss"], "steps": [0, 10**6], "points": 10}
    (curve,) = ask({"series": q})["curves"]
    assert not curve["raw"] and curve["source"] == "columns"
    assert curve["y"] == curve["last"] and curve["lo"] == curve["min"]
    assert curve["hi"] == curve["max"] and curve["n"] == curve["count"]
    assert len(curve["y"]) == len(curve["x"]) > 1
    assert all(lo <= y <= hi for lo, y, hi in finite_triples(curve))


def test_preview_envelope(ask, roles) -> None:
    """A preview curve has the envelope although it keeps no ``first``."""
    overview = ask({"series": {"from": "scaling/lr-sweep", "y": ["train/loss"], "points": 50}})
    assert overview["meta"]["from_preview"] == overview["meta"]["curves"] > 0
    for curve in overview["curves"]:
        assert curve["first"][0] is None
        assert None not in curve["y"] and curve["y"] == curve["last"]
        assert curve["lo"] == curve["min"] and curve["hi"] == curve["max"]
        assert curve["n"] == curve["count"]
        assert all(lo <= y <= hi for lo, y, hi in finite_triples(curve))


def test_grouped_envelope(ask) -> None:
    """A grouped curve answers ``y`` as the mean of its runs."""
    q = {"from": "tokenizer", "y": ["val/ppl"], "by": ["config.tokenizer"], "band": "minmax"}
    for curve in ask({"series": q | {"points": 8}})["curves"]:
        assert curve["y"] == curve["mean"] and len(curve["y"]) == len(curve["x"])
        assert all(lo <= y <= hi for lo, y, hi in finite_triples(curve))
    for curve in ask({"series": q | {"band": "none"}})["curves"]:
        assert curve["y"] == curve["mean"]
        assert curve["lo"] == [None] * len(curve["x"]) == curve["hi"]


def test_single_point_envelope(clocked) -> None:
    """A run cut to one step is a raw point; a group of them is one bucket with a band."""
    q = {"from": "x", "y": ["m"], "steps": [0, 0]}
    for curve in clocked({"series": q})["curves"]:
        assert curve["raw"] and curve["x"] == [0] and curve["y"] == [0.0]
    (curve,) = clocked({"series": q | {"by": ["config.arm"], "band": "minmax"}})["curves"]
    assert curve["y"] == curve["mean"] == [0.0] and curve["lo"] == curve["hi"] == [0.0]


def test_budget_envelope(ask) -> None:
    """The envelope adds arrays but no points: the chart budget holds and the JSON stays under 2x."""
    a = ask({"series": {"from": ".", "y": ["train/loss"], "points": 5000}}, caller="view")
    assert a["meta"]["points"] * a["meta"]["curves"] <= 30_000 + a["meta"]["curves"]
    assert any("lo" in c for c in a["curves"])
    legacy = {
        **a,
        "curves": [
            {k: v for k, v in c.items() if k not in ("y", "lo", "hi", "n") or c["raw"]}
            for c in a["curves"]
        ],
    }
    assert len(json.dumps(a)) < 2 * len(json.dumps(legacy))


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


def test_an_unknown_band_lists_the_valid_ones() -> None:
    """A band that isn't one names the valid values."""
    from beamtime.query.kinds import band_stats

    with pytest.raises(QueryError, match="bands: minmax, std, stderr, none"):
        band_stats([[1.0, 2.0]], "sd")


def test_a_resumed_runs_curve_names_where_the_attempts_meet(ask, roles) -> None:
    """A run with a second attempt carries the resume step, also mapped to another x axis; a
    run with one attempt carries none."""
    base = {"from": roles["resumed"], "y": ["train/loss"], "points": 10}
    (curve,) = ask({"series": base})["curves"]
    assert len(curve["resumes"]) == 1 and curve["resumes"][0] > 0
    (timed,) = ask({"series": base | {"x": "_elapsed"}})["curves"]
    assert len(timed["resumes"]) == 1 and 0 < timed["resumes"][0] < timed["x"][-1]
    plain = ask({"series": {"from": roles["killed"], "y": ["train/loss"]}})["curves"][0]
    assert "resumes" not in plain


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


def test_file_columns(ask) -> None:
    """``columns`` narrows and orders the answer; a wrong name gets the closest one."""
    a = ask({"file": {"path": "data/3f9a21c0-fit.csv", "view": "scaling", "columns": ["acc", "lr"]}})
    assert a["columns"] == ["acc", "lr"] and a["rows"][1] == [0.85, 0.003]
    with pytest.raises(QueryError, match=r"no column 'acc '.*columns: lr, acc\. Did you mean 'acc'"):
        ask({"file": {"path": "data/3f9a21c0-fit.csv", "view": "scaling", "columns": ["acc "]}})


def test_csv_dialect(tmp_path: Path) -> None:
    """A semicolon CSV, an index column and a duplicate name are errors with the fix."""
    for text, message in [
        ("a;b\n1;2\n", r"semicolon|;-separated.*to_csv\(path, index=False\)"),
        ("a\tb\n1\t2\n", r"tab-separated.*to_csv"),
        (",a\n0,1\n", r"empty column name.*to_csv"),
        ("a,a\n1,2\n", r"'a' twice"),
    ]:
        file = tmp_path / "t.csv"
        file.write_text(text)
        with pytest.raises(QueryError, match=message):
            read_table(file)


def test_semicolon_inside_quotes(tmp_path: Path) -> None:
    """A quoted header cell containing a semicolon in a comma CSV is fine."""
    file = tmp_path / "t.csv"
    file.write_text('"a;b",c\n1,2\n')
    assert read_table(file) == (["a;b", "c"], [[1, 2]])


def test_ragged_csv_row(tmp_path: Path) -> None:
    """A row with the wrong number of cells names its line."""
    file = tmp_path / "t.csv"
    file.write_text("a,b\n1,2\n3\n")
    with pytest.raises(QueryError, match=r"t.csv line 3: 1 cells, the header has 2"):
        read_table(file)


def test_csv_blank_lines(tmp_path: Path) -> None:
    """A blank line, often left at the end by an editor, is no row and no error."""
    file = tmp_path / "t.csv"
    file.write_text("a,b\n1,2\n\n3,4\n\n")
    assert read_table(file) == (["a", "b"], [[1, 2], [3, 4]])


def test_csv_bom(tmp_path: Path) -> None:
    """The byte order mark Excel writes does not end up in the first column name."""
    file = tmp_path / "t.csv"
    file.write_bytes(b"\xef\xbb\xbfa,b\n1,\n")
    assert read_table(file) == (["a", "b"], [[1, None]])


@pytest.mark.parametrize(
    "query, code, text",
    [
        ({"runs": {"from": "scalng"}}, "not_found", "Did you mean 'scaling'"),
        ({"runs": {"select": ["metric.val/accc.max"]}}, "not_found", "'val/acc'"),
        ({"runs": {"select": ["config.lrr"]}}, "not_found", "'lr'"),
        ({"data": {"from": ".", "key": "sample"}}, "not_found", "'samples'"),
        ({"runs": {"from": "@cluster/x"}}, "invalid", "no source @cluster"),
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


def test_attempts_after_requeue(ask, roles) -> None:
    """A resumed run counts two attempts; a run that never resumed counts one."""
    a = ask(
        {"runs": {"from": ".", "where": {"run.attempts": {"gt": 1}}, "select": ["run.attempts"]}}
    )
    rows = table(a)
    assert roles["resumed"] in [r["run.id"] for r in rows]
    assert all(r["run.attempts"] > 1 for r in rows)
    one = ask({"runs": {"from": roles["killed"], "select": ["run.attempts"]}})
    assert table(one)[0]["run.attempts"] == 1


def test_last_logged_sorts_and_matches_the_file(ask, logdir, roles) -> None:
    """``run.last_logged`` is the metrics file's mtime and sorts newest first."""
    a = ask(
        {"runs": {"from": ".", "select": ["run.last_logged"], "sort": ["-run.last_logged"],
                  "limit": 500}}
    )  # fmt: skip
    times = [r["run.last_logged"] for r in table(a) if r["run.last_logged"] is not None]
    assert times == sorted(times, reverse=True) and times
    run = next(p for p in logdir.rglob(roles["resumed"]) if p.is_dir())
    one = ask({"runs": {"from": roles["resumed"], "select": ["run.last_logged"]}})
    assert table(one)[0]["run.last_logged"] == (run / "_metrics.jsonl").stat().st_mtime


@pytest.mark.parametrize("kind", ["keys", "data", "timeline", "groups"])
def test_seeds_belongs_to_runs_and_series_only(ask, kind) -> None:
    """``seeds`` on a kind that cannot aggregate is an error that lists the kind's fields."""
    body = {"key": "x", "seeds": "config.seed"} if kind == "data" else {"seeds": "config.seed"}
    with pytest.raises(QueryError, match="unknown field 'seeds'"):
        ask({kind: body})


def test_models_import_is_light() -> None:
    """Importing the query structs loads neither the index nor the kinds."""
    code = (
        "import sys, beamtime.query.models; "
        "bad = [n for n in ('beamtime.index.index', 'beamtime.query.kinds', 'beamtime.query.select') "
        "if n in sys.modules]; "
        "print(','.join(bad))"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == ""


def test_run_started_is_run_created_at(ask) -> None:
    """``run.started`` is ``run.created_at``, the run's first start: the column keeps the typed name."""
    a = ask(
        {
            "runs": {
                "from": "scaling/lr-sweep",
                "select": ["run.started", "run.created_at"],
                "sort": ["-run.started"],
            }
        }
    )
    assert a["columns"][1:] == ["run.started", "run.created_at"]
    rows = table(a)
    assert rows and all(r["run.started"] == r["run.created_at"] is not None for r in rows)
    assert [r["run.started"] for r in rows] == sorted(
        (r["run.started"] for r in rows), reverse=True
    )
    newest = rows[0]["run.started"]
    where = ask({"runs": {"from": "scaling/lr-sweep", "where": {"run.started": {"ge": newest}}}})
    assert len(where["rows"]) >= 1


def test_bare_metric_key_means_last(ask) -> None:
    """``metric.<key>`` is ``metric.<key>.last`` in select, sort and where."""
    bare = ask(
        {
            "runs": {
                "from": "scaling/lr-sweep",
                "where": {"run.status": "finished", "metric.val/acc": {"gt": 0}},
                "select": ["metric.val/acc", "metric.val/acc.last"],
                "sort": ["-metric.val/acc"],
            }
        }
    )
    assert bare["columns"][1:] == ["metric.val/acc", "metric.val/acc.last"]
    rows = table(bare)
    assert rows and all(r["metric.val/acc"] == r["metric.val/acc.last"] for r in rows)
    values = [r["metric.val/acc"] for r in rows]
    assert values == sorted(values, reverse=True)
    explicit = ask(
        {
            "runs": {
                "from": "scaling/lr-sweep",
                "where": {"run.status": "finished", "metric.val/acc.last": {"gt": 0}},
                "select": ["metric.val/acc.last"],
                "sort": ["-metric.val/acc.last"],
            }
        }
    )
    assert [r["metric.val/acc.last"] for r in table(explicit)] == values


def test_bare_metric_key_parsing() -> None:
    """The last segment is the stat only if it names one; keys with dots stay whole."""
    f = parse_field("metric.val/acc")
    assert (f.key, f.stat, f.window, f.text) == ("val/acc", "last", None, "metric.val/acc")
    f = parse_field("metric.layer.0.grad")
    assert (f.key, f.stat) == ("layer.0.grad", "last")
    f = parse_field("metric.layer.0.grad.max")
    assert (f.key, f.stat) == ("layer.0.grad", "max")
    f = parse_field("metric.loss.min")
    assert (f.key, f.stat) == ("loss", "min")
    f = parse_field("metric.loss.min.last")
    assert (f.key, f.stat) == ("loss.min", "last")
    f = parse_field("metric.loss[10:20]")
    assert (f.key, f.stat, f.window) == ("loss", "last", (10, 20))
    with pytest.raises(QueryError, match="windowed statistics"):
        parse_field("metric.loss.ema_last[10:20]")
    with pytest.raises(QueryError, match="metric.<key>"):
        parse_field("metric.")


@pytest.fixture
def behind(logdir: Path, tmp_path: Path):
    """An index of the log dir that caught up with no time for streams.

    :param logdir: The log dir.
    :param tmp_path: Pytest's temporary directory.
    :return: The open index and the number of runs whose streams were deferred."""
    index = Index(logdir=logdir, cache=tmp_path / "cache")
    deferred = index.catch_up(".", budget_s=0.0).behind
    assert deferred > 0
    yield index, deferred
    index.close()


def test_series_reads_every_run(ask, behind) -> None:
    """A query ingests the streams of the runs it reads, whatever the catch-up budget."""
    index, deferred = behind
    q = {"series": {"from": ".", "y": ["train/loss"], "points": "all"}}
    want = ask(q)["curves"]
    a = run(q, logdir=index.logdir, index=index, budget_s=0.0)
    assert len(a["curves"]) == len(want) > 0
    assert a["meta"]["freshness"]["behind"] <= deferred - len(want)


def test_windowed_field_has_a_value_for_every_run(ask, behind) -> None:
    """A windowed field is computed from the columns of every selected run."""
    index, _ = behind
    q = {"runs": {"from": "scaling", "select": ["metric.train/loss.mean[0:50]"], "limit": 200}}
    want = [r[1] for r in ask(q)["rows"]]
    got = [r[1] for r in run(q, logdir=index.logdir, index=index, budget_s=0.0)["rows"]]
    assert got == want and any(v is not None for v in got)


def test_behind_counts_only_runs_the_answer_did_not_read(behind, roles) -> None:
    """Runs a query ingested leave the behind count; a second query ingests nothing."""
    index, _ = behind
    db = index.store.db
    run_id = roles["resumed"]
    folder = db.execute("SELECT folder FROM runs WHERE id = ?", (run_id,)).fetchone()[0]
    in_folder = db.execute("SELECT count(*) FROM runs WHERE folder = ?", (folder,)).fetchone()[0]
    assert in_folder > 1
    q = {
        "series": {
            "from": folder,
            "where": {"run.id": run_id},
            "y": ["train/loss"],
            "points": "all",
        }
    }
    first = run(q, logdir=index.logdir, index=index, budget_s=0.0)
    assert len(first["curves"]) == 1
    assert first["meta"]["freshness"]["behind"] == in_folder - 1
    calls = []
    original = index.ingester.ingest_streams
    index.ingester.ingest_streams = lambda d: calls.append(d) or original(d)
    second = run(q, logdir=index.logdir, index=index, budget_s=0.0)
    assert calls == [] and second["curves"] == first["curves"]


@pytest.fixture
def hide(tmp_path: Path, fresh_logdir):
    """A fresh log dir with one run of ``scaling/lr-sweep`` hidden by its flag.

    :param tmp_path: Pytest's temporary directory.
    :param fresh_logdir: Writes a generated log dir.
    :return: The log dir, the hidden run's directory and an ``ask`` function."""
    logdir = tmp_path / "beamtime"
    fresh_logdir(logdir, 1)
    run_dir = next(
        r for r in sorted((logdir / "scaling" / "lr-sweep").iterdir()) if (r / "_run.json").exists()
    )
    info = json.loads((run_dir / "_run.json").read_text())
    (run_dir / "_run.json").write_text(json.dumps(info | {"hidden": True}))
    config = json.loads((run_dir / "_config.json").read_text())
    (run_dir / "_config.json").write_text(json.dumps(config | {"hidden_only": 1}))
    index = Index(logdir=logdir, cache=tmp_path / "cache")
    index.catch_up(".", budget_s=float("inf"))

    def answer(query: dict) -> dict:
        return run(query, logdir=logdir, index=index)

    yield logdir, run_dir, answer
    index.close()


def test_hidden_runs_are_left_out(hide) -> None:
    """Every kind leaves a hidden run out, and ``hidden: true`` brings it back."""
    _, run_dir, ask = hide
    group = "scaling/lr-sweep"
    visible = table(ask({"runs": {"from": group}}))
    shown = table(ask({"runs": {"from": group, "hidden": True}}))
    assert run_dir.name not in {r["run.id"] for r in visible}
    assert run_dir.name in {r["run.id"] for r in shown}
    n = len(visible)
    assert len(shown) == n + 1
    flags = table(ask({"runs": {"from": group, "hidden": True, "select": ["run.hidden"]}}))
    assert [r["run.hidden"] for r in flags].count(True) == 1
    only = table(ask({"runs": {"from": group, "hidden": True, "where": {"run.hidden": True}}}))
    assert len(only) == 1
    keys = ask({"keys": {"from": group}})
    assert "config.hidden_only" not in {r[0] for r in keys["config"]["rows"]}
    keys = ask({"keys": {"from": group, "hidden": True}})
    assert "config.hidden_only" in {r[0] for r in keys["config"]["rows"]}
    series = ask({"series": {"from": group, "y": ["train/loss"], "points": 5}})
    assert len(series["curves"]) == n
    series = ask({"series": {"from": group, "y": ["train/loss"], "points": 5, "hidden": True}})
    assert len(series["curves"]) == n + 1
    rows = {r["path"]: r for r in table(ask({"groups": {"from": "."}}))}
    total = rows["."]["runs"]
    assert rows[group]["runs"] == n and rows[group]["hidden"] == 1 and rows[group]["direct"] == n
    assert rows["."]["hidden"] == 1
    rows = {r["path"]: r for r in table(ask({"groups": {"from": ".", "hidden": True}}))}
    assert rows[group]["runs"] == n + 1 and rows[group]["direct"] == n + 1
    assert rows["."]["runs"] == total + 1


def test_hidden_run_named_by_id_shows(hide) -> None:
    """A run named in ``from`` counts although it is hidden."""
    _, run_dir, ask = hide
    one = table(ask({"runs": {"from": run_dir.name, "select": ["run.hidden"]}}))
    assert len(one) == 1 and one[0]["run.hidden"] is True


def test_hidden_only_key(hide) -> None:
    """A key only hidden runs have is unknown by default and known with ``hidden``."""
    _, _, ask = hide
    query = {"from": "scaling/lr-sweep", "where": {"config.hidden_only": 1}}
    with pytest.raises(QueryError, match="hidden_only"):
        ask({"runs": query})
    assert len(table(ask({"runs": query | {"hidden": True}}))) == 1


def test_hidden_with_depth(hide) -> None:
    """Depth and visibility both narrow the selection."""
    _, _, ask = hide
    assert len(table(ask({"runs": {"from": "scaling", "depth": 1}}))) == 0
    deep = table(ask({"runs": {"from": "scaling", "depth": 2, "select": ["run.hidden"]}}))
    assert deep and not any(r["run.hidden"] for r in deep)
    deep = table(ask({"runs": {"from": "scaling", "depth": 2, "hidden": True}}))
    assert len(deep) == len(table(ask({"runs": {"from": "scaling", "depth": 2}}))) + 1


def test_hidden_group_tools_and_timeline(hide) -> None:
    """The group tools and the timeline see visible runs only unless asked."""
    from beamtime.query.facts import run_facts

    logdir, run_dir, ask = hide
    n = len(table(ask({"runs": {"from": "scaling/lr-sweep"}})))
    with Index(logdir=logdir, cache=logdir.parent / "cache") as index:
        kwargs = dict(scope="scaling/lr-sweep", run_id=None, now=datetime.now().timestamp())
        assert len(run_facts(index, **kwargs)) == n
        facts = run_facts(index, **kwargs, hidden=True)
        assert len(facts) == n + 1 and run_dir.name in {f.id for f in facts}
        assert [f.id for f in run_facts(index, **{**kwargs, "run_id": run_dir.name})] == [
            run_dir.name
        ]


def test_hidden_events_in_timeline(hide) -> None:
    """A hidden run's events stay out of the timeline unless asked."""
    _, run_dir, ask = hide
    query = {"from": "scaling/lr-sweep", "full": True, "limit": 10000}
    assert run_dir.name not in json.dumps(ask({"timeline": query}))
    assert run_dir.name in json.dumps(ask({"timeline": query | {"hidden": True}}))
