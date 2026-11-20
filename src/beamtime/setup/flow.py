"""The wizard: the steps of the first setup, the review, the apply and the next steps."""

import os
import re
import shlex
import shutil
import socket
import subprocess
import textwrap
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import msgspec

from beamtime.settings import PRESETS, expand_path, user_settings_path
from beamtime.setup.agents import CLIENTS, client_named, migrate_text, start_command
from beamtime.setup.apply import apply
from beamtime.setup.changes import since
from beamtime.setup.importers import detect, files
from beamtime.setup.plan import (
    BLOCK_HEADS,
    PATH_START,
    Answers,
    Planner,
    Remote,
    command,
    display_path,
    import_name,
    log_root,
    plan,
    release,
    review,
)
from beamtime.setup.remotes import SSH_BLOCK, Probe, probe, remote_name_problem
from beamtime.setup.scan import SCRATCH_VARS, Scan
from beamtime.setup.stale import Stale, stale_remote
from beamtime.setup.term import Aborted, Add, FormRow, Option, Term

NUMBERS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")
STYLE_NAMES = {"careful": "careful", "hands-on": "hands-on", "analysis": "analysis only"}
SHOWN = {
    "draft": "draft for me",
    "after_verdicts": "after verdicts",
    "builtin_first": "built-in first",
}
TUNE: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "launch_runs": ("launch runs", [("never", "never"), ("ask", "ask"), ("allowed", "allowed")]),
    "memory_updates": (
        "memory updates",
        [("suggest", "suggest"), ("after verdicts", "after_verdicts")],
    ),
    "save_views": ("save views", [("draft for me", "draft"), ("save", "save")]),
    "research_record": (
        "research record",
        [("off", "off"), ("encouraged", "encouraged"), ("required", "required")],
    ),
    "seeds": ("seeds per point", [("2", "2"), ("3", "3"), ("5", "5")]),
    "significance": ("significance", [("0.90", "0.9"), ("0.95", "0.95"), ("0.99", "0.99")]),
    "proposal_words": (
        "proposal length",
        [("100 words", "100"), ("150 words", "150"), ("300 words", "300")],
    ),
    "memory_tokens": ("memory budget", [("1k", "1000"), ("1.5k", "1500"), ("3k", "3000")]),
    "render_rounds": ("render rounds", [("1", "1"), ("2", "2"), ("3", "3")]),
    "custom_blocks": ("custom blocks", [("built-in first", "builtin_first"), ("free", "free")]),
}
RULE_OPTIONS = [
    Option("record", "Write the rules", "Beamtime is the record"),
    Option("none", "Skip", "only the MCP server; agents find the tools on their own"),
]


