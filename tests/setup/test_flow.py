"""The wizard on a pseudo-terminal: the first setup on the mockup's project, key by key."""

import dataclasses
import os
import re
import shlex
import shutil
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import msgspec
import pytest
import yaml

from beamtime import __version__
from beamtime.cli import build_parser, params_of
from beamtime.guide.rules import write_block
from beamtime.ops.registry import SetupParams
from beamtime.setup.apply import apply
from beamtime.setup.flow import FirstSetup, fill, run, setup
from beamtime.setup.plan import Answers, Remote, command, plan
from beamtime.setup.remotes import Probe
from beamtime.setup.scan import Past, Scan, scan
from beamtime.setup.term import Term

from .test_importers import event, simple, start, write_events
from .test_stale import bin, look, old  # noqa: F401

ENTER, SPACE, DOWN, UP, CTRL_C = b"\r", b" ", b"\x1b[B", b"\x1b[A", b"\x03"
WHERE, LOGDIR, HOSTS = (
    "Where do your runs happen?",
    "Where should runs on this machine go?",
    "Which machines?",
)
AGENTS, STYLE = (
    "Which coding agents should know about Beamtime?",
    "How much should agents do on their own?",
)
RULES, IMPORT = "Tell agents that Beamtime is the record?", "Bring in past work?"
GIT, SDK = "Keep the research record in git?", "Add the Beamtime SDK to this project's environment?"
REVIEW = "Ready. Nothing has been written yet."
HANDOFF = "Hand the notes and memory to your agent now?"
posix = pytest.mark.skipif(sys.platform == "win32", reason="needs a pseudo-terminal")


def fake_which(name: str) -> str | None:
    """Find only ``uv``, so the MCP command is the project's own and no real program runs.

    :param name: The program.
    :return: A path for ``uv``, else ``None``."""
    return "/usr/bin/uv" if name == "uv" else None


def fake_probe(hosts: list[str], paths: dict[str, str | None] | None = None) -> dict[str, Probe]:
    """Answer for the mockup's machines: juwels has Beamtime and a gpfs scratch, lab-gpu has not.

    :param hosts: The ssh hosts.
    :param paths: The log dir per host.
    :return: One probe per host."""
    ok = Probe("juwels", "ok", command="beamtime", version="0.3.0", scratch=True, fstype="gpfs")
    bare = Probe("lab-gpu", "no_beamtime", python="3.12.1")
    return {h: ok if h == "juwels" else bare for h in hosts}


@dataclass
class Session:
    """What the wizard did on a pseudo-terminal."""

    value: object
    output: str
    stuck: str | None


def drive(call: Callable[[Term], object], script: list[tuple[str, bytes]]) -> Session:
    """Run the wizard on a pseudo-terminal; type each key group once its prompt is on the screen.

    :param call: Takes the terminal and runs the wizard.
    :param script: Pairs of a question's title to wait for and the keys to type then.
    :return: The result, the output, and what the script waited for in vain."""
    import pty
    import termios

    master, slave = pty.openpty()
    inp, out = os.fdopen(os.dup(slave), "r"), os.fdopen(os.dup(slave), "w")
    chunks = bytearray()
    stuck: list[str] = []

    def drain() -> None:
        while True:
            try:
                if not (data := os.read(master, 4096)):
                    return
            except OSError:
                return
            chunks.extend(data)

    def feed() -> None:
        pos = 0
        for expect, keys in script:
            deadline = time.monotonic() + 10
            while True:
                text = chunks.decode(errors="replace")
                at = text.find(f"◆  {expect}", pos)
                if at >= 0 and not termios.tcgetattr(slave)[3] & termios.ICANON:
                    break
                if time.monotonic() > deadline:
                    stuck.append(expect)
                    os.write(master, CTRL_C)
                    return
                time.sleep(0.005)
            pos = at + len(expect) + 3
            os.write(master, keys)

    threads = [
        threading.Thread(target=drain, daemon=True),
        threading.Thread(target=feed, daemon=True),
    ]
    for t in threads:
        t.start()
    value = call(Term(inp=inp, out=out, color=False, raw=True, width=110))
    threads[1].join(12)
    inp.close(), out.close(), os.close(slave)
    threads[0].join(2)
    os.close(master)
    return Session(value, chunks.decode().replace("\r\n", "\n"), stuck[0] if stuck else None)


def titles(output: str) -> list[str]:
    """List the questions the wizard answered, from its collapsed lines.

    :param output: What it printed.
    :return: The titles, in order."""
    found = re.findall(r"◇  ([^\n\r\x1b]+)", output)
    return [t for t in found if not t.startswith(("Looking around", "Checking", "Setting up"))]


def snapshot(*roots: Path) -> dict[str, bytes]:
    """Read every file below some folders.

    :param roots: The folders.
    :return: The bytes of each file by path."""
    return {
        str(p): p.read_bytes()
        for root in roots
        for p in sorted(root.rglob("*"))
        if p.is_file() and ".venv" not in p.parts
    }


def parse(words: list[str]) -> SetupParams:
    """Parse command line words the way the CLI does.

    :param words: The words after ``beamtime``.
    :return: The parameters of ``setup``."""
    return msgspec.convert(params_of("setup", build_parser().parse_args(words)), SetupParams)


def printed_command(output: str) -> list[str]:
    """Take the command the wizard printed from its output.

    :param output: What it printed.
    :return: Its words after ``beamtime``."""
    lines = output.split("This command makes the same setup:")[1].splitlines()
    text = " ".join(line.removeprefix("│  ") for line in lines if line.startswith("│  "))
    return shlex.split(text.replace("\\ ", " ").replace("\\", " "))[1:]


def make_project(base: Path, home: Path, path: str) -> Scan:
    """Build the mockup's first-setup project and scan it: a uv environment without Beamtime,
    Lightning, a SLURM script, TensorBoard and W&B runs, notes, Claude Code and codex, two ssh hosts.

    :param base: The folder the project goes in.
    :param home: The fake home, which gets the ssh config.
    :param path: The ``PATH`` of the machine.
    :return: The scan."""
    root = base / "egnn-md"
    (root / "jobs").mkdir(parents=True)
    (root / "train.py").write_text("import lightning as L\n")
    (root / "jobs" / "train.sbatch").write_text("#SBATCH --nodes=1\nrsync -a out/ juwels:r/\n")
    (root / "pyproject.toml").write_text("[project]\nname = 'egnn'\n[tool.uv]\n")
    (root / ".venv" / "lib" / "python3.12" / "site-packages").mkdir(parents=True)
    for version in ("version_0", "version_1"):
        file = root / "lightning_logs" / version / "events.out.tfevents.1700000000.host"
        write_events(file, start(1.7e9), event(1.7e9, 1, simple("val/loss", 0.5)))
    for name in ("offline-run-20260105_101500-a1b2c3d4", "offline-run-20260106_080000-e5f6a7b8"):
        (root / "wandb" / name).mkdir(parents=True)
        (root / "wandb" / name / "run.wandb").write_bytes(b"")
    (root / "NOTES.md").write_text("# Notes\nresults so far\n")
    (root / "notebook").mkdir()
    (root / "notebook" / "a.md").write_text("one\n")
    (root / "notebook" / "b.md").write_text("two\n")
    (root / "CLAUDE.md").write_text("Keep results in NOTES.md.\n")
    (root / ".claude").mkdir()
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "config").write_text("Host juwels\n  User jdoe\nHost lab-gpu\n")
    return scan(root, home=home, mounts=Path("/nonexistent"), env={"DISPLAY": ":0", "PATH": path})


@pytest.fixture
def egnn(tmp_path: Path, home: Path, tools) -> Scan:
    """The mockup's project in the test's folder.

    :param tmp_path: The test's temporary directory.
    :param home: The fake home.
    :param tools: Makes a ``PATH`` of fake programs.
    :return: The scan."""
    return make_project(tmp_path, home, tools("codex"))


def beamtime_logdir(tmp_path: Path) -> Path:
    """Make another project's log dir with one run, as the index cache would know it.

    :param tmp_path: The test's temporary directory.
    :return: The log dir."""
    other = tmp_path / "egnn-v1"
    (other / "beamtime" / "g" / "r1").mkdir(parents=True)
    (other / "beamtime.yaml").write_text("logdir: beamtime\n")
    (other / "beamtime" / "g" / "r1" / "_run.json").write_text("{}")
    return other / "beamtime"


# the keys of the first setup with every default taken, to the review.
TO_REVIEW = [
    (WHERE, ENTER),
    (LOGDIR, ENTER),
    (HOSTS, ENTER),
    ("Where do runs go on juwels?", ENTER),
    (AGENTS, ENTER),
    (STYLE, ENTER),
    (RULES, ENTER),
    (IMPORT, ENTER),
    (GIT, ENTER),
    (SDK, ENTER),
]


def first(
    egnn: Scan, script: list[tuple[str, bytes]], answers: Answers | None = None
) -> tuple[Session, Answers]:
    """Run the first setup's questions on a terminal, with the fake probe and the fake ``which``.

    :param egnn: The scan.
    :param script: The keys.
    :param answers: The starting answers; by default those of no flag.
    :return: The session and the answers it filled."""
    answers = answers or Answers.defaults(egnn)
    done = drive(lambda t: run(t, egnn, answers, probe=fake_probe, which=fake_which), script)
    return done, answers


