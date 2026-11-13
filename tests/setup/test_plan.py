"""The answers of the setup: flags in, defaults from the scan, the command out."""

import dataclasses
import json
import shlex
import shutil
import subprocess
from pathlib import Path

import msgspec
import pytest
import yaml

from beamtime.cli import build_parser, params_of
from beamtime.format.tree import iter_runs
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import InitParams
from beamtime.setup.apply import ApplyError, apply
from beamtime.setup.plan import Answers, Change, Remote, command, flags, plan, review
from beamtime.setup.scan import Scan, scan

DESK = {"DISPLAY": ":0", "PATH": ""}


def look(root: Path, home: Path, **env: str) -> Scan:
    """Scan a project with the fixture home and a desk environment.

    :param root: The project root.
    :param home: The fake home.
    :param env: Environment variables added to the desk's.
    :return: The scan."""
    return scan(root, home=home, mounts=Path("/nonexistent/mounts"), env={**DESK, **env})


def parse(argv: list[str], op: str = "init") -> InitParams:
    """Parse command line words the way the CLI does.

    :param argv: The words after ``beamtime``.
    :param op: The command.
    :return: The parameters of ``init``."""
    args = build_parser().parse_args(argv)
    return msgspec.convert(params_of(op, args), InitParams)


def repeat(text: str, s: Scan) -> Answers:
    """Run a printed command: parse it and fill the answers from it.

    :param text: The command as ``command()`` wrote it.
    :param s: The scan the defaults come from.
    :return: The answers it makes."""
    words = shlex.split(text.replace("\\\n", " "))
    assert words[:3] == ["beamtime", "init", "--yes"]
    return Answers.from_params(parse(words[1:]), s)


@pytest.fixture(params=["first", "teammate", "cluster", "update"])
def scene(request, tmp_path: Path, home: Path) -> Scan:
    """Build the scan of each scenario of the mockup.

    :param request: The scenario name.
    :param tmp_path: The test's temporary directory.
    :param home: The fake home.
    :return: The scan."""
    root = tmp_path / "project"
    root.mkdir()
    env = {}
    match request.param:
        case "first":
            pass
        case "teammate":
            (root / "beamtime.yaml").write_text(
                yaml.safe_dump({"logdir": "runs", "remotes": {"juwels": {"path": "/p"}}})
            )
        case "cluster":
            (tmp_path / "bin").mkdir()
            (tmp_path / "bin" / "sbatch").write_text("#!/bin/sh\n")
            (tmp_path / "bin" / "sbatch").chmod(0o755)
            env = {"PATH": str(tmp_path / "bin")}
        case "update":
            (root / "beamtime" / "g" / "r1").mkdir(parents=True)
            (root / "beamtime" / "g" / "r1" / "_run.json").write_text("{}")
    found = look(root, home, **env)
    assert found.flow == request.param
    return dataclasses.replace(found, stale=("rules", "mcp") if request.param == "update" else ())


def test_every_flag_parses() -> None:
    """Each flag of the spec's table lands in its field."""
    p = parse(
        [
            "init", "--runs", "both", "--logdir", "runs", "--link-logdir", "/scratch/x",
            "--remote", "a=u@h:/p", "--remote", "b", "--skip-remote", "c",
            "--install-remote", "a", "--ssh-share", "a", "--cache", "memory",
            "--agents", "claude-code,codex", "--agent-style", "hands-on",
            "--agent-set", "seeds=5,launch_runs=allowed", "--no-rules",
            "--import", "tb", "--import", "wandb", "--import-notes", "NOTES.md",
            "--import-memory", "mem", "--git", "none", "--sdk", "--role", "full",
            "--update", "rules,remote:a", "--migrate-with", "claude-code", "--check", "--yes",
        ]
    )  # fmt: skip
    assert p.runs == "both" and p.logdir == "runs" and p.link_logdir == "/scratch/x"
    assert p.remote == ["a=u@h:/p", "b"] and p.skip_remote == ["c"]
    assert p.install_remote == ["a"] and p.ssh_share == ["a"] and p.cache == "memory"
    assert p.agents == ["claude-code", "codex"] and p.agent_style == "hands-on"
    assert p.agent_set == ["seeds=5", "launch_runs=allowed"] and p.no_rules
    assert p.import_ == ["tb", "wandb"] and p.import_notes == ["NOTES.md"]
    assert p.import_memory == ["mem"] and p.git == "none" and p.sdk and p.role == "full"
    assert p.update == ["rules", "remote:a"] and p.migrate_with == "claude-code"
    assert p.check and p.yes
    assert parse(["init", "--no-agents", "--no-sdk"]).no_agents


