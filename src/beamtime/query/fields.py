"""Fields: the dotted paths a query filters, sorts and shows, and how to fetch them."""

import json
import math
import re
from dataclasses import dataclass
from typing import Any

from beamtime.query.models import QueryError, closest

STATS = (
    "first",
    "last",
    "ema_last",
    "min",
    "min_step",
    "max",
    "max_step",
    "mean",
    "count",
    "last_step",
    "nonfinite",
    "slope_last10pct",
    "nonfinite_step",
    "rise_step",
)
# statistics the run card doesn't hold: they are computed from the columns, like windows.
SERIES_STATS = ("nonfinite_step", "rise_step")
# the statistics that are a step, so a metric can be read at it: ``metric.<a>[<b>.<step stat>]``.
STEP_STATS = ("min_step", "max_step", "last_step", *SERIES_STATS)
RISE_DEFAULT = 10.0
WINDOW_STATS = ("first", "last", "min", "max", "mean", "count")

RUN_COLUMNS = {
    "id": "id",
    "name": "name",
    "status": "status",
    "created_at": "created_at",
    "ended_at": "ended_at",
    "path": "path",
    "hidden": "hidden",
    "group": "folder",
    "tags": "tags",
    "last_logged": "metrics_mtime",
}
RUN_CARD = {
    "duration_s": "$.duration_s",
    "steps": "$.steps",
    "steps_per_s": "$.steps_per_s",
    "error": "$.error",
    "warnings": "$.warnings",
}
RUN_INFO = {
    "host": "$.host.hostname",
    "job_key": "$.job_key",
    "commit": "$.git.commit",
    "branch": "$.git.branch",
    "dirty": "$.git.dirty",
}
# computed from several RUN_INFO fields, so it has no single JSON path of its own.
RUN_COMPUTED = ("code", "epoch", "progress", "attempts")
# one comparable identity for a run's code: the short commit, plus the diff's short hash
# when the checkout was dirty, so the same commit and the same changes compare equal.
CODE_SQL = (
    "CASE WHEN json_extract(info, '$.git.dirty') THEN "
    "substr(json_extract(info, '$.git.commit'), 1, 7) || '+' || "
    "json_extract(info, '$.git.diff_sha') "
    "ELSE substr(json_extract(info, '$.git.commit'), 1, 7) END"
)
# the epoch (from 1 when the metric starts at 0) and the epochs done of ``max_epochs``, from the
# card and the config alone: both are null without an ``epoch`` metric, the second also without a
# positive ``max_epochs``.
EPOCH_SQL = (
    "(json_extract(card, '$.metrics.\"epoch\".last') "
    "+ (json_extract(card, '$.metrics.\"epoch\".first') = 0))"
)
PROGRESS_SQL = (
    f"MIN(1.0, ({EPOCH_SQL} - 1) / (SELECT t.value FROM json_tree(config) t "
    "WHERE t.key = 'max_epochs' AND t.type IN ('integer', 'real') AND t.value > 0 LIMIT 1))"
)
# the attempts a run recorded; 0 for a run without any (older or still empty runs).
ATTEMPTS_SQL = "COALESCE(json_array_length(info, '$.attempts'), 0)"
PROPOSAL = ("status", "check", "progress", "verdict")
# run fields that mean the same as a canonical one (``created_at`` is the run's first start).
RUN_SAME = {"started": "created_at"}
# what people try for a run field that has another name.
RUN_ALIASES = {
    "start": "created_at",
    "created": "created_at",
    "finished": "ended_at",
    "end": "ended_at",
    "ended": "ended_at",
    "duration": "duration_s",
    "time": "duration_s",
    "state": "status",
    "folder": "group",
    "dir": "path",
}

