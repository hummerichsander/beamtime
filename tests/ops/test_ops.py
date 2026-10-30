import json
from pathlib import Path

import pytest

from beamtime.cli.conditions import parse_where
from beamtime.cli.format import num, render, spark, table
from beamtime.ops import call
from beamtime.ops.budget import cut
from beamtime.ops.context import Context, OpError
from beamtime.query import run as run_query
from beamtime.settings import load


def test_condition_strings() -> None:
    """--where strings become the object form; repeated fields combine."""
    assert parse_where(["config.lr<1e-3", "config.lr>=1e-4", "run.status=finished"]) == {
        "config.lr": {"lt": 1e-3, "ge": 1e-4},
        "run.status": "finished",
    }
    assert parse_where(["run.name~lr-*", "config.seed in 0,1", "a!=true", "b=null"]) == {
        "run.name": {"glob": "lr-*"},
        "config.seed": {"in": [0, 1]},
        "a": {"ne": True},
        "b": None,
    }
    with pytest.raises(ValueError, match="operator"):
        parse_where(["config.lr"])
    with pytest.raises(ValueError, match="twice"):
        parse_where(["a=1", "a=2"])


def test_settings_levels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """User settings merge under the project's, key by key, with provenance."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    user = tmp_path / "cfg" / "beamtime" / "settings.yaml"
    user.parent.mkdir(parents=True)
    user.write_text(
        "remotes:\n  cluster: {host: c, command: bt, cache: /x}\nlogdir: nope\ntheme: dark\n"
    )
    (tmp_path / "beamtime.yaml").write_text(
        "schema: 1\nlogdir: runs\nremotes:\n  cluster: {path: /scratch}\nbogus: 1\n"
    )
    s = load(tmp_path)
    assert s.get("logdir") == "runs" and s.get("theme") == "dark"
    assert s.get("remotes")["cluster"] == {
        "host": "c",
        "command": "bt",
        "cache": "/x",
        "path": "/scratch",
    }
    levels = {k: level for k, _, level in s.flat()}
    assert levels["remotes.cluster.host"] == "user"
    assert levels["remotes.cluster.path"] == "project"
    assert levels["logdir"] == "project" and levels["theme"] == "user"
    assert any("belongs in the project" in p for p in s.problems)
    assert any("bogus" in p for p in s.problems)


def test_budget_cut_and_cursor() -> None:
    """Long answers are cut at whole items; the cursor continues where they stopped."""
    rows = [[i, "x" * 100] for i in range(1000)]
    first = cut({"kind": "runs", "rows": list(rows), "meta": {}}, 0, max_chars=5000)
    assert first["meta"]["cut"] and len(json.dumps(first)) < 5500
    n = int(first["meta"]["next"])
    second = cut({"kind": "runs", "rows": list(rows), "meta": {}}, n, max_chars=5000)
    assert second["rows"][0][0] == n
    small = cut({"kind": "runs", "rows": rows[:3], "meta": {}}, 0)
    assert "next" not in small["meta"]


def test_context_resolution(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The root is found like the SDK finds it; BEAMTIME_LOGDIR wins for the log dir."""
    (project / "sub").mkdir()
    monkeypatch.chdir(project / "sub")
    ctx = Context.make()
    assert ctx.root == project.resolve() and ctx.root_reason == "git repository"
    assert ctx.logdir == (project / "beamtime").resolve()
    monkeypatch.setenv("BEAMTIME_LOGDIR", str(project / "elsewhere"))
    assert Context.make().logdir == (project / "elsewhere").resolve()


def test_reading_operations_wrap_queries(ctx: Context) -> None:
    """runs, series, keys and timeline answer like the query layer."""
    params = {"from": "scaling/lr-sweep", "select": ["config.lr"], "limit": 5}
    a = call("runs", params, ctx)
    b = run_query({"runs": {"from": "scaling/lr-sweep", "select": ["config.lr"], "limit": 5}},
                  logdir=ctx.logdir)  # fmt: skip
    assert a["rows"] == b["rows"]
    s = call("series", {"from": "tokenizer", "y": ["val/ppl"], "by": ["config.tokenizer"]}, ctx)
    assert len(s["curves"]) == 2
    assert call("keys", {}, ctx)["runs"] == 26
    assert call("timeline", {"limit": 3}, ctx)["entries"]
    q = call("query", {"query": {"groups": {"from": "."}}}, ctx)
    assert q["kind"] == "groups"


