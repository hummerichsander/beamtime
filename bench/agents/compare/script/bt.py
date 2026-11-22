"""Beamtime's operations as Python functions, so their answers land in variables.

``ops()`` names them, ``params(name)`` describes one, and every operation is a function:
``bt.runs({"from": "long/schedules", "limit": 200})``. Answers are plain dicts, whole and uncut,
and a read already made is answered from disk, so asking twice costs nothing."""

import hashlib
import json
from functools import partial
from pathlib import Path
from typing import Any

from beamtime.ops import call as _call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL

ROOT = Path(__file__).resolve().parent
# view: the answer is read by code, not by a context window, so it arrives whole and unpaged.
CALLER = "view"
CACHE = ROOT / ".bt-cache"
# reads whose answer is about the moment, not the data; the rest of the data is fixed in a session.
FRESH = ("status", "wait", "resume", "logs")
# what msgspec says when a parameter name is wrong; any other failure is about the data, and
# naming the parameters there answers a question the caller did not ask.
NAME_ERRORS = ("Object contains unknown field", "Object missing required field")


def ops() -> dict[str, str]:
    """Name every operation with its summary.

    :return: The operation names and what they do."""
    return {name: op.summary for name, op in sorted(BY_TOOL.items()) if not op.user_only}


def params(name: str) -> dict[str, Any]:
    """Describe one operation's parameters.

    :param name: The operation, e.g. ``runs``.
    :return: Its summary and its parameters as a JSON schema."""
    from beamtime.mcp.server import schema

    op = operation(name)
    return {"summary": op.summary, "params": schema(op) if op.params is not None else {}}


def call(name: str, args: dict[str, Any] | None = None, **kw: Any) -> dict[str, Any]:
    """Call one operation.

    :param name: The operation, e.g. ``runs``.
    :param args: Its parameters by their own names, for those Python cannot spell (``from``).
    :param kw: More parameters; a trailing underscore is dropped, so ``from_`` is ``from``.
    :return: The answer.
    :raises OpError: When the call is rejected; the message names the parameters it takes."""
    op = operation(name)
    given = {**(args or {}), **{k[:-1] if k.endswith("_") else k: v for k, v in kw.items()}}
    # the MCP path attributes an agent's write this way when it names no author.
    if op.writes and "author" in (op.params.__struct_fields__ if op.params else ()):
        given.setdefault("author", "agent")
    if (found := load(op, given)) is not None:
        return found
    try:
        answer = _call(op.name, given, Context.make(root=ROOT, caller=CALLER))
    except OpError as e:
        # an MCP client validates against the schema; here a wrong name would cost a whole turn.
        if any(s in str(e) for s in NAME_ERRORS):
            takes = ", ".join(fields(op)) or "no parameters"
            raise OpError(f"{e}. {name} takes: {takes}") from None
        raise
    save(op, given, answer)
    return answer


def cacheable(op: Any) -> bool:
    """Say whether an operation's answer may be kept.

    :param op: Its registry entry.
    :return: Whether it is a read whose answer the data alone decides."""
    return not op.writes and op.tool not in FRESH


def slot(op: Any, given: dict[str, Any]) -> Path:
    """Name the file that holds one call's answer.

    :param op: The operation's registry entry.
    :param given: Its parameters.
    :return: The file, which need not exist."""
    text = json.dumps([op.name, given], sort_keys=True, default=str)
    return CACHE / f"{op.tool}-{hashlib.sha256(text.encode()).hexdigest()[:16]}.json"


def load(op: Any, given: dict[str, Any]) -> dict[str, Any] | None:
    """Give a call's answer from an earlier run of this session, if it was kept.

    Every script is its own interpreter, so without this a second look at the same data would
    cost another turn.

    :param op: The operation's registry entry.
    :param given: Its parameters.
    :return: The answer, or ``None`` when there is none."""
    if not cacheable(op):
        return None
    try:
        return json.loads(slot(op, given).read_text())
    except (OSError, ValueError):
        return None


def save(op: Any, given: dict[str, Any], answer: dict[str, Any]) -> None:
    """Keep a call's answer for the next script.

    :param op: The operation's registry entry.
    :param given: Its parameters.
    :param answer: The answer to keep; one that is not JSON is skipped."""
    if not cacheable(op):
        return
    try:
        CACHE.mkdir(exist_ok=True)
        slot(op, given).write_text(json.dumps(answer))
    except (OSError, TypeError, ValueError):
        pass


def fields(op: Any) -> tuple[str, ...]:
    """Name the parameters an operation takes, as they are written.

    :param op: Its registry entry.
    :return: The parameter names."""
    if op.params is None:
        return ()
    return tuple(getattr(op.params, "__struct_encode_fields__", op.params.__struct_fields__))


def operation(name: str) -> Any:
    """Look one operation up.

    :param name: The operation.
    :return: Its registry entry.
    :raises KeyError: When there is no such operation, or it is user-only."""
    if (op := BY_TOOL.get(name)) is None or op.user_only:
        raise KeyError(f"no operation {name!r}; ops() lists them")
    return op


def __getattr__(name: str) -> Any:
    """Give every operation as a module-level function.

    :param name: The attribute asked for.
    :return: The operation as a function.
    :raises AttributeError: When no operation has that name."""
    if name in BY_TOOL and not BY_TOOL[name].user_only:
        return partial(call, name)
    raise AttributeError(name)
