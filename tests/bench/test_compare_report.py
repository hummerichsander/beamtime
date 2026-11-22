"""Tests of the benchmark's report (``compare/tables.py``, ``figures.py``); fixture records only."""

import json
import sys
from pathlib import Path
from typing import Any

import pytest

BENCH = Path(__file__).resolve().parents[2] / "bench" / "agents"
sys.path.insert(0, str(BENCH / "compare"))
sys.path.insert(0, str(BENCH))

import figures  # noqa: E402
import tables  # noqa: E402

SETUPS = ["mcp", "cli", "files", "tensorboard"]
TASKS = ["best-config", "failures"]
SEEDS = [7, 8, 9]
MODEL = "claude-sonnet-5-5"


def record(task: str, setup: str, seed: int, **extra: Any) -> dict[str, Any]:
    """Make the record of a session; tokens and seconds depend on the setup and seed.

    :param task: The task id.
    :param setup: The setup.
    :param seed: The data seed.
    :param extra: Fields that replace the defaults.
    :return: The record."""
    n = SETUPS.index(setup) + 1
    tokens = {"input": 10, "cache_write": 100 * n, "cache_read": 1000 * n, "output": 50 * seed}
    return {
        "task": task,
        "setup": setup,
        "seed": seed,
        "rep": 0,
        "status": "ok",
        "seconds": 30.0 * n + seed,
        "turns": 3 + n,
        "tokens": tokens | {"total": sum(tokens.values())},
        "cost_usd": 0.1 * n,
        "tools": {"Bash": n, "Read": 1},
        "leak": False,
        "other_model": False,
    } | extra


def make_batch(
    folder: Path,
    *,
    skip: set[tuple[str, str]] = frozenset(),
    edit: Any = None,
    model: str = MODEL,
    alias: str | None = None,
) -> Path:
    """Write a batch of graded sessions: every task, setup and seed once.

    :param folder: The batch's folder.
    :param skip: (task, setup) pairs that get no session.
    :param edit: Called as ``edit(name, record, grade)`` to change a session before it is written.
    :param model: The batch's model id.
    :param alias: The model alias it was started with; none in batches before Decision 18.
    :return: The folder."""
    folder.mkdir(parents=True)
    (folder / "batch.json").write_text(
        json.dumps(
            {
                "model": model,
                **({"alias": alias} if alias else {}),
                "claude_version": "2.9.9",
                "started": "2026-05-04T10:00:00+00:00",
                "setups": SETUPS,
                "tasks": TASKS,
                "seeds": SEEDS,
                "reps": 1,
            }
        )
    , encoding="utf-8")
    for task in TASKS:
        for setup in SETUPS:
            if (task, setup) in skip:
                continue
            for seed in SEEDS:
                name = f"{task}-{setup}-{seed}-0"
                rec = record(task, setup, seed)
                grade: dict[str, Any] | None = {
                    "score": 1.0 if seed != 9 else 0.5,
                    "correct": seed != 9,
                    "checks": {},
                    "notes": "",
                }
                if edit:
                    rec, grade = edit(name, rec, grade)
                (folder / name).mkdir()
                (folder / name / "record.json").write_text(json.dumps(rec), encoding="utf-8")
                if grade is not None:
                    (folder / name / "grade.json").write_text(json.dumps(grade), encoding="utf-8")
    return folder


@pytest.fixture(autouse=True)
def no_latex(monkeypatch: pytest.MonkeyPatch) -> None:
    """Render figures without LaTeX, which keeps the tests fast and independent of the machine.

    :param monkeypatch: The pytest monkeypatch."""
    monkeypatch.setattr(figures.shutil, "which", lambda name: None)


def row(text: str, start: str) -> str:
    """Find a table row of a report.

    :param text: The report.
    :param start: The row's first cells, e.g. ``| best-config | mcp |``.
    :return: The row."""
    (line,) = [line for line in text.splitlines() if line.startswith(start)]
    return line