_WINDOW = re.compile(r"\[(-?\d*):(-?\d*)\]$")
_REF = re.compile(r"\[([^\[\]]+)\]$")
_RISE = re.compile(r"(.+)\.rise_step(?::(.*))?")
_CONFIG_PART = re.compile(r'\.([^.\[\]"]+)|\["([^"]+)"\]')
_CONFIG = re.compile(r'(?:\.[^.\[\]"]+|\["[^"]+"\])+')


@dataclass(frozen=True)
class Field:
    """A parsed field such as ``metric.val/acc.mean[1000:2000]`` or ``metric.a[b.min_step]``."""

    text: str
    ns: str
    path: tuple[str, ...]
    stat: str | None = None
    window: tuple[int | None, int | None] | None = None
    arg: float | None = None
    ref: "Field | None" = None

    @property
    def key(self) -> str:
        """The metric or value key, or the run attribute."""
        return self.path[0] if self.path else ""


def json_path(parts: tuple[str, ...]) -> str:
    """Build a SQLite JSON path with every key quoted.

    :param parts: The keys.
    :return: E.g. ``$."model"."lr"``."""
    for p in parts:
        if '"' in p:
            raise QueryError(f"keys with double quotes can't be queried: {p!r}")
    return "$" + "".join(f'."{p}"' for p in parts)


def parse_field(text: str) -> Field:
    """Parse a field.

    :param text: E.g. ``config.lr``, ``config["a.b"]``, ``metric.val/acc.max``.
    :return: The field."""
    ns, _, rest = text.partition(".")
    if ns.startswith("config["):
        ns, rest = "config", text[len("config") :]
    elif rest:
        rest = "." + rest
    match ns:
        case "run":
            name = RUN_SAME.get(rest[1:], rest[1:])
            known = [*RUN_COLUMNS, *RUN_CARD, *RUN_INFO, *RUN_COMPUTED]
            if name not in known:
                fields = [f"run.{k}" for k in known]
                hint = (
                    f" Did you mean 'run.{alias}'?"
                    if (alias := RUN_ALIASES.get(name))
                    else closest(text, fields)
                )
                raise QueryError(
                    f"unknown run field {text!r}.{hint} Run fields: {', '.join(fields)}"
                )
            return Field(text=text, ns="run", path=(name,))
        case "config":
            if not _CONFIG.fullmatch(rest):
                raise QueryError(
                    f"{text!r} is not a config field; write config.lr, "
                    'config.optimizer.lr, or config["a.b"] for a key with a dot'
                )
            parts = tuple(a or b for a, b in _CONFIG_PART.findall(rest))
            return Field(text=text, ns="config", path=parts)
        case "metric":
            body = rest[1:]
            window = ref = None
            if m := _WINDOW.search(body):
                window = (int(m[1]) if m[1] else None, int(m[2]) if m[2] else None)
                body = body[: m.start()]
            elif m := _REF.search(body):
                ref = step_reference(text, m[1])
                body = body[: m.start()]
            arg = None
            if rise := _RISE.fullmatch(body):
                key, stat, arg = rise[1], "rise_step", rise_factor(text, rise[2])
            else:
                key, _, stat = body.rpartition(".")
            if arg is None and (not key or stat not in STATS):
                # a bare key is its last value; a key ending in a stat name needs ``.last``.
                key, stat = body, "last"
            if not key:
                raise QueryError(
                    f"{text!r}: a metric field is metric.<key>.<stat> or metric.<key> (the last "
                    f"value); stats: {', '.join(STATS)}"
                )
            if window is not None and stat not in WINDOW_STATS:
                raise QueryError(f"{text!r}: windowed statistics are {', '.join(WINDOW_STATS)}")
            if ref is not None and stat != "last":
                raise QueryError(f"{text!r}: a metric read at a step takes no statistic of its own")
            return Field(
                text=text, ns="metric", path=(key,), stat=stat, window=window, arg=arg, ref=ref
            )
        case "value":
            if not rest[1:]:
                raise QueryError(f"{text!r} names no value key, e.g. value.test/acc")
            return Field(text=text, ns="value", path=(rest[1:],))
        case "proposal":
            if rest[1:] not in PROPOSAL:
                raise QueryError(
                    f"unknown proposal field {text!r}; fields: "
                    + ", ".join(f"proposal.{p}" for p in PROPOSAL)
                )
            return Field(text=text, ns="proposal", path=(rest[1:],))
        case _:
            raise QueryError(
                f"unknown field {text!r}: fields start with run., config., metric., "
                "value. or proposal."
            )