@posix
def test_questions_in_order_with_the_mockups_defaults(egnn: Scan, tmp_path: Path) -> None:
    """Enter through every question asks the mockup's questions in order and prefills what was found."""
    other = beamtime_logdir(tmp_path)
    found = dataclasses.replace(egnn, past=(*egnn.past, Past(found=_found(other), other=True)))
    answers = Answers.defaults(found)
    done = drive(
        lambda t: run(t, found, answers, probe=fake_probe, which=fake_which),
        [*TO_REVIEW, (REVIEW, DOWN + DOWN + ENTER)],
    )
    assert done.stuck is None and done.value is None
    assert titles(done.output)[:10] == [
        WHERE,
        LOGDIR,
        HOSTS,
        "Where do runs go on juwels?",
        AGENTS,
        STYLE,
        RULES,
        IMPORT,
        GIT,
        SDK,
    ]
    assert answers.runs == "both" and answers.logdir == "beamtime"
    assert answers.remotes == [Remote("juwels", None, "${SCRATCH}/egnn-md/beamtime")]
    assert answers.agents == ["claude-code", "codex"] and answers.agent_style == "careful"
    assert answers.rules and answers.git == "record" and answers.sdk
    assert answers.imports == ["lightning_logs/", "wandb/"]
    assert answers.import_notes == ["NOTES.md", "notebook/"]
    assert [p for p in answers.imports if "egnn-v1" in p] == []
    out = done.output
    for line in ("Set up Beamtime for ", "Nothing is written until you confirm", "Looking around"):
        assert line in out
    assert "beamtime is not installed there" in out and "juwels · lab-gpu" in out.replace("  ", " ")
    assert "CLAUDE.md line 1" in out and "1 Beamtime run" in out
    for group in ("the project (shared through git)", "this machine", "imports"):
        assert group in out.split(REVIEW)[1]


def _found(path: Path):
    """Detect a Beamtime log dir.

    :param path: The log dir.
    :return: What it holds."""
    from beamtime.setup.importers import detect

    found = detect(path)
    assert found is not None
    return found


@posix
def test_show_the_command_makes_the_same_answers(egnn: Scan) -> None:
    """The printed command, parsed back, gives the answers the prompts gave."""
    done, answers = first(egnn, [*TO_REVIEW, (REVIEW, DOWN + DOWN + ENTER)])
    assert done.stuck is None and done.value is None
    assert "Nothing was written. This command makes the same setup:" in done.output
    again = Answers.from_params(parse(printed_command(done.output)), egnn)
    assert again == answers


