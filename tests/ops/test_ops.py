import dataclasses
import json
import os
import shutil
import sys
from pathlib import Path

import pytest

from beamtime.query.conditions import parse_where
from beamtime.cli.format import num, render, spark, table
from beamtime.format.ids import new_run_id
from beamtime.ops import call
from beamtime.ops.budget import OLD_CURVE_FIELDS, cut
from beamtime.ops.context import Context, OpError
from beamtime.query import run as run_query
from beamtime.remote import answer
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


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("val/acc.max>0.9", ("val/acc.max", "gt", 0.9)),
        ("metric.val/loss.mean[0:1000]<=0.5", ("metric.val/loss.mean[0:1000]", "le", 0.5)),
        ('config["a<b"]=1', ('config["a<b"]', "eq", 1)),
        ("config['x=y'] != -3", ("config['x=y']", "ne", -3)),
        ("config.lr>=-1e-4", ("config.lr", "ge", -1e-4)),
        ("config.lr = 3E-4", ("config.lr", "eq", 3e-4)),
        ('config.tag="1"', ("config.tag", "eq", "1")),
        ("config.tag='true'", ("config.tag", "eq", "true")),
        ("config.name=a=b", ("config.name", "eq", "a=b")),
        ('config.opt in adam, "sgd,momentum", 3', ("config.opt", "in", ["adam", "sgd,momentum", 3])),
        ("run.name~lr-*", ("run.name", "glob", "lr-*")),
        ('config.note=""', ("config.note", "eq", "")),
        ("config.min in 1,2", ("config.min", "in", [1, 2])),
    ],
)
def test_condition_syntax(text: str, expected: tuple) -> None:
    """Brackets and quotes protect operators; quoted values stay text; lists split outside quotes."""
    from beamtime.query.conditions import parse_condition

    assert parse_condition(text) == expected


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("config.lr=", "no value after '='"),
        ("=3", "no field"),
        ('config.tag="1', "quote is not closed"),
        ("config.lr", "operators"),
    ],
)
def test_condition_errors(text: str, message: str) -> None:
    """Malformed conditions say what is missing."""
    from beamtime.query.conditions import parse_condition

    with pytest.raises(ValueError, match=message):
        parse_condition(text)


def test_condition_errors_name_the_flag() -> None:
    """The caller names the string in the message: ``--where`` by default, ``until`` for ``wait``."""
    from beamtime.query.conditions import parse_where

    with pytest.raises(ValueError, match="^--where 'x'"):
        parse_where(["x"])
    with pytest.raises(ValueError, match="^until 'x'"):
        parse_where(["x"], flag="until")


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
        "colormap: magma\ncolormap_diverging: RdBu\n"
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
    moved = [p for p in s.problems if "moved to the chart settings" in p]
    assert len(moved) == 2 and not any("unknown setting 'colormap" in p for p in s.problems)
    assert s.get("colormap") is None


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
    assert call("keys", {}, ctx)["runs"] == 47
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


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point HOME at an empty folder, so the setup's scan never reads the real one.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :return: The fake home."""
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.mark.usefixtures("fake_home")
def test_init_is_idempotent(ctx: Context, project: Path) -> None:
    """init writes beamtime.yaml and the .gitignore block once."""
    call("init", {"yes": True}, ctx)
    assert call("init", {"yes": True}, ctx)["lines"] == ["already set up"]
    assert (project / ".gitignore").read_text().count("# beamtime:") == 1
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


def test_source_add_list_rm(ctx: Context, project: Path) -> None:
    """Adding a remote writes the user settings by default; ``--command`` skips the ssh probe."""
    from beamtime.settings import user_settings_path

    added = call(
        "source add",
        {"name": "cluster", "remote": "login.hpc:/scratch/me/beamtime", "command": "bt"},
        ctx,
    )
    assert added["name"] == "cluster"
    assert user_settings_path().is_file()
    saved = load(project)
    assert saved.get("remotes")["cluster"] == {
        "host": "login.hpc",
        "path": "/scratch/me/beamtime",
        "command": "bt",
    }
    listed = call("source list", {}, ctx)
    assert ["cluster", "login.hpc", "/scratch/me/beamtime", "bt", None] in listed["rows"]
    call("source rm", {"name": "cluster"}, ctx)
    assert not (load(project).get("remotes") or {})
    with pytest.raises(OpError, match="no remote"):
        call("source rm", {"name": "cluster"}, ctx)


