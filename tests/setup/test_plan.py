"""The answers of the setup: flags in, defaults from the scan, the command out."""

import dataclasses
import shlex
from pathlib import Path

import msgspec
import pytest
import yaml

from beamtime.cli import build_parser, params_of
from beamtime.ops.registry import InitParams
from beamtime.setup.plan import Answers, Remote, command, flags
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
