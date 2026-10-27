"""Compact ``--where`` strings such as ``config.lr<1e-3``, in the object form."""

import re
from typing import Any

OPS = {"=": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge", "~": "glob"}
_CONDITION = re.compile(
    r"^(?P<field>.+?)\s*(?P<op><=|>=|!=|=|<|>|~|\s+in\s+)\s*(?P<value>.*)$"
)


def value_of(text: str) -> Any:
    """Read a condition value: numbers, true, false and null, else text.

    :param text: The value as written.
    :return: The value."""
    match text:
        case "true":
            return True
        case "false":
            return False
        case "null":
            return None
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            continue
    return text


def parse_condition(text: str) -> tuple[str, str, Any]:
    """Split one condition string.

    :param text: E.g. ``run.status=finished``, ``config.lr in 1e-3,3e-4``.
    :return: Field, operator name and value."""
    if (m := _CONDITION.match(text.strip())) is None:
        raise ValueError(
            f"--where {text!r}: write field, operator and value, e.g. config.lr<1e-3; "
            "operators: = != < <= > >= ~ (glob) and 'in a,b'"
        )
    op = m["op"].strip()
    value = m["value"].strip()
    if op == "in":
        return m["field"], "in", [value_of(v.strip()) for v in value.split(",")]
    return m["field"], OPS[op], value_of(value)


def parse_where(conditions: list[str]) -> dict[str, Any]:
    """Combine ``--where`` strings into one condition (AND).

    :param conditions: The strings.
    :return: The condition in the object form."""
    where: dict[str, dict[str, Any]] = {}
    for text in conditions:
        field, op, value = parse_condition(text)
        ops = where.setdefault(field, {})
        if op in ops:
            raise ValueError(f"--where: {field} {op} is given twice")
        ops[op] = value
    return {f: ops["eq"] if list(ops) == ["eq"] else ops for f, ops in where.items()}