def test_source_add_to_the_project(ctx: Context, project: Path) -> None:
    """``--project`` writes to the project's ``beamtime.yaml`` instead of the user settings."""
    call("source add", {"name": "box", "remote": "h:/p", "command": "bt", "project": True}, ctx)
    text = (project / "beamtime.yaml").read_text()
    assert "box" in text and "remotes" in text
    assert load(project).get("remotes")["box"]["host"] == "h"


def test_source_add_keeps_the_file_and_checks_the_path(ctx: Context, project: Path) -> None:
    """Adding a remote to ``beamtime.yaml`` keeps its comments; a path that isn't absolute is
    refused."""
    (project / "beamtime.yaml").write_text("schema: 1\n# our cluster setup\nlogdir: beamtime\n")
    call("source add", {"name": "box", "remote": "h:/p", "command": "bt", "project": True}, ctx)
    text = (project / "beamtime.yaml").read_text()
    assert "# our cluster setup" in text and "logdir: beamtime" in text
    call("source rm", {"name": "box"}, ctx)
    assert "# our cluster setup" in (project / "beamtime.yaml").read_text()
    with pytest.raises(OpError, match="absolute"):
        call("source add", {"name": "x", "remote": "h:relative", "command": "bt"}, ctx)


def test_source_probe_expands_the_path_on_the_remote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The venv probe lets the remote shell expand ``~`` and ``${VAR}`` in the log dir's path."""
    import subprocess

    from beamtime.setup.remotes import probe_command

    home = tmp_path / "home"
    venv = home / "proj" / ".venv" / "bin" / "beamtime"
    venv.parent.mkdir(parents=True)
    (home / "proj" / "beamtime").mkdir()
    venv.write_text("#!/bin/sh\n")
    venv.chmod(0o755)
    real = subprocess.run

    def remote(argv: list[str], **kw) -> subprocess.CompletedProcess:
        # the last argument is the line ssh hands the remote shell; no beamtime on its PATH.
        line = argv[-1].replace("command -v beamtime", "false")
        env = {"HOME": str(home), "PROJ": str(home / "proj"), "PATH": "/usr/bin:/bin"}
        return real(["sh", "-c", line], env=env, **kw)

    monkeypatch.setattr(subprocess, "run", remote)
    assert probe_command("h", "~/proj/beamtime") == "~/proj/beamtime/../.venv/bin/beamtime"
    assert probe_command("h", "${PROJ}/beamtime") == "${PROJ}/beamtime/../.venv/bin/beamtime"
    assert probe_command("h", "/nowhere/beamtime") is None


@pytest.fixture
def launcher_on_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a fake ``beamtime`` with the serve extra first on ``PATH``.

    :param tmp_path: The test's temporary directory.
    :param monkeypatch: The environment patcher.
    :return: The fake launcher."""
    folder = tmp_path / "bin"
    folder.mkdir()
    script = folder / "beamtime"
    script.write_text('#!/bin/sh\necho "beamtime 0.3.0"\n')
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{folder}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    return script


@pytest.mark.skipif(sys.platform == "win32", reason="the fake launcher is a shell script")
def test_mcp_install_for_cursor(ctx: Context, project: Path, launcher_on_path: Path) -> None:
    """Cursor's project config gets a portable entry that names the workspace."""
    call("mcp install", {"client": "cursor"}, ctx)
    entry = json.loads((project / ".cursor" / "mcp.json").read_text())["mcpServers"]["beamtime"]
    assert entry == {"command": "beamtime", "args": ["--root", "${workspaceFolder}", "mcp"]}


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
    assert "3 of 47 runs" in render(call("runs", {"limit": 3}, ctx))


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
    from beamtime.serve.api import page_of

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
    with pytest.raises(Exception, match="colormap"):  # no longer a setting
        call("set", {"key": "colormap", "value": "magma"}, ctx)
    if pytest.importorskip("scienceplots"):
        with pytest.raises(OpError, match="unknown style"):
            call("set", {"key": "figure_style", "value": ["science", "nope"]}, ctx)


@pytest.mark.usefixtures("fake_home")
def test_instructions_block(project: Path) -> None:
    """init --instructions adds the agent rules as one marked block; a rerun replaces it."""
    from beamtime.guide.rules import END, START

    ctx = Context.make(caller="cli")
    (project / "AGENTS.md").write_text("# My rules\n\nBe brief.\n")
    call("init", {"instructions": True, "yes": True}, ctx)
    text = (project / "AGENTS.md").read_text()
    assert text.startswith("# My rules\n\nBe brief.\n") and text.count(START) == 1
    assert "`guide`" in text and "@<name>/<group>" in text
    stale = text.replace("Read `guide`", "Read the old guide")
    (project / "AGENTS.md").write_text(stale + "\nMine after.\n")
    lines = call("init", {"instructions": True, "yes": True}, ctx)["lines"]
    again = (project / "AGENTS.md").read_text()
    assert any("updated" in line for line in lines)
    assert again.count(START) == 1 and "Read `guide`" in again and again.endswith("Mine after.\n")
    assert again.index(END) < again.index("Mine after.")
    assert not any(
        "Agent rules" in line for line in call("init", {"instructions": True, "yes": True}, ctx)["lines"]
    )