def test_no_flags_leave_everything_open() -> None:
    """Without flags every field is unset, so the scan decides."""
    assert parse(["init"]) == InitParams()


def test_instructions_is_a_hidden_alias(capsys, scene: Scan) -> None:
    """``--instructions`` still parses, sets the rules, and is not in the help."""
    assert Answers.from_params(parse(["init", "--instructions"]), scene).rules
    with pytest.raises(SystemExit):
        build_parser().parse_args(["init", "--help"])
    out = capsys.readouterr().out
    assert "--instructions" not in out and "--no-rules" in out


def test_defaults_come_from_the_scan(scene: Scan) -> None:
    """The log dir and the stale items come from the scan; the rest is conservative."""
    a = Answers.from_params(parse(["init"]), scene)
    assert a == Answers.defaults(scene)
    assert a.logdir == ("runs" if scene.flow == "teammate" else "beamtime")
    assert a.update == list(scene.stale)
    assert (a.agents, a.imports, a.remotes, a.sdk, a.cache) == ([], [], [], False, None)
    assert command(a, scene) == "beamtime init --yes"


def test_logdir_outside_the_project(tmp_path: Path, home: Path) -> None:
    """A log dir outside the root stays an absolute path."""
    root = tmp_path / "project"
    root.mkdir()
    (root / "beamtime.yaml").write_text(f"logdir: {tmp_path / 'scratch'}\n")
    assert Answers.defaults(look(root, home)).logdir == str(tmp_path / "scratch")


def test_command_prints_only_differences(scene: Scan) -> None:
    """A changed answer is one flag; an answer that equals the default is not printed."""
    answers = Answers.from_params(parse(["init", "--git", "none", "--sdk"]), scene)
    assert flags(answers, scene) == ["--git none", "--sdk"]
    same = Answers.from_params(parse(["init", "--git", "record", "--runs", "here"]), scene)
    assert flags(same, scene) == []


def test_command_round_trips(scene: Scan) -> None:
    """Parsing the printed command gives the same answers, for every scenario."""
    argv = [
        "init", "--runs", "both", "--logdir", "my runs", "--link-logdir", "/scratch/my runs",
        "--remote", "juwels:${SCRATCH}/egnn", "--remote", "lab-gpu=jdoe@lab.example.org",
        "--remote", "a=u@h:/p x", "--skip-remote", "old", "--install-remote", "juwels",
        "--ssh-share", "juwels", "--cache", "/tmp/my cache", "--agents", "claude-code,codex",
        "--agent-style", "analysis", "--agent-set", "seeds=5,launch_runs=allowed", "--no-rules",
        "--import", "tb logs", "--import", "wandb", "--import-notes", "NOTES.md",
        "--import-memory", "mem", "--git", "none", "--sdk", "--role", "full",
        "--update", "rules,remote:juwels", "--migrate-with", "claude-code",
    ]  # fmt: skip
    answers = Answers.from_params(parse(argv), scene)
    assert answers != Answers.defaults(scene)
    assert repeat(command(answers, scene), scene) == answers


def test_round_trip_of_each_answer_alone(scene: Scan) -> None:
    """Each flag alone survives the trip, including those that undo a default."""
    for argv in (
        ["--no-agents"], ["--no-sdk"], ["--no-rules"], ["--update", ""], ["--logdir", "x"],
        ["--agents", "codex"], ["--sdk"], ["--agent-style", "careful"],
    ):  # fmt: skip
        answers = Answers.from_params(parse(["init", *argv]), scene)
        assert repeat(command(answers, scene), scene) == answers, argv


