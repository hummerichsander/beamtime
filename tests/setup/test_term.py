"""The prompt primitives, driven through a pseudo-terminal and over a pipe."""

from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
import os
import re
import sys
import threading
import time

import pytest

from beamtime.setup.term import Aborted, Add, FormRow, Option, Term, name_of

UP, DOWN, RIGHT, LEFT = b"\x1b[A", b"\x1b[B", b"\x1b[C", b"\x1b[D"
ENTER, SPACE, BACKSPACE, CTRL_C = b"\r", b" ", b"\x7f", b"\x03"
SGR = re.compile(r"\x1b\[[0-9;]*m")
ESC = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

OPTIONS = [Option("a", "Alpha", "first"), Option("b", "Beta"), Option("c", "Gamma")]

posix = pytest.mark.skipif(sys.platform == "win32", reason="needs a pseudo-terminal")


@dataclass
class Run:
    """What a prompt did on a pseudo-terminal."""

    value: object
    error: BaseException | None
    output: str
    before: list
    after: list


def drive(
    call: Callable[[Term], object], keys: bytes, *, color: bool = False, width: int = 80
) -> Run:
    """Run a prompt on a pseudo-terminal and feed it keys once the terminal is in raw mode.

    :param call: Takes the terminal and asks the question.
    :param keys: The bytes to type.
    :param color: Whether the terminal colors its output.
    :param width: The terminal's width in columns.
    :return: The answer or error, the output and the terminal attributes before and after."""
    import pty
    import termios

    master, slave = pty.openpty()
    before = termios.tcgetattr(slave)
    inp, out = os.fdopen(os.dup(slave), "r"), os.fdopen(os.dup(slave), "w")
    chunks: list[bytes] = []

    def drain() -> None:
        while True:
            try:
                if not (data := os.read(master, 4096)):
                    return
            except OSError:
                return
            chunks.append(data)

    def feed() -> None:
        if not keys:
            return
        deadline = time.monotonic() + 5
        while termios.tcgetattr(slave)[3] & termios.ICANON and time.monotonic() < deadline:
            time.sleep(0.005)
        os.write(master, keys)

    threads = [
        threading.Thread(target=drain, daemon=True),
        threading.Thread(target=feed, daemon=True),
    ]
    for t in threads:
        t.start()
    value, error = None, None
    try:
        value = call(Term(inp=inp, out=out, color=color, raw=True, width=width))
    except Aborted as e:
        error = e
    after = termios.tcgetattr(slave)
    inp.close(), out.close(), os.close(slave)
    threads[1].join(2)
    threads[0].join(2)
    os.close(master)
    return Run(value, error, b"".join(chunks).decode().replace("\r\n", "\n"), before, after)


def pipe(lines: str) -> tuple[Term, StringIO]:
    """A terminal over a pipe: numbered fallback, no color.

    :param lines: What the person types.
    :return: The terminal and its output."""
    out = StringIO()
    return Term(inp=StringIO(lines), out=out, color=False, raw=False), out


@posix
def test_select_by_arrows_digits_and_vim_keys():
    run = drive(lambda t: t.select("Pick", OPTIONS, "a"), DOWN + ENTER)
    assert run.value == "b"
    assert drive(lambda t: t.select("Pick", OPTIONS, "a"), b"3" + ENTER).value == "c"
    assert drive(lambda t: t.select("Pick", OPTIONS, "b"), b"jk" + UP + ENTER).value == "a"
    assert "Pick" in run.output and "Beta" in run.output
    assert run.before == run.after


@posix
def test_select_collapses_to_the_answer():
    run = drive(lambda t: t.select("Pick", OPTIONS, "a"), DOWN + ENTER)
    assert run.output.endswith("◇  Pick\n│  Beta\n│\n")


@posix
def test_multi_with_add_row_rejecting_then_accepting():
    def check(value: str) -> Option | str:
        return Option(value, value.title()) if value == "new" else f"{value} is not a log dir"

    add = Add("Add a path", "Path", check)
    keys = DOWN + SPACE + b"+" + b"bad" + ENTER + BACKSPACE * 3 + b"new" + ENTER + ENTER
    run = drive(lambda t: t.multi("Pick", OPTIONS, ["a"], add), keys)
    assert run.value == ["a", "b", "new"]
    assert "bad is not a log dir" in run.output
    assert run.output.endswith("◇  Pick\n│  Alpha, Beta, New\n│\n")


@posix
def test_multi_add_row_cancelled_with_escape():
    add = Add("Add a path", "Path", lambda v: Option(v, v))
    keys = b"+" + b"x" + b"\x1b" + b"2" + ENTER
    assert drive(lambda t: t.multi("Pick", OPTIONS, ["b"], add), keys).value == ["b"]


@posix
def test_enter_on_unticked():
    run = drive(lambda t: t.multi("Pick", OPTIONS, ["a"]), DOWN + ENTER)
    assert run.value == ["a", "b"]
    assert drive(lambda t: t.multi("Pick", OPTIONS, ["a"]), ENTER).value == ["a"]
    assert drive(lambda t: t.multi("Pick", OPTIONS, ["a"]), DOWN + SPACE + ENTER).value == [
        "a",
        "b",
    ]


@posix
def test_multi_exclusive_row_clears_the_others():
    options = [*OPTIONS, Option("none", "None", exclusive=True)]
    run = drive(lambda t: t.multi("Pick", options, ["a", "b"]), b"4" + SPACE + ENTER)
    assert run.value == ["none"]
    run = drive(lambda t: t.multi("Pick", options, ["none"]), b"1" + SPACE + ENTER)
    assert run.value == ["a"]


