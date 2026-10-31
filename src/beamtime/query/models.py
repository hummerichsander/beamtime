"""The query language's object form as msgspec structs, with helpful errors."""

import difflib
import re
from typing import Any, Literal

import msgspec


class QueryError(ValueError):
    """A query that can't be answered as written; the message says how to fix it."""

    def __init__(self, message: str, *, code: Literal["invalid", "not_found"] = "invalid"):
        """Create the error.

        :param message: What is wrong and what to do.
        :param code: ``invalid`` (exit code 3) or ``not_found`` (exit code 4)."""
        super().__init__(message)
        self.code = code


def closest(word: str, options: list[str], n: int = 3) -> str:
    """Suggest the closest matches for an unknown name.

    :param word: The unknown name.
    :param options: The known names.
    :param n: How many to suggest.
    :return: E.g. `` Did you mean 'val/acc' or 'val/loss'?``, or an empty string."""
    matches = difflib.get_close_matches(word, options, n=n, cutoff=0.5)
    if not matches:
        return ""
    return " Did you mean " + " or ".join(repr(m) for m in matches) + "?"


class Struct(msgspec.Struct, kw_only=True, forbid_unknown_fields=True):
    """Base of the query structs: unknown fields are errors."""


class Selection(Struct, kw_only=True):
    """How every query kind selects runs."""

    from_: str = msgspec.field(default=".", name="from")
    depth: Literal["all"] | int = "all"
    where: dict[str, Any] = msgspec.field(default_factory=dict)
    seeds: str | None = None


class Keys(Selection, kw_only=True):
    """What exists in a selection: metrics, config keys, data keys and tags."""


class Runs(Selection, kw_only=True):
    """A run table."""

    select: list[str] | None = None
    sort: list[str] = msgspec.field(default_factory=list)
    limit: int | None = None


class Smooth(Struct, kw_only=True):
    """Smoothing applied to the raw data before downsampling."""

    ema: float


class Series(Selection, kw_only=True):
    """Curves of metrics."""

    y: list[str]
    x: str = "_step"
    steps: list[int | None] | None = None
    points: int | Literal["all"] | None = None
    smooth: Smooth | None = None
    by: list[str] | None = None
    band: Literal["minmax", "std", "stderr", "none"] = "minmax"


class Data(Selection, kw_only=True):
    """Logged tables, images and text."""

    key: str
    step: Literal["last", "all"] | int | list[int] = "last"
    limit: int | None = None


class Timeline(Selection, kw_only=True):
    """Notes and run events in time order."""

    types: list[str] | None = None
    since: str | None = None
    limit: int | None = None
    full: bool = False


class Groups(Selection, kw_only=True):
    """The group tree with what is attached to it."""


class File(Struct, kw_only=True):
    """A data file stored with a view."""

    path: str
    view: str = "."


class Importance(Selection, kw_only=True):
    """How strongly config fields relate to a target (v1.1)."""

    target: str
    fields: list[str] | None = None


KINDS: dict[str, type[Struct]] = {
    "keys": Keys,
    "runs": Runs,
    "series": Series,
    "data": Data,
    "timeline": Timeline,
    "groups": Groups,
    "file": File,
    "importance": Importance,
}


def parse(query: Any) -> tuple[str, Struct]:
    """Validate a query in its object form.

    :param query: A mapping with exactly one key, the kind, e.g. ``{"runs": {...}}``.
    :return: The kind and the validated struct."""
    if not isinstance(query, dict) or len(query) != 1:
        raise QueryError(
            "a query is a mapping with exactly one kind, e.g. {runs: {from: .}}; "
            f"kinds: {', '.join(KINDS)}"
        )
    ((kind, body),) = query.items()
    if kind not in KINDS:
        raise QueryError(f"unknown query kind {kind!r}.{closest(kind, list(KINDS))}")
    model = KINDS[kind]
    try:
        return kind, msgspec.convert(body or {}, type=model, strict=False)
    except msgspec.ValidationError as e:
        raise QueryError(explain(kind, model, str(e))) from None


def explain(kind: str, model: type[Struct], message: str) -> str:
    """Turn a msgspec validation message into advice.

    :param kind: The query kind.
    :param model: Its struct.
    :param message: msgspec's message.
    :return: The message with the allowed fields and the closest match."""
    names = [f.encode_name for f in msgspec.structs.fields(model)]
    if m := re.search(r"unknown field `([^`]+)`", message):
        return (
            f"{kind}: unknown field {m[1]!r}.{closest(m[1], names)} "
            f"Fields of {kind}: {', '.join(names)}."
        )
    if m := re.search(r"missing required field `([^`]+)`", message):
        return f"{kind}: {m[1]!r} is required. Fields of {kind}: {', '.join(names)}."
    return f"{kind}: {message.replace('`$.', '`')}"