def test_errors_carry_exit_codes(ctx: Context) -> None:
    """Invalid queries exit 2, missing things 4."""
    with pytest.raises(OpError) as e:
        call("runs", {"from": "nope"}, ctx)
    assert e.value.code == 4
    with pytest.raises(OpError) as e:
        call("runs", {"where": {"config.lr": {"less": 1}}}, ctx)
    assert e.value.code == 2
    with pytest.raises(OpError) as e:
        call("runs", {"limit": "many"}, ctx)
    assert e.value.code == 2


def test_card_output_status(ctx: Context, roles: dict[str, str]) -> None:
    """card, output and status describe a run and the project."""
    c = call("card", {"run": roles["diverging"]}, ctx)
    assert c["run"]["status"] == "failed" and c["run"]["error"].startswith("FloatingPoint")
    assert c["config"]["lr"] == 0.01 and c["metrics"]["train/loss"]["nonfinite"] == 10
    assert c["events"][-1]["description"].startswith("failed:")
    short = call("card", {"run": roles["diverging"][-8:]}, ctx)
    assert short["run"]["id"] == roles["diverging"]
    out = call("output", {"run": roles["diverging"], "tail": 3}, ctx)
    assert out["lines"][-1].startswith("FloatingPointError") and len(out["lines"]) == 3
    grep = call("output", {"run": roles["diverging"], "grep": "Traceback", "tail": None}, ctx)
    assert len(grep["lines"]) == 1 and grep["lines"][0].split(":")[0].isdigit()
    s = call("status", {}, ctx)
    assert s["runs"]["lost"] == 1 and s["daemon"] is None


def test_output_collapses_carriage_returns(ctx: Context, roles: dict[str, str]) -> None:
    """Progress bars written with carriage returns show their last state."""
    run = next(p for p in ctx.logdir.rglob(roles["killed"]) if p.is_dir())
    with (run / "_output.log").open("a") as f:
        f.write("progress 10%\rprogress 50%\rprogress 100%\n")
    out = call("output", {"run": roles["killed"], "tail": 1}, ctx)
    assert out["lines"] == ["progress 100%"]


def test_init_is_idempotent(ctx: Context, project: Path) -> None:
    """init writes beamtime.yaml and the .gitignore entry once."""
    call("init", {}, ctx)
    call("init", {}, ctx)
    assert (project / ".gitignore").read_text().count("beamtime/") == 1
    assert "logdir: beamtime" in (project / "beamtime.yaml").read_text()


def test_mv_rm_gc(ctx: Context, roles: dict[str, str]) -> None:
    """Runs move and go to the trash; running runs are refused; gc needs yes."""
    with pytest.raises(OpError, match="still running"):
        call("mv", {"source": roles["running"], "to": "archive"}, ctx)
    with pytest.raises(OpError, match="reserved"):
        call("mv", {"source": roles["killed"], "to": "notes"}, ctx)
    moved = call("mv", {"source": roles["killed"], "to": "archive/old"}, ctx)
    assert (ctx.logdir / moved["path"] / "_run.json").exists()
    with pytest.raises(OpError, match="still running"):
        call("rm", {"target": "scaling/long-context"}, ctx)
    call("rm", {"target": "archive"}, ctx)
    assert not (ctx.logdir / "archive").exists()
    preview = call("gc", {}, ctx)
    assert (ctx.logdir / "_trash").is_dir() and not preview["deleted"]
    done = call("gc", {"yes": True}, ctx)
    assert done["deleted"] and not list((ctx.logdir / "_trash").iterdir())


def test_doctor_and_settings(ctx: Context) -> None:
    """doctor checks the setup; settings lists values with their levels."""
    d = call("doctor", {}, ctx)
    checks = {row[0]: row[1] for row in d["rows"]}
    assert checks["python"] and checks["root"] and checks["cache"]
    assert not d["meta"]["failed"]
    s = call("settings", {}, ctx)
    assert ["logdir", "beamtime", "built-in"] in s["rows"]


def test_mcp_install_for_cursor(ctx: Context, project: Path) -> None:
    """Cursor's project config gets an entry that names the project root."""
    call("mcp install", {"client": "cursor"}, ctx)
    config = json.loads((project / ".cursor" / "mcp.json").read_text())
    args = config["mcpServers"]["beamtime"]["args"]
    assert args[-1] == "mcp" and args[:2] == ["--root", str(project.resolve())]