def test_no_flag_undoes_a_stale_default(scene: Scan) -> None:
    """With stale items, an empty update list is a flag of its own."""
    answers = Answers.from_params(parse(["init", "--update", ""]), scene)
    assert answers.update == []
    assert flags(answers, scene) == (["--update ''"] if scene.stale else [])


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("lab-gpu=jdoe@host", Remote("lab-gpu", "jdoe@host", None)),
        ("juwels:${SCRATCH}/x", Remote("juwels", None, "${SCRATCH}/x")),
        ("a=u@h:/p", Remote("a", "u@h", "/p")),
        ("a=u@h:~/p=1", Remote("a", "u@h", "~/p=1")),
        ("juwels:/a=b", Remote("juwels", None, "/a=b")),
        ("juwels", Remote("juwels")),
    ],
)
def test_remote_grammar(text: str, want: Remote) -> None:
    """``NAME[=HOST][:PATH]``: the first of ``=`` and ``:`` ends the name; the path starts with ``/~$``."""
    assert Remote.parse(text) == want
    assert Remote.parse(str(want)) == want


@pytest.mark.parametrize("text", ["", "=h", "a=", "a:rel/path", "a=h:rel", ":/p"])
def test_remote_grammar_errors(text: str) -> None:
    """A missing name or host and a relative path are refused."""
    with pytest.raises(ValueError, match="--remote"):
        Remote.parse(text)


def test_command_quotes(scene: Scan) -> None:
    """Paths with spaces and shell characters are quoted so the line runs as written."""
    answers = Answers.from_params(
        parse(["init", "--logdir", "my runs", "--import", "a b/$x", "--remote", "j:${SCRATCH}/x"]),
        scene,
    )
    text = command(answers, scene)
    assert "--logdir 'my runs'" in text
    assert "--import 'a b/$x'" in text
    assert "--remote 'j:${SCRATCH}/x'" in text
    assert text.startswith("beamtime init --yes \\\n  --")
    assert repeat(text, scene) == answers


@pytest.mark.parametrize(
    "argv",
    [
        ["--agents", "nobody"],
        ["--migrate-with", "nobody"],
        ["--agents", "codex", "--no-agents"],
        ["--sdk", "--no-sdk"],
        ["--agent-set", "seeds"],
        ["--agent-set", "colour=red"],
        ["--remote", "a:rel"],
        ["--update", "bogus"],
        ["--update", "rules,remote:"],
    ],
)
def test_contradictions_and_unknown_names(argv: list[str], scene: Scan) -> None:
    """Flags that contradict each other or name nothing known are refused."""
    with pytest.raises(ValueError):
        Answers.from_params(parse(["init", *argv]), scene)


CSV = Path(__file__).parent / "fixtures" / "csv"


def git_init(root: Path) -> None:
    """Make the project a git checkout.

    :param root: The project root."""
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)


def fingerprint(*roots: Path) -> dict[str, bytes | str]:
    """Record every file, folder and link below the roots, with contents and link targets.

    :param roots: The trees to hash.
    :return: Path to content, so equal trees compare equal."""
    out: dict[str, bytes | str] = {}
    for top in roots:
        for p in sorted(top.rglob("*")):
            if p.is_symlink():
                out[str(p)] = f"-> {p.readlink()}"
            elif p.is_file():
                out[str(p)] = p.read_bytes()
            else:
                out[str(p)] = "dir"
    return out


def uv_on_path(name: str) -> str | None:
    """Pretend that ``uv`` is installed and nothing else.

    :param name: The program asked for.
    :return: A fake path for ``uv``."""
    return "/usr/bin/uv" if name == "uv" else None


def make_plan(root: Path, home: Path, *argv: str, **env: str) -> list[Change]:
    """Scan a project and plan what the flags ask for.

    :param root: The project root.
    :param home: The fake home.
    :param argv: Flags of ``init``.
    :param env: Environment variables added to the desk's.
    :return: The changes."""
    s = look(root, home, **env)
    return plan(s, Answers.from_params(parse(["init", *argv]), s), which=uv_on_path)


@pytest.fixture
def project(project_tree: Path, home: Path) -> Path:
    """A git checkout of the fixture project.

    :param project_tree: The uv project.
    :param home: The fake home, so the scan never reads the real one.
    :return: The project root."""
    git_init(project_tree)
    return project_tree