@posix
def test_text_and_form():
    assert (
        drive(lambda t: t.text("Name", "dflt"), b"ab" + BACKSPACE + b"c d" + ENTER).value == "ac d"
    )
    assert drive(lambda t: t.text("Name", "dflt"), ENTER).value == "dflt"
    rows = [FormRow("m", "metric", ("loss", "mae")), FormRow("s", "seeds", ("2", "3", "5"), True)]
    run = drive(lambda t: t.form("Tune", rows, {"s": "3"}), RIGHT + DOWN + LEFT + b"l" + ENTER)
    assert run.value == {"m": "mae", "s": "3"}
    assert "detected" in run.output


@posix
def test_task_lines_appear_under_the_title():
    def work(term: Term) -> None:
        with term.task("Scanning") as task:
            task.line("3 runs")
            task.line("2 notes")

    run = drive(work, b"")
    assert "◇  Scanning" in run.output and "│  3 runs" in run.output and "│  2 notes" in run.output


@posix
def test_ctrl_c_aborts_and_restores_the_terminal():
    for call, keys in [
        (lambda t: t.select("Pick", OPTIONS, "a"), DOWN + CTRL_C),
        (lambda t: t.multi("Pick", OPTIONS, ["a"]), CTRL_C),
        (lambda t: t.text("Name", "x"), b"a" + CTRL_C),
        (lambda t: t.select("Pick", OPTIONS, "a"), b"q"),
    ]:
        run = drive(call, keys)
        assert isinstance(run.error, Aborted)
        assert run.before == run.after
        assert run.output.endswith("\x1b[?25h")


@posix
def test_no_color():
    run = drive(lambda t: t.select("Pick", OPTIONS, "a", hint="why"), ENTER)
    assert not SGR.search(run.output)
    assert SGR.search(drive(lambda t: t.select("Pick", OPTIONS, "a"), ENTER, color=True).output)
    term, out = pipe("\n")
    term.select("Pick", OPTIONS, "a")
    term.say(["a", ""])
    term.collapse("Pick", "Alpha")
    with term.task("Work") as task:
        task.line("done")
    assert "\x1b" not in out.getvalue()


@posix
def test_narrow():
    hint = "a hint that is far longer than the terminal is wide, so it must be cut"
    options = [Option("a", "Alpha", hint), Option("b", "Beta", hint)]
    run = drive(lambda t: t.select("Pick", options, "a", hint=hint), DOWN + ENTER, width=30)
    lines = ESC.sub("", run.output).split("\n")
    assert max(len(line) for line in lines) <= 29
    assert any(line.endswith("…") and line.startswith("│  ") for line in lines)
    colored = Term(out=StringIO(), color=True, width=20).clip(
        "\x1b[32mabcdefghijklmnopqrstuvwxyz\x1b[0m"
    )
    assert len(SGR.sub("", colored)) == 19 and colored.endswith("…\x1b[0m")


def test_numbered_fallback_over_a_pipe():
    term, out = pipe("2\n")
    assert term.select("Pick", OPTIONS, "a") == "b"
    assert "1. * Alpha" in out.getvalue() and "2.   Beta" in out.getvalue()
    assert pipe("\n")[0].select("Pick", OPTIONS, "c") == "c"
    assert pipe("9\n0\n3\n")[0].select("Pick", OPTIONS, "a") == "c"

    assert pipe("1,3\n")[0].multi("Pick", OPTIONS, ["b"]) == ["a", "c"]
    assert pipe("\n")[0].multi("Pick", OPTIONS, ["b"]) == ["b"]
    assert pipe("2 3\n")[0].multi("Pick", OPTIONS, []) == ["b", "c"]

    options = [*OPTIONS, Option("none", "None", exclusive=True)]
    assert pipe("1,4\n")[0].multi("Pick", options, []) == ["none"]

    add = Add("Add a path", "Path", lambda v: Option(v, v) if v == "ok" else "not a log dir")
    term, out = pipe("4\nbad\nok\n")
    assert term.multi("Pick", OPTIONS, ["a"], add) == ["ok"]
    assert "not a log dir" in out.getvalue()

    assert pipe("  hello \n")[0].text("Name", "dflt") == "hello"
    assert pipe("\n")[0].text("Name", "dflt") == "dflt"
    rows = [FormRow("m", "metric", ("loss", "mae")), FormRow("s", "seeds", ("2", "3"))]
    assert pipe("2\n\n")[0].form("Tune", rows, {"s": "3"}) == {"m": "mae", "s": "3"}


def test_fallback_end_of_input_aborts():
    with pytest.raises(Aborted):
        pipe("")[0].select("Pick", OPTIONS, "a")


def test_detect_on_a_pipe_asks_by_lines_without_color():
    term = Term.detect()
    assert not term.raw and not term.color


def test_key_names():
    assert [name_of(c) for c in "\r \x03x7\x7f\x00"] == [
        "enter",
        "space",
        "ctrl-c",
        "char:x",
        "digit:7",
        "backspace",
        None,
    ]


@posix
def test_q_is_typed_in_the_add_row():
    add = Add("Add a path", "Path", lambda v: Option(v, v))
    run = drive(lambda t: t.multi("Pick", OPTIONS, ["a"], add), b"+quartz" + ENTER + ENTER)
    assert run.error is None and run.value == ["a", "quartz"]
    assert isinstance(drive(lambda t: t.multi("Pick", OPTIONS, ["a"], add), b"q").error, Aborted)


def test_fallback_add_of_a_listed_value_is_not_doubled():
    add = Add("Add a path", "Path", lambda v: Option("a", "Alpha"))
    assert pipe("1,4\nx\n")[0].multi("Pick", OPTIONS, [], add) == ["a"]