@posix
def test_change_an_answer_keeps_the_later_answers(egnn: Scan) -> None:
    """Changing one answer asks the later questions again, each starting on its earlier answer."""
    script = [
        *TO_REVIEW[:-1],
        (SDK, b"2" + ENTER),
        (REVIEW, DOWN + ENTER),
        ("Which answer?", b"9" + ENTER),
        (GIT, b"2" + ENTER),
        (SDK, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = first(egnn, script)
    assert done.stuck is None
    assert answers.git == "none" and not answers.sdk
    assert titles(done.output).count(SDK) == 2 and titles(done.output).count(WHERE) == 1
    assert answers.agents == ["claude-code", "codex"]


@posix
def test_no_agents(egnn: Scan) -> None:
    """Choosing None for agents skips the agent questions."""
    script = [
        (WHERE, ENTER),
        (LOGDIR, ENTER),
        (HOSTS, ENTER),
        ("Where do runs go on juwels?", ENTER),
        (AGENTS, SPACE + DOWN + SPACE + DOWN * 7 + ENTER),
        (IMPORT, ENTER),
        (GIT, ENTER),
        (SDK, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = first(egnn, script)
    assert done.stuck is None
    assert answers.agents == []
    assert STYLE not in titles(done.output) and RULES not in titles(done.output)
    assert "Agent settings" not in titles(done.output)


@posix
def test_remote_only(egnn: Scan) -> None:
    """Runs on other machines only skips the log dir question."""
    script = [
        (WHERE, b"2" + ENTER),
        (HOSTS, ENTER),
        ("Where do runs go on juwels?", ENTER),
        (AGENTS, ENTER),
        (STYLE, ENTER),
        (RULES, ENTER),
        (IMPORT, ENTER),
        (GIT, ENTER),
        (SDK, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = first(egnn, script)
    assert done.stuck is None and answers.runs == "remote"
    assert LOGDIR not in titles(done.output) and HOSTS in titles(done.output)


@posix
def test_install_and_path_per_machine(egnn: Scan) -> None:
    """A second machine without Beamtime asks to install it, then where its runs go."""
    script = [
        (WHERE, ENTER),
        (LOGDIR, ENTER),
        (HOSTS, DOWN + SPACE + ENTER),
        ("Where do runs go on juwels?", ENTER),
        ("Install Beamtime on lab-gpu?", ENTER),
        ("Where do runs go on lab-gpu?", ENTER),
        (AGENTS, ENTER),
        (STYLE, ENTER),
        (RULES, ENTER),
        (IMPORT, ENTER),
        (GIT, ENTER),
        (SDK, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = first(egnn, script)
    assert done.stuck is None
    assert answers.remotes == [
        Remote("juwels", None, "${SCRATCH}/egnn-md/beamtime"),
        Remote("lab-gpu", None, "~/egnn-md/beamtime"),
    ]
    assert answers.install_remotes == ["lab-gpu"]
    assert "✓ ssh  ✗ beamtime not found" in done.output and "${SCRATCH} is gpfs" in done.output
    assert "beamtime[serve]==" in done.output
    assert "other machines" in done.output.split(REVIEW)[-1]


@pytest.mark.parametrize("where", [WHERE, AGENTS, IMPORT, REVIEW])
@posix
def test_abort_leaves_no_trace(egnn: Scan, home: Path, where: str) -> None:
    """Ctrl-c at any question, the review included, writes nothing."""
    before = snapshot(egnn.root, home)
    asked = [t for t, _ in TO_REVIEW]
    script = [*TO_REVIEW[: asked.index(where) if where in asked else len(asked)], (where, CTRL_C)]
    done, _ = first(egnn, script)
    assert done.stuck is None and done.value is None
    assert done.output.rstrip().endswith("Nothing was written.")
    assert snapshot(egnn.root, home) == before


def tree(root: Path, home: Path) -> dict[str, str]:
    """Read a project and its home as text, with their own paths made alike.

    Imported runs and notes carry random ids, so they are counted instead of compared.

    :param root: The project.
    :param home: The home.
    :return: The text of each file by path below its folder, and the counts."""
    out: dict[str, str] = {}
    for base, name in ((root, "root"), (home, "home")):
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(base).as_posix()
            if (
                not p.is_file()
                or ".venv" in p.parts
                or "imported" in p.parts
                or ".cache" in p.parts
                or "/notes/" in f"/{rel}"
            ):
                continue
            out[f"{name}/{rel}"] = (
                p.read_text(errors="replace").replace(str(root), "ROOT").replace(str(home), "HOME")
            )
    out["runs"] = str(len(list(root.rglob("_run.json"))))
    out["notes"] = str(len(list(root.glob("*/notes/*"))))
    return out


@posix
def test_write_it_gives_the_files_of_the_command(
    egnn: Scan, tmp_path: Path, home: Path, tools, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Write it makes the same files as ``setup --yes`` with the command the review prints."""
    keys = [(t, b"2" + ENTER if t == SDK else k) for t, k in TO_REVIEW]
    answers = Answers.defaults(egnn)
    wrote = drive(
        lambda t: setup(t, egnn, answers, probe=fake_probe, which=fake_which),
        [*keys, (REVIEW, ENTER), (HANDOFF, DOWN + ENTER)],
    )
    assert wrote.stuck is None and "Beamtime is set up." in wrote.output
    assert "Run it later:  beamtime setup --migrate-with claude-code" in wrote.output
    assert (egnn.root / "beamtime.yaml").is_file() and (home / ".codex" / "config.toml").is_file()

    twin_home = tmp_path / "twin-home"
    twin = make_project(tmp_path / "twin", twin_home, tools("codex"))
    monkeypatch.setenv("HOME", str(twin_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(twin_home / ".config"))
    words = shlex.split(command(answers, egnn).replace("\\\n", " "))
    assert words[:3] == ["beamtime", "setup", "--yes"]
    apply(plan(twin, Answers.from_params(parse(words[1:]), twin), which=fake_which))
    assert tree(twin.root, twin_home) == tree(egnn.root, home)
    assert int(tree(twin.root, twin_home)["runs"]) >= 2


def test_existing_agent_style_is_the_default(tmp_path: Path, home: Path) -> None:
    """What the project's ``beamtime.yaml`` already holds is the preselected answer."""
    root = tmp_path / "p"
    root.mkdir()
    (root / "beamtime.yaml").write_text(
        yaml.safe_dump({"agent": {"style": "hands-on", "seeds": 5, "main_metric": "val/loss"}})
    )
    found = scan(root, home=home, mounts=Path("/nonexistent"), env={"DISPLAY": ":0", "PATH": ""})
    answers = Answers.defaults(found)
    fill(found, answers)
    assert answers.agent_style == "hands-on"
    assert answers.agent_set == {"seeds": "5"}
    assert FirstSetup().steps()


class Picks:
    """A terminal that answers ``select`` with one choice and ``form`` with its start values."""

    def __init__(self, choice: str) -> None:
        """Keep the choice.

        :param choice: What ``select`` answers."""
        self.choice = choice
        self.start: dict[str, str] = {}

    def select(self, *args: object, **kwargs: object) -> str:
        """Answer with the choice.

        :return: The choice."""
        return self.choice

    def form(self, title: str, rows: object, start: dict[str, str]) -> dict[str, str]:
        """Take the start values as they are.

        :param title: The form's title.
        :param rows: The rows.
        :param start: The values it starts on.
        :return: The start values."""
        self.start = dict(start)
        return start

    def paint(self, role: str, text: str) -> str:
        """Leave text uncolored.

        :param role: The color role.
        :param text: The text.
        :return: The text."""
        return text


@pytest.fixture
def hands_on(tmp_path: Path, home: Path) -> Scan:
    """A project whose ``beamtime.yaml`` says hands-on, five seeds and a main metric.

    :param tmp_path: The test's temporary directory.
    :param home: The fake home.
    :return: The scan."""
    root = tmp_path / "p"
    root.mkdir()
    (root / "beamtime.yaml").write_text(
        yaml.safe_dump({"agent": {"style": "hands-on", "seeds": 5, "main_metric": "val/loss"}})
    )
    return scan(root, home=home, mounts=Path("/nonexistent"), env={"DISPLAY": ":0", "PATH": ""})


def written_agent(found: Scan, answers: Answers) -> dict:
    """Apply the plan of the answers and read back the project's ``agent``.

    :param found: The scan.
    :param answers: The answers.
    :return: The ``agent`` mapping in ``beamtime.yaml``."""
    apply(plan(found, answers, which=fake_which))
    return yaml.safe_load((found.root / "beamtime.yaml").read_text())["agent"]


def same_command(found: Scan, answers: Answers) -> bool:
    """Say whether the printed command makes the same answers.

    :param found: The scan.
    :param answers: The answers.
    :return: ``True`` when they are equal."""
    words = shlex.split(command(answers, found).replace("\\\n", " "))
    return Answers.from_params(parse(words[1:]), found) == answers


@pytest.mark.parametrize("style", ["careful", "analysis"])
def test_another_preset_is_written_and_drops_overrides(hands_on: Scan, style: str) -> None:
    """Picking another preset writes it without the old single keys; the conventions stay."""
    answers = Answers.defaults(hands_on)
    assert (answers.agent_style, answers.agent_set) == ("hands-on", {"seeds": "5"})
    FirstSetup().ask_style(Picks(style), answers, hands_on)
    assert same_command(hands_on, answers)
    assert written_agent(hands_on, answers) == {"style": style, "main_metric": "val/loss"}


@pytest.mark.parametrize("style", ["careful", "analysis"])
def test_agent_style_flag_is_written(hands_on: Scan, style: str) -> None:
    """``--agent-style`` on a hands-on project writes that preset, as the wizard does."""
    answers = Answers.from_params(SetupParams(agent_style=style, yes=True), hands_on)
    assert answers.agent_set == {}
    assert written_agent(hands_on, answers) == {"style": style, "main_metric": "val/loss"}


def test_each_setting_starts_from_the_projects_values(hands_on: Scan) -> None:
    """``Choose each setting`` starts on hands-on's values with the project's seeds."""
    answers = Answers.defaults(hands_on)
    setup = FirstSetup()
    picks = Picks("custom")
    setup.ask_style(picks, answers, hands_on)
    setup.ask_tune(picks, answers, hands_on)
    assert picks.start["launch_runs"] == "allowed" and picks.start["seeds"] == "5"
    assert (answers.agent_style, answers.agent_set) == ("hands-on", {"seeds": "5"})
    agent = {"style": "hands-on", "seeds": 5, "main_metric": "val/loss"}
    assert written_agent(hands_on, answers) == agent


def test_tune_form_has_a_proposal_length_row(hands_on: Scan) -> None:
    """``Choose each setting`` asks for the proposal length, and ``--agent-set`` plans it."""
    answers = Answers.defaults(hands_on)
    picks = Picks("custom")
    FirstSetup().ask_tune(picks, answers, hands_on)
    assert picks.start["proposal_words"] == "150 words"
    assert "proposal_words" not in answers.agent_set
    params = SetupParams(agent_set=["proposal_words=300"], yes=True)
    answers = Answers.from_params(params, hands_on)
    assert answers.agent_set["proposal_words"] == "300"
    assert written_agent(hands_on, answers)["proposal_words"] == 300


def test_a_dropped_override_returns_to_the_preset(hands_on: Scan) -> None:
    """A single key set back to the preset leaves the file and the command alike."""
    answers = Answers.defaults(hands_on)
    answers.agent_set = {}
    assert same_command(hands_on, answers)
    assert written_agent(hands_on, answers) == {"style": "hands-on", "main_metric": "val/loss"}


def test_typed_subfolder_reads_as_its_log_dir(tmp_path: Path, home: Path) -> None:
    """A typed folder inside another log dir offers that log dir's runs and name, as the review."""
    other = beamtime_logdir(tmp_path)
    (other / "g" / "sub" / "r2").mkdir(parents=True)
    (other / "g" / "sub" / "r2" / "_run.json").write_text("{}")
    root = tmp_path / "p"
    root.mkdir()
    found = scan(root, home=home, mounts=Path("/nonexistent"), env={"DISPLAY": ":0", "PATH": ""})
    row = FirstSetup().check_path(str(other / "g" / "sub"), found, False)
    assert row.label == "2 Beamtime runs"
    assert "imported/egnn-v1 " in row.hint


def test_over_a_pipe_without_raw_keys(tmp_path: Path, home: Path) -> None:
    """The numbered fallback runs the whole wizard: questions, writing and next steps."""
    root = tmp_path / "plain"
    root.mkdir()
    found = scan(root, home=home, mounts=Path("/nonexistent"), env={"DISPLAY": ":0", "PATH": ""})
    out = StringIO()
    term = Term(inp=StringIO("\n" * 20), out=out, color=False, raw=False)
    written = setup(term, found, Answers.defaults(found), which=fake_which)
    assert "beamtime.yaml" in written
    assert (root / "beamtime.yaml").is_file()
    assert "Beamtime is set up." in out.getvalue()
    assert "beamtime proposal set" in out.getvalue()


class Tty(StringIO):
    """A stream that says it is a terminal."""

    def isatty(self) -> bool:
        """Claim to be a terminal.

        :return: ``True``."""
        return True


def test_setup_asks_only_on_a_terminal_for_a_first_setup(
    tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``setup`` runs the wizard for a first setup on a terminal without ``--yes``, else not."""
    from beamtime.ops.admin import setup
    from beamtime.ops.context import Context

    root = tmp_path / "p"
    root.mkdir()
    seen: list[str] = []
    monkeypatch.setattr(
        "beamtime.setup.flow.setup",
        lambda term, found, answers, **kw: seen.append(found.flow) or [],
    )
    ctx = Context.make(root=root)
    setup(ctx, SetupParams())
    assert seen == []
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", Tty())
    setup(ctx, SetupParams(yes=True))
    assert seen == [] and (root / "beamtime.yaml").exists()
    (root / "beamtime.yaml").unlink()
    setup(ctx, SetupParams())
    assert seen == ["first"]


MATE_AGENTS = "Which coding agents do you use on this machine?"
MATE_HOSTS = "Which of the project's machines do you use?"
MATE_SSH, MATE_REACH = "Log in to juwels once per session?", "How do you reach lab-gpu?"
LAB = "jdoe@lab-gpu.physik.example.org"


def mate_probe(hosts: list[str], paths: dict[str, str | None] | None = None) -> dict[str, Probe]:
    """Answer for the teammate's machines: juwels asks for a code, any other host is fine.

    :param hosts: The ssh hosts.
    :param paths: The log dir per host.
    :return: One probe per host."""
    code = Probe("juwels", "needs_code", detail="Permission denied (keyboard-interactive)")
    fine = Probe("lab-gpu", "ok", command="beamtime", version="0.3.0")
    return {h: code if h == "juwels" else fine for h in hosts}


def make_mate(base: Path, home: Path, path: str, env: dict[str, str] | None = None) -> Scan:
    """Build the mockup's teammate project: the team's files, two remotes, and Cursor on this machine.

    :param base: The folder the project goes in.
    :param home: The fake home, which gets an ssh config with juwels only.
    :param path: The ``PATH`` of the machine.
    :param env: More environment variables of the machine.
    :return: The scan."""
    from beamtime.guide.rules import render, write_block
    from beamtime.ops.registry import OPS
    from beamtime.settings import resolve_agent
    from beamtime.setup.plan import gitignore_text

    root = base / "egnn-md"
    root.mkdir()
    team = {
        "logdir": "beamtime",
        "agent": {"style": "careful"},
        "remotes": {
            "juwels": {"path": "${SCRATCH}/egnn-md/beamtime"},
            "lab-gpu": {"path": "~/egnn-md/beamtime"},
        },
    }
    (root / "beamtime.yaml").write_text(yaml.safe_dump(team, sort_keys=False))
    (root / "pyproject.toml").write_text("[project]\nname = 'egnn'\n[tool.uv]\n")
    (root / ".venv" / "lib" / "python3.12" / "site-packages").mkdir(parents=True)
    (root / ".mcp.json").write_text('{"mcpServers": {"beamtime": {"command": "uv"}}}')
    (root / ".gitignore").write_text(gitignore_text("", "beamtime", "record"))
    user_only = sorted(o.name for o in OPS if o.user_only)
    write_block(root / "AGENTS.md", render(resolve_agent({"style": "careful"}), user_only))
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "config").write_text("Host juwels\n  User jdoe\n")
    machine = {"DISPLAY": ":0", "PATH": path, **(env or {})}
    return scan(root, home=home, mounts=Path("/nonexistent"), env=machine)


@pytest.fixture
def mate(tmp_path: Path, home: Path, tools) -> Scan:
    """The teammate's project in the test's folder, with Cursor installed and unregistered.

    :param tmp_path: The test's temporary directory.
    :param home: The fake home.
    :param tools: Makes a ``PATH`` of fake programs.
    :return: The scan."""
    return make_mate(tmp_path, home, tools("cursor"))


def team(
    scan: Scan, script: list[tuple[str, bytes]], answers: Answers | None = None
) -> tuple[Session, Answers]:
    """Run the questions of the scan's flow on a terminal, with the teammate's fake probe.

    :param scan: The scan.
    :param script: The keys.
    :param answers: The starting answers; by default those of no flag.
    :return: The session and the answers it filled."""
    answers = answers or Answers.defaults(scan)
    done = drive(lambda t: run(t, scan, answers, probe=mate_probe, which=fake_which), script)
    return done, answers


MATE_KEYS = [
    (MATE_AGENTS, ENTER),
    (MATE_HOSTS, ENTER),
    (MATE_SSH, ENTER),
    (MATE_REACH, LAB.encode() + ENTER),
]


@posix
def test_teammate_asks_the_machines_part_only(mate: Scan) -> None:
    """A project with beamtime.yaml and two remotes asks agents, remotes, how to reach, ssh sharing."""
    assert mate.flow == "teammate"
    done, answers = team(mate, [*MATE_KEYS, (REVIEW, CTRL_C)])
    assert done.stuck is None
    assert titles(done.output) == [MATE_AGENTS, MATE_HOSTS, MATE_SSH, MATE_REACH]
    assert answers.agents == ["cursor"]
    assert answers.remotes == [Remote("juwels"), Remote("lab-gpu", LAB)]
    assert answers.ssh_share == ["juwels"] and answers.skip_remotes == []
    out = done.output
    assert "This project uses Beamtime already. Only this machine's part is left." in out
    assert "lab-gpu is not there" not in out and "no such host here" in out
    assert "needs a password or code" in out and "ControlMaster auto" in out
    review = out.split(REVIEW)[1]
    assert "beamtime.yaml  unchanged" in review and "this machine" in review
    assert "remotes.lab-gpu" in review and f"host: {LAB}" in review.replace("'", "")
    assert "MCP server for Cursor" in review and "AGENTS.md" not in review
    labels = [c.label for c in plan(mate, answers, which=fake_which)]
    assert "beamtime.yaml" not in labels and ".gitignore" not in labels
    assert answers.rules and "AGENTS.md" not in labels


@posix
def test_teammate_show_the_command_makes_the_same_answers(mate: Scan) -> None:
    """The command printed in the teammate flow, parsed back, gives the answers of the prompts."""
    done, answers = team(mate, [*MATE_KEYS, (REVIEW, DOWN + DOWN + ENTER)])
    assert done.stuck is None and done.value is None
    again = Answers.from_params(parse(printed_command(done.output)), mate)
    assert again == answers
    assert "--ssh-share juwels" in done.output and f"--remote lab-gpu={LAB}" in done.output


@posix
def test_teammate_skips_what_the_person_leaves_out(mate: Scan) -> None:
    """An empty way to reach a host, and Skip at the ssh question, leave both remotes out."""
    script = [
        (MATE_AGENTS, SPACE + ENTER),
        (MATE_HOSTS, ENTER),
        (MATE_SSH, DOWN + DOWN + ENTER),
        (MATE_REACH, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = team(mate, script)
    assert done.stuck is None
    assert answers.agents == [] and answers.remotes == [] and answers.ssh_share == []
    assert answers.skip_remotes == ["juwels", "lab-gpu"]
    again = Answers.from_params(
        parse(["setup", "--yes", "--no-agents", "--skip-remote", "juwels", "--skip-remote", "lab-gpu"]),
        mate,
    )
    assert again == answers


@posix
def test_teammate_shows_the_ssh_lines_then_asks_again(mate: Scan) -> None:
    """Show them prints the block and asks the same question again."""
    script = [
        (MATE_AGENTS, ENTER),
        (MATE_HOSTS, ENTER),
        (MATE_SSH, DOWN + ENTER),
        (MATE_SSH, ENTER),
        (MATE_REACH, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = team(mate, script)
    assert done.stuck is None and answers.ssh_share == ["juwels"]
    assert "ControlPersist 12h" in done.output.split("yourself, any time:")[1]


@posix
def test_teammate_adds_a_host_of_their_own(mate: Scan) -> None:
    """A typed host is the person's own: it goes to their settings and is probed like the others."""
    script = [
        (MATE_AGENTS, ENTER),
        (MATE_HOSTS, DOWN + DOWN + ENTER + b"me@box.example.org" + ENTER + ENTER),
        (MATE_SSH, DOWN + DOWN + ENTER),
        (MATE_REACH, LAB.encode() + ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = team(mate, script)
    assert done.stuck is None
    assert answers.remotes == [Remote("lab-gpu", LAB), Remote("box", "me@box.example.org")]
    assert answers.skip_remotes == ["juwels"]


@posix
def test_teammate_abort_leaves_no_trace(mate: Scan, home: Path) -> None:
    """Ctrl-c at any question of the teammate flow, the review included, writes nothing."""
    before = snapshot(mate.root, home)
    for at in range(len(MATE_KEYS) + 1):
        script = [*MATE_KEYS[:at], (REVIEW if at == len(MATE_KEYS) else MATE_KEYS[at][0], CTRL_C)]
        done, _ = team(mate, script)
        assert done.stuck is None and done.output.rstrip().endswith("Nothing was written.")
        assert snapshot(mate.root, home) == before


@posix
def test_teammate_writes_only_this_machine(mate: Scan, home: Path, monkeypatch) -> None:
    """Writing it changes the user settings and the agent's config, and not one file of the team."""
    shared = snapshot(mate.root)
    answers = Answers.defaults(mate)
    done = drive(
        lambda t: setup(t, mate, answers, probe=mate_probe, which=fake_which),
        [*MATE_KEYS[:2], (MATE_SSH, DOWN + DOWN + ENTER), *MATE_KEYS[3:], (REVIEW, ENTER)],
    )
    assert done.stuck is None
    mine = yaml.safe_load((home / ".config" / "beamtime" / "settings.yaml").read_text())
    assert mine["remotes"]["lab-gpu"]["host"] == LAB
    assert mine["remotes"]["juwels"] == {"enabled": False}
    assert (mate.root / ".cursor" / "mcp.json").is_file()
    changed = {k for k, v in snapshot(mate.root).items() if shared.get(k) != v}
    assert changed == {str(mate.root / ".cursor" / "mcp.json")}
    assert "Beamtime is set up on this machine." in done.output
    assert "beamtime serve --open" in done.output


@posix
def test_teammate_for_a_missing_registration_only(tmp_path: Path, home: Path, tools) -> None:
    """With the remotes in the user settings, an unregistered agent alone starts the flow."""
    mine = home / ".config" / "beamtime"
    mine.mkdir(parents=True)
    (mine / "settings.yaml").write_text(
        yaml.safe_dump({"remotes": {"juwels": {"host": "juwels"}, "lab-gpu": {"host": LAB}}})
    )
    found = make_mate(tmp_path, home, tools("cursor"))
    assert found.flow == "teammate"
    script = [(MATE_AGENTS, ENTER), (MATE_HOSTS, ENTER), (MATE_SSH, ENTER), (REVIEW, CTRL_C)]
    done, answers = team(found, script)
    assert done.stuck is None and answers.agents == ["cursor"]
    assert answers.remotes == [Remote("juwels"), Remote("lab-gpu")]
    assert "Checking 2 machines" in done.output and MATE_REACH not in titles(done.output)
    assert titles(done.output) == [MATE_AGENTS, MATE_HOSTS, MATE_SSH]


@posix
def test_teammate_keeps_a_team_that_ignores_the_whole_log_dir(
    tmp_path: Path, home: Path, tools
) -> None:
    """A .gitignore that keeps the whole log dir out stays as the team wrote it."""
    from beamtime.setup.plan import gitignore_text

    found = make_mate(tmp_path, home, tools("cursor"))
    (found.root / ".gitignore").write_text(gitignore_text("", "beamtime", "none"))
    done, answers = team(found, [*MATE_KEYS, (REVIEW, CTRL_C)])
    assert answers.git == "none"
    assert ".gitignore" not in [c.label for c in plan(found, answers, which=fake_which)]


def test_a_team_file_without_log_dir_or_agent_stays_unchanged(tmp_path: Path, home: Path, tools) -> None:
    """A beamtime.yaml that names remotes only stays as it is, whatever agents the person picks."""
    found = make_mate(tmp_path, home, tools("cursor"))
    remotes = {"remotes": {"juwels": {"path": "/p"}}}
    (found.root / "beamtime.yaml").write_text(yaml.safe_dump(remotes))
    answers = Answers.defaults(found)
    answers.agents = ["cursor"]
    assert "beamtime.yaml" not in [c.label for c in plan(found, answers, which=fake_which)]


CL_ROLE, CL_RUNS = "What should this machine do?", "Where should runs go on this cluster?"
CL_CACHE = "Keep an index on this cluster between connections?"
CL_AGENTS = "Which coding agents run on this node?"
SCRATCH_LINK = "${SCRATCH}/egnn-md/beamtime"


def make_cluster(base: Path, home: Path, path: str) -> Scan:
    """Build the mockup's cluster checkout: beamtime.yaml from git, sbatch, nfs home, scratch.

    :param base: The folder the project goes in.
    :param home: The fake home, which is on nfs.
    :param path: The ``PATH`` of the node.
    :return: The scan."""
    root = base / "egnn-md"
    root.mkdir()
    (root / "beamtime.yaml").write_text("logdir: beamtime\n")
    (root / ".gitignore").write_text("beamtime/**/_*\n")
    scratch = base / "scratch"
    scratch.mkdir()
    mounts = base / "mounts"
    mounts.write_text(
        f"/dev/sda1 / ext4 rw 0 0\nserver:/h {home.resolve()} nfs4 rw 0 0\n"
        f"gpfs0 {scratch.resolve()} gpfs rw 0 0\n"
    )
    env = {"PATH": path, "SCRATCH": str(scratch)}
    return scan(root, home=home, mounts=mounts, env=env)


@pytest.fixture
def cluster(tmp_path: Path, home: Path, tools, monkeypatch: pytest.MonkeyPatch) -> Scan:
    """The cluster checkout in the test's folder, with sbatch and Claude Code on ``PATH``.

    :param tmp_path: The test's temporary directory.
    :param home: The fake home.
    :param tools: Makes a ``PATH`` of fake programs.
    :param monkeypatch: The environment patcher, for ``$SCRATCH``.
    :return: The scan."""
    monkeypatch.setenv("SCRATCH", str(tmp_path / "scratch"))
    return make_cluster(tmp_path, home, tools("sbatch", "claude"))


def on_cluster(
    scan: Scan, script: list[tuple[str, bytes]], answers: Answers | None = None
) -> tuple[Session, Answers]:
    """Run the cluster questions on a terminal.

    :param scan: The scan.
    :param script: The keys.
    :param answers: The starting answers; by default those of no flag.
    :return: The session and the answers it filled."""
    answers = answers or Answers.defaults(scan)
    return drive(lambda t: run(t, scan, answers, which=fake_which), script), answers


@posix
def test_cluster_recording_asks_role_link_and_cache(cluster: Scan) -> None:
    """Role record asks the link and the cache, and no agents, and the project file is unchanged."""
    assert cluster.flow == "cluster"
    done, answers = on_cluster(
        cluster, [(CL_ROLE, ENTER), (CL_RUNS, ENTER), (CL_CACHE, ENTER), (REVIEW, CTRL_C)]
    )
    assert done.stuck is None
    assert titles(done.output) == [CL_ROLE, CL_RUNS, CL_CACHE]
    assert answers.role == "record" and answers.agents == [] and answers.cache is None
    assert answers.link_logdir == SCRATCH_LINK
    out = done.output
    assert "This looks like a cluster login node. Setup here is short." in out
    assert "SLURM (sbatch)" in out and "no browser" not in out and "$HOME is nfs4" in out
    review = out.split(REVIEW)[1]
    assert "log dir link" in review and "beamtime.yaml  unchanged" in review


@posix
def test_cluster_full_asks_agents_too(cluster: Scan) -> None:
    """Role full adds the agents, starting on the one found, and the cache can go to local disk."""
    script = [
        (CL_ROLE, DOWN + ENTER),
        (CL_RUNS, DOWN + ENTER),
        (CL_CACHE, DOWN + ENTER),
        (CL_AGENTS, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = on_cluster(cluster, script)
    assert done.stuck is None
    assert titles(done.output) == [CL_ROLE, CL_RUNS, CL_CACHE, CL_AGENTS]
    assert answers.role == "full" and answers.agents == ["claude-code"]
    assert answers.link_logdir is None and answers.cache == "/tmp/{user}/beamtime-cache"


@posix
def test_cluster_another_place_for_runs(cluster: Scan) -> None:
    """Another place asks for the path and links it."""
    script = [
        (CL_ROLE, ENTER),
        (CL_RUNS, DOWN + DOWN + ENTER),
        ("Where?", b"/p/project/egnn" + ENTER),
        (CL_CACHE, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = on_cluster(cluster, script)
    assert done.stuck is None and answers.link_logdir == "/p/project/egnn"


@posix
@pytest.mark.parametrize("role", [ENTER, DOWN + ENTER])
def test_cluster_show_the_command_makes_the_same_answers(cluster: Scan, role: bytes) -> None:
    """The cluster flow's printed command, parsed back, gives the answers of the prompts."""
    script = [
        (CL_ROLE, role),
        (CL_RUNS, ENTER),
        (CL_CACHE, DOWN + ENTER),
        *([(CL_AGENTS, ENTER)] if role != ENTER else []),
        (REVIEW, DOWN + DOWN + ENTER),
    ]
    done, answers = on_cluster(cluster, script)
    assert done.stuck is None and done.value is None
    again = Answers.from_params(parse(printed_command(done.output)), cluster)
    assert again == answers
    assert f"--link-logdir '{SCRATCH_LINK}'" in done.output


@posix
def test_cluster_abort_leaves_no_trace(cluster: Scan, home: Path) -> None:
    """Ctrl-c at any cluster question writes nothing."""
    before = snapshot(cluster.root, home)
    keys = [(CL_ROLE, ENTER), (CL_RUNS, ENTER), (CL_CACHE, ENTER)]
    for at in range(len(keys) + 1):
        script = [*keys[:at], (REVIEW if at == len(keys) else keys[at][0], CTRL_C)]
        done, _ = on_cluster(cluster, script)
        assert done.stuck is None and done.output.rstrip().endswith("Nothing was written.")
        assert snapshot(cluster.root, home) == before


@posix
def test_cluster_writes_the_link_and_the_cache(cluster: Scan, home: Path, tmp_path: Path) -> None:
    """Writing it links the log dir to scratch and sets the cache, and leaves beamtime.yaml alone."""
    team_file = (cluster.root / "beamtime.yaml").read_bytes()
    answers = Answers.defaults(cluster)
    script = [(CL_ROLE, ENTER), (CL_RUNS, ENTER), (CL_CACHE, DOWN + ENTER), (REVIEW, ENTER)]
    done = drive(lambda t: setup(t, cluster, answers, which=fake_which), script)
    assert done.stuck is None
    link = cluster.root / "beamtime"
    assert link.is_symlink() and link.resolve() == (tmp_path / "scratch" / "egnn-md" / "beamtime").resolve()
    mine = yaml.safe_load((home / ".config" / "beamtime" / "settings.yaml").read_text())
    assert mine["cache"] == "/tmp/{user}/beamtime-cache" and "remotes" not in mine
    assert (cluster.root / "beamtime.yaml").read_bytes() == team_file
    assert "Beamtime is set up on this cluster." in done.output
    assert "beamtime source add " in done.output and "Jobs need no change" in done.output


def test_setup_asks_on_a_terminal_for_a_teammate_and_a_cluster(
    tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """``setup`` runs the wizard for a teammate and a cluster too, on a terminal and without --yes."""
    from beamtime.ops.admin import setup
    from beamtime.ops.context import Context

    seen: list[str] = []
    monkeypatch.setattr(
        "beamtime.setup.flow.setup",
        lambda term, found, answers, **kw: seen.append(found.flow) or [],
    )
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", Tty())
    monkeypatch.setenv("PATH", tools("cursor"))
    root = make_mate(tmp_path, home, tools("cursor")).root
    setup(Context.make(root=root), SetupParams())
    assert seen == ["teammate"]
    monkeypatch.setenv("PATH", tools("cursor", "sbatch"))
    setup(Context.make(root=root), SetupParams())
    assert seen == ["teammate", "cluster"]


UPDATES = f"What should be brought up to {__version__}?"


def old_probe(hosts: list[str], paths: dict[str, str | None] | None = None) -> dict[str, Probe]:
    """Answer for the update project's machine: juwels has Beamtime 0.1.1.

    :param hosts: The ssh hosts.
    :param paths: The log dir per host.
    :return: One probe per host."""
    return {h: Probe(h, "ok", command="beamtime", version="0.1.1") for h in hosts}


@pytest.fixture
def upgrade(old: Path, home: Path) -> Scan:
    """The project set up with 0.1.1 (the ``old`` fixture), and a remote juwels this machine knows.

    :param old: The project root.
    :param home: The fake home.
    :return: The scan."""
    (old / "beamtime.yaml").write_text(
        "schema: 1\ncolormap: viridis\nremotes:\n  juwels:\n    path: /p/scratch/egnn/beamtime\n"
    )
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "config").write_text("Host juwels\n  User jdoe\n")
    (home / ".config" / "beamtime").mkdir(parents=True)
    (home / ".config" / "beamtime" / "settings.yaml").write_text("remotes:\n  juwels: {}\n")
    return look(old, home)


def refresh(scan_: Scan, script: list[tuple[str, bytes]], **kw) -> tuple[Session, Answers]:
    """Run the questions of the update on a terminal with the old remote's probe.

    :param scan_: The scan.
    :param script: The keys.
    :return: The session and the answers it filled."""
    answers = Answers.defaults(scan_)
    done = drive(lambda t: run(t, scan_, answers, probe=old_probe, which=fake_which, **kw), script)
    return done, answers


def plan_of(scan_: Scan, answers: Answers) -> list[tuple[str, str, str | None, str]]:
    """Reduce a plan to what it shows: where, label, before, after.

    :param scan_: The scan.
    :param answers: The answers.
    :return: One tuple per change."""
    return [(c.where, c.label, c.before, c.after) for c in plan(scan_, answers, which=fake_which)]


@posix
def test_update_asks_what_is_stale_then_what_is_new(upgrade: Scan) -> None:
    """The data check, the ticked list with a remote the probe found old, then style and rules."""
    assert upgrade.flow == "update"
    done, answers = refresh(
        upgrade, [(UPDATES, ENTER), (STYLE, ENTER), (RULES, ENTER), (REVIEW, CTRL_C)]
    )
    assert done.stuck is None
    out = done.output
    assert "its setup is from 0.1.1." in out and "Only what surrounds them is updated." in out
    assert "read as they are" in out and "! beamtime 0.1.1" in out
    assert titles(out) == [UPDATES, STYLE, RULES]
    assert "remote:juwels" in answers.update
    assert answers.update == ["rules", "mcp", "skills", "settings", "sdk", "remote:juwels"]
    assert answers.imports == ["runs-old/"] and answers.agents == ["claude-code"]
    assert "+ Add a path" in out and "New since your setup" in out
    review = out.split(REVIEW)[1]
    assert review.index("your data  nothing is rewritten") < review.index("beamtime.yaml")
    assert "kept as they are" not in review
    assert "pip install --user" in review and "colormap" in review


@posix
def test_update_lists_what_was_unticked_as_kept(upgrade: Scan) -> None:
    """An unticked item is not planned, even where a chosen agent would plan it again."""
    untick = DOWN + DOWN + SPACE + DOWN + DOWN + DOWN + DOWN + SPACE + UP
    done, answers = refresh(
        upgrade, [(UPDATES, untick + ENTER), (STYLE, ENTER), (RULES, ENTER), (REVIEW, CTRL_C)]
    )
    assert done.stuck is None
    assert answers.update == ["rules", "mcp", "settings", "sdk"]
    review = done.output.split(REVIEW)[1]
    assert "kept as they are  Claude Code skills · Beamtime on juwels" in review
    labels = [label for _, label, _, _ in plan_of(upgrade, answers)]
    assert ".claude/skills/" not in labels and "juwels" not in labels and "Agent rules in CLAUDE.md" in labels


@posix
def test_update_keeps_a_rules_block_edited_by_hand(upgrade: Scan, home: Path) -> None:
    """A hand-edited block starts unticked and stays as it is, whatever the agent answers say."""
    write_block(upgrade.root / "CLAUDE.md", "Written by hand.")
    found = look(upgrade.root, home)
    done, answers = refresh(
        found, [(UPDATES, ENTER), (STYLE, ENTER), (RULES, ENTER), (REVIEW, CTRL_C)]
    )
    assert done.stuck is None and "rules" not in answers.update and answers.rules
    assert "kept as they are  Agent rules" in done.output.split(REVIEW)[1]
    assert not [c for c in plan_of(found, answers) if "CLAUDE.md" in c[1]]


@posix
def test_update_command_makes_the_same_plan(upgrade: Scan) -> None:
    """The printed ``beamtime setup --yes`` command, parsed back, plans what the screens plan."""
    untick = DOWN + DOWN + SPACE + DOWN
    keys = [(UPDATES, untick + ENTER), (STYLE, DOWN + ENTER), (RULES, ENTER)]
    done, answers = refresh(upgrade, [*keys, (REVIEW, DOWN + DOWN + ENTER)])
    assert done.stuck is None and done.value is None
    assert "kept as they are  Claude Code skills" in done.output.split(REVIEW)[1]
    again = Answers.from_params(parse(printed_command(done.output)), upgrade)
    assert again.update == answers.update and again.imports == answers.imports
    assert plan_of(upgrade, again) == plan_of(upgrade, answers) != []
    assert "--agent-style hands-on" in done.output and "remote:juwels" in done.output


@posix
def test_update_abort_leaves_no_trace(upgrade: Scan, home: Path) -> None:
    """Ctrl-c at any question of the update, the review included, writes nothing."""
    before = snapshot(upgrade.root, home)
    keys = [(UPDATES, ENTER), (STYLE, ENTER), (RULES, ENTER)]
    for at in range(len(keys) + 1):
        script = [*keys[:at], (REVIEW if at == len(keys) else keys[at][0], CTRL_C)]
        done, _ = refresh(upgrade, script)
        assert done.stuck is None and done.output.rstrip().endswith("Nothing was written.")
        assert snapshot(upgrade.root, home) == before


@posix
def test_update_writes_and_ends_with_what_changed(
    upgrade: Scan, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Writing it brings the project up to date, leaves the data alone and lists the changes."""
    import beamtime

    def upgraded(commands: list[list[str]], root: Path, requirements: Path | None) -> None:
        packages = root / ".venv" / "lib" / "python3.11" / "site-packages"
        shutil.rmtree(packages / "beamtime-0.1.1.dist-info")
        (packages / f"beamtime-{__version__}.dist-info").mkdir()

    monkeypatch.setattr("beamtime.setup.sdk.install", upgraded)
    monkeypatch.setattr(beamtime, "__version__", "0.3.0", raising=False)
    untick = DOWN * 6 + SPACE + UP
    answers = Answers.defaults(upgrade)
    done = drive(
        lambda t: setup(t, upgrade, answers, probe=old_probe, which=fake_which),
        [
            ("What should be brought up to 0.3.0?", untick + ENTER),
            (STYLE, ENTER),
            (RULES, ENTER),
            (REVIEW, ENTER),
        ],
    )
    assert done.stuck is None
    root = upgrade.root
    assert "colormap" not in (root / "beamtime.yaml").read_text()
    assert "Written by hand" not in (root / "CLAUDE.md").read_text()
    assert (root / "beamtime" / "imported").is_dir() and (root / "runs-old").is_dir()
    out = done.output
    assert "Beamtime 0.3.0 is set up. Nothing in beamtime/ was rewritten." in out
    assert "Changed since 0.1.1, where you may notice it" in out
    assert "The setup command is now `beamtime setup`; `init` is gone." in out
    assert "Agents read the new rules from their next session on." in out
    assert [s.item for s in look(root, home).stale] == []


def test_setup_asks_on_a_terminal_for_an_update(
    upgrade: Scan, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``setup`` runs the wizard for an update on a terminal, and plans from the flags without one."""
    from beamtime.ops.admin import setup as operation
    from beamtime.ops.context import Context

    seen: list[str] = []
    monkeypatch.setattr(
        "beamtime.setup.flow.setup",
        lambda term, found, answers, **kw: seen.append(found.flow) or [],
    )
    context = Context.make(root=upgrade.root)
    operation(context, SetupParams())
    assert seen == []
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", Tty())
    operation(context, SetupParams())
    assert seen == ["update"]


class Said(Picks):
    """A terminal that records what ``select`` offered and what was said."""

    def __init__(self, choice: str = "later") -> None:
        """Keep the choice.

        :param choice: What ``select`` answers."""
        super().__init__(choice)
        self.options: list[tuple[str, str]] = []
        self.lines: list[str] = []

    def select(self, title: str, options: list, default: str, *args: object, **kwargs: object) -> str:
        """Record the rows and the default, and answer with the choice.

        :param title: The question.
        :param options: The rows.
        :param default: The row the cursor starts on.
        :return: The choice."""
        self.options = [(o.value, o.label) for o in options]
        self.default = default
        return self.choice

    def say(self, lines: list[str]) -> None:
        """Record lines.

        :param lines: The lines."""
        self.lines += lines


@pytest.fixture
def handover(tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch) -> Scan:
    """A set-up project with a notes file and an instruction that keeps results in it.

    :param tmp_path: The test's temporary directory.
    :param home: The fake home.
    :param monkeypatch: Puts the project's folder in as the working directory.
    :return: The scan."""
    root = tmp_path / "p"
    root.mkdir()
    (root / "beamtime.yaml").write_text("logdir: beamtime\n")
    (root / "NOTES.md").write_text("# Notes\nresults so far\n")
    (root / "CLAUDE.md").write_text("Keep results in NOTES.md.\n")
    monkeypatch.chdir(root)
    return scan(root, home=home, mounts=Path("/nonexistent"), env={"PATH": ""})


def on_path(*names: str) -> Callable[[str], str | None]:
    """Find only the named programs.

    :param names: The programs that exist.
    :return: A ``which``."""
    return lambda name: f"/bin/{name}" if name in names else None


def test_start_command_per_client() -> None:
    """Claude Code gets the slash command, Codex and Gemini a sentence, editors nothing."""
    from beamtime.setup.agents import client_named, start_command

    paths = ["NOTES.md", "notebook/"]
    claude = start_command(client_named("claude-code"), paths, "CLAUDE.md:1")
    assert claude == ["claude", "/beamtime:migrate NOTES.md notebook/ CLAUDE.md:1"]
    codex = start_command(client_named("codex"), paths)
    assert codex == ["codex", "Run the beamtime migrate prompt with paths NOTES.md notebook/"]
    gemini = start_command(client_named("gemini"), [], "CLAUDE.md:1")
    assert gemini == ["gemini", "-i", "Run the beamtime migrate prompt and conflict CLAUDE.md:1"]
    assert start_command(client_named("cursor"), paths) is None


def test_hand_off_start_replaces_the_process(
    handover: Scan, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Start calls ``os.execvp`` with the client's command, the paths and the conflict."""
    from beamtime.setup.flow import hand_off

    called: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(os, "execvp", lambda file, args: called.append((file, args)))
    term = Said("claude-code")
    answers = Answers(logdir="beamtime", agents=["claude-code", "cursor"], import_notes=["NOTES.md"])
    hand_off(term, handover, answers, which=on_path("claude"))
    assert called == [("claude", ["claude", "/beamtime:migrate NOTES.md CLAUDE.md:1"])]
    assert term.options == [
        ("claude-code", "Start Claude Code now"),
        ("copy", "Copy the prompt"),
        ("later", "Later"),
    ]
    assert term.default == "claude-code"


def test_hand_off_offers_start_only_for_an_installed_agent(handover: Scan) -> None:
    """Without the agent's program on ``PATH`` the rows are copy and later, copy first."""
    from beamtime.setup.flow import hand_off

    term = Said("later")
    answers = Answers(logdir="beamtime", agents=["claude-code"], import_notes=["NOTES.md"])
    hand_off(term, handover, answers, which=on_path())
    assert [v for v, _ in term.options] == ["copy", "later"] and term.default == "copy"
    assert term.lines == ["Run it later:  beamtime setup --migrate-with claude-code"]


def test_hand_off_copy_uses_the_first_clipboard_tool(
    handover: Scan, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Copy runs the first of pbcopy, wl-copy, xclip and clip that exists, else prints the prompt."""
    from beamtime.setup import flow

    sent: list[tuple[list[str], bytes]] = []
    monkeypatch.setattr(
        flow.subprocess, "run", lambda cmd, input, check: sent.append((cmd, input))
    )
    answers = Answers(logdir="beamtime", agents=["cursor"], import_notes=["NOTES.md"])
    term = Said("copy")
    flow.hand_off(term, handover, answers, which=on_path("xclip", "clip"))
    text = "Run the beamtime migrate prompt with paths NOTES.md and conflict CLAUDE.md:1"
    assert sent == [(["/bin/xclip", "-selection", "clipboard"], text.encode())]
    assert term.lines == ["The migrate prompt is on your clipboard."]
    term = Said("copy")
    flow.hand_off(term, handover, answers, which=on_path())
    assert len(sent) == 1 and f"  {text}" in term.lines


def test_hand_off_asks_nothing_without_an_agent_or_without_work(handover: Scan) -> None:
    """No agent, or neither notes nor a conflict to hand over, means no question."""
    from beamtime.setup.flow import hand_off

    class Never(Said):
        def select(self, *args: object, **kwargs: object) -> str:
            raise AssertionError("asked")

    hand_off(Never(), handover, Answers(logdir="beamtime", import_notes=["NOTES.md"]))
    clean = dataclasses.replace(handover, conflicts=())
    hand_off(Never(), clean, Answers(logdir="beamtime", agents=["claude-code"]))
    first = dataclasses.replace(handover, flow="first")
    hand_off(Never(), first, Answers(logdir="beamtime", agents=["claude-code"], rules=False))


def test_wizard_leaves_notes_to_the_agent_and_asks_after_the_write(
    handover: Scan, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With an agent the review does not write the notes as they are; the command says why."""
    from beamtime.setup import flow
    from beamtime.setup.flow import Step

    (handover.root / "beamtime.yaml").unlink()
    found = scan(handover.root, home=handover.home, mounts=Path("/nonexistent"), env={"PATH": ""})
    answers = Answers.defaults(found)
    answers.agents, answers.import_notes = ["claude-code"], ["NOTES.md"]
    monkeypatch.setattr(flow, "intro", lambda *a: None)
    idle = Step(id="idle", title="idle", ask=lambda *a: None, when=lambda *a: False)
    final = flow.run(Said("write"), found, answers, steps=[idle], which=fake_which)
    assert final is not None and final.migrate_with == "claude-code"
    assert "notes" not in [c.label for c in plan(found, final, which=fake_which)]
    assert "--migrate-with claude-code" in command(final, found)


def test_migrate_with_goes_straight_to_the_agent(
    handover: Scan, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``ask=False`` starts the named agent without a question."""
    from beamtime.setup.flow import hand_off

    called: list[list[str]] = []
    monkeypatch.setattr(os, "execvp", lambda file, args: called.append(args))
    answers = Answers(logdir="beamtime", migrate_with="codex")
    hand_off(Never := Said("nothing"), handover, answers, ask=False, which=on_path("codex"))
    assert called == [["codex", "Run the beamtime migrate prompt with paths NOTES.md and conflict CLAUDE.md:1"]]
    assert Never.options == []


def test_migrate_with_alone_skips_the_wizard(
    handover: Scan, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """In a set-up project, ``--migrate-with`` hands over at once on a terminal and names the command without."""
    from beamtime.ops.admin import setup as operation
    from beamtime.ops.context import Context

    monkeypatch.setenv("PATH", tools())
    seen: list[tuple[str, bool]] = []
    monkeypatch.setattr(
        "beamtime.setup.flow.hand_off",
        lambda term, found, answers, ask, which=None: seen.append((answers.migrate_with, ask)),
    )
    monkeypatch.setattr(
        "beamtime.setup.flow.setup", lambda *a, **kw: seen.append(("wizard", True)) or []
    )
    context = Context.make(root=handover.root)
    params = SetupParams(migrate_with="claude-code")
    out = operation(context, params)
    assert seen == [] and out["lines"] == [
        "to hand the notes and memory to Claude Code, run: claude "
        "'/beamtime:migrate NOTES.md CLAUDE.md:1'"
    ]
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", Tty())
    operation(context, params)
    assert seen == [("claude-code", False)]


def set_up(root: Path, home: Path, path: str, *words: str) -> Scan:
    """Set a project up with ``beamtime setup --yes`` and the words, and scan it again.

    :param root: The project root.
    :param home: The fake home.
    :param path: The ``PATH`` of the machine.
    :param words: The flags.
    :return: The scan of the set-up project."""
    env = {"DISPLAY": ":0", "PATH": path}
    (home / ".ssh").mkdir(parents=True, exist_ok=True)
    (home / ".ssh" / "config").write_text("Host juwels\n  User jdoe\n")
    first = scan(root, home=home, mounts=Path("/nonexistent"), env=env)
    answers = Answers.from_params(parse(["setup", "--yes", *words]), first)
    apply(plan(first, answers, which=fake_which), lambda text: None)
    return scan(root, home=home, mounts=Path("/nonexistent"), env=env)


@pytest.fixture
def current(project_tree: Path, home: Path, tools) -> Scan:
    """A project set up with Claude Code and a remote juwels, as the scan's ``current`` flow.

    :param project_tree: The project root.
    :param home: The fake home.
    :param tools: Makes a ``PATH`` of fake programs.
    :return: The scan."""
    words = ("--agents", "claude-code", "--remote", "juwels=juwels:${SCRATCH}/x/beamtime")
    return set_up(project_tree, home, tools(), *words)


def edit_agent(scan_: Scan, style: str) -> Scan:
    """Change the project's agent style by hand, as a person editing ``beamtime.yaml`` would.

    :param scan_: The scan of the set-up project.
    :param style: The new style.
    :return: The scan after the edit."""
    file = scan_.root / "beamtime.yaml"
    given = yaml.safe_load(file.read_text())
    file.write_text(yaml.safe_dump({**given, "agent": {"style": style}}))
    return dataclasses.replace(scan_, project=scan(scan_.root, home=scan_.home).project)


def reconfigure_run(scan_: Scan, script: list[tuple[str, bytes]]) -> tuple[Session, Answers]:
    """Run the wizard in a current setup on a terminal, from the saved answers.

    :param scan_: The scan.
    :param script: The keys.
    :return: The session and the answers it changed."""
    answers = Answers.saved(scan_)
    done = drive(lambda t: run(t, scan_, answers, probe=fake_probe, which=fake_which), script)
    return done, answers


def labels(scan_: Scan, answers: Answers) -> list[str]:
    """List the labels a plan changes.

    :param scan_: The scan.
    :param answers: The answers.
    :return: One label per change."""
    return [c.label for c in plan(scan_, answers, which=fake_which)]


LIST = "Which answer?"


def test_saved_plans_nothing(current: Scan) -> None:
    """The saved answers of a set-up project change nothing, and say what is set up."""
    assert current.flow == "current"
    saved = Answers.saved(current)
    assert plan(current, saved, which=fake_which) == []
    assert saved.runs == "both" and saved.agents == ["claude-code"] and saved.rules
    assert saved.remotes == [Remote("juwels", "juwels", "${SCRATCH}/x/beamtime")]
    assert saved.git == "record" and not saved.sdk and not saved.imports


def test_saved_after_the_agent_settings_changed(current: Scan) -> None:
    """Editing ``agent`` in ``beamtime.yaml`` plans exactly the rewrite of the rules block."""
    edited = edit_agent(current, "hands-on")
    assert labels(edited, Answers.saved(edited)) == ["Agent rules in CLAUDE.md"]


def test_saved_skip_remote(current: Scan, home: Path) -> None:
    """A remote this machine switched off stays off."""
    file = home / ".config" / "beamtime" / "settings.yaml"
    mine = yaml.safe_load(file.read_text())
    mine["remotes"]["juwels"]["enabled"] = False
    file.write_text(yaml.safe_dump(mine))
    saved = Answers.saved(current)
    assert saved.remotes == [] and saved.skip_remotes == ["juwels"]
    assert plan(current, saved, which=fake_which) == []


def test_saved_without_the_rules_and_with_git_none(project_tree: Path, home: Path, tools) -> None:
    """Setting up with no rules and git none is what the saved answers say too."""
    words = ("--agents", "claude-code", "--no-rules", "--git", "none")
    found = set_up(project_tree, home, tools(), *words)
    saved = Answers.saved(found)
    assert not saved.rules and saved.git == "none"
    assert plan(found, saved, which=fake_which) == []


@posix
def test_reconfigure_lists_the_steps_and_asks_only_the_pick(current: Scan) -> None:
    """The list has every applying step with its summary; one pick asks that step and no other."""
    script = [(LIST, b"9" + ENTER), (GIT, b"2" + ENTER), (REVIEW, ENTER)]
    done, answers = reconfigure_run(current, script)
    assert done.stuck is None and done.value is answers and answers.git == "none"
    assert titles(done.output) == [LIST, GIT, REVIEW]
    for text in (WHERE, "both", "juwels", "Claude Code", "careful", "Review the changes"):
        assert text in done.output
    assert "Set up with " in done.output and "Pick what to change." in done.output
    review_part = done.output.split(f"◇  {GIT}")[-1]
    assert ".gitignore" in review_part and "CLAUDE.md" not in review_part
    assert labels(current, answers) == [".gitignore"]


@posix
def test_reconfigure_after_the_agent_settings_changed(current: Scan) -> None:
    """The list names the mismatch, starts on the review, and Enter reviews the rules change."""
    edited = edit_agent(current, "hands-on")
    done, answers = reconfigure_run(edited, [(LIST, ENTER), (REVIEW, DOWN + DOWN + ENTER)])
    assert done.stuck is None
    line = "The rules in CLAUDE.md don't match beamtime.yaml; the review rewrites them."
    assert line in done.output
    assert titles(done.output) == [LIST, REVIEW]
    assert "Agent rules in CLAUDE.md" in done.output
    again = Answers.from_params(parse(printed_command(done.output)), edited)
    assert labels(edited, again) == labels(edited, answers) == ["Agent rules in CLAUDE.md"]


@posix
def test_reconfigure_new_steps(project_tree: Path, home: Path, tools) -> None:
    """Choosing agents where there were none also asks the style and the rules."""
    bare = set_up(project_tree, home, tools(), "--no-agents")
    assert bare.flow == "current" and Answers.saved(bare).agents == []
    script = [
        (LIST, b"3" + ENTER),
        (AGENTS, UP * 8 + SPACE + ENTER),
        (STYLE, ENTER),
        (RULES, ENTER),
        (REVIEW, ENTER),
    ]
    done, answers = reconfigure_run(bare, script)
    assert done.stuck is None
    assert titles(done.output) == [LIST, AGENTS, STYLE, RULES, REVIEW]
    assert answers.agents == ["claude-code"] and answers.rules
    assert "Agent rules in CLAUDE.md" in done.output


@posix
def test_reconfigure_change_again(current: Scan) -> None:
    """``Change an answer`` at the review returns to the list, not to the order of the steps."""
    script = [
        (LIST, b"9" + ENTER),
        (GIT, b"2" + ENTER),
        (REVIEW, DOWN + ENTER),
        (LIST, b"9" + ENTER),
        (GIT, ENTER),
        (REVIEW, CTRL_C),
    ]
    done, answers = reconfigure_run(current, script)
    assert done.stuck is None
    assert titles(done.output) == [LIST, GIT, REVIEW, LIST, GIT]
    assert answers.git == "none"


@posix
def test_reconfigure_abort(current: Scan) -> None:
    """Ctrl-c on the list writes nothing."""
    before = snapshot(current.root, current.home)
    done, _ = reconfigure_run(current, [(LIST, CTRL_C)])
    assert done.stuck is None and done.value is None
    assert "Nothing was written." in done.output
    assert snapshot(current.root, current.home) == before


@posix
def test_reconfigure_review_without_changes(current: Scan) -> None:
    """Reviewing answers that plan nothing says so and writes nothing."""
    done, _ = reconfigure_run(current, [(LIST, DOWN * 9 + ENTER)])
    assert done.stuck is None and done.value is None
    assert "Nothing to change." in done.output


def test_setup_reconfigures_a_current_project_on_a_terminal(
    current: Scan, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """On a terminal ``setup`` hands the saved answers to the wizard; without one it asks nothing."""
    from beamtime.ops.admin import setup as operation
    from beamtime.ops.context import Context

    monkeypatch.setenv("PATH", tools())
    seen: list[Answers] = []
    monkeypatch.setattr(
        "beamtime.setup.flow.setup", lambda term, found, answers, **kw: seen.append(answers) or []
    )
    context = Context.make(root=current.root)
    assert operation(context, SetupParams())["lines"] == ["already set up"]
    assert seen == []
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", Tty())
    operation(context, SetupParams())
    assert [a.agents for a in seen] == [["claude-code"]] and seen[0].runs == "both"
    operation(context, SetupParams(git="none"))
    assert seen[1].git == "none" and seen[1].agents == ["claude-code"]


def test_setup_without_a_terminal_rewrites_the_edited_rules_only_on_request(
    current: Scan, monkeypatch: pytest.MonkeyPatch, tools
) -> None:
    """``setup`` alone says ``already set up`` after an edit of ``agent``; ``--update rules`` rewrites."""
    from beamtime.guide.rules import read_block
    from beamtime.ops.admin import setup as operation
    from beamtime.ops.context import Context

    monkeypatch.setenv("PATH", tools())
    edited = edit_agent(current, "hands-on")
    context = Context.make(root=edited.root)
    block = read_block(edited.root / "CLAUDE.md")
    assert operation(context, SetupParams())["lines"] == ["already set up"]
    operation(context, SetupParams(yes=True, update=["rules"]))
    assert read_block(edited.root / "CLAUDE.md") != block


def test_saved_remote_without_a_host(current: Scan, home: Path) -> None:
    """A remote whose settings name no host (ssh then uses its name) is left as it is."""
    file = home / ".config" / "beamtime" / "settings.yaml"
    mine = yaml.safe_load(file.read_text())
    del mine["remotes"]["juwels"]["host"]
    mine["remotes"]["juwels"]["command"] = "beamtime"
    file.write_text(yaml.safe_dump(mine))
    assert plan(current, Answers.saved(current), which=fake_which) == []


@posix
def test_reconfigure_command_plans_the_review(current: Scan) -> None:
    """The command shown after a pick plans what the review listed, with the remote and agents."""
    script = [(LIST, b"9" + ENTER), (GIT, b"2" + ENTER), (REVIEW, DOWN + DOWN + ENTER)]
    done, answers = reconfigure_run(current, script)
    assert done.stuck is None
    again = Answers.from_params(parse(printed_command(done.output)), current)
    assert labels(current, again) == labels(current, answers) == [".gitignore"]