@pytest.mark.skipif(sys.platform == "win32", reason="the fake launcher is a shell script")
def test_mcp_install_instructions_go_to_the_clients_file(
    ctx: Context, project: Path, launcher_on_path: Path
) -> None:
    """--instructions writes the generated block into the file the client reads."""
    from beamtime.guide.rules import START

    lines = call("mcp install", {"client": "gemini", "instructions": True}, ctx)["lines"]
    assert any("GEMINI.md" in line for line in lines)
    assert (project / "GEMINI.md").read_text().count(START) == 1
    assert not (project / "AGENTS.md").exists()
    assert (project / ".gemini" / "settings.json").is_file()


@pytest.mark.skipif(sys.platform == "win32", reason="the fake launcher is a shell script")
def test_init_and_mcp_install_work_without_a_local_log_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, launcher_on_path: Path, fake_home: Path
) -> None:
    """A project that has never logged a run yet (no local log dir) can still set up its
    instructions and register the MCP server; neither needs a source to exist."""
    import subprocess

    root = tmp_path / "proj"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    monkeypatch.chdir(root)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("BEAMTIME_CACHE", str(tmp_path / "cache"))
    monkeypatch.delenv("BEAMTIME_LOGDIR", raising=False)
    ctx = Context.make(caller="cli")
    assert not ctx.logdir.is_dir()

    init = call("init", {"instructions": True, "yes": True}, ctx)
    assert any("AGENTS.md" in line for line in init["lines"])
    assert "@<name>/<group>" in (root / "AGENTS.md").read_text()

    installed = call("mcp install", {"client": "cursor"}, ctx)
    config = json.loads((root / ".cursor" / "mcp.json").read_text())
    assert config["mcpServers"]["beamtime"]["args"] == ["--root", "${workspaceFolder}", "mcp"]
    assert not any("error" in line.lower() for line in installed["lines"])


