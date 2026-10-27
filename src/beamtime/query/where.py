"""Conditions of ``where``: a mapping from field to condition, combined with AND."""

import fnmatch
from typing import Any

from beamtime.query.models import QueryError

OPS = ("eq", "ne", "lt", "le", "gt", "ge", "in", "nin", "has", "exists", "glob")


def fields_of(where: dict[str, Any]) -> list[str]:
    """List the fields a condition refers to.

    :param where: The condition.
    :return: The field names, in order of appearance."""
    out: list[str] = []
    for key, cond in where.items():
        match key:
            case "any":
                if not isinstance(cond, list):
                    raise QueryError("'any' takes a list of conditions")
                for sub in cond:
                    out += fields_of(sub)
            case "not":
                if not isinstance(cond, dict):
                    raise QueryError("'not' takes a condition")
                out += fields_of(cond)
            case _:
                if isinstance(cond, dict):
                    for op in cond:
                        if op not in OPS:
                            raise QueryError(
                                f"unknown operator {op!r} on {key}; operators: {', '.join(OPS)}"
                            )
                out.append(key)
    return list(dict.fromkeys(out))


def number(value: Any) -> Any:
    """Convert numeric strings to numbers (YAML reads ``1e-3`` as a string).

    :param value: A condition value.
    :return: The number, or the value unchanged."""
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    return value


def compare(op: str, actual: Any, expected: Any) -> bool:
    """Apply one operator.

    :param op: The operator.
    :param actual: The field's value; ``None`` if the run doesn't have it.
    :param expected: The condition's value.
    :return: Whether the condition holds."""
    if isinstance(actual, (int, float)) and not isinstance(actual, bool):
        expected = [number(e) for e in expected] if isinstance(expected, list) else number(expected)
    match op:
        case "exists":
            return (actual is not None) == bool(expected)
        case "eq":
            return actual == expected
        case "ne":
            return actual != expected
        case "in":
            return actual in (expected if isinstance(expected, list) else [expected])
        case "nin":
            return actual not in (expected if isinstance(expected, list) else [expected])
        case "has":
            return isinstance(actual, list) and expected in actual
        case "glob":
            return isinstance(actual, str) and fnmatch.fnmatchcase(actual, str(expected))
        case "lt" | "le" | "gt" | "ge":
            if actual is None:
                return False
            try:
                match op:
                    case "lt":
                        return actual < expected
                    case "le":
                        return actual <= expected
                    case "gt":
                        return actual > expected
                    case _:
                        return actual >= expected
            except TypeError:
                return False
        case _:
            raise QueryError(f"unknown operator {op!r}")


def matches(where: dict[str, Any], values: dict[str, Any]) -> bool:
    """Evaluate a condition for one run.

    :param where: The condition.
    :param values: Field name to the run's value.
    :return: Whether the run matches."""
    for key, cond in where.items():
        match key:
            case "any":
                if not any(matches(sub, values) for sub in cond):
                    return False
            case "not":
                if matches(cond, values):
                    return False
            case _:
                actual = values.get(key)
                ops = cond if isinstance(cond, dict) else {"eq": cond}
                if not all(compare(op, actual, exp) for op, exp in ops.items()):
                    return False
    return True