def test_report_files(tmp_path: Path) -> None:
    """The report writes the table and the four figure files, with the facts and every measure."""
    batch = tables.Batch(folder=make_batch(tmp_path / "compare-1"))
    files = tables.write_report(batch, tmp_path / "out")
    assert sorted(p.name for p in files) == [
        "results.md",
        "time-per-task.pdf",
        "time-per-task.svg",
        "tokens-vs-score.pdf",
        "tokens-vs-score.svg",
    ]
    assert all(p.stat().st_size > 0 for p in files)
    text = (tmp_path / "out" / "results.md").read_text(encoding="utf-8")
    assert MODEL in text and "2.9.9" in text and "2026-05-04" in text and "7, 8, 9" in text
    head = "| task | setup | n | tokens | uncached | cost | seconds | turns | tool calls | score |"
    head += " correct |"
    assert head in text
    assert row(text, "| best-config | mcp | 3 |").endswith("| 0.83 | 2/3 |")
    assert row(text, "| mcp | 6 |").endswith("| 0.83 | 4/6 |")


def test_ungraded_left_out(tmp_path: Path) -> None:
    """Ungraded sessions and sessions not yet graded are counted, not averaged."""

    def edit(name, rec, grade):
        if name == "best-config-mcp-7-0":
            return rec | {"ungraded": "crashed"}, None
        if name == "best-config-mcp-8-0":
            return rec | {"ungraded": "usage limit"}, None
        if name == "best-config-mcp-9-0":
            return rec, None
        return rec, grade

    batch = tables.Batch(folder=make_batch(tmp_path / "compare-1", edit=edit))
    text = tables.results(batch)
    assert "| best-config | mcp |" not in text
    assert "21 graded sessions of 24" in text
    assert "1 crashed, 1 not graded yet, 1 usage limit" in text


def test_timeout_scores_zero(tmp_path: Path) -> None:
    """A graded timeout is a session like any other and enters the mean with its 0."""

    def edit(name, rec, grade):
        if name == "failures-cli-7-0":
            return rec | {"status": "timeout"}, grade | {"score": 0.0, "correct": False}
        return rec, grade

    batch = tables.Batch(folder=make_batch(tmp_path / "compare-1", edit=edit))
    assert row(tables.results(batch), "| failures | cli | 3 |").endswith("| 0.50 | 1/3 |")


def test_leak_listed_and_left_out_of_figures(tmp_path: Path) -> None:
    """A leaked session is named and stays in the table, but not in the figures' rows."""

    def edit(name, rec, grade):
        return (rec | {"leak": True}, grade) if name == "failures-files-8-0" else (rec, grade)

    batch = tables.Batch(folder=make_batch(tmp_path / "compare-1", edit=edit))
    assert "Leaked (in the tables, left out of the figures): failures-files-8-0." in tables.results(
        batch
    )
    assert "| failures | files | 3 |" in tables.results(batch)
    assert len(batch.plotted) == len(batch.graded) - 1
    assert not any(
        r["task"] == "failures" and r["setup"] == "files" and r["seed"] == 8 for r in batch.plotted
    )


def test_other_model_listed(tmp_path: Path) -> None:
    """A session flagged ``other_model`` is named in the report."""

    def edit(name, rec, grade):
        return (
            (rec | {"other_model": True}, grade) if name == "best-config-cli-7-0" else (rec, grade)
        )

    batch = tables.Batch(folder=make_batch(tmp_path / "compare-1", edit=edit))
    assert "took part in: best-config-cli-7-0." in tables.results(batch)


