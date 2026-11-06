"""Fields: the dotted paths a query filters, sorts and shows, and how to fetch them."""

import json
import re
from dataclasses import dataclass
from typing import Any

from beamtime.query.models import QueryError

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
)
WINDOW_STATS = ("first", "last", "min", "max", "mean", "count")

RUN_COLUMNS = {
    "id": "id",
    "name": "name",
    "status": "status",
    "created_at": "created_at",
    "ended_at": "ended_at",
    "path": "path",
    "group": "folder",
    "tags": "tags",
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
RUN_COMPUTED = ("code",)
# one comparable identity for a run's code: the short commit, plus the diff's short hash
# when the checkout was dirty, so the same commit and the same changes compare equal.
CODE_SQL = (
    "CASE WHEN json_extract(info, '$.git.dirty') THEN "
    "substr(json_extract(info, '$.git.commit'), 1, 7) || '+' || "
    "json_extract(info, '$.git.diff_sha') "
    "ELSE substr(json_extract(info, '$.git.commit'), 1, 7) END"
)
PROPOSAL = ("status", "check", "progress", "verdict")

_WINDOW = re.compile(r"\[(-?\d*):(-?\d*)\]$")
_CONFIG_PART = re.compile(r'\.([^.\[\]"]+)|\["([^"]+)"\]')
_CONFIG = re.compile(r'(?:\.[^.\[\]"]+|\["[^"]+"\])+')


@dataclass(frozen=True)
class Field:
    """A parsed field such as ``metric.val/acc.mean[1000:2000]``."""

    text: str
    ns: str
    path: tuple[str, ...]
    stat: str | None = None
    window: tuple[int | None, int | None] | None = None

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
            name = rest[1:]
            known = [*RUN_COLUMNS, *RUN_CARD, *RUN_INFO, *RUN_COMPUTED]
            if name not in known:
                raise QueryError(
                    f"unknown run field {text!r}. Run fields: "
                    + ", ".join(f"run.{k}" for k in known)
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
            window = None
            if m := _WINDOW.search(body):
                window = (int(m[1]) if m[1] else None, int(m[2]) if m[2] else None)
                body = body[: m.start()]
            key, _, stat = body.rpartition(".")
            if not key or stat not in STATS:
                raise QueryError(
                    f"{text!r}: a metric field is metric.<key>.<stat>; stats: {', '.join(STATS)}"
                )
            if window is not None and stat not in WINDOW_STATS:
                raise QueryError(f"{text!r}: windowed statistics are {', '.join(WINDOW_STATS)}")
            return Field(text=text, ns="metric", path=(key,), stat=stat, window=window)
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
            return f"json_extract(info, '{RUN_INFO[name]}')"
        case "config":
            return f"json_extract(config, '{json_path(field.path)}')"
        case "metric":
            if field.window is not None:
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
    if field.ns == "run" and field.key == "dirty":
        return bool(value) if value is not None else None
    if isinstance(value, str) and value[:1] in "[{" and field.ns in ("config", "value"):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value
