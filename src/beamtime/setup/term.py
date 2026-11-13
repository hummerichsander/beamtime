"""Prompt primitives for the setup wizard, on the standard library only."""

import codecs
import os
import re
import select
import shutil
import sys
from collections.abc import Callable, Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from types import TracebackType
from typing import TextIO

STYLES = {
    "m": "90",
    "r": "90",
    "k": "90",
    "g": "32",
    "w": "33",
    "b": "31",
    "a": "94",
    "t": "1",
    "i": "7",
}
ARROWS = {"A": "up", "B": "down", "C": "right", "D": "left"}
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|.")


class Aborted(Exception):
    """The person quit a prompt with ctrl-c, `q` or the end of input."""


@dataclass(frozen=True)
class Option:
    """One row of a `select` or `multi` prompt."""

    value: str
    label: str
    hint: str | None = None
    exclusive: bool = False


@dataclass(frozen=True)
class Add:
    """The `+ Add` row of a `multi` prompt; `check` returns the new option or the error to show."""

    label: str
    prompt: str
    check: Callable[[str], Option | str]


@dataclass(frozen=True)
class FormRow:
    """One setting of a `form`: key, label, the values to cycle through, and whether detected."""

    key: str
    label: str
    values: tuple[str, ...]
    detected: bool = False


def name_of(ch: str) -> str | None:
    """Name a typed character as `keys()` yields it, or `None` for control characters to ignore.

    :param ch: One decoded character.
    :return: The key name."""
    match ch:
        case "\r" | "\n":
            return "enter"
        case " ":
            return "space"
        case "\x03" | "\x04":
            return "ctrl-c"
        case "\x7f" | "\x08":
            return "backspace"
    if ch.isdigit():
        return f"digit:{ch}"
    return f"char:{ch}" if ch.isprintable() else None


def posix_keys(fd: int) -> Iterator[str]:
    """Yield key names from a POSIX terminal in raw mode, restoring its attributes on close.

    :param fd: File descriptor of the terminal.
    :return: The key names."""
    import termios

    saved = termios.tcgetattr(fd)
    raw = termios.tcgetattr(fd)
    raw[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG | termios.IEXTEN)
    raw[6][termios.VMIN], raw[6][termios.VTIME] = 1, 0
    termios.tcsetattr(fd, termios.TCSADRAIN, raw)
    decoder = codecs.getincrementaldecoder("utf-8")(errors="ignore")
    pending = b""
    try:
        while True:
            if not (b := pending or os.read(fd, 1)):
                yield "ctrl-c"
                return
            pending = b""
            if not (ch := decoder.decode(b)):
                continue
            if ch != "\x1b":
                if key := name_of(ch):
                    yield key
            elif not select.select([fd], [], [], 0.05)[0]:
                yield "esc"
            elif (second := os.read(fd, 1)) not in (b"[", b"O"):
                yield "esc"
                pending = second
            else:
                while (c := os.read(fd, 1)) and not 0x40 <= c[0] <= 0x7E:
                    pass
                if key := ARROWS.get(c.decode("ascii", "ignore")):
                    yield key
    finally:
        # flush: on BSD any other restore leaves the kernel's PENDIN flag set.
        termios.tcsetattr(fd, termios.TCSAFLUSH, saved)


def windows_keys() -> Iterator[str]:
    """Yield key names from the Windows console.

    :return: The key names."""
    import msvcrt

    arrows = {"H": "up", "P": "down", "K": "left", "M": "right"}
    while True:
        if (ch := msvcrt.getwch()) in ("\x00", "\xe0"):
            if key := arrows.get(msvcrt.getwch()):
                yield key
        elif key := ("esc" if ch == "\x1b" else name_of(ch)):
            yield key


class TaskLines:
    """A task's header and the lines that appear under it as work finishes."""

    def __init__(self, term: "Term", title: str) -> None:
        self.term = term
        self.title = title
        self.count = 0

    def __enter__(self) -> "TaskLines":
        glyph = self.term.paint("a", "◒") if self.term.raw else self.term.paint("m", "◇")
        self.term.emit([f"{glyph}  {self.term.paint('t', self.title)}"])
        return self

    def line(self, text: str) -> None:
        """Show one line under the task's title.

        :param text: The line."""
        self.term.emit([self.term.rail(text)])
        self.count += 1

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        term = self.term
        if term.raw:
            glyph = term.paint("b", "✗") if kind else term.paint("m", "◇")
            up = self.count + 1
            term.write(f"\x1b[{up}A\r{glyph}  {term.paint('t', self.title)}\x1b[K\x1b[{up}B")
        if not kind:
            term.emit([term.rail("")])


