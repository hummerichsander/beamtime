"""The query language's object form as msgspec structs, with helpful errors."""

import difflib
import re
from typing import Annotated, Any, Literal

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


Where = Annotated[
    dict[str, Any],
    msgspec.Meta(
        description="field -> value or {op: value}; ops eq ne lt le gt ge in nin has "
        "exists glob; also any: [...], not: {...}. Fields: run.status, config.lr, "
        "metric.val/acc.max, metric.train/loss.mean[0:1000], value.test/acc"
    ),
]
Fields = Annotated[
    list[str] | None,
    msgspec.Meta(description="fields such as run.name, config.lr, metric.val/acc.max"),
]
Group = Annotated[str, msgspec.Meta(description="group below the log dir, or a run id")]
RunId = Annotated[str, msgspec.Meta(description="the run id")]
Sort = Annotated[list[str], msgspec.Meta(description="fields; a leading - sorts descending")]
Seeds = Annotated[str | None, msgspec.Meta(description="e.g. config.seed: average over seeds")]
RowsBy = Annotated[
    list[str] | None,
    msgspec.Meta(description="one row per value of these fields, e.g. config.lr"),
]
AggregateBy = Annotated[
    list[str] | None, msgspec.Meta(description="aggregate runs by these fields, e.g. config.lr")
]
ExportTo = Annotated[
    str | None,
    msgspec.Meta(
        description="write all of it to this .csv or .json file below .beamtime/exports/ "
        "and answer the path (outside the token budget)"
    ),
]
SeriesY = Annotated[list[str], msgspec.Meta(description="metric keys, e.g. train/loss")]
SeriesX = Annotated[str, msgspec.Meta(description="_step, _t, _elapsed or a metric key")]
Steps = Annotated[list[int | None] | None, msgspec.Meta(description="[first, last] step window")]
SeriesPoints = Annotated[
    int | Literal["all"] | None,
    msgspec.Meta(description="points per curve; all: every logged point, as exports ask"),
]
Grep = Annotated[str | None, msgspec.Meta(description="regular expression; show its matches")]
Tail = Annotated[int, msgspec.Meta(description="lines (with grep: matches) per run")]
Context = Annotated[int, msgspec.Meta(description="lines around each match")]
Until = Annotated[
    str,
    msgspec.Meta(
        description="finished: no run is running; or a condition such as "
        "'metric.val/acc.max>0.9' that one run meets"
    ),
]
Timeout = Annotated[
    float, msgspec.Meta(description="seconds; over MCP at most 45, then call again")
]
DiagnoseMetrics = Annotated[
    list[str] | None,
    msgspec.Meta(description="metrics a run must have; default: those most runs have"),
]
Targets = Annotated[
    list[str], msgspec.Meta(description="two or more runs or groups, on one source")
]
CompareMetrics = Annotated[
    list[str] | None, msgspec.Meta(description="metric keys to tabulate; default: all logged")
]
ReadDraft = Annotated[str | None, msgspec.Meta(description="read from this draft instead")]


class Selection(Struct, kw_only=True):
    """How every query kind selects runs."""

    from_: Group = msgspec.field(default=".", name="from")
    depth: Literal["all"] | int = "all"
    where: Where = msgspec.field(default_factory=dict)
    hidden: Annotated[bool, msgspec.Meta(description="include hidden (test) runs")] = False


class Keys(Selection, kw_only=True):
    """What exists in a selection: metrics, config keys, data keys and tags."""


class Runs(Selection, kw_only=True):
    """A run table."""

    select: Fields = None
    sort: Sort = msgspec.field(default_factory=list)
    limit: int | None = None
    by: RowsBy = None
    seeds: Seeds = None


class Smooth(Struct, kw_only=True):
    """Smoothing applied to the raw data before downsampling."""

    ema: float


class Series(Selection, kw_only=True):
    """Curves of metrics."""

    y: SeriesY
    x: SeriesX = "_step"
    steps: Steps = None
    points: SeriesPoints = None
    smooth: Smooth | None = None
    by: AggregateBy = None
    seeds: Seeds = None
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
    columns: list[str] | None = None


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


# importance answers only an error until v1.1, so the kinds a caller may ask for leave it out.
LIVE_KINDS = tuple(kind for kind in KINDS if kind != "importance")
QueryBody = Annotated[
    dict[str, Any], msgspec.Meta(description=f"one kind: {', '.join(LIVE_KINDS)}")
]
Cursor = str | None


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
