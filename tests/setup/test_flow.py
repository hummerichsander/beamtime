"""The wizard on a pseudo-terminal: the first setup on the mockup's project, key by key."""

import dataclasses
import os
import re
import shlex
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

from beamtime.cli import build_parser, params_of
from beamtime.ops.registry import InitParams
from beamtime.setup.apply import apply
from beamtime.setup.flow import FirstSetup, fill, run, setup
from beamtime.setup.plan import Answers, Remote, command, plan
from beamtime.setup.remotes import Probe
from beamtime.setup.scan import Past, Scan, scan
from beamtime.setup.term import Term

from .test_importers import event, simple, start, write_events

ENTER, SPACE, DOWN, CTRL_C = b"\r", b" ", b"\x1b[B", b"\x03"
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


def parse(words: list[str]) -> InitParams:
    """Parse command line words the way the CLI does.

    :param words: The words after ``beamtime``.
    :return: The parameters of ``init``."""
    return msgspec.convert(params_of("init", build_parser().parse_args(words)), InitParams)


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
    """Write it makes the same files as ``init --yes`` with the command the review prints."""
    keys = [(t, b"2" + ENTER if t == SDK else k) for t, k in TO_REVIEW]
    answers = Answers.defaults(egnn)
    wrote = drive(
        lambda t: setup(t, egnn, answers, probe=fake_probe, which=fake_which),
        [*keys, (REVIEW, ENTER)],
    )
    assert wrote.stuck is None and "Beamtime is set up." in wrote.output
    assert (egnn.root / "beamtime.yaml").is_file() and (home / ".codex" / "config.toml").is_file()

    twin_home = tmp_path / "twin-home"
    twin = make_project(tmp_path / "twin", twin_home, tools("codex"))
    monkeypatch.setenv("HOME", str(twin_home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(twin_home / ".config"))
    words = shlex.split(command(answers, egnn).replace("\\\n", " "))
    assert words[:3] == ["beamtime", "init", "--yes"]
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


def test_init_asks_only_on_a_terminal_for_a_first_setup(
    tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``init`` runs the wizard for a first setup on a terminal without ``--yes``, else not."""
    from beamtime.ops.admin import init
    from beamtime.ops.context import Context

    root = tmp_path / "p"
    root.mkdir()
    seen: list[str] = []
    monkeypatch.setattr(
        "beamtime.setup.flow.setup",
        lambda term, found, answers, **kw: seen.append(found.flow) or [],
    )
    ctx = Context.make(root=root)
    init(ctx, InitParams())
    assert seen == []
    monkeypatch.setattr(sys, "stdin", Tty())
    monkeypatch.setattr(sys, "stdout", Tty())
    init(ctx, InitParams(yes=True))
    assert seen == [] and (root / "beamtime.yaml").exists()
    (root / "beamtime.yaml").unlink()
    init(ctx, InitParams())
    assert seen == ["first"]