def test_yes_writes_everything_in_order(project: Path, home: Path, tmp_path: Path) -> None:
    """One plan writes the project, the machine, the agents and the imports, in review order."""
    scratch = tmp_path / "scratch" / "bt"
    changes = make_plan(
        project, home, "--link-logdir", str(scratch), "--remote", "juwels=jdoe@login:~/egnn/bt",
        "--cache", "memory", "--agents", "claude-code", "--agent-style", "hands-on",
        "--agent-set", "seeds=5,main_metric=val/loss", "--import", str(CSV / "train.csv"),
    )  # fmt: skip
    assert [c.where for c in changes] == [
        "project", "project", "project", "machine", "project", "project", "project", "import"
    ]  # fmt: skip
    assert changes[0].label == "beamtime.yaml" and changes[-1].label.startswith("1 CSV")
    lines: list[str] = []
    apply(changes, lines.append)
    assert len(lines) == len(changes)

    given = yaml.safe_load((project / "beamtime.yaml").read_text())
    assert given["logdir"] == "beamtime" and given["remotes"] == {"juwels": {"path": "~/egnn/bt"}}
    assert given["agent"] == {"style": "hands-on", "seeds": 5, "main_metric": "val/loss"}
    mine = yaml.safe_load((home / ".config" / "beamtime" / "settings.yaml").read_text())
    assert mine["cache"] == "memory" and mine["remotes"] == {"juwels": {"host": "jdoe@login"}}
    assert (project / "beamtime").is_symlink() and scratch.is_dir()
    assert "/beamtime" in (project / ".git" / "info" / "exclude").read_text().splitlines()
    assert "beamtime/**/_*" in (project / ".gitignore").read_text()
    server = json.loads((project / ".mcp.json").read_text())["mcpServers"]["beamtime"]
    assert server["command"] == "uv"
    assert "Beamtime is the record" in (project / "CLAUDE.md").read_text()
    assert (project / ".claude" / "skills").is_dir()
    runs = list(iter_runs(scratch))
    assert len(runs) == 1 and "imported/" in str(runs[0])

    again = make_plan(
        project, home, "--link-logdir", str(scratch), "--remote", "juwels=jdoe@login:~/egnn/bt",
        "--cache", "memory", "--agents", "claude-code", "--agent-style", "hands-on",
        "--agent-set", "seeds=5,main_metric=val/loss",
    )  # fmt: skip
    assert again == []


def test_defaults_not_written(project: Path, home: Path) -> None:
    """With the defaults only the log dir and the ignore block are written, nothing on this machine."""
    changes = make_plan(project, home)
    assert [c.label for c in changes] == ["beamtime.yaml", ".gitignore"]
    apply(changes)
    given = yaml.safe_load((project / "beamtime.yaml").read_text())
    assert given == {"schema": 1, "logdir": "beamtime"}
    assert not (home / ".config").exists()
    assert make_plan(project, home) == []


def test_gitignore_upgrade(project: Path, home: Path) -> None:
    """An old ``beamtime/`` line becomes the marked block where it stood; a rerun and a switch keep one block."""
    (project / ".gitignore").write_text("node_modules/\nbeamtime/\n.env\n")
    apply(make_plan(project, home))
    lines = (project / ".gitignore").read_text().splitlines()
    assert lines[0] == "node_modules/" and lines[-1] == ".env"
    assert "beamtime/" not in lines and lines.count("beamtime/**/artifacts/") == 1
    assert lines.index("# end beamtime") < lines.index(".env")
    apply(make_plan(project, home, "--git", "none"))
    text = (project / ".gitignore").read_text()
    assert text.count("# beamtime:") == 1 and "beamtime/\n" in text and "**" not in text
    assert text.endswith(".env\n") and make_plan(project, home, "--git", "none") == []


def test_agent_values_are_checked_and_converted(project: Path, home: Path) -> None:
    """``--agent-set`` values follow the key's rule: numbers become numbers, bad ones are refused."""
    for pair, word in (("seeds=abc", "integer"), ("launch_runs=sometimes", "never"),
                       ("significance=1.5", "between 0 and 1"), ("seeds=0", "integer")):  # fmt: skip
        with pytest.raises(ValueError, match=f"--agent-set {pair}.*{word}"):
            make_plan(project, home, "--agent-set", pair)
    apply(make_plan(project, home, "--agent-set", "seeds=5,significance=0.9,seed_key=123"))
    agent = yaml.safe_load((project / "beamtime.yaml").read_text())["agent"]
    assert agent == {"style": "careful", "seeds": 5, "significance": 0.9, "seed_key": "123"}


