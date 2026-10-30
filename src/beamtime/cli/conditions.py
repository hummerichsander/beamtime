"""Compact ``--where`` strings such as ``config.lr<1e-3``, in the object form.

The operator is the first one outside quotes and brackets, so a field may be written
``config["a<b"]``; a quoted value stays text (``config.tag="1"``), and ``in`` takes a comma
list whose items may be quoted."""

from typing import Any

OPS = {"=": "eq", "!=": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge", "~": "glob"}
HELP = (
    "write field, operator and value, e.g. config.lr<1e-3; operators: = != < <= > >= ~ (glob) "
    "and 'in a,b'; quote values that must stay text: config.tag=\"1\""
)


def value_of(text: str) -> Any:
    """Read a condition value: quoted text as is, numbers, true, false and null, else text.

    :param text: The value as written.
    :return: The value."""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
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


def split_outside(text: str) -> list[tuple[int, str]]:
    """List the characters of a string that are outside quotes and brackets.

    :param text: The string.
    :return: ``(position, character)`` pairs."""
    out, quote, depth = [], None, 0
    for i, ch in enumerate(text):
        if quote is not None:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append((i, ch))
    if quote is not None:
        raise ValueError(f"--where {text!r}: a quote is not closed")
    return out


def operator(text: str) -> tuple[int, int, str]:
    """Find the first operator outside quotes and brackets.

    :param text: The condition.
    :return: Its start, its end and the operator as written (``in`` for the list form)."""
    free = split_outside(text)
    positions = {i for i, _ in free}
    for i, ch in free:
        two = text[i : i + 2]
        if two in ("<=", ">=", "!=") and i + 1 in positions:
            return i, i + 2, two
        if ch in "=<>~":
            return i, i + 1, ch
        # ' in ' as a word, with whitespace on both sides.
        if ch.isspace() and text[i + 1 : i + 3] == "in" and text[i + 3 : i + 4].isspace():
            return i, i + 4, "in"
    raise ValueError(f"--where {text!r}: {HELP}")


def items(text: str) -> list[Any]:
    """Split an ``in`` list at the commas outside quotes.

    :param text: E.g. ``1e-3, "a,b", 3``.
    :return: The values."""
    cuts = [i for i, ch in split_outside(text) if ch == ","]
    parts = [text[a + 1 : b] for a, b in zip([-1, *cuts], [*cuts, len(text)], strict=True)]
    return [value_of(p.strip()) for p in parts]


def parse_condition(text: str) -> tuple[str, str, Any]:
    """Split one condition string.

    :param text: E.g. ``run.status=finished``, ``config.lr in 1e-3,3e-4``.
    :return: Field, operator name and value."""
    text = text.strip()
    start, end, op = operator(text)
    field, value = text[:start].strip(), text[end:].strip()
    if not field:
        raise ValueError(f"--where {text!r}: no field before {op!r}; {HELP}")
    if not value:
        empty = f'{field}{op}""'
        raise ValueError(f"--where {text!r}: no value after {op!r}; for empty text write {empty}")
    if op == "in":
        return field, "in", items(value)
    return field, OPS[op], value_of(value)


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
