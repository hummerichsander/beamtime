"""Beamtime's operations as Python functions, so their answers land in variables.

``ops()`` names them, ``params(name)`` describes one, and every operation is a function:
``bt.runs({"from": "long/schedules", "limit": 200})``. Answers are plain dicts, whole and uncut,
and a read already made is answered from disk, so asking twice costs nothing."""

import hashlib
import json
import os
import shutil
from functools import partial
from pathlib import Path
from typing import Any

from beamtime import remote
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL

# view: the answer is read by code, not by a context window, so it arrives whole and unpaged.
CALLER = "view"
# no code runs code, and a user-only operation stays the user's, here as everywhere.
HIDDEN = ("script",)
# reads whose answer is about the moment, not the data; the rest of the data is fixed in a session.
FRESH = ("status", "wait", "resume", "logs")
# what msgspec says when a parameter name is wrong; any other failure is about the data, and
# naming the parameters there answers a question the caller did not ask.
NAME_ERRORS = ("Object contains unknown field", "Object missing required field")


def ops() -> dict[str, str]:
    """Name every operation with its summary.

    :return: The operation names and what they do."""
    return {name: op.summary for name, op in sorted(BY_TOOL.items()) if shown(op)}


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
    if op.writes and "author" in (op.params.__struct_fields__ if op.params else ()):
        given.setdefault("author", os.environ.get("BEAMTIME_AUTHOR", "agent"))
    context = Context.make(caller=CALLER)
    if (found := load(op, given, context)) is not None:
        return found
    try:
        answer = remote.answer(op.name, given, context)
    except OpError as e:
        # an MCP client validates against the schema; here a wrong name would cost a whole turn.
        if any(s in str(e) for s in NAME_ERRORS):
            takes = ", ".join(fields(op)) or "no parameters"
            raise OpError(f"{e}. {name} takes: {takes}") from None
        raise
    if op.writes:
        forget(context)
    save(op, given, answer, context)
    return answer


def cacheable(op: Any) -> bool:
    """Say whether an operation's answer may be kept.

    :param op: Its registry entry.
    :return: Whether it is a read whose answer the data alone decides."""
    return not op.writes and op.tool not in FRESH


def slot(op: Any, given: dict[str, Any], context: Context) -> Path:
    """Name the file that holds one call's answer.

    :param op: The operation's registry entry.
    :param given: Its parameters.
    :param context: The project the call runs in.
    :return: The file, which need not exist."""
    text = json.dumps([op.name, given], sort_keys=True, default=str)
    name = f"{op.tool}-{hashlib.sha256(text.encode()).hexdigest()[:16]}.json"
    return cache(context) / name


def load(op: Any, given: dict[str, Any], context: Context) -> dict[str, Any] | None:
    """Give a call's answer from an earlier run of this session, if it was kept.

    Every script is its own interpreter, so without this a second look at the same data would
    cost another turn.

    :param op: The operation's registry entry.
    :param given: Its parameters.
    :param context: The project the call runs in.
    :return: The answer, or ``None`` when there is none."""
    if not cacheable(op):
        return None
    try:
        return json.loads(slot(op, given, context).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def save(op: Any, given: dict[str, Any], answer: dict[str, Any], context: Context) -> None:
    """Keep a call's answer for the next script.

    :param op: The operation's registry entry.
    :param given: Its parameters.
    :param answer: The answer to keep; one that is not JSON is skipped.
    :param context: The project the call runs in."""
    if not cacheable(op):
        return
    try:
        text = json.dumps(answer)
        # drafts() leaves .beamtime/ with the .gitignore that keeps the cache out of the project.
        from beamtime.views.store import drafts

        drafts(context)
        file = slot(op, given, context)
        file.parent.mkdir(exist_ok=True)
        file.write_text(text, encoding="utf-8")
    except (OSError, TypeError, ValueError):
        pass


def forget(context: Context) -> None:
    """Drop every kept answer, because a write may have changed any of them.

    :param context: The project the call runs in."""
    shutil.rmtree(cache(context), ignore_errors=True)


def cache(context: Context) -> Path:
    """Name the folder that keeps answers.

    :param context: The project the call runs in.
    :return: The folder, which need not exist."""
    return context.root / ".beamtime" / "bt-cache"


def fields(op: Any) -> tuple[str, ...]:
    """Name the parameters an operation takes, as they are written.

    :param op: Its registry entry.
    :return: The parameter names."""
    if op.params is None:
        return ()
    return tuple(getattr(op.params, "__struct_encode_fields__", op.params.__struct_fields__))


def shown(op: Any) -> bool:
    """Say whether ``bt`` offers an operation.

    :param op: Its registry entry.
    :return: Whether it is neither user-only nor hidden."""
    return not op.user_only and op.tool not in HIDDEN


def operation(name: str) -> Any:
    """Look one operation up.

    :param name: The operation.
    :return: Its registry entry.
    :raises KeyError: When there is no such operation, or ``bt`` does not offer it."""
    if (op := BY_TOOL.get(name)) is None or not shown(op):
        raise KeyError(f"no operation {name!r}; ops() lists them")
    return op


def __getattr__(name: str) -> Any:
    """Give every operation as a module-level function.

    :param name: The attribute asked for.
    :return: The operation as a function.
    :raises AttributeError: When no operation has that name."""
    if name in BY_TOOL and shown(BY_TOOL[name]):
        return partial(call, name)
    raise AttributeError(name)