def test_a_projects_own_agent_settings_stay(project: Path, home: Path) -> None:
    """Without a flag for the style the project's ``agent`` is kept, and the rules follow it."""
    (project / "beamtime.yaml").write_text(
        "schema: 1\nlogdir: beamtime\nagent:\n  style: analysis\n"
    )
    apply(make_plan(project, home, "--agents", "claude-code"))
    assert "style: analysis" in (project / "beamtime.yaml").read_text()
    assert "Never launch" not in (project / "CLAUDE.md").read_text()


def test_sdk_step(project: Path, home: Path) -> None:
    """The SDK step is left out when Beamtime is current, and planned when it is old or lacks serve."""
    from beamtime import __version__

    def sdk(*argv: str) -> list[Change]:
        return [c for c in make_plan(project, home, *argv) if "environment" in c.label]

    packages = project / ".venv" / "lib" / "python3.11" / "site-packages"
    shutil.rmtree(packages / "beamtime-0.2.0.dist-info")
    (packages / "beamtime-0.0.1.dist-info").mkdir()
    (change,) = sdk("--sdk")
    assert change.before == "beamtime 0.0.1" and "uv add beamtime" in change.after
    shutil.rmtree(packages / "beamtime-0.0.1.dist-info")
    (packages / f"beamtime-{__version__}.dist-info").mkdir()
    assert sdk("--sdk") == [] and sdk("--sdk", "--agents", "claude-code") == []
    shutil.rmtree(packages / "starlette-0.40.0.dist-info")
    assert sdk("--sdk") == []
    (change,) = sdk("--sdk", "--agents", "claude-code")
    assert "uv add --dev" in change.after and sdk() == []


def test_sdk_refusals(tmp_path: Path, home: Path) -> None:
    """``--sdk`` without an environment, or with an old Python, is refused with the reason."""
    root = tmp_path / "bare"
    root.mkdir()
    with pytest.raises(ValueError, match="no Python environment"):
        make_plan(root, home, "--sdk")
    (root / "pyproject.toml").write_text("[tool.uv]\n")
    (root / ".venv" / "lib" / "python3.8" / "site-packages").mkdir(parents=True)
    with pytest.raises(ValueError, match="3.10 or newer"):
        make_plan(root, home, "--sdk")


def test_apply_stops_at_the_first_failure() -> None:
    """The later changes don't run, and the error names what was done."""
    ran: list[str] = []

    def ok(name: str) -> Change:
        return Change(
            where="project", label=name, before=None, after=name, run=lambda: ran.append(name)
        )

    def broken() -> None:
        raise OSError("disk full")

    bad = Change(where="project", label="b", before=None, after="b", run=broken)
    lines: list[str] = []
    with pytest.raises(ApplyError, match="b: disk full") as caught:
        apply([ok("a"), bad, ok("c")], lines.append)
    assert ran == ["a"] and lines == ["a"]
    assert [c.label for c in caught.value.done] == ["a"] and caught.value.failed is bad


def test_a_failing_install_names_what_was_done(project: Path, home: Path, monkeypatch) -> None:
    """``init --yes`` stops at the failing SDK install; the earlier files stay and the answer says so."""

    def fail(command, **kw):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("beamtime.setup.sdk.subprocess.run", fail)
    packages = project / ".venv" / "lib" / "python3.11" / "site-packages"
    shutil.rmtree(packages / "beamtime-0.2.0.dist-info")
    ctx = Context.make(root=project, caller="cli")
    with pytest.raises(OpError, match=r"done: beamtime.yaml, \.gitignore"):
        call("init", {"sdk": True, "yes": True}, ctx)
    assert (project / "beamtime.yaml").is_file() and (project / ".gitignore").is_file()


def test_no_trace(scene: Scan, tmp_path: Path, home: Path) -> None:
    """Planning, the review without ``--yes`` and every refusal leave the project and home byte-identical."""
    root = scene.root
    before = fingerprint(root, home)
    link = [] if scene.flow == "update" else ["--link-logdir", str(tmp_path / "scratch")]
    argv = ["--agents", "other", "--cache", "memory", "--git", "none", "--remote", "j=h:~/x", *link]
    s = look(root, home)
    answers = Answers.from_params(parse(["init", *argv]), s)
    changes = plan(s, answers, which=uv_on_path)
    assert changes and "\n".join(review(changes))
    ctx = Context.make(root=root, caller="cli")
    out = call("init", {"agents": ["other"], "cache": "memory", "git": "none"}, ctx)
    assert any(line.startswith("Nothing was written.") for line in out["lines"])
    assert out["written"] == []
    assert any(line.startswith("beamtime init --yes") for line in out["lines"])
    for bad in ({"agent_set": ["seeds=abc"]}, {"import_": [str(tmp_path / "nope")]},
                {"sdk": True}):  # fmt: skip
        with pytest.raises(OpError):
            call("init", {**bad, "yes": True}, ctx)
    assert fingerprint(root, home) == before