UPDATE_LABELS = {
    "rules": "Agent rules",
    "mcp": "MCP server registration",
    "skills": "Claude Code skills",
    "settings": "beamtime.yaml",
    "sdk": "SDK in the project environment",
}
AGENT_SINCE = "0.3.0"
RULES_LABEL = "Agent rules in "
CLIPBOARDS = (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"], ["clip"])
Frame = Callable[[Term, Scan, Answers], tuple[list[str], list[str]]]


def always(answers: Answers, scan: Scan) -> bool:
    """Ask the step in every case.

    :param answers: The answers so far.
    :param scan: The facts of the project and the machine.
    :return: ``True``."""
    return True


@dataclass(frozen=True, kw_only=True)
class Step:
    """One question: how it is asked, when, and how its answer reads in the list of answers."""

    id: str
    title: str
    ask: Callable[[Term, Answers, Scan], None]
    when: Callable[[Answers, Scan], bool] = always
    summary: Callable[[Answers, Scan], str] | None = None


def run(
    term: Term,
    scan: Scan,
    answers: Answers,
    *,
    steps: list[Step] | None = None,
    probe: Callable[..., dict[str, Probe]] = probe,
    which: Callable[[str], str | None] = shutil.which,
) -> Answers | None:
    """Ask the questions and the review, and write nothing.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers from the flags; the scan's findings fill what they leave open.
    :param steps: The questions; by default those of the scan's flow.
    :param probe: Asks the remote hosts what they have.
    :param which: Looks up a program on ``PATH``.
    :return: The answers to write, or ``None`` when the person quit or wanted only the command."""
    flag = answers.migrate_with
    update = Update(probe=probe, which=which) if scan.flow == "update" else None
    steps = steps or (update.steps() if update else flow_steps(scan, probe, which))
    if scan.flow != "current":
        fill(scan, answers)
    try:
        intro(term, scan)
        if scan.flow == "current":
            return reconfigure(term, scan, answers, steps, flag=flag, which=which)
        start = 0
        while True:
            for step in steps[start:]:
                if step.when(answers, scan):
                    step.ask(term, answers, scan)
            hand_off_to(answers, flag)
            match confirm(term, scan, answers, which, update.frame if update else None):
                case "write":
                    return answers
                case "change":
                    start = pick_answer(term, steps, answers, scan)
                case "command":
                    show_command(term, scan, answers)
                    return None
                case _:
                    term.say(["Nothing to change."])
                    return None
    except Aborted:
        term.emit(["Nothing was written."])
        return None


def hand_off_to(answers: Answers, flag: str | None) -> None:
    """Name the agent that gets the imported notes and memory: the flag's, else the first chosen.

    :param answers: The answers; ``migrate_with`` is set in place.
    :param flag: The agent of ``--migrate-with``, if given."""
    answers.migrate_with = flag or (
        answers.agents[0]
        if answers.agents and (answers.import_notes or answers.import_memory)
        else None
    )


def reconfigure(
    term: Term,
    scan: Scan,
    answers: Answers,
    steps: list[Step],
    *,
    flag: str | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> Answers | None:
    """List the saved answers, ask only the picked step and what it newly enables, and review.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The saved answers, with the flags on top; changed in place.
    :param steps: The questions of the first setup.
    :param flag: The agent of ``--migrate-with``, if given.
    :param which: Looks up a program on ``PATH``.
    :return: The answers to write, or ``None`` when the person wanted no more than the command."""
    while True:
        if (i := pick_answer(term, steps, answers, scan, which=which, review=True)) is not None:
            before = [step.when(answers, scan) for step in steps]
            steps[i].ask(term, answers, scan)
            for step, was in zip(steps[i + 1 :], before[i + 1 :], strict=True):
                if not was and step.when(answers, scan):
                    step.ask(term, answers, scan)
        hand_off_to(answers, flag)
        match confirm(term, scan, answers, which):
            case "write":
                return answers
            case "change":
                continue
            case "command":
                show_command(term, scan, answers)
                return None
            case _:
                term.say(["Nothing to change."])
                return None


def setup(
    term: Term,
    scan: Scan,
    answers: Answers,
    *,
    probe: Callable[..., dict[str, Probe]] = probe,
    which: Callable[[str], str | None] = shutil.which,
) -> list[str]:
    """Run the whole wizard: the questions, the review, the writing and the next steps.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers from the flags.
    :param probe: Asks the remote hosts what they have.
    :param which: Looks up a program on ``PATH``.
    :return: The labels of the changes written; empty when nothing was.
    :raises ApplyError: A change failed; the ones before it stay done."""
    flag = answers.migrate_with
    if (final := run(term, scan, answers, probe=probe, which=which)) is None:
        return []
    changes = plan(scan, final, which=which)
    said: list[str] = []
    try:
        with term.task("Updating" if scan.flow == "update" else "Setting up") as task:

            def line(text: str) -> None:
                said.append(text)
                task.line(f"{term.paint('g', '✓')} {text}")

            done = apply(changes, line)
    except KeyboardInterrupt:
        term.say([f"Interrupted. Done so far: {', '.join(said) or 'nothing'}"])
        return []
    next_steps(term, scan, final)
    hand_off(term, scan, final, ask=flag is None, which=which)
    return [c.label for c in done]


def fill(scan: Scan, answers: Answers) -> None:
    """Preselect what the scan found, where the flags left an answer at its plain default.

    :param scan: The facts of the project and the machine.
    :param answers: The answers; changed in place."""
    if scan.flow == "update":
        if not answers.agents:
            answers.agents = [a.client for a in scan.agents if a.registered]
        return
    if scan.flow in ("teammate", "cluster"):
        if not answers.agents:
            answers.agents = [a.client for a in scan.agents if a.command]
        if answers.git == "record" and BLOCK_HEADS["none"] in read_lines(scan.root / ".gitignore"):
            answers.git = "none"
        return
    if answers.runs == "here" and scan.job_scripts and scan.ssh_hosts:
        answers.runs = "both"
    if not answers.agents:
        answers.agents = [a.client for a in scan.agents]
    if not answers.sdk and sdk_applies(scan):
        answers.sdk = True


def read_lines(path: Path) -> list[str]:
    """Read the lines of a file, none when it is missing.

    :param path: The file.
    :return: The lines."""
    return path.read_text(encoding="utf-8").splitlines() if path.is_file() else []


def flow_steps(
    scan: Scan, probe: Callable[..., dict[str, Probe]], which: Callable[[str], str | None]
) -> list[Step]:
    """List the questions of the scan's flow.

    :param scan: The facts of the project and the machine.
    :param probe: Asks the remote hosts what they have.
    :param which: Looks up a program on ``PATH``.
    :return: The steps."""
    match scan.flow:
        case "teammate":
            return Teammate(probe=probe).steps()
        case "cluster":
            return Cluster().steps()
        case _:
            return FirstSetup(probe=probe, which=which).steps()


def sdk_applies(scan: Scan) -> bool:
    """Say whether the SDK is worth asking about: an environment without Beamtime that can take it.

    :param scan: The facts of the project and the machine.
    :return: ``True`` when the environment lacks Beamtime and its Python is recent enough."""
    from beamtime.setup.sdk import sdk_blocker

    env = scan.env
    return env is not None and env.beamtime_version is None and sdk_blocker(env) is None


def intro(term: Term, scan: Scan) -> None:
    """Show the header and what the scan found.

    :param term: The terminal.
    :param scan: The facts of the project and the machine."""
    from beamtime import __version__

    root = display_path(scan.root, scan.home)
    old = setup_release(scan)
    lead = {
        "current": f"Set up with {old or __version__}. Pick what to change.",
        "teammate": "This project uses Beamtime already. Only this machine's part is left.",
        "cluster": "This looks like a cluster login node. Setup here is short.",
        "update": "This project uses Beamtime already; its setup is "
        + (f"from {old}." if old else "older than this release."),
    }.get(scan.flow, f"Set up Beamtime for {root}.")
    term.emit(
        [
            f"{term.paint('a', '///')} {term.paint('t', 'beamtime')} "
            f"{term.paint('m', __version__)}",
            term.paint("r", "┌"),
            term.rail(lead),
            *(
                [
                    term.rail(
                        "Runs, notes and views need nothing. Only what surrounds them is updated."
                    )
                ]
                if scan.flow == "update"
                else []
            ),
            term.rail(
                term.paint(
                    "m", "Nothing is written until you confirm at the end; ctrl-c leaves no trace."
                )
            ),
            term.rail(""),
        ]
    )
    with term.task(f"Looking around {root}") as task:
        for key, value in facts(term, scan):
            task.line(f"{term.paint('m', key.ljust(11))}{value}")


def facts(term: Term, scan: Scan) -> list[tuple[str, str]]:
    """Word what the scan found, one fact per line.

    :param term: The terminal, for its colors.
    :param scan: The facts of the project and the machine.
    :return: Pairs of the fact's name and its text."""
    m = lambda text: term.paint("m", text)  # noqa: E731
    out: list[tuple[str, str]] = []
    if scan.flow == "cluster":
        names = {"slurm": "SLURM (sbatch)", "pbs": "PBS (qsub)", "lsf": "LSF (bsub)"}
        machine = [socket.gethostname().split(".")[0], names.get(scan.scheduler or "")]
        if not scan.display:
            machine.append("no browser")
        out.append(("machine", f" {m('·')} ".join(x for x in machine if x)))
    if scan.flow == "update":
        from beamtime import __version__

        if was := setup_release(scan):
            out.append(
                ("beamtime", f"{__version__} here {m('· the project was set up with ' + was)}")
            )
        out.append(("log dir", f"{shown(scan.project.logdir, scan)} {m('·')} {counts(scan)}"))
        if scan.project.remotes:
            names = f" {m('·')} ".join(scan.project.remotes)
            out.append(("remotes", f"{names} {m('(from beamtime.yaml)')}"))
    if scan.project.settings and scan.flow in ("teammate", "cluster"):
        agent = (Planner.read(scan.root / "beamtime.yaml").get("agent") or {}).get("style")
        project = ["beamtime.yaml", f"logdir {shown(scan.project.logdir, scan).rstrip('/')}"]
        if agent:
            project.append(f"agents {agent}")
        out.append(("project", f" {m('·')} ".join(project)))
        if scan.project.remotes:
            names = f" {m('·')} ".join(scan.project.remotes)
            out.append(("remotes", f"{names} {m('(from beamtime.yaml)')}"))
    if scan.flow == "cluster" and (disks := disk_facts(scan)):
        out.append(("disks", f" {m('·')} ".join(disks)))
    git = scan.git
    out.append(
        ("git", f"{git.branch or 'detached'} {m('· ' + ('clean' if git.clean else 'dirty'))}")
        if git.root
        else ("git", "not a git checkout")
    )
    if env := scan.env:
        where = f"{env.python or 'Python'} in {env.path.name if env.path else '?'} ({env.tool})"
        missing = (
            term.paint("w", "· beamtime is not installed there") if not env.beamtime_version else ""
        )
        out.append(("python", f"{where} {missing}".strip()))
    code = []
    if scan.framework:
        code.append("the code uses PyTorch Lightning")
    code += [f"{j.path} ({j.scheduler.upper()})" for j in scan.job_scripts]
    if code:
        out.append(("code", f" {m('·')} ".join(code)))
    own = [p.found for p in scan.past if not p.other]
    if own:
        out.append(
            ("past runs", f" {m('·')} ".join(f"{f.label} in {shown(f.path, scan)}" for f in own))
        )
    for p in scan.past:
        if p.other:
            out.append(
                (
                    "beamtime",
                    f"{p.found.label} in {shown(p.found.path, scan)} "
                    f"{m('· another project this machine has indexed')}",
                )
            )
    if scan.notes:
        out.append(
            (
                "notes",
                f" {m('·')} ".join(
                    f"{notes_name(n)} ({n.n} files)" if n.path.is_dir() else notes_name(n)
                    for n in scan.notes
                ),
            )
        )
    if scan.agents:
        names = [
            f"{a.label} ({', '.join(a.files)})" if a.files else f"{a.client} on PATH"
            for a in scan.agents
        ]
        out.append(("agents", f" {m('·')} ".join(names)))
    if scan.conflicts:
        c = scan.conflicts[0]
        out.append(("rules", f"{c.file} line {c.line}: {c.text.strip()}"))
    if scan.ssh_hosts:
        names = f" {m('·')} ".join(h.name for h in scan.ssh_hosts)
        out.append(("ssh hosts", f"{names} {m('(from ~/.ssh/config)')}"))
    return out


def disk_facts(scan: Scan) -> list[str]:
    """Word the filesystems that matter on a cluster: ``$HOME``, scratch and ``/tmp``.

    :param scan: The facts of the project and the machine.
    :return: One phrase per disk with a known filesystem."""
    out = []
    for d in scan.disks:
        if not d.fstype:
            continue
        if d.label == "home":
            out.append(f"$HOME is {d.fstype}")
        elif d.label == "tmp":
            out.append(f"/tmp is {'local' if not d.network else d.fstype}")
        elif d.label in SCRATCH_VARS:
            out.append(f"${{{d.label}}} = {d.path} ({d.fstype})")
    return out


def setup_release(scan: Scan) -> str | None:
    """Name the oldest release that wrote a rules block of this project.

    :param scan: The facts of the project and the machine.
    :return: The release, or ``None`` when no block has one (none, or edited by hand)."""
    found = [a.release for a in scan.agents if a.has_block and a.release]
    return min(found, key=release, default=None)


def counts(scan: Scan) -> str:
    """Count what the log dir holds, in words.

    :param scan: The facts of the project and the machine.
    :return: E.g. ``214 runs, 31 notes, 4 proposals, 2 memories``."""
    p = scan.project
    words = [
        (p.runs, "run", "runs"),
        (p.notes, "note", "notes"),
        (p.proposals, "proposal", "proposals"),
        (p.memories, "memory", "memories"),
    ]
    return (
        ", ".join(f"{n} {one if n == 1 else many}" for n, one, many in words if n) or "no runs yet"
    )


def shown(path: Path, scan: Scan) -> str:
    """Write a path as the person would: below the project, then ``~``, else absolute.

    :param path: The path.
    :param scan: The facts of the project and the machine.
    :return: The path as it goes into an answer."""
    root = scan.root.resolve()
    if path.is_relative_to(root):
        return path.relative_to(root).as_posix() + ("/" if path.is_dir() else "")
    return display_path(path, scan.home) + ("/" if path.is_dir() else "")


def notes_name(notes: Any) -> str:
    """Name a folder or file of notes or memory.

    :param notes: A ``scan.Notes``.
    :return: E.g. ``notebook/``, ``NOTES.md`` or ``Claude Code memory``."""
    if ".claude" in notes.path.parts:
        return "Claude Code memory"
    return notes.path.name + ("/" if notes.path.is_dir() else "")


def confirm(
    term: Term,
    scan: Scan,
    answers: Answers,
    which: Callable[[str], str | None],
    frame: Frame | None = None,
) -> str:
    """Show the review and ask what to do with it.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers.
    :param which: Looks up a program on ``PATH``.
    :param frame: The lines before and after the changes, for flows that have them.
    :return: ``write``, ``change``, ``command``, or ``none`` when there is nothing to change."""
    try:
        changes = plan(scan, answers, which=which)
    except ValueError as e:
        term.say([f"{term.paint('w', '!')} {e}", ""])
        return "change"
    if not changes:
        return "none"
    body = [line if line.startswith(" ") else term.paint("t", line) for line in review(changes)]
    if frame:
        head, tail = frame(term, scan, answers)
        body = [*head, *body, *tail]
    if scan.flow in ("teammate", "cluster") and all(c.label != "beamtime.yaml" for c in changes):
        body += ["", f"{term.paint('t', 'beamtime.yaml')}  {term.paint('m', 'unchanged')}"]
    return term.select(
        "Ready. Nothing has been written yet.",
        [
            Option("write", "Write it"),
            Option("change", "Change an answer"),
            Option("command", "Show the command and quit"),
        ],
        "write",
        body=[*body, ""],
    )


def pick_answer(
    term: Term,
    steps: list[Step],
    answers: Answers,
    scan: Scan,
    *,
    which: Callable[[str], str | None] = shutil.which,
    review: bool = False,
) -> int | None:
    """Ask which answer to change; the later answers stay as they are, as the defaults.

    With ``review`` the list ends on ``Review the changes``, starts there when the answers plan a
    change, and says first when a rules block no longer matches the project's settings.

    :param term: The terminal.
    :param steps: The questions.
    :param answers: The answers.
    :param scan: The facts of the project and the machine.
    :param which: Looks up a program on ``PATH``.
    :param review: Whether the list is the start of a reconfiguration.
    :return: The index of the step to go back to, or ``None`` for the review."""
    rows = [(i, s) for i, s in enumerate(steps) if s.summary and s.when(answers, scan)]
    options = [Option(s.id, s.title, s.summary(answers, scan)) for _, s in rows]
    body: list[str] = []
    default = options[0].value
    if review:
        options.append(Option("review", "Review the changes"))
        try:
            pending = plan(scan, answers, which=which)
        except ValueError:
            pending = []
        files = [
            c.label.removeprefix(RULES_LABEL) for c in pending if c.label.startswith(RULES_LABEL)
        ]
        if files:
            names = ", ".join(files)
            text = f"The rules in {names} don't match beamtime.yaml; the review rewrites them."
            body = [term.paint("m", text), ""]
        default = "review" if pending else default
    chosen = term.select("Which answer?", options, default, body=body)
    return next((i for i, s in rows if s.id == chosen), None)


def migrate_args(scan: Scan, answers: Answers) -> tuple[list[str], str | None]:
    """Name what the migrate prompt gets: the notes and memory files, and the instruction conflict.

    :param scan: The facts of the project and the machine.
    :param answers: The answers.
    :return: The paths as the agent finds them from the root, and ``file:line`` or ``None``."""
    found = [*answers.import_notes, *answers.import_memory]
    if not found and answers.migrate_with and scan.flow == "current":
        found = [shown(n.path, scan) for n in scan.notes]
    writes_rules = (
        answers.rules
        if scan.flow == "first"
        else "rules" in answers.update
        if scan.flow == "update"
        else scan.flow == "current"
    )
    conflict = scan.conflicts[0] if scan.conflicts and writes_rules else None
    return found, f"{conflict.file}:{conflict.line}" if conflict else None


def hand_off(
    term: Term,
    scan: Scan,
    answers: Answers,
    *,
    ask: bool = True,
    which: Callable[[str], str | None] = shutil.which,
) -> None:
    """Offer the notes, memory and an instruction conflict to the person's agent, once written.

    Starting replaces this process with the agent's session.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers; ``migrate_with`` names the agent when ``ask`` is false.
    :param ask: Whether to ask what to do; ``--migrate-with`` goes straight to the agent.
    :param which: Looks up a program on ``PATH``."""
    paths, conflict = migrate_args(scan, answers)
    if ask:
        agents = [client_named(a) for a in answers.agents]
        if not agents or not (paths or conflict):
            return
        starters = [c for c in agents if c.start and which(c.start[0])]
        choice = term.select(
            "Hand the notes and memory to your agent now?",
            [
                *[Option(c.name, f"Start {c.label} now", shlex.join(c.start)) for c in starters],
                Option("copy", "Copy the prompt", "for an editor-based agent"),
                Option(
                    "later",
                    "Later",
                    f"beamtime setup --migrate-with {agents[0].name} brings this back",
                ),
            ],
            starters[0].name if starters else "copy",
            body=hand_off_body(term, scan, answers, paths, conflict),
        )
    else:
        choice = answers.migrate_with or "copy"
    client = client_named(choice) if choice not in ("copy", "later") else None
    argv = start_command(client, paths, conflict) if client else None
    match choice:
        case "later":
            term.say([f"Run it later:  beamtime setup --migrate-with {answers.agents[0]}"])
        case _ if argv and which(argv[0]):
            term.say([f"Starting {client.label} with the migrate prompt."])
            os.chdir(scan.root)
            os.execvp(argv[0], argv)
        case _:
            copy(term, migrate_text(paths, conflict), which)


def migrate_lines(scan: Scan, answers: Answers) -> list[str]:
    """Say how to start the agent with the migrate prompt, for a run without a terminal.

    :param scan: The facts of the project and the machine.
    :param answers: The answers; ``migrate_with`` names the agent.
    :return: The lines."""
    client = client_named(answers.migrate_with or "other")
    paths, conflict = migrate_args(scan, answers)
    if argv := start_command(client, paths, conflict):
        return [f"to hand the notes and memory to {client.label}, run: {shlex.join(argv)}"]
    return [
        f"to hand the notes and memory to {client.label}, give it: {migrate_text(paths, conflict)}"
    ]


def hand_off_body(
    term: Term, scan: Scan, answers: Answers, paths: list[str], conflict: str | None
) -> list[str]:
    """Say what the agent will do, for the hand-off question.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers.
    :param paths: The notes and memory files.
    :param conflict: ``file:line`` of an instruction that keeps results elsewhere, if any.
    :return: The lines under the question."""
    label = client_named(answers.agents[0]).label
    n = sum(x.n for x in scan.notes if shown(x.path, scan) in paths) or len(paths)
    files = f"{n} {'file' if n == 1 else 'files'}"
    lines = []
    if paths:
        lines += [
            f"{label} reads the {files} of notes and memory, writes them as typed notes",
            "linked to the imported runs, and drafts a first memory for the project. Its",
            "writes are new files; nothing you have is changed.",
        ]
    if conflict:
        file, _, line = conflict.rpartition(":")
        lines += [""] if paths else []
        lines += [
            f"It also moves the experiment section of {file} (line {line}) into Beamtime",
            f"and shows you the diff before it touches {file}.",
        ]
    return lines


def copy(term: Term, text: str, which: Callable[[str], str | None]) -> None:
    """Put the migrate prompt on the clipboard with the first tool found, else print it.

    :param term: The terminal.
    :param text: The prompt.
    :param which: Looks up a program on ``PATH``."""
    for tool in CLIPBOARDS:
        if path := which(tool[0]):
            subprocess.run([path, *tool[1:]], input=text.encode(), check=False)
            return term.say(["The migrate prompt is on your clipboard."])
    term.say(["No clipboard tool found. Give this to your agent:", "", f"  {text}"])


def show_command(term: Term, scan: Scan, answers: Answers) -> None:
    """Print the command that makes the same setup.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers."""
    term.say(["Nothing was written. This command makes the same setup:", ""])
    term.say(command(answers, scan).splitlines())


def next_steps(term: Term, scan: Scan, answers: Answers) -> None:
    """Say what to do next, with the code for the project's framework.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers."""
    name = scan.root.name
    if scan.flow == "update":
        return next_steps_updated(term, scan, answers)
    if scan.flow in ("teammate", "cluster"):
        return next_steps_there(term, scan, answers)
    if scan.framework == "lightning":
        code = [
            "from beamtime.lightning import BeamtimeLogger",
            f'trainer = Trainer(logger=BeamtimeLogger(dir="{name}/baseline"))',
        ]
    else:
        code = ["import beamtime", f'run = beamtime.init(dir="{name}/baseline")']
    third = (
        f'Ask your agent:     "Propose the next experiment for {name}."'
        if answers.agents
        else f"Before the next run, write down what you expect:  beamtime proposal set {name}"
    )
    a = term.paint("a", "{}")
    term.emit(
        [
            f"{term.paint('r', '└')}  {term.paint('t', 'Beamtime is set up.')}",
            "",
            f"   {term.paint('m', 'Next')}",
            f"   {a.format('1')}  Log a run. In your training script:",
            *[f"        {line}" for line in code],
            f"   {a.format('2')}  Look at your runs:  beamtime serve --open",
            f"   {a.format('3')}  {third}",
        ]
    )


def next_steps_updated(term: Term, scan: Scan, answers: Answers) -> None:
    """Say that the data stayed, and what changed since the setup's release.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers."""
    from beamtime import __version__

    old = setup_release(scan)
    logdir = shown(scan.project.logdir, scan)
    lines = [
        f"{term.paint('r', '└')}  "
        + term.paint("t", f"Beamtime {__version__} is set up. Nothing in {logdir} was rewritten.")
    ]
    if changed := since(old or "0.0.0", __version__):
        title = (
            f"Changed {f'since {old}' if old else 'in recent releases'}, where you may notice it"
        )
        lines += ["", f"   {term.paint('m', title)}"]
        lines += [f"   {term.paint('a', '·')}  {line}" for line in changed]
    if answers.agents and answers.rules:
        lines += ["", "   Agents read the new rules from their next session on."]
    term.emit(lines)


def next_steps_there(term: Term, scan: Scan, answers: Answers) -> None:
    """Say what to do next on a teammate's machine or a cluster, whose project is set up already.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers."""
    n = lambda i: term.paint("a", str(i))  # noqa: E731
    code = lambda text: term.paint("c", text)  # noqa: E731
    rail = term.paint("r", "└")
    if scan.flow == "teammate":
        lines = [
            f"{rail}  {term.paint('t', 'Beamtime is set up on this machine.')}",
            "",
            f"   {n(1)}  See the team's runs from every source:  {code('beamtime serve --open')}",
        ]
        if answers.agents:
            ask = f'"What does the project memory say about {scan.root.name}?"'
            lines.append(f"   {n(2)}  Ask your agent:  {code(ask)}")
        return term.emit(lines)
    where = Path(expand_path(answers.link_logdir or answers.logdir))
    where = (where if where.is_absolute() else scan.root / where).resolve()
    name = socket.gethostname().split(".")[0]
    other = f"or run beamtime setup there; it finds {name} in ~/.ssh/config."
    jobs = f"Jobs need no change: {code('beamtime.init()')} finds the project and writes there."
    term.emit(
        [
            f"{rail}  {term.paint('t', 'Beamtime is set up on this cluster.')}",
            "",
            f"   {n(1)}  {jobs}",
            f"      {term.paint('m', 'A requeued job continues its run.')}",
            f"   {n(2)}  On your laptop, in the project:",
            f"        {code(f'beamtime source add {name} {name}:{where}')}",
            f"      {term.paint('m', other)}",
        ]
    )


@dataclass(frozen=True)
class Row:
    """A path of past work: the answer it fills, how many runs or files, and how it reads."""

    field: str
    n: int
    label: str
    dest: str | None = None
    kind: str | None = None


class FirstSetup:
    """The questions of the first setup, in the order of the mockup."""

    style_hint: str | None = None
    rules_hint = "Agents read this block at the start of every session."

    def __init__(
        self,
        *,
        probe: Callable[..., dict[str, Probe]] = probe,
        which: Callable[[str], str | None] = shutil.which,
    ) -> None:
        """Keep what the questions share: the probe, what it found and the paths of past work.

        :param probe: Asks the remote hosts what they have.
        :param which: Looks up a program on ``PATH``."""
        self.probe = probe
        self.which = which
        self.probes: dict[str, Probe] = {}
        self.fine = False
        self.rows: dict[str, Row] = {}
        self.imports_asked = False

    def steps(self) -> list[Step]:
        """List the questions in order.

        :return: The steps."""

        def hosts(a: Answers, s: Scan) -> bool:
            return a.runs != "here"

        def agents(a: Answers, s: Scan) -> bool:
            return bool(a.agents)

        return [
            Step(
                id="where",
                title="Where do your runs happen?",
                ask=self.ask_where,
                summary=lambda a, s: {
                    "here": "on this machine",
                    "remote": "on other machines",
                    "both": "both",
                }[a.runs],
            ),
            Step(
                id="logdir",
                title="Where should runs on this machine go?",
                ask=self.ask_logdir,
                when=lambda a, s: a.runs != "remote",
                summary=lambda a, s: a.logdir.rstrip("/") + "/",
            ),
            Step(
                id="hosts",
                title="Which machines?",
                ask=self.ask_hosts,
                when=hosts,
                summary=lambda a, s: ", ".join(r.name for r in a.remotes) or "none",
            ),
            Step(
                id="machines",
                title="Install and log dir on each machine",
                ask=self.ask_machines,
                when=hosts,
                summary=lambda a, s: ", ".join(f"{r.name} {r.path}" for r in a.remotes) or "none",
            ),
            Step(
                id="agents",
                title="Which coding agents should know about Beamtime?",
                ask=self.ask_agents,
                summary=lambda a, s: ", ".join(client_named(x).label for x in a.agents) or "none",
            ),
            Step(
                id="style",
                title="How much should agents do on their own?",
                ask=self.ask_style,
                when=agents,
                summary=lambda a, s: "custom" if self.fine else STYLE_NAMES[a.agent_style],
            ),
            Step(
                id="tune",
                title="Agent settings",
                ask=self.ask_tune,
                when=lambda a, s: bool(a.agents) and self.fine,
                summary=self.tune_summary,
            ),
            Step(
                id="rules",
                title="Tell agents that Beamtime is the record?",
                ask=self.ask_rules,
                when=agents,
                summary=lambda a, s: "yes" if a.rules else "skipped",
            ),
            Step(
                id="import",
                title="Bring in past work?",
                ask=self.ask_imports,
                summary=self.import_summary,
            ),
            Step(
                id="git",
                title="Keep the research record in git?",
                ask=self.ask_git,
                summary=lambda a, s: "yes" if a.git == "record" else "no",
            ),
            Step(
                id="sdk",
                title="Add the Beamtime SDK to this project's environment?",
                ask=self.ask_sdk,
                when=lambda a, s: sdk_applies(s),
                summary=lambda a, s: "yes" if a.sdk else "no",
            ),
        ]

    def ask_where(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask where the runs happen; local-only drops the remotes.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        both = None
        if scan.job_scripts and scan.ssh_hosts:
            n = len(scan.ssh_hosts)
            count = NUMBERS[n] if n < len(NUMBERS) else n
            both = f"{scan.job_scripts[0].path} and {count} ssh hosts found"
        a.runs = term.select(
            "Where do your runs happen?",
            [
                Option("here", "On this machine"),
                Option("remote", "On other machines", "clusters or workstations; I look from here"),
                Option("both", "Both", both),
            ],
            a.runs,
        )
        if a.runs == "here":
            a.remotes, a.install_remotes = [], []

    def ask_logdir(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask where runs on this machine go.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        text = term.text(
            "Where should runs on this machine go?",
            a.logdir.rstrip("/") + "/",
            "In the project and kept out of git. A path elsewhere (~/data/egnn) gets a link here.",
        )
        a.logdir = text.rstrip("/") or a.logdir

    def ask_hosts(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask which machines hold runs; ssh aliases and typed hosts alike.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        named = {h: j.path for j in scan.job_scripts for h in j.hosts}
        current = {r.host or r.name: r for r in a.remotes}
        options = [
            Option(
                h.name,
                h.name,
                f"~/.ssh/config · named in {named[h.name]}" if h.name in named else "~/.ssh/config",
            )
            for h in scan.ssh_hosts
        ]
        options += [Option(h, h, "added") for h in current if h not in {o.value for o in options}]
        default = list(current) or [o.value for o in options if o.value in named]

        picked = term.multi(
            "Which machines?",
            options,
            default,
            Add("Add a host", "an ssh alias or user@host", check_host),
        )
        a.remotes = [current.get(h) or new_remote(h) for h in picked]
        a.install_remotes = [n for n in a.install_remotes if n in {r.name for r in a.remotes}]

    def ask_machines(self, term: Term, a: Answers, scan: Scan) -> None:
        """Check every machine at once, then ask per machine: install, and where runs go.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        if not a.remotes:
            return
        project = scan.root.name
        if todo := [h for h in (r.host or r.name for r in a.remotes) if h not in self.probes]:
            title = f"Checking {todo[0] if len(todo) == 1 else f'{len(todo)} machines'}"
            with term.task(title) as task:
                found = self.probe(todo, {h: f"${{SCRATCH}}/{project}/beamtime" for h in todo})
                for host in todo:
                    self.probes[host] = found[host]
                    task.line(probe_line(term, host, found[host]))
        kept: list[Remote] = []
        for i, r in enumerate(a.remotes, 1):
            host = r.host or r.name
            found = self.probes[host]
            if found.status == "old_python":
                term.say(
                    [f"{host}: {found.detail}; Beamtime can't run there, so it is left out.", ""]
                )
                continue
            a.install_remotes = [n for n in a.install_remotes if n != r.name]
            if found.status == "no_beamtime" and not self.ask_install(term, a, r, host):
                continue
            default = r.path or (
                f"${{SCRATCH}}/{project}/beamtime" if found.scratch else f"~/{project}/beamtime"
            )
            kept.append(
                msgspec.structs.replace(
                    r, path=self.ask_path(term, host, default, i, len(a.remotes))
                )
            )
        a.remotes = kept

    def ask_install(self, term: Term, a: Answers, remote: Remote, host: str) -> bool:
        """Ask whether to install Beamtime on a machine that lacks it.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param remote: The remote.
        :param host: Its ssh host.
        :return: ``False`` when the machine is skipped."""
        from beamtime import __version__

        pip = f"python3 -m pip install --user beamtime[serve]=={__version__}"
        cmd = f"ssh {host} {shlex.quote(pip)}"
        while True:
            choice = term.select(
                f"Install Beamtime on {host}?",
                [
                    Option("yes", "Install it", "after you confirm, as the last step"),
                    Option("show", "Show me the command"),
                    Option("skip", f"Skip {host} for now"),
                ],
                "yes",
                body=[term.paint("m", cmd)],
            )
            if choice != "show":
                break
            term.say(["Run it yourself, any time:", cmd, ""])
        if choice == "skip":
            return False
        a.install_remotes.append(remote.name)
        return True

    def ask_path(self, term: Term, host: str, default: str, i: int, n: int) -> str:
        """Ask where the runs go on a machine.

        :param term: The terminal.
        :param host: The ssh host.
        :param default: The path preselected.
        :param i: Which machine this is.
        :param n: How many machines there are.
        :return: The path; it starts with ``/``, ``~`` or ``$``."""
        hint = f"~ and ${{VAR}} expand on {host}." + (f"  {i} of {n}" if n > 1 else "")
        while True:
            path = term.text(f"Where do runs go on {host}?", default, hint).strip()
            if path.startswith(PATH_START):
                return path
            term.say(["A path starts with /, ~ or $.", ""])

    def ask_agents(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask which coding agents get the MCP server and the rules.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        pick_agents(term, a, scan, "Which coding agents should know about Beamtime?")

    def ask_style(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask how much agents do on their own.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        options = [
            Option("careful", "Careful", "propose and analyze; you launch runs"),
            Option("hands-on", "Hands-on", "may also launch runs"),
            Option("analysis", "Analysis only", "no proposals; tables, charts and views"),
            Option("custom", "Choose each setting"),
        ]
        body = [
            "Main metric, seed key and domain are not asked;",
            "set them later under agent: in beamtime.yaml.",
        ]
        default = "custom" if self.fine or a.agent_set else a.agent_style
        chosen = term.select(
            "How much should agents do on their own?",
            options,
            default,
            self.style_hint,
            body=[term.paint("m", b) for b in body],
        )
        self.fine = chosen == "custom"
        if not self.fine:
            a.agent_style, a.agent_set = chosen, {}

    def ask_tune(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask for each agent setting, starting from the project's values; keep what differs from
        the style's preset.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        preset = PRESETS[a.agent_style]
        rows, start = [], {}
        for key, (label, values) in TUNE.items():
            have = a.agent_set.get(key, str(preset[key]))
            if have not in [stored for _, stored in values]:
                values = [*values, (have, have)]
            rows.append(FormRow(key, label, tuple(shown for shown, _ in values)))
            start[key] = next(shown for shown, stored in values if stored == have)
        chosen = term.form("Agent settings", rows, start)
        a.agent_set = {}
        for key, (_, values) in TUNE.items():
            stored = next((s for d, s in values if d == chosen[key]), chosen[key])
            if stored != str(preset[key]):
                a.agent_set[key] = stored

    def tune_summary(self, a: Answers, scan: Scan) -> str:
        """Word the agent settings that differ from the style's preset.

        :param a: The answers.
        :param scan: The facts of the project and the machine.
        :return: One line."""
        changed = [f"{TUNE[k][0]} {SHOWN.get(v, v)}" for k, v in a.agent_set.items() if k in TUNE]
        return (
            f"custom: {', '.join(changed)}" if changed else f"same as {STYLE_NAMES[a.agent_style]}"
        )

    def ask_rules(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask whether to write the rules block, showing it.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        from beamtime.guide.rules import render
        from beamtime.ops.registry import OPS
        from beamtime.settings import resolve_agent

        planner = Planner(scan=scan, answers=a, which=self.which)
        block = render(
            resolve_agent(planner.agent_given()), sorted(o.name for o in OPS if o.user_only)
        )
        names = " and ".join(dict.fromkeys(client_named(x).rules for x in a.agents))
        body = [term.paint("m", f"Written to {names}, between beamtime markers:"), ""]
        width = max(term.columns() - 8, 40)
        for line in block.splitlines():
            indent = "  " if line.startswith("- ") else ""
            body += [f"  {w}" for w in textwrap.wrap(line, width, subsequent_indent=indent) or [""]]
        if scan.conflicts:
            c = scan.conflicts[0]
            body += [
                "",
                f"{term.paint('w', '!')} {c.file} line {c.line} sends results elsewhere:",
                f"  {c.text.strip()}",
                term.paint("m", "  Your agent folds that section into Beamtime notes after setup"),
                term.paint("m", "  and shows you the diff."),
            ]
        choice = term.select(
            "Tell agents that Beamtime is the record?",
            RULE_OPTIONS,
            "record" if a.rules else "none",
            self.rules_hint,
            body,
        )
        a.rules = choice == "record"

    def ask_imports(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask which past work to bring in: what the scan found, and paths the person adds.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        found: dict[str, bool] = {}
        for past in sorted(scan.past, key=lambda p: p.other):
            value = shown(past.found.path, scan)
            self.rows[value] = Row(
                "imports",
                past.found.n,
                past.found.label,
                import_name(past.found.path),
                past.found.kind,
            )
            found[value] = not past.other
        for notes in scan.notes:
            value = shown(notes.path, scan)
            self.rows[value] = Row(f"import_{notes.kind}", notes.n, notes_name(notes))
            found[value] = True
        current = [v for v in (*a.imports, *a.import_notes, *a.import_memory) if v in self.rows]
        default = (
            current
            if self.imports_asked
            else list(dict.fromkeys([*current, *(v for v in found if found[v])]))
        )
        self.imports_asked = True
        by_agent = bool(a.agents)
        options = [
            self.option(v, by_agent, v in found) for v in self.rows if v in found or v in current
        ]
        add = Add(
            "Add a path",
            "a log dir, a notes folder or memory files",
            lambda t: self.check_path(t, scan, by_agent),
        )
        picked = term.multi("Bring in past work?", options, default, add)
        for field in ("imports", "import_notes", "import_memory"):
            setattr(a, field, [v for v in picked if self.rows[v].field == field])

    def option(self, value: str, by_agent: bool, scanned: bool) -> Option:
        """Make the row of one past-work path.

        :param value: The path as it goes into an answer.
        :param by_agent: Whether an agent turns notes and memory into typed ones.
        :param scanned: Whether the scan found it, or the person added it.
        :return: The row."""
        row = self.rows[value]
        files = f"{row.n} {'file' if row.n == 1 else 'files'}"
        match row.field:
            case "imports":
                hint = f"{value}  →  imported/{row.dest}" + (
                    " · with its notes" if row.kind == "beamtime" else ""
                )
            case "import_notes":
                hint = f"{files}  →  " + (
                    "typed notes, by your agent" if by_agent else "one note per file, as written"
                )
            case _:
                hint = f"{files}  →  " + (
                    "the project memory, by your agent"
                    if by_agent
                    else "one note per file, as written"
                )
        return Option(value, row.label, hint + ("" if scanned else "  · added"))

    def check_path(self, text: str, scan: Scan, by_agent: bool) -> Option | str:
        """Check a path the person typed: runs, notes or memory.

        :param text: The path.
        :param scan: The facts of the project and the machine.
        :param by_agent: Whether an agent turns notes and memory into typed ones.
        :return: The row to add, or the reason the path is no use."""
        path = (scan.root / expand_path(text.strip())).resolve()
        if not text.strip() or not path.exists():
            return f"{text.strip() or 'a path'}: no such file or folder"
        from beamtime.format.tree import is_run

        value = shown(path, scan)
        if found := detect(path):
            if found.kind == "beamtime" and not is_run(path):
                found = detect(source := log_root(path)) or found
                path = source
            self.rows[value] = Row("imports", found.n, found.label, import_name(path), found.kind)
        elif n := sum(1 for _ in files(path)):
            memory = re.search(r"memory|^claude\.md$|^agents\.md$", path.name, re.IGNORECASE)
            label = path.name + ("/" if path.is_dir() else "")
            self.rows[value] = Row("import_memory" if memory else "import_notes", n, label)
        else:
            return "no runs, notes or memory files found here"
        return self.option(value, by_agent, False)

    def import_summary(self, a: Answers, scan: Scan) -> str:
        """Word what comes in.

        :param a: The answers.
        :param scan: The facts of the project and the machine.
        :return: One line."""
        runs = sum(self.rows[v].n for v in a.imports if v in self.rows)
        docs = sum(self.rows[v].n for v in (*a.import_notes, *a.import_memory) if v in self.rows)
        parts = [
            runs and f"{runs} runs",
            docs and f"{docs} {'file' if docs == 1 else 'files'} of notes and memory",
        ]
        return " · ".join(p for p in parts if p) or "nothing"

    def ask_git(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask whether the research record goes into git.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        a.git = term.select(
            "Keep the research record in git?",
            [
                Option(
                    "record",
                    "Yes",
                    "proposals, notes, memory and views are committed; run data stays out",
                ),
                Option("none", "No", "the whole log dir stays out of git"),
            ],
            a.git,
        )

    def ask_sdk(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask whether to add the SDK to the project's environment.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        from beamtime.setup.sdk import sdk_commands

        env = scan.env
        place = env.path.name if env and env.path else f"the {env.tool} environment"
        add = shlex.join(sdk_commands(env, False)[0]) if env and sdk_commands(env, False) else None
        a.sdk = (
            term.select(
                "Add the Beamtime SDK to this project's environment?",
                [Option("yes", "Yes", add), Option("no", "No", "I install it myself")],
                "yes" if a.sdk else "no",
                body=[
                    term.paint(
                        "m", f"The project runs in {place}, which does not have beamtime yet."
                    )
                ],
            )
            == "yes"
        )


class Update(FirstSetup):
    """The questions of an update: what is stale, and only what is new since the setup's release."""

    style_hint = "New since your setup: one preset instead of rules spelled out by hand."
    rules_hint = "New since your setup: the rules say where findings belong."

    def __init__(
        self,
        *,
        probe: Callable[..., dict[str, Probe]] = probe,
        which: Callable[[str], str | None] = shutil.which,
    ) -> None:
        """Keep what the questions share, and the stale remotes the probe finds.

        :param probe: Asks the remote hosts what they have.
        :param which: Looks up a program on ``PATH``."""
        super().__init__(probe=probe, which=which)
        self.remote_stale: list[Stale] = []
        self.total = 0

    def steps(self) -> list[Step]:
        """List the questions in order; the agent questions only for a setup before they existed.

        :return: The steps."""
        from beamtime import __version__

        new = [s for s in super().steps() if s.id in ("style", "tune", "rules")]
        return [
            Step(id="data", title="Checking runs, notes and views", ask=self.ask_data),
            Step(
                id="check",
                title="Checking machines",
                ask=self.ask_check,
                when=lambda a, s: bool(self.hosts(s)),
            ),
            Step(
                id="updates",
                title=f"What should be brought up to {__version__}?",
                ask=self.ask_updates,
                summary=self.updates_summary,
            ),
            *[
                replace(step, when=lambda a, s, ask=step.when: ask(a, s) and self.agents_are_new(s))
                for step in new
            ],
        ]

    def agents_are_new(self, scan: Scan) -> bool:
        """Say whether the setup is older than the agent settings and the rules question.

        :param scan: The facts of the project and the machine.
        :return: ``True`` when its release is before 0.3.0 or unknown."""
        return (old := setup_release(scan)) is None or release(old) < release(AGENT_SINCE)

    def ask_data(self, term: Term, a: Answers, scan: Scan) -> None:
        """Say that the data needs nothing, before anything is asked.

        :param term: The terminal.
        :param a: The answers.
        :param scan: The facts of the project and the machine."""
        p = scan.project
        done = lambda key, text: (  # noqa: E731
            f"{term.paint('g', '✓')} {key.ljust(15)}{term.paint('m', text)}"
        )
        with term.task("Checking runs, notes and views") as task:
            if p.runs:
                task.line(done(f"{p.runs} runs", "read as they are"))
            if p.notes or p.proposals or p.memories:
                task.line(done("notes, proposals", "read as they are"))
            task.line(done("views", "read as they are"))
            task.line(done("index", "a cache; rebuilt in the background when its schema changed"))

    def hosts(self, scan: Scan) -> dict[str, str]:
        """List the remotes of the project and of this machine that are not switched off.

        :param scan: The facts of the project and the machine.
        :return: Each remote's name with the ssh host it is reached by."""
        mine, given = user_remotes(), project_remotes(scan)
        names = [*given, *(n for n in mine if n not in given)]
        return {
            n: (mine.get(n) or {}).get("host") or n
            for n in names
            if (mine.get(n) or {}).get("enabled") is not False
        }

    def ask_check(self, term: Term, a: Answers, scan: Scan) -> None:
        """Probe the remotes at once; one with an older Beamtime becomes a ticked item.

        :param term: The terminal.
        :param a: The answers; ``update`` gains the stale remotes.
        :param scan: The facts of the project and the machine."""
        given = {**user_remotes(), **project_remotes(scan)}
        aliases = {h.name for h in scan.ssh_hosts}
        hosts = self.hosts(scan)
        reach = {n: h for n, h in hosts.items() if "@" in h or h in aliases}
        names = list(hosts)
        self.remote_stale = []
        with term.task(
            f"Checking {names[0] if len(names) == 1 else f'{len(names)} machines'}"
        ) as t:
            found = (
                self.probe(
                    list(reach.values()),
                    {h: (given.get(n) or {}).get("path") for n, h in reach.items()},
                )
                if reach
                else {}
            )
            for name, host in hosts.items():
                if name not in reach:
                    t.line(
                        f"{name.ljust(12)}{term.paint('w', '!')} ssh  "
                        + term.paint("m", "no such host here; add it to ~/.ssh/config")
                    )
                    continue
                t.line(probe_line(term, name, found[host]))
                if found[host].status == "ok" and (item := stale_remote(name, found[host].version)):
                    self.remote_stale.append(item)
                    if item.item not in a.update:
                        a.update = [*a.update, item.item]

    def ask_updates(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask which stale items to bring up to date, and which more past work to bring in.

        :param term: The terminal.
        :param a: The answers; ``update`` and the imports are changed in place.
        :param scan: The facts of the project and the machine."""
        from beamtime import __version__

        by_agent = bool(a.agents)
        current = [*a.update, *a.imports, *a.import_notes, *a.import_memory]
        options = []
        for stale in [*scan.stale, *self.remote_stale]:
            if stale.item != "runs":
                options.append(
                    Option(stale.item, self.name_of(stale), f"{stale.before}  →  {stale.after}")
                )
            elif past := next(
                (p for p in scan.past if shown(p.found.path, scan) == stale.path), None
            ):
                found = past.found
                self.rows[stale.path] = Row(
                    "imports", found.n, found.label, import_name(found.path), found.kind
                )
                options.append(self.option(stale.path, by_agent, True))
        shown_rows = {o.value for o in options}
        options += [
            self.option(v, by_agent, False)
            for v in self.rows
            if v in current and v not in shown_rows
        ]
        self.total = len(options)
        picked = term.multi(
            f"What should be brought up to {__version__}?",
            options,
            current,
            Add(
                "Add a path",
                "another log dir, notes folder or memory files",
                lambda t: self.check_path(t, scan, by_agent),
            ),
        )
        items = {s.item for s in [*scan.stale, *self.remote_stale]}
        a.update = [*(u for u in a.update if u not in items), *(v for v in picked if v in items)]
        for field in ("imports", "import_notes", "import_memory"):
            setattr(a, field, [v for v in picked if v in self.rows and self.rows[v].field == field])

    def updates_summary(self, a: Answers, scan: Scan) -> str:
        """Count what is brought up to date.

        :param a: The answers.
        :param scan: The facts of the project and the machine.
        :return: One line."""
        n = len(a.update) + len(a.imports) + len(a.import_notes) + len(a.import_memory)
        return f"{n} of {self.total} things"

    def name_of(self, stale: Stale) -> str:
        """Name a stale item as a row of the list.

        :param stale: The item.
        :return: E.g. ``Agent rules``, ``Beamtime on juwels`` or the folder of runs."""
        if stale.item.startswith("remote:"):
            return f"Beamtime on {stale.item.removeprefix('remote:')}"
        return stale.path or UPDATE_LABELS.get(stale.item, stale.item)

    def kept(self, a: Answers, scan: Scan) -> list[str]:
        """Name the stale items the answers leave as they are.

        :param a: The answers.
        :param scan: The facts of the project and the machine.
        :return: The names, in the order of the list."""
        out = []
        for stale in [*scan.stale, *self.remote_stale]:
            match stale.item:
                case "runs":
                    taken = stale.path in a.imports
                case "rules":
                    taken = "rules" in a.update and a.rules
                case _:
                    taken = stale.item in a.update
            if not taken:
                out.append(self.name_of(stale))
        return out

    def frame(self, term: Term, scan: Scan, a: Answers) -> tuple[list[str], list[str]]:
        """Write the lines around the review: the data, untouched, first, and what was kept last.

        :param term: The terminal.
        :param scan: The facts of the project and the machine.
        :param a: The answers.
        :return: The lines before the changes and the lines after them."""
        logdir = shown(scan.project.logdir, scan)
        head = [
            f"{term.paint('t', 'your data')}  {term.paint('m', 'nothing is rewritten')}",
            f"  {term.paint('m', logdir.ljust(18))}{counts(scan)} · as they are",
            "",
        ]
        kept = self.kept(a, scan)
        tail = (
            ["", f"{term.paint('t', 'kept as they are')}  {term.paint('m', ' · '.join(kept))}"]
            if kept
            else []
        )
        return head, tail


class Teammate:
    """The questions of a teammate on a project that uses Beamtime: this machine's part only."""

    def __init__(self, *, probe: Callable[..., dict[str, Probe]] = probe) -> None:
        """Keep what the questions share: the probe and what it found.

        :param probe: Asks the remote hosts what they have."""
        self.probe = probe
        self.probes: dict[str, Probe] = {}
        self.picked = False

    def steps(self) -> list[Step]:
        """List the questions in order.

        :return: The steps."""
        return [
            Step(
                id="agents",
                title="Which coding agents do you use on this machine?",
                ask=lambda term, a, s: pick_agents(
                    term, a, s, "Which coding agents do you use on this machine?"
                ),
                summary=lambda a, s: ", ".join(client_named(x).label for x in a.agents) or "none",
            ),
            Step(
                id="hosts",
                title="Which of the project's machines do you use?",
                ask=self.ask_hosts,
                when=lambda a, s: bool(s.project.remotes),
                summary=lambda a, s: ", ".join(r.name for r in a.remotes) or "none",
            ),
            Step(
                id="check",
                title="Checking the machines",
                ask=self.ask_check,
                when=lambda a, s: bool(a.remotes),
            ),
            Step(
                id="ssh",
                title="Log in once per session?",
                ask=self.ask_ssh,
                when=lambda a, s: any(self.shareable(r, s) for r in a.remotes),
            ),
            Step(
                id="reach",
                title="How do you reach a machine?",
                ask=self.ask_reach,
                when=lambda a, s: any(self.unreachable(r, s) for r in a.remotes),
            ),
        ]

    def ask_hosts(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask which of the project's remotes to use, and which own hosts to add.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        given, mine = project_remotes(scan), user_remotes()
        current = {(r.name if r.name in given else r.host or r.name): r for r in a.remotes}
        aliases = {h.name for h in scan.ssh_hosts}
        options = []
        for name in given:
            host = (mine.get(name) or {}).get("host") or name
            if (mine.get(name) or {}).get("enabled") is False:
                hint = "beamtime.yaml · skipped on this machine before"
            elif host == name:
                hint = f"beamtime.yaml · {'in' if name in aliases else 'not in'} ~/.ssh/config"
            else:
                hint = f"beamtime.yaml · as {host} in your settings"
            options.append(Option(name, name, hint))
        options += [Option(h, h, "added") for h in current if h not in given]
        default = (
            list(current)
            if self.picked
            else [n for n in given if (mine.get(n) or {}).get("enabled") is not False]
        )
        picked = term.multi(
            "Which of the project's machines do you use?",
            options,
            default,
            Add("Add a host", "an ssh alias or user@host", check_host),
        )
        self.picked = True
        a.remotes = [current.get(v) or (Remote(v) if v in given else new_remote(v)) for v in picked]
        a.skip_remotes = [n for n in given if n not in picked]

    def ask_check(self, term: Term, a: Answers, scan: Scan) -> None:
        """Check every machine at once; one that ssh can't find is named, not asked.

        :param term: The terminal.
        :param a: The answers.
        :param scan: The facts of the project and the machine."""
        self.check(term, a.remotes, scan)

    def check(self, term: Term, remotes: list[Remote], scan: Scan) -> None:
        """Probe the machines not probed yet, in one task, and word what was found.

        :param term: The terminal.
        :param remotes: The remotes to check.
        :param scan: The facts of the project and the machine."""
        given = project_remotes(scan)
        todo = {
            h: (given.get(r.name) or {}).get("path")
            for r in remotes
            if (h := self.address(r)) not in self.probes and not self.unreachable(r, scan)
        }
        names = [self.address(r) for r in remotes]
        title = f"Checking {names[0] if len(names) == 1 else f'{len(names)} machines'}"
        with term.task(title) as task:
            self.probes.update(self.probe(list(todo), todo) if todo else {})
            for r in remotes:
                host = self.address(r)
                if self.unreachable(r, scan):
                    task.line(
                        f"{host.ljust(12)}{term.paint('w', '!')} ssh  "
                        + term.paint(
                            "m", "no such host here; add it to ~/.ssh/config or type user@host"
                        )
                    )
                else:
                    task.line(probe_line(term, host, self.probes[host]))

    def ask_reach(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask how to reach each project remote that ssh doesn't know here; empty leaves it out.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        kept: list[Remote] = []
        for r in a.remotes:
            if not self.unreachable(r, scan):
                kept.append(r)
                continue
            host = term.text(
                f"How do you reach {r.name}?",
                "",
                f"user@host or an alias; leave empty to skip {r.name}.",
            ).strip()
            if not host:
                a.skip_remotes.append(r.name)
                continue
            kept.append(msgspec.structs.replace(r, host=host))
            self.check(term, kept[-1:], scan)
        a.remotes = kept

    def ask_ssh(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask, per host that needs a password and a code, whether to share one login.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        a.ssh_share = []
        kept: list[Remote] = []
        for r in a.remotes:
            if not self.shareable(r, scan):
                kept.append(r)
                continue
            host = self.address(r)
            lines = SSH_BLOCK.format(mark="", host=host).splitlines()[1:]
            while True:
                choice = term.select(
                    f"Log in to {host} once per session?",
                    [
                        Option("add", "Add these lines and log in now"),
                        Option("show", "Show them; I'll add them myself"),
                        Option("skip", f"Skip {host} for now"),
                    ],
                    "add",
                    body=[
                        "Adds to ~/.ssh/config:",
                        *[term.paint("c", f"  {line}") for line in lines],
                        term.paint(
                            "m",
                            "Then one login (password and code) lasts while you work; "
                            "Beamtime reuses it.",
                        ),
                    ],
                )
                if choice != "show":
                    break
                term.say(["Add these lines to ~/.ssh/config yourself, any time:", *lines, ""])
            if choice == "skip":
                a.skip_remotes.append(r.name)
                continue
            if choice == "add":
                a.ssh_share.append(r.name)
            kept.append(r)
        a.remotes = kept

    def address(self, remote: Remote) -> str:
        """Say how this machine reaches a remote: its own host, the user's setting, else its name.

        :param remote: The remote.
        :return: The ssh host."""
        return remote.host or (user_remotes().get(remote.name) or {}).get("host") or remote.name

    def unreachable(self, remote: Remote, scan: Scan) -> bool:
        """Tell whether a project remote has no way to be reached from here yet.

        :param remote: The remote.
        :param scan: The facts of the project and the machine.
        :return: ``True`` for a remote of the project that is no ssh alias and has no host."""
        host = self.address(remote)
        return (
            remote.name in project_remotes(scan)
            and "@" not in host
            and host not in {h.name for h in scan.ssh_hosts}
        )

    def shareable(self, remote: Remote, scan: Scan) -> bool:
        """Tell whether a remote asks for a password and a code and is an alias that can share one.

        :param remote: The remote.
        :param scan: The facts of the project and the machine.
        :return: ``True`` when the probe saw ``needs_code`` on an alias of the ssh config."""
        host = self.address(remote)
        found = self.probes.get(host)
        return (
            found is not None
            and found.status == "needs_code"
            and host in {h.name for h in scan.ssh_hosts}
        )


class Cluster:
    """The questions on a cluster login node: role, runs, cache, and agents for role ``full``."""

    def steps(self) -> list[Step]:
        """List the questions in order.

        :return: The steps."""
        terminal = tuple(c for c in CLIENTS if c.start or c.name == "other")
        return [
            Step(
                id="role",
                title="What should this machine do?",
                ask=self.ask_role,
                summary=lambda a, s: "record runs" if a.role == "record" else "record and look",
            ),
            Step(
                id="runs",
                title="Where should runs go on this cluster?",
                ask=self.ask_runs,
                summary=lambda a, s: (
                    f"{a.logdir.rstrip('/')}/ -> {a.link_logdir}"
                    if a.link_logdir
                    else "in the checkout"
                ),
            ),
            Step(
                id="cache",
                title="Keep an index on this cluster between connections?",
                ask=self.ask_cache,
                summary=lambda a, s: "no" if a.cache in (None, "memory") else a.cache,
            ),
            Step(
                id="agents",
                title="Which coding agents run on this node?",
                ask=lambda term, a, s: pick_agents(
                    term, a, s, "Which coding agents run on this node?", terminal
                ),
                when=lambda a, s: a.role == "full",
                summary=lambda a, s: ", ".join(client_named(x).label for x in a.agents) or "none",
            ),
        ]

    def ask_role(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask whether the node only records runs or also shows them; recording needs no agents.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        a.role = term.select(
            "What should this machine do?",
            [
                Option("record", "Record runs", "I look at them from my laptop"),
                Option(
                    "full", "Record runs and look at them here", "agents and the CLI on this node"
                ),
            ],
            a.role,
        )
        if a.role == "record":
            a.agents = []

    def ask_runs(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask where runs go: a link to scratch, the checkout, or another place.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        name = a.logdir.rstrip("/")
        scratch = next((d for d in scan.disks if d.label in SCRATCH_VARS), None)
        target = f"${{{scratch.label}}}/{scan.root.name}/{Path(name).name}" if scratch else None
        options = []
        if target:
            options.append(Option("link", f"Link {name}/ to {target}", "recommended"))
        options += [
            Option("keep", "Keep runs in the checkout", "$HOME has a small quota"),
            Option("other", "Another place"),
        ]
        if a.link_logdir:
            default = "link" if a.link_logdir == target else "other"
        else:
            path = scan.root / expand_path(name)
            default = "link" if target and (path.is_symlink() or not scan.project.runs) else "keep"
        match term.select("Where should runs go on this cluster?", options, default):
            case "link":
                a.link_logdir = target
            case "other":
                typed = term.text("Where?", a.link_logdir or "", "~ and $VARS expand.")
                a.link_logdir = typed.strip() or None
            case _:
                a.link_logdir = None

    def ask_cache(self, term: Term, a: Answers, scan: Scan) -> None:
        """Ask whether the index survives between connections, on this node's local disk.

        :param term: The terminal.
        :param a: The answers; changed in place.
        :param scan: The facts of the project and the machine."""
        local = "/tmp/{user}/beamtime-cache"
        kept = a.cache or user_cache()
        node = socket.gethostname().split(".")[0]
        options = [
            Option("memory", "No", "index in memory per connection (default)"),
            Option("tmp", f"Yes, in {local}", f"local disk on {node}"),
        ]
        if kept not in (None, "memory", local):
            options.append(Option("current", kept, "from your settings"))
        default = "memory" if kept in (None, "memory") else "tmp" if kept == local else "current"
        note = "Your laptop's view of these runs starts faster with one, on the same node."
        match term.select(
            "Keep an index on this cluster between connections?",
            options,
            default,
            body=[term.paint("m", note)],
        ):
            case "tmp":
                a.cache = local
            case "current":
                a.cache = kept
            case _:
                a.cache = "memory" if kept else None


def project_remotes(scan: Scan) -> dict[str, dict[str, Any]]:
    """Read the remotes the project's ``beamtime.yaml`` names.

    :param scan: The facts of the project and the machine.
    :return: Each remote's name with its settings."""
    return remotes_of(Planner.read(scan.root / "beamtime.yaml"))


def user_remotes() -> dict[str, dict[str, Any]]:
    """Read the remotes this machine's settings name.

    :return: Each remote's name with its settings."""
    return remotes_of(Planner.read(user_settings_path()))


def remotes_of(settings: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Take the ``remotes`` table of a settings file.

    :param settings: The file's mapping.
    :return: Each remote's name with its settings; empty when the table is missing or malformed."""
    given = settings.get("remotes")
    if not isinstance(given, dict):
        return {}
    return {n: v if isinstance(v, dict) else {} for n, v in given.items()}


def user_cache() -> str | None:
    """Read the ``cache`` this machine's settings hold.

    :return: The setting, or ``None``."""
    given = Planner.read(user_settings_path()).get("cache")
    return given if isinstance(given, str) else None


def pick_agents(
    term: Term, a: Answers, scan: Scan, title: str, clients: tuple[Any, ...] = CLIENTS
) -> None:
    """Ask which of the agent clients to set up; the ones the scan found are marked with why.

    :param term: The terminal.
    :param a: The answers; changed in place.
    :param scan: The facts of the project and the machine.
    :param title: The question.
    :param clients: The clients to offer, from the client table."""
    found = {f.client: f for f in scan.agents}
    hints = {"other": "prints its MCP config to paste"}
    options = [
        Option(
            c.name,
            c.label,
            (found_hint(found[c.name], scan) if found[c.name].files else "on PATH")
            if c.name in found
            else hints.get(c.name),
        )
        for c in clients
    ]
    options.append(Option("none", "None", "I use Beamtime without an agent", exclusive=True))
    picked = term.multi(title, options, a.agents or ["none"])
    a.agents = [v for v in picked if v != "none"]


def check_host(text: str) -> Option | str:
    """Check a typed host as it is typed.

    :param text: An ssh alias or ``user@host``.
    :return: The row to add, or what is wrong with the text."""
    host = text.strip()
    if not host or any(c.isspace() for c in host):
        return "an ssh alias or user@host"
    if problem := remote_name_problem(source_name(host)):
        return problem
    hint = (
        "added · used as given" if "@" in host else "added · not in ~/.ssh/config, ssh resolves it"
    )
    return Option(host, host, hint)


def found_hint(agent: Any, scan: Scan) -> str:
    """Say which file shows that an agent is used in the project.

    :param agent: A ``scan.AgentFound``.
    :param scan: The facts of the project and the machine.
    :return: E.g. ``found .claude/``."""
    name = agent.files[0]
    return f"found {name}" + ("/" if (scan.root / name).is_dir() else "")


def source_name(host: str) -> str:
    """Make the source name of a host: the machine's name without user and domain.

    :param host: An ssh alias or ``user@host``.
    :return: The name."""
    return host.rpartition("@")[2].split(".")[0]


def new_remote(host: str) -> Remote:
    """Make the remote of a host the person picked.

    :param host: An ssh alias or ``user@host``.
    :return: The remote; its host is left out when it is the name."""
    name = source_name(host)
    return Remote(name, None if host == name else host)


def probe_line(term: Term, host: str, found: Probe) -> str:
    """Word what the probe found on a host, in the mockup's shape.

    :param term: The terminal, for its colors.
    :param host: The ssh host.
    :param found: The probe.
    :return: One line."""
    good, bad, m = term.paint("g", "✓"), term.paint("b", "✗"), lambda t: term.paint("m", t)  # noqa: E731
    name = host.ljust(12)
    match found.status:
        case "ok":
            from beamtime import __version__

            if found.version and release(found.version) < release(__version__):
                warn, note = term.paint("w", "!"), m(f"· older than {__version__}")
                return f"{name}{good} ssh  {warn} beamtime {found.version}  {note}"
            disk = f" {m('· ' + disk_note(found))}" if disk_note(found) else ""
            return f"{name}{good} ssh  {good} beamtime {found.version}{disk}"
        case "no_beamtime":
            return (
                f"{name}{good} ssh  {bad} beamtime not found  {m(f'· python {found.python} there')}"
            )
        case "old_python":
            return f"{name}{good} ssh  {bad} {found.detail}"
        case "needs_code":
            return f"{name}{bad} ssh  needs a password or code, which a check can't give"
        case "unknown_host":
            return f"{name}{bad} ssh  host key not known yet; connect once with ssh {host}"
        case _:
            return f"{name}{bad} ssh  {found.detail}"


def disk_note(found: Probe) -> str:
    """Say what the log dir's disk means for the index.

    :param found: The probe.
    :return: E.g. ``${SCRATCH} is gpfs, index in memory``, or an empty string."""
    from beamtime.index.cache import NETWORK_FS

    if not (found.scratch and found.fstype):
        return ""
    where = "${SCRATCH} is " + found.fstype
    return f"{where}, index in memory" if found.fstype in NETWORK_FS else where