def step_reference(text: str, body: str) -> Field:
    """Parse the step of ``metric.<a>[<b>.<step stat>]``.

    :param text: The field text, for the error.
    :param body: What is inside the brackets, e.g. ``val/loss.min_step``.
    :return: The step field."""
    ref = parse_field(f"metric.{body}")
    if ref.window is not None or ref.ref is not None or ref.stat not in STEP_STATS:
        raise QueryError(
            f"{text!r}: inside [ ] a metric is read at a step statistic of another, "
            f"metric.<a>[<b>.<step stat>]; step stats: {', '.join(STEP_STATS)} "
            "(rise_step:<k> takes a factor)"
        )
    return ref


def rise_factor(text: str, arg: str | None) -> float:
    """Parse the factor of ``rise_step:<k>``.

    :param text: The field text, for the error.
    :param arg: The text after the colon, or ``None`` for ``rise_step`` alone.
    :return: The factor; 10 without one."""
    if arg is None:
        return RISE_DEFAULT
    try:
        k = float(arg)
    except ValueError:
        k = 0.0
    if not 0 < k < math.inf:
        raise QueryError(
            f"{text!r}: rise_step:<k> takes a positive number k, "
            "e.g. metric.train/loss.rise_step:10 (the first step above k times the lowest value "
            "before it; rise_step alone is k = 10)"
        )
    return k


def metric_key(text: str) -> str | None:
    """Give the metric key of a metric field.

    :param text: A field such as ``metric.val/acc.max`` or ``metric.val/acc``.
    :return: The key, or ``None`` if the text is not a metric field."""
    try:
        field = parse_field(text)
    except QueryError:
        return None
    return field.key if field.ns == "metric" else None


def sql(field: Field) -> str | None:
    """Give the SQL expression that fetches a field from the ``runs`` table.

    :param field: The field.
    :return: The expression, or ``None`` if it is computed outside SQL."""
    match field.ns:
        case "run":
            name = field.key
            if name in RUN_COLUMNS:
                return RUN_COLUMNS[name]
            if name in RUN_CARD:
                return f"json_extract(card, '{RUN_CARD[name]}')"
            if name == "code":
                return CODE_SQL
            if name == "epoch":
                return EPOCH_SQL
            if name == "progress":
                return PROGRESS_SQL
            if name == "attempts":
                return ATTEMPTS_SQL
            return f"json_extract(info, '{RUN_INFO[name]}')"
        case "config":
            return f"json_extract(config, '{json_path(field.path)}')"
        case "metric":
            if field.window is not None or field.ref is not None or field.stat in SERIES_STATS:
                return None
            return f"json_extract(card, '{json_path(('metrics', field.key, field.stat))}')"
        case "value":
            return f"json_extract(card, '{json_path(('values', field.key))}')"
        case "proposal":
            return None
        case _:
            raise ValueError(f"unknown namespace {field.ns!r}")


def decode_cell(field: Field, value: Any) -> Any:
    """Turn what SQLite returns into the field's value.

    :param field: The field.
    :param value: The SQL result; JSON text for lists and objects.
    :return: The value."""
    if field.ns == "run" and field.key == "tags":
        return json.loads(value) if value else []
    if field.ns == "run" and field.key in ("dirty", "hidden"):
        return bool(value) if value is not None else None
    if isinstance(value, str) and value[:1] in "[{" and field.ns in ("config", "value"):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value