def test_text_rendering(ctx: Context) -> None:
    """Numbers are compact, tables aligned, curves one line with a sparkline."""
    assert [num(3e-4), num(0.93123), num(1234567.0), num(None), num(12)] == [
        "3e-4", "0.931", "1.23e6", "-", "12"
    ]  # fmt: skip
    lines = table(["run.id", "run.name", "config.lr"], [["id1", "a", 1e-3], ["id2", "bb", 0.1]])
    assert lines[0].split() == ["run", "config.lr", "id"]
    assert lines[1].index("0.001") == lines[0].index("config.lr")
    assert spark([1, 2, 3, None, 5]) == "▁▃▅ █"
    text = render(call("series", {"from": "tokenizer", "y": ["val/ppl"]}, ctx))
    assert text.count("val/ppl") == 6 and "curves from 6 runs" in text
    assert "3 of 26 runs" in render(call("runs", {"limit": 3}, ctx))


def test_note_rm_moves_the_note_and_its_versions_to_the_trash(ctx: Context, project: Path) -> None:
    """Removing a note removes its earlier versions too; listings forget them."""
    first = call("note add", {"group": "scaling/lr-sweep", "type": "idea", "description": "a"}, ctx)
    second = call("note add", {"group": "scaling/lr-sweep", "type": "idea", "description": "b",
                               "supersedes": first["version"]}, ctx)  # fmt: skip
    answer = call("note rm", {"note": second["version"]}, ctx)
    assert answer["notes"] == [second["version"], first["version"]]
    trash = list((project / "beamtime" / "_trash").rglob("*.md"))
    assert sorted(t.stem for t in trash) == sorted(answer["notes"])
    ids = [e["id"] for e in call("notes", {"from": "scaling/lr-sweep", "limit": 100}, ctx)["entries"]]
    assert first["version"] not in ids and second["version"] not in ids
    with pytest.raises(OpError, match="no note"):
        call("note rm", {"note": "20990101-000000-zzzz"}, ctx)


def test_moving_a_group_keeps_membership_and_old_paths(ctx: Context, project: Path) -> None:
    """A moved group's proposal still finds its runs, and its old path still resolves."""
    from beamtime.serve.app import page_of

    before = call("check", {"group": "scaling/lr-sweep"}, ctx)
    answer = call("mv", {"source": "scaling/lr-sweep", "to": "scaling/learning-rate"}, ctx)
    assert answer["path"] == "scaling/learning-rate"
    assert "_moves.jsonl" in answer["lines"][1]
    after = call("check", {"group": "scaling/learning-rate"}, ctx)
    assert after["result"] == before["result"] and after["result"] is not None
    assert len(call("runs", {"from": "scaling/lr-sweep", "limit": 100}, ctx)["rows"]) == 17
    assert page_of(ctx, "scaling/lr-sweep") == ("scaling/learning-rate", None)
    with pytest.raises(OpError, match="exists"):
        call("mv", {"source": "scaling/learning-rate", "to": "tokenizer"}, ctx)
    with pytest.raises(OpError, match="inside"):
        call("mv", {"source": "scaling", "to": "scaling/deeper"}, ctx)


def test_naming_a_run(ctx: Context, roles: dict) -> None:
    """A given name shows wherever the run's name does; the id stays."""
    run = roles["killed"]
    call("name", {"run": run, "name": "warmup baseline"}, ctx)
    rows = call("runs", {"from": run, "select": ["run.name"]}, ctx)["rows"]
    assert rows[0][1] == "warmup baseline"
    assert call("card", {"run": run}, ctx)["run"]["name"] == "warmup baseline"
    with pytest.raises(OpError, match="groups are renamed"):
        call("name", {"run": "scaling", "name": "x"}, ctx)


def test_set_writes_beamtime_yaml_and_keeps_the_rest(ctx: Context, project: Path) -> None:
    """Settings from the UI land in beamtime.yaml; other keys and comments stay."""
    path = project / "beamtime.yaml"
    path.write_text("schema: 1\n# where runs go\nlogdir: beamtime\nfigure_style:\n  - science\n")
    call("set", {"key": "figure_style", "value": "[science, ieee]"}, ctx)
    call("set", {"key": "theme_mode", "value": "dark"}, ctx)
    text = path.read_text()
    assert "# where runs go\nlogdir: beamtime\n" in text
    assert "figure_style: [science, ieee]\n" in text and text.count("figure_style") == 1
    assert ctx.settings.get("figure_style") == ["science", "ieee"]
    assert ctx.settings.get("theme_mode") == "dark"
    with pytest.raises(OpError, match="theme_mode is"):
        call("set", {"key": "theme_mode", "value": "sepia"}, ctx)
    with pytest.raises(OpError, match="no theme"):
        call("set", {"key": "theme", "value": "nope"}, ctx)
    if pytest.importorskip("scienceplots"):
        with pytest.raises(OpError, match="unknown style"):
            call("set", {"key": "figure_style", "value": ["science", "nope"]}, ctx)