def test_page_of_finds_an_unindexed_copy_and_suggests_a_group(
    ctx: Context, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run copied after the last index walk resolves by id; a typo'd group names the close one."""
    from beamtime.index.index import Index
    from beamtime.serve.api import page_of

    # a running daemon or a held lock makes the budgeted catch-up a no-op.
    monkeypatch.setattr(Index, "catch_up", lambda *a, **k: None)
    run = next(ctx.logdir.rglob("_run.json")).parent
    copy = ctx.logdir / "scaling" / "fresh" / new_run_id()
    copy.parent.mkdir(parents=True)
    shutil.copytree(run, copy)
    assert page_of(ctx, copy.name) == (copy.relative_to(ctx.logdir).as_posix(), copy.name)
    with pytest.raises(OpError, match=r"Did you mean 'lr-sweep'\?.*Top-level groups: ") as e:
        page_of(ctx, "scaling/lr-sweeps")
    assert e.value.code == 4


def test_page_of_opens_a_run_by_suffix_and_refuses_reserved_names(ctx: Context, roles: dict) -> None:
    """A run page opens by a unique id suffix of four characters or more; authored folders are no pages."""
    from beamtime.serve.api import page_of

    run = roles["killed"]
    path, found = page_of(ctx, run[-8:])
    assert found == run and path.endswith(run)
    assert page_of(ctx, path) == (path, run)
    with pytest.raises(OpError, match="authored or machine files") as e:
        page_of(ctx, "scaling/lr-sweep/proposal")
    assert e.value.code == 4


def test_find_run_takes_a_suffix_of_four_characters_or_more(ctx: Context, roles: dict) -> None:
    """Run arguments resolve like pages: id, unique suffix or name; a short suffix and a group are no run."""
    from beamtime.ops.reading import find_run

    run = roles["killed"]
    expected = find_run(ctx, run)
    assert expected.name == run
    assert find_run(ctx, run[-4:]) == expected
    call("name", {"run": run, "name": "warmup baseline"}, ctx)
    assert find_run(ctx, "warmup baseline") == expected
    for word in (run[-3:], "scaling", "../../etc/passwd"):
        with pytest.raises(OpError, match="no run") as e:
            find_run(ctx, word)
        assert e.value.code == 4


def test_find_run_without_index(ctx: Context, roles: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    """A run the index does not know yet (catch-up unavailable) is found by walking the tree."""
    from beamtime.index.index import Index
    from beamtime.ops.reading import find_run

    monkeypatch.setattr(Index, "catch_up", lambda *a, **k: None)
    monkeypatch.setattr(Index, "run_path", lambda *a, **k: None)
    assert find_run(ctx, roles["killed"]).name == roles["killed"]


SERIES = {"from": "scaling/lr-sweep", "y": ["train/loss"], "points": 20}
ENVELOPE = ("x", "y", "lo", "hi", "n")


@pytest.mark.parametrize("caller", ["cli", "mcp"])
@pytest.mark.parametrize("params", [SERIES, SERIES | {"by": ["config.lr"]}], ids=["runs", "by"])
def test_cli_and_mcp_series_carry_the_envelope_only(ctx: Context, caller: str, params: dict) -> None:
    """The CLI and MCP get y/lo/hi/n and none of last/min/max/count/mean."""
    context = dataclasses.replace(ctx, caller=caller)
    for got in (call("series", params, context), answer("series", params, context)):
        assert got["curves"]
        for curve in got["curves"]:
            assert all(k in curve for k in ENVELOPE)
            assert not set(OLD_CURVE_FIELDS) & set(curve)


def test_web_and_wire_series_keep_both(ctx: Context) -> None:
    """The web UI and a remote's answer (serve --stdio) keep the old fields next to the envelope."""
    by = SERIES | {"by": ["config.lr"]}
    for context in (
        dataclasses.replace(ctx, caller="view"),
        dataclasses.replace(ctx, caller="cli", wire=True),
        dataclasses.replace(ctx, caller="cli", wire=True, whole=True),
    ):
        plain, grouped = call("series", SERIES, context), call("series", by, context)
        assert all(set(OLD_CURVE_FIELDS[:4]) <= set(c) for c in plain["curves"])
        assert all({"mean", "y"} <= set(c) for c in grouped["curves"])


def test_the_page_fits_more_curves_without_the_old_fields(ctx: Context) -> None:
    """The strip comes before the cut: the same budget holds more curves than with both."""
    query = {"from": ".", "y": ["train/loss"], "points": 100}
    both = call("series", query, dataclasses.replace(ctx, wire=True))
    lean = call("series", query, ctx)
    assert both["meta"].get("cut") and lean["meta"].get("cut")
    assert len(lean["curves"]) > len(both["curves"])


def test_curve_line_reads_the_envelope() -> None:
    """One path over y, with the band from lo and hi when there is one."""
    from beamtime.cli.format import curve_line

    raw = {"run": "r1", "name": "alpha", "metric": "loss", "x": [0, 1, 2], "y": [3.0, 2.0, 1.0]}
    assert curve_line(raw).startswith("alpha  loss  first 3  min 1  max 3  last 1  ")
    binned = {
        "run": "r1", "metric": "loss", "x": [0, 1], "y": [2.0, 1.0],
        "lo": [1.5, 0.5], "hi": [3.0, 1.5], "n": [4, 4],
    }  # fmt: skip
    assert "min 0.5  max 3  last 1" in curve_line(binned)
    grouped = {
        "by": {"config.lr": 0.1}, "runs": ["a", "b"], "metric": "loss", "x": [0, 1],
        "y": [2.0, 1.0], "lo": [None, None], "hi": [None, None], "n": [2, 2],
    }  # fmt: skip
    line = curve_line(grouped)
    assert "min 1  max 2  last 1" in line and line.endswith("runs 2")
    assert curve_line(raw | {"y": [None]}).endswith("no data")


def test_last_logged_shows_as_its_age_in_text_only(ctx: Context, roles: dict[str, str]) -> None:
    """The CLI table shows ``run.last_logged`` as ``3m ago``; the answer keeps the epoch."""
    from beamtime.cli.format import ago

    now = 1_790_000_000.0
    assert ago(now - 5, now) == "5s ago"
    assert ago(now - 180, now) == "3m ago"
    assert ago(now - 2 * 3600 - 5, now) == "2h ago"
    assert ago(now - 4 * 86400, now) == "4d ago"
    assert ago(now + 30, now) == "0s ago"

    answer = call("runs", {"from": roles["resumed"], "select": ["run.id", "run.last_logged"]}, ctx)
    assert isinstance(answer["rows"][0][1], float)
    text = render(answer)
    assert " ago" in text and "e9" not in text
    assert table(["run.last_logged"], [[None]])[1] == "-"
