"""The wizard: the steps of the first setup, the review, the apply and the next steps."""

import re
import shlex
import shutil
import textwrap
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import msgspec

from beamtime.settings import PRESETS, expand_path
from beamtime.setup.agents import CLIENTS, client_named
from beamtime.setup.apply import apply
from beamtime.setup.importers import detect, files
from beamtime.setup.plan import (
    PATH_START,
    Answers,
    Planner,
    Remote,
    command,
    display_path,
    import_name,
    log_root,
    plan,
    review,
)
from beamtime.setup.remotes import Probe, probe, remote_name_problem
from beamtime.setup.scan import Scan
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
    "memory_tokens": ("memory budget", [("1k", "1000"), ("1.5k", "1500"), ("3k", "3000")]),
    "render_rounds": ("render rounds", [("1", "1"), ("2", "2"), ("3", "3")]),
    "custom_blocks": ("custom blocks", [("built-in first", "builtin_first"), ("free", "free")]),
}
RULE_OPTIONS = [
    Option("record", "Write the rules", "Beamtime is the record"),
    Option("none", "Skip", "only the MCP server; agents find the tools on their own"),
]


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
    :param steps: The questions; by default those of the first setup.
    :param probe: Asks the remote hosts what they have.
    :param which: Looks up a program on ``PATH``.
    :return: The answers to write, or ``None`` when the person quit or wanted only the command."""
    steps = steps or FirstSetup(probe=probe, which=which).steps()
    fill(scan, answers)
    try:
        intro(term, scan)
        start = 0
        while True:
            for step in steps[start:]:
                if step.when(answers, scan):
                    step.ask(term, answers, scan)
            match confirm(term, scan, answers, which):
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
    if (final := run(term, scan, answers, probe=probe, which=which)) is None:
        return []
    changes = plan(scan, final, which=which)
    said: list[str] = []
    try:
        with term.task("Setting up") as task:

            def line(text: str) -> None:
                said.append(text)
                task.line(f"{term.paint('g', '✓')} {text}")

            done = apply(changes, line)
    except KeyboardInterrupt:
        term.say([f"Interrupted. Done so far: {', '.join(said) or 'nothing'}"])
        return []
    next_steps(term, scan, final)
    return [c.label for c in done]


def fill(scan: Scan, answers: Answers) -> None:
    """Preselect what the scan found, where the flags left an answer at its plain default.

    :param scan: The facts of the project and the machine.
    :param answers: The answers; changed in place."""
    if answers.runs == "here" and scan.job_scripts and scan.ssh_hosts:
        answers.runs = "both"
    if not answers.agents:
        answers.agents = [a.client for a in scan.agents]
    if not answers.sdk and sdk_applies(scan):
        answers.sdk = True


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
    term.emit(
        [
            f"{term.paint('a', '///')} {term.paint('t', 'beamtime')} "
            f"{term.paint('m', __version__)}",
            term.paint("r", "┌"),
            term.rail(f"Set up Beamtime for {root}."),
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


def confirm(term: Term, scan: Scan, answers: Answers, which: Callable[[str], str | None]) -> str:
    """Show the review and ask what to do with it.

    :param term: The terminal.
    :param scan: The facts of the project and the machine.
    :param answers: The answers.
    :param which: Looks up a program on ``PATH``.
    :return: ``write``, ``change``, ``command``, or ``none`` when there is nothing to change."""
    try:
        changes = plan(scan, answers, which=which)
    except ValueError as e:
        term.say([f"{term.paint('w', '!')} {e}", ""])
        return "change"
    if not changes:
        return "none"
    body = [line if line.startswith(" ") else term.paint("t", line) for line in review(changes)]
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


def pick_answer(term: Term, steps: list[Step], answers: Answers, scan: Scan) -> int:
    """Ask which answer to change; the later answers stay as they are, as the defaults.

    :param term: The terminal.
    :param steps: The questions.
    :param answers: The answers.
    :param scan: The facts of the project and the machine.
    :return: The index of the step to go back to."""
    rows = [(i, s) for i, s in enumerate(steps) if s.summary and s.when(answers, scan)]
    options = [Option(s.id, s.title, s.summary(answers, scan)) for _, s in rows]
    chosen = term.select("Which answer?", options, options[0].value)
    return next(i for i, s in rows if s.id == chosen)


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

        def check(text: str) -> Option | str:
            host = text.strip()
            if not host or any(c.isspace() for c in host):
                return "an ssh alias or user@host"
            if problem := remote_name_problem(source_name(host)):
                return problem
            hint = (
                "added · used as given"
                if "@" in host
                else "added · not in ~/.ssh/config, ssh resolves it"
            )
            return Option(host, host, hint)

        picked = term.multi(
            "Which machines?",
            options,
            default,
            Add("Add a host", "an ssh alias or user@host", check),
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
            for c in CLIENTS
        ]
        options.append(Option("none", "None", "I use Beamtime without an agent", exclusive=True))
        picked = term.multi(
            "Which coding agents should know about Beamtime?",
            options,
            a.agents or ["none"],
        )
        a.agents = [v for v in picked if v != "none"]

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
            "Agents read this block at the start of every session.",
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