def test_incomplete_batch(tmp_path: Path) -> None:
    """Figures are refused naming the setup and task when one has no session; nothing is written."""
    folder = make_batch(tmp_path / "compare-1", skip={("failures", "files")})
    with pytest.raises(ValueError, match="files/failures"):
        tables.write_report(tables.Batch(folder=folder), tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_incomplete_when_all_leaked(tmp_path: Path) -> None:
    """A setup whose sessions of a task all leaked has no point for it: the figures are refused."""

    def edit(name, rec, grade):
        return (rec | {"leak": True}, grade) if name.startswith("failures-cli-") else (rec, grade)

    folder = make_batch(tmp_path / "compare-1", edit=edit)
    with pytest.raises(ValueError, match="cli/failures"):
        tables.write_report(tables.Batch(folder=folder), tmp_path / "out")


def test_main_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The command exits with the refusal's message."""
    folder = make_batch(tmp_path / "compare-1", skip={("best-config", "mcp")})
    monkeypatch.setattr(sys, "argv", ["tables.py", str(folder), "--out", str(tmp_path / "out")])
    with pytest.raises(SystemExit, match="mcp/best-config"):
        tables.main()


def test_main_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command prints the files it wrote."""
    folder = make_batch(tmp_path / "compare-1")
    monkeypatch.setattr(sys, "argv", ["tables.py", str(folder), "--out", str(tmp_path / "out")])
    tables.main()
    assert "results.md" in capsys.readouterr().out


def test_two_models(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Two batches, one per model, get a report each and a table side by side; one model twice
    is refused."""
    sonnet = make_batch(tmp_path / "compare-1", alias="sonnet")
    haiku = make_batch(tmp_path / "compare-2", model="claude-haiku-5-5", alias="haiku")
    out = tmp_path / "out"
    monkeypatch.setattr(sys, "argv", ["tables.py", str(sonnet), str(haiku), "--out", str(out)])
    tables.main()
    printed = capsys.readouterr().out
    text = (out / "models.md").read_text(encoding="utf-8")

    assert (out / "sonnet" / "results.md").exists() and (out / "haiku" / "results.md").exists()
    assert (out / "haiku" / "tokens-vs-score.svg").exists() and "models.md" in printed
    assert "| setup | model | n | tokens |" in text
    assert row(text, f"| mcp | {MODEL} | 6 |").endswith("| 0.83 | 4/6 |")
    assert row(text, "| mcp | claude-haiku-5-5 | 6 |")
    monkeypatch.setattr(sys, "argv", ["tables.py", str(sonnet), str(sonnet), "--out", str(out)])
    with pytest.raises(SystemExit, match="one batch per model"):
        tables.main()


def test_no_latex_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without LaTeX the style list gains ``no-latex``; with it, it is the plain theme."""
    assert figures.style() == ["science", "nature", "no-latex"]
    monkeypatch.setattr(figures.shutil, "which", lambda name: "/usr/bin/latex")
    assert figures.style() == ["science", "nature"]


def test_no_rc_overrides() -> None:
    """The report modules never touch rc params or pass keywords that shadow them."""
    for module in (figures, tables):
        source = Path(module.__file__).read_text(encoding="utf-8")
        for word in ("rcParams", "rc_context", "fontsize", "linewidth", "color=", "cmap", "plt.rc"):
            assert word not in source, f"{module.__name__} uses {word}"


def test_geometric_mean() -> None:
    """The geometric mean skips non-positive values and gives 0 for none."""
    assert figures.geometric_mean([1, 100]) == pytest.approx(10)
    assert figures.geometric_mean([0, 4, 9]) == pytest.approx(6)
    assert figures.geometric_mean([]) == 0.0


def test_goal(tmp_path: Path) -> None:
    """The report states mcp's mean tokens against files' and whether the target holds.

    :param tmp_path: The pytest temporary folder."""
    batch = tables.Batch(folder=make_batch(tmp_path / "b"))

    assert (
        "mcp 1,510 against files 3,710 mean tokens over 6 sessions both ran: 0.41x, target 1.5x, "
        "**met**. Mean score mcp 0.833, files 0.833."
    ) in tables.results(batch)


def test_goal_needs_mcp_and_files(tmp_path: Path) -> None:
    """Without files sessions there is no goal section.

    :param tmp_path: The pytest temporary folder."""
    skip = {(t, "files") for t in TASKS}
    batch = tables.Batch(folder=make_batch(tmp_path / "b", skip=skip))

    assert "### Goal" not in tables.results(batch)


def test_check_setups_named(tmp_path: Path) -> None:
    """A batch that ran cli as a check says so.

    :param tmp_path: The pytest temporary folder."""
    folder = make_batch(tmp_path / "b")
    meta = json.loads((folder / "batch.json").read_text(encoding="utf-8"))
    (folder / "batch.json").write_text(json.dumps(meta | {"checks": ["cli"]}), encoding="utf-8")

    assert "Regression check, first seed only and no target: cli." in tables.results(
        tables.Batch(folder=folder)
    )


def gap_batch(
    folder: Path,
    sessions: dict[tuple[str, str], tuple[int, float]],
    *,
    reps: int = 3,
    only: dict[tuple[str, str], set[int]] | None = None,
) -> tables.Batch:
    """Write a batch of mcp and script sessions, one per rep of seed 7.

    :param folder: The batch's folder.
    :param sessions: (task, setup) to the total tokens and the score of each of its sessions.
    :param reps: The reps per task and setup.
    :param only: (task, setup) to the reps that get a session; every rep otherwise.
    :return: The batch."""
    folder.mkdir()
    meta = {"model": MODEL, "claude_version": "2.9.9", "started": "2026-05-04T10:00:00+00:00"}
    meta |= {"setups": ["mcp", "script"], "tasks": TASKS, "seeds": [7], "reps": reps}
    (folder / "batch.json").write_text(json.dumps(meta), encoding="utf-8")
    for (task, setup), (total, score) in sessions.items():
        for rep in (only or {}).get((task, setup), range(reps)):
            name = f"{task}-{setup}-7-{rep}"
            rec = record(task, "mcp", 7, rep=rep) | {"setup": setup}
            rec["tokens"] = {"input": 0, "cache_write": 0, "output": total, "total": total}
            (folder / name).mkdir()
            (folder / name / "record.json").write_text(json.dumps(rec), encoding="utf-8")
            grade = {"score": score, "correct": score == 1.0, "checks": {}, "notes": ""}
            (folder / name / "grade.json").write_text(json.dumps(grade), encoding="utf-8")
    return tables.Batch(folder=folder)


def test_gaps(tmp_path: Path) -> None:
    """A task where script is cheaper at the same score is a candidate with an empty construct.

    :param tmp_path: The pytest temporary folder."""
    batch = gap_batch(
        tmp_path / "b",
        {
            ("best-config", "mcp"): (1000, 1.0),
            ("best-config", "script"): (690, 1.0),
            ("failures", "mcp"): (1000, 1.0),
            ("failures", "script"): (900, 1.0),
        },
    )

    text = "\n".join(tables.gaps(batch))

    assert "| best-config | 690 | 1,000 | 0.69x | 1.00 | 1.00 |  |" in text
    assert "| failures |" not in text
    assert "Inconclusive" not in text
    assert "### Gaps" in tables.results(batch)


def test_gaps_cheaper_but_wrong_is_no_gap(tmp_path: Path) -> None:
    """A cheaper session that scores lower than mcp's is not a candidate.

    :param tmp_path: The pytest temporary folder."""
    batch = gap_batch(
        tmp_path / "b",
        {
            ("best-config", "mcp"): (1000, 1.0),
            ("best-config", "script"): (500, 0.5),
        },
    )

    assert "| best-config |" not in "\n".join(tables.gaps(batch))


def test_gaps_without_script(tmp_path: Path) -> None:
    """A batch without script sessions has no gaps section.

    :param tmp_path: The pytest temporary folder."""
    batch = tables.Batch(folder=make_batch(tmp_path / "b"))

    assert tables.gaps(batch) == []
    assert "### Gaps" not in tables.results(batch)


def test_gaps_needs_reps(tmp_path: Path) -> None:
    """With one rep the section calls itself inconclusive and still lists the rows.

    :param tmp_path: The pytest temporary folder."""
    batch = gap_batch(
        tmp_path / "b",
        {("best-config", "mcp"): (1000, 1.0), ("best-config", "script"): (500, 1.0)},
        reps=1,
    )

    text = "\n".join(tables.gaps(batch))

    assert "Inconclusive: one rep per task cannot separate a gap from session variance" in text
    assert "| best-config | 500 | 1,000 | 0.50x |" in text


def test_gaps_excludes_stated(tmp_path: Path) -> None:
    """A task whose prompt states the procedure is left out however wide script wins.

    :param tmp_path: The pytest temporary folder."""
    batch = gap_batch(
        tmp_path / "b",
        {("check-all", "mcp"): (1000, 1.0), ("check-all", "script"): (100, 1.0)},
    )

    text = "\n".join(tables.gaps(batch))

    assert "| check-all |" not in text
    assert "the prompt states the procedure: check-all" in text
    assert "No task qualifies." in text


def test_gaps_pairs_only(tmp_path: Path) -> None:
    """Only the sessions both arms ran enter the medians; a task one arm ran is not paired.

    :param tmp_path: The pytest temporary folder."""
    batch = gap_batch(
        tmp_path / "b",
        {
            ("best-config", "mcp"): (1000, 1.0),
            ("best-config", "script"): (100, 1.0),
            ("failures", "script"): (10, 1.0),
        },
        only={("best-config", "mcp"): {0, 1}},
    )

    text = "\n".join(tables.gaps(batch))

    assert "| best-config | 100 | 1,000 | 0.10x |" in text
    assert "failures" not in text