def test_import_of_a_folder_in_a_log_dir_goes_through_its_root(
    project: Path, home: Path, tmp_path: Path
) -> None:
    """A group inside another project's log dir imports that log dir whole; a run goes alone; the project's own log dir is refused."""
    other = tmp_path / "other"
    (other / "beamtime" / "g").mkdir(parents=True)
    (other / "beamtime.yaml").write_text("logdir: beamtime\n")
    for name in ("r1", "r2"):
        run = other / "beamtime" / "g" / name
        run.mkdir()
        (run / "_run.json").write_text(json.dumps({"schema": 1, "id": name, "proposals": {}}))
        (run / "checkpoint.bin").write_bytes(b"x" * 2000)
    (other / "beamtime" / "h").mkdir()
    (other / "beamtime" / "h" / "r3").mkdir()
    (other / "beamtime" / "h" / "r3" / "_run.json").write_text('{"schema": 1, "id": "r3"}')

    (change,) = make_plan(project, home, "--import", str(other / "beamtime" / "g"))[-1:]
    assert "inside this log dir, so all of it is imported" in change.after
    assert "kB" in change.after and "byte for byte" in change.after
    assert change.label == "3 Beamtime runs"
    apply([change])
    names = {p.name for p in iter_runs(project / "beamtime" / "imported" / "other")}
    assert names == {"r1", "r2", "r3"}

    (change,) = make_plan(project, home, "--import", str(other / "beamtime" / "g" / "r1"))[-1:]
    assert "inside" not in change.after

    with pytest.raises(ValueError, match="own log dir"):
        make_plan(project, home, "--import", str(project / "beamtime" / "imported"))


def test_import_of_a_project_goes_through_its_log_dir(
    project: Path, home: Path, tmp_path: Path
) -> None:
    """A project folder imports its log dir, so groups keep their paths; this project is refused."""
    other = tmp_path / "other"
    (other / "runs" / "g" / "r1").mkdir(parents=True)
    (other / "beamtime.yaml").write_text("logdir: runs\n")
    (other / "runs" / "g" / "r1" / "_run.json").write_text('{"schema": 1, "id": "r1"}')

    (change,) = make_plan(project, home, "--import", str(other))[-1:]
    assert "is a project, so its log dir is imported" in change.after
    apply([change])
    runs = [p.relative_to(project / "beamtime") for p in iter_runs(project / "beamtime" / "imported")]
    assert runs == [Path("imported/other/g/r1")]

    with pytest.raises(ValueError, match="own log dir"):
        make_plan(project, home, "--import", str(project))


def test_notes_come_in_as_written_unless_an_agent_takes_them(project: Path, home: Path) -> None:
    """Notes files become notes after the log dir exists; ``--migrate-with`` leaves them to the agent."""
    (project / "NOTES.md").write_text("# Findings\n\nlr 1e-3 diverges.\n")
    assert not any(
        c.label == "notes"
        for c in make_plan(
            project, home, "--import-notes", "NOTES.md", "--migrate-with", "claude-code"
        )
    )
    changes = make_plan(project, home, "--import-notes", "NOTES.md")
    assert changes[-1].label == "notes" and changes[-1].after == "1 notes, as written"
    apply(changes)
    assert any(p.read_text().count("lr 1e-3") for p in (project / "beamtime").rglob("*.md"))


def test_review_groups_by_where(project: Path, home: Path) -> None:
    """The review names where each change lands and shows what was there before."""
    (project / ".gitignore").write_text("beamtime/\n")
    text = review(make_plan(project, home, "--cache", "memory", "--import", str(CSV / "train.csv")))
    assert [x for x in text if x and not x.startswith(" ")] == [
        "the project (shared through git)", "this machine", "imports"
    ]  # fmt: skip
    assert "    was: the log dir ignored as a whole" in text