class Term:
    """Prompts that draw on a terminal with raw keys, or ask by numbered lines over a pipe."""

    def __init__(
        self,
        *,
        inp: TextIO | None = None,
        out: TextIO | None = None,
        color: bool = True,
        raw: bool = True,
        width: int | None = None,
    ) -> None:
        self.inp = inp or sys.stdin
        self.out = out or sys.stdout
        self.color = color
        self.raw = raw
        self.width = width
        self.drawn = 0

    @classmethod
    def detect(cls) -> "Term":
        """Build the terminal for the process: raw keys on a terminal, no color for `NO_COLOR`.

        :return: The terminal."""
        tty = sys.stdin.isatty() and sys.stdout.isatty()
        raw = tty and os.environ.get("TERM") != "dumb"
        return cls(color=sys.stdout.isatty() and "NO_COLOR" not in os.environ, raw=raw)

    def select(
        self,
        title: str,
        options: Sequence[Option],
        default: str,
        hint: str | None = None,
        body: Sequence[str] = (),
    ) -> str:
        """Ask for one of several options.

        :param title: The question.
        :param options: The rows.
        :param default: The value of the row the cursor starts on, and the answer to an empty line.
        :param hint: A muted line under the title.
        :param body: Lines shown under the hint.
        :return: The chosen value."""
        values = [o.value for o in options]
        cur = values.index(default) if default in values else 0
        if not self.raw:
            self.head_plain(title, hint, body)
            self.numbered(options, [cur])
            while (
                picked := self.numbers(self.ask(f"Choose [{cur + 1}]: "), len(options), [cur])
            ) is None or len(picked) != 1:
                self.write("Pick one number.\n")
            return options[picked[0]].value

        def frame() -> list[str]:
            rows = [
                self.row(self.paint("a", "●") if i == cur else self.paint("m", "○"), o, i == cur)
                for i, o in enumerate(options)
            ]
            return [
                *self.head(title, hint, body),
                *rows,
                self.foot("↑↓ move · enter confirm · q quits"),
            ]

        with self.session(frame, quit_on_q=True) as keys:
            for key in keys:
                match key:
                    case "up" | "char:k":
                        cur = (cur - 1) % len(options)
                    case "down" | "char:j":
                        cur = (cur + 1) % len(options)
                    case _ if key.startswith("digit:") and 0 < int(key[6:]) <= len(options):
                        cur = int(key[6:]) - 1
                    case "enter":
                        break
                self.draw(frame())
        self.erase()
        self.collapse(title, options[cur].label)
        return options[cur].value

    def multi(
        self, title: str, options: Sequence[Option], default: Sequence[str], add: Add | None = None
    ) -> list[str]:
        """Ask for any number of options, with an optional row that adds a checked entry.

        :param title: The question.
        :param options: The rows.
        :param default: The values ticked at the start.
        :param add: The `+ Add` row, or `None`.
        :return: The ticked values, in the order of the rows."""
        options = list(options)
        ticked = [o.value for o in options if o.value in default]
        if not self.raw:
            self.head_plain(title, None, ())
            self.numbered(options, [i for i, o in enumerate(options) if o.value in ticked], add)
            while True:
                line = self.ask("Choose, comma separated [Enter keeps the marked ones]: ")
                picked = self.numbers(
                    line,
                    len(options) + (add is not None),
                    [options.index(o) for o in options if o.value in ticked],
                )
                if picked is None:
                    self.write("Pick numbers from the list.\n")
                    continue
                ticked = []
                for i in picked:
                    if i < len(options):
                        ticked = self.tick(options, ticked, options[i])
                        continue
                    while isinstance(found := add.check(self.ask(f"{add.prompt}: ").strip()), str):
                        self.write(f"{found}\n")
                    if found.value not in [o.value for o in options]:
                        options.append(found)
                    ticked = self.tick(options, ticked, found)
                return [o.value for o in options if o.value in ticked]

        cur = next((i for i, o in enumerate(options) if o.value in ticked), 0)
        moved = False
        typed: str | None = None
        error: str | None = None

        def frame() -> list[str]:
            rows = [
                self.row(
                    self.paint("a", "◼") if o.value in ticked else self.paint("m", "◻"), o, i == cur
                )
                for i, o in enumerate(options)
            ]
            if add is not None and typed is not None:
                cursor = self.paint("a", "▍")
                rows.append(
                    self.rail(
                        f"{self.paint('a', '+')} {self.paint('m', add.prompt)} {typed}{cursor}"
                    )
                )
                if error:
                    rows.append(self.rail(f"  {self.paint('w', '!')} {self.paint('w', error)}"))
            elif add is not None:
                on = cur == len(options)
                rows.append(self.rail(self.paint("a" if on else "m", f"+ {add.label}…")))
            more = " · + adds your own" if add else ""
            return [
                *self.head(title, None, ()),
                *rows,
                self.foot(f"{len(ticked)} selected · ↑↓ move · space select · enter confirm{more}"),
            ]

        with self.session(frame) as keys:
            for key in keys:
                if typed is not None:
                    error = None
                    match key:
                        case "enter" if typed.strip():
                            match add.check(typed.strip()):
                                case str() as error:
                                    pass
                                case Option() as found:
                                    if found.value not in [o.value for o in options]:
                                        options.append(found)
                                    cur = [o.value for o in options].index(found.value)
                                    if found.value not in ticked:
                                        ticked = self.tick(options, ticked, found)
                                    typed = None
                        case "esc":
                            typed = None
                        case "backspace":
                            typed = typed[:-1]
                        case "space":
                            typed += " "
                        case _ if key.startswith(("char:", "digit:")):
                            typed += key.split(":", 1)[1]
                    self.draw(frame())
                    continue
                on_add = add is not None and cur == len(options)
                match key:
                    case "char:q":
                        raise Aborted
                    case "up" | "char:k":
                        cur, moved = (cur - 1) % (len(options) + (add is not None)), True
                    case "down" | "char:j":
                        cur, moved = (cur + 1) % (len(options) + (add is not None)), True
                    case "char:+" if add is not None:
                        cur, typed = len(options), ""
                    case _ if key.startswith("digit:") and 0 < int(key[6:]) <= len(options):
                        cur, moved = int(key[6:]) - 1, True
                    case "space" | "enter" if on_add:
                        typed = ""
                    case "space":
                        ticked = self.tick(options, ticked, options[cur], toggle=True)
                    case "enter":
                        if moved and options[cur].value not in ticked:
                            ticked = self.tick(options, ticked, options[cur])
                        break
                self.draw(frame())
        self.erase()
        chosen = [o for o in options if o.value in ticked]
        self.collapse(title, ", ".join(o.label for o in chosen) or "none")
        return [o.value for o in chosen]

    def text(self, title: str, default: str, hint: str | None = None) -> str:
        """Ask for a line of text.

        :param title: The question.
        :param default: The answer to an empty line, shown as a placeholder.
        :param hint: A muted line under the title.
        :return: The typed text, or the default."""
        if not self.raw:
            self.head_plain(title, hint, ())
            return self.ask(f"[{default}] ").strip() or default
        typed = ""

        def frame() -> list[str]:
            shown = (
                typed + self.paint("a", "▍")
                if typed
                else self.paint("a", "▍") + self.paint("m", default)
            )
            return [
                *self.head(title, hint, ()),
                self.rail(f"{self.paint('a', '›')} {shown}"),
                self.foot("enter confirm"),
            ]

        with self.session(frame) as keys:
            for key in keys:
                match key:
                    case "enter":
                        break
                    case "backspace":
                        typed = typed[:-1]
                    case "space":
                        typed += " "
                    case _ if key.startswith(("char:", "digit:")):
                        typed += key.split(":", 1)[1]
                self.draw(frame())
        self.erase()
        self.collapse(title, typed.strip() or default)
        return typed.strip() or default

    def form(self, title: str, rows: Sequence[FormRow], default: dict[str, str]) -> dict[str, str]:
        """Ask for several settings, each one a choice among a few values.

        :param title: The question.
        :param rows: The settings.
        :param default: The starting value by key; a missing key starts on the first value.
        :return: The chosen value of each setting by key."""
        answers = {
            r.key: default[r.key] if default.get(r.key) in r.values else r.values[0] for r in rows
        }
        if not self.raw:
            self.head_plain(title, None, ())
            for r in rows:
                self.numbered(
                    [Option(v, v) for v in r.values],
                    [r.values.index(answers[r.key])],
                    heading=r.label,
                )
                while (
                    picked := self.numbers(
                        self.ask(f"{r.label} [{r.values.index(answers[r.key]) + 1}]: "),
                        len(r.values),
                        [r.values.index(answers[r.key])],
                    )
                ) is None or len(picked) != 1:
                    self.write("Pick one number.\n")
                answers[r.key] = r.values[picked[0]]
            return answers
        cur = 0

        def frame() -> list[str]:
            width = max(len(r.label) for r in rows) + 2
            lines = []
            for i, r in enumerate(rows):
                label = (r.label + " " * width)[:width]
                choices = "  ".join(self.choice(v, v == answers[r.key]) for v in r.values)
                note = "  " + self.paint("m", "detected") if r.detected else ""
                mark = self.paint("a", "›") if i == cur else " "
                lines.append(
                    self.rail(
                        f"{mark} {self.paint('a' if i == cur else 'c', label)}{choices}{note}"
                    )
                )
            return [
                *self.head(title, None, ()),
                *lines,
                self.foot("↑↓ setting · ←→ value · enter confirm · q quits"),
            ]

        with self.session(frame, quit_on_q=True) as keys:
            for key in keys:
                row = rows[cur]
                step = 0
                match key:
                    case "up" | "char:k":
                        cur = (cur - 1) % len(rows)
                    case "down" | "char:j":
                        cur = (cur + 1) % len(rows)
                    case "right" | "char:l":
                        step = 1
                    case "left" | "char:h":
                        step = -1
                    case "enter":
                        break
                if step:
                    answers[row.key] = row.values[
                        (row.values.index(answers[row.key]) + step) % len(row.values)
                    ]
                self.draw(frame())
        self.erase()
        self.collapse(title, ", ".join(f"{r.label} {answers[r.key]}" for r in rows))
        return answers

    def task(self, title: str) -> TaskLines:
        """Start a task whose lines appear as work finishes.

        :param title: The task's title.
        :return: A context manager with `line(text)`."""
        return TaskLines(self, title)

    def say(self, lines: Iterable[str]) -> None:
        """Show lines on the rail; an empty line shows the bare rail.

        :param lines: The lines."""
        self.emit([self.rail(line) for line in lines])

    def collapse(self, title: str, summary: str) -> None:
        """Show an answered step as its title and the answer.

        :param title: The question.
        :param summary: The answer in a few words."""
        self.emit(
            [
                f"{self.paint('m', '◇')}  {self.paint('t', title)}",
                self.rail(self.paint("m", summary)),
                self.rail(""),
            ]
        )

    def paint(self, style: str, text: str) -> str:
        """Color text with one of the mockup's span classes (`m`, `g`, `w`, `b`, `a`, `t`).

        :param style: The class letter.
        :param text: The text.
        :return: The text with escapes around it, or unchanged without color."""
        if not self.color or style not in STYLES:
            return text
        return f"\x1b[{STYLES[style]}m{text}\x1b[0m"

    def rail(self, text: str) -> str:
        """Put text on the rail.

        :param text: The text, empty for the bare rail.
        :return: The line."""
        return f"{self.paint('r', '│')}  {text}" if text else self.paint("r", "│")

    def keys(self) -> Iterator[str]:
        """Yield `up`, `down`, `left`, `right`, `space`, `enter`, `esc`, `backspace`, `digit:<n>`,
        `char:<c>` and `ctrl-c`.

        :return: The key names."""
        if sys.platform == "win32":
            yield from windows_keys()
        else:
            yield from posix_keys(self.inp.fileno())

    @contextmanager
    def session(
        self, frame: Callable[[], list[str]], quit_on_q: bool = False
    ) -> Iterator[Iterator[str]]:
        """Draw the first frame and hand out keys; ctrl-c, end of input and `q` raise `Aborted`.

        :param frame: Builds the lines of the active block.
        :param quit_on_q: Whether `q` quits.
        :return: The keys."""
        raw_keys = self.keys()

        def checked() -> Iterator[str]:
            for key in raw_keys:
                if key == "ctrl-c" or (quit_on_q and key == "char:q"):
                    raise Aborted
                yield key

        self.write("\x1b[?25l")
        self.draw(frame())
        try:
            yield checked()
        finally:
            raw_keys.close()
            self.write("\x1b[?25h")

    def draw(self, lines: list[str]) -> None:
        """Replace the active block with new lines.

        :param lines: The block's lines."""
        self.erase()
        self.emit(lines)
        self.drawn = len(lines)

    def erase(self) -> None:
        """Remove the active block from the screen."""
        if self.drawn:
            self.write(f"\x1b[{self.drawn}A\r\x1b[J")
            self.drawn = 0

    def emit(self, lines: Iterable[str]) -> None:
        """Write lines, each cut to the terminal's width so a long hint never wraps the rail.

        :param lines: The lines."""
        self.write("".join(f"{self.clip(line)}\n" for line in lines))

    def write(self, text: str) -> None:
        """Write and flush.

        :param text: The text."""
        self.out.write(text)
        self.out.flush()

    def clip(self, line: str) -> str:
        """Cut a line to the terminal's width with an ellipsis, counting only visible characters.

        :param line: The line, possibly with color escapes.
        :return: The line, shortened if needed."""
        room = self.columns() - 1
        if len(ANSI.sub(lambda m: "" if len(m[0]) > 1 else m[0], line)) <= room:
            return line
        kept, seen = [], 0
        for token in ANSI.findall(line):
            if len(token) > 1:
                kept.append(token)
            elif seen < room - 1:
                kept.append(token)
                seen += 1
            else:
                break
        return "".join(kept) + "…" + ("\x1b[0m" if self.color else "")

    def columns(self) -> int:
        """The terminal's width.

        :return: The number of columns."""
        if self.width:
            return self.width
        try:
            return os.get_terminal_size(self.out.fileno()).columns
        except (OSError, ValueError, AttributeError):
            return shutil.get_terminal_size().columns

    def head(self, title: str, hint: str | None, body: Sequence[str]) -> list[str]:
        """Lines of an active step above its rows.

        :param title: The question.
        :param hint: A muted line, or `None`.
        :param body: Further lines.
        :return: The lines."""
        lines = [f"{self.paint('a', '◆')}  {self.paint('t', title)}"]
        lines += [self.rail(self.paint("m", hint))] if hint else []
        lines += [self.rail(b) for b in body]
        return lines + [self.rail("")] if hint or body else lines

    def row(self, mark: str, option: Option, on: bool) -> str:
        """One option row.

        :param mark: The glyph in front of the label.
        :param option: The option.
        :param on: Whether the cursor is on it.
        :return: The line."""
        hint = f"  {self.paint('m', option.hint)}" if option.hint else ""
        return self.rail(f"{mark} {self.paint('a' if on else 'c', option.label)}{hint}")

    def foot(self, keys: str) -> str:
        """The line that closes an active step.

        :param keys: The key help.
        :return: The line."""
        return f"{self.paint('r', '└')}  {self.paint('k', keys)}"

    def choice(self, value: str, on: bool) -> str:
        """One value of a form row; the chosen one is inverted, or bracketed without color.

        :param value: The value.
        :param on: Whether it is chosen.
        :return: The text."""
        if not on:
            return self.paint("m", value)
        return self.paint("i", f" {value} ") if self.color else f"[{value}]"

    def tick(
        self, options: Sequence[Option], ticked: list[str], option: Option, toggle: bool = False
    ) -> list[str]:
        """Tick an option (or flip it); an exclusive option clears the others and vice versa.

        :param options: All rows.
        :param ticked: The ticked values.
        :param option: The option to tick.
        :param toggle: Whether a ticked option is unticked.
        :return: The new ticked values."""
        if option.value in ticked:
            return [v for v in ticked if v != option.value] if toggle else ticked
        if option.exclusive:
            return [option.value]
        exclusive = {o.value for o in options if o.exclusive}
        return [v for v in ticked if v not in exclusive] + [option.value]

    def head_plain(self, title: str, hint: str | None, body: Sequence[str]) -> None:
        """Print a question for the numbered fallback.

        :param title: The question.
        :param hint: A line under it, or `None`.
        :param body: Further lines."""
        self.emit([self.paint("t", title), *([hint] if hint else []), *body])

    def numbered(
        self,
        options: Sequence[Option],
        marked: list[int],
        add: Add | None = None,
        heading: str | None = None,
    ) -> None:
        """Print numbered rows for the fallback.

        :param options: The rows.
        :param marked: Indexes of the rows to mark as the default.
        :param add: The `+ Add` row, printed last.
        :param heading: A label printed above the rows."""
        lines = [heading] if heading else []
        for i, o in enumerate(options):
            lines.append(
                f"  {i + 1}. {'*' if i in marked else ' '} {o.label}"
                + (f"  {self.paint('m', o.hint)}" if o.hint else "")
            )
        if add is not None:
            lines.append(f"  {len(options) + 1}.   + {add.label}")
        self.emit(lines)

    def numbers(self, line: str, count: int, default: list[int]) -> list[int] | None:
        """Read `2` or `1,3` as zero-based row indexes; an empty line gives the default.

        :param line: The typed line.
        :param count: The number of rows.
        :param default: The indexes for an empty line.
        :return: The indexes, or `None` if the line is not valid."""
        if not (parts := line.replace(",", " ").split()):
            return default
        if not all(p.isdigit() and 0 < int(p) <= count for p in parts):
            return None
        return [int(p) - 1 for p in parts]

    def ask(self, prompt: str) -> str:
        """Read one line for the fallback.

        :param prompt: The prompt to print first.
        :return: The line without its newline."""
        self.write(prompt)
        try:
            line = self.inp.readline()
        except KeyboardInterrupt as error:
            raise Aborted from error
        if not line:
            raise Aborted
        return line.rstrip("\r\n")
