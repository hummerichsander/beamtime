"""Lexical checks of custom-block code, and placeholders in declared queries.

There is no JavaScript parser here: the checks look at the code's text with comments and strings
masked, which is enough for what a block must not do. Syntax errors show in the render."""

import re
from typing import Any

KITS = (1,)
LIBS = ("d3", "uplot", "katex")
KINDS = ("keys", "runs", "series", "data", "timeline", "groups", "file")
MAX_BYTES = 64_000
MAX_NUMBERS = 200
NETWORK = (
    "fetch",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "sendBeacon",
    "importScripts",
    "Worker",
    "SharedWorker",
)
PLACEHOLDER = re.compile(r"^\$([A-Za-z_]\w*)$")

COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
STRING = re.compile(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"")
NUMBERS = re.compile(rf"(?:-?\d+(?:\.\d+)?(?:e-?\d+)?\s*,\s*){{{MAX_NUMBERS},}}", re.I)
COLOR = re.compile(r"#[0-9a-f]{3,8}\b|\b(?:rgba?|hsla?)\(", re.I)


def problems(code: str) -> list[tuple[str, str]]:
    """Check a custom block's code.

    :param code: The ES module's text.
    :return: ``(message, fix)`` for every rule it breaks."""
    out = []
    if len(code.encode()) > MAX_BYTES:
        out.append(
            (
                f"the code is {len(code.encode()) // 1000} KB",
                f"keep it under {MAX_BYTES // 1000} KB",
            )
        )
    bare = COMMENT.sub(" ", code)
    # colors are looked for in strings too, where they live; the rest ignores string contents.
    for m in COLOR.finditer(bare):
        out.append((f"color literal {m.group(0)!r}", "take colors from bt.theme"))
        break
    bare = STRING.sub('""', bare)
    if not re.search(r"export\s+default\b", bare):
        out.append(("no default export", "export default function render(root) { ... }"))
    if re.search(r"(^|[;\s])import\s*[\s{*\"(]|\bimport\s*\(", bare):
        out.append(("imports a module", "use bt and the libraries in libs (bt.lib.d3, ...)"))
    for name in NETWORK:
        if re.search(rf"\b{name}\b", bare):
            out.append((f"uses {name}", "declare a query and read it with bt.useData"))
    if NUMBERS.search(bare):
        out.append(
            (f"more than {MAX_NUMBERS} numbers inline", "put data in a data file or a query")
        )
    return out


def placeholders(value: Any, out: set[str] | None = None) -> set[str]:
    """Find the ``$name`` placeholders in a query.

    :param value: The query or a part of it.
    :param out: Names found so far.
    :return: The names."""
    out = set() if out is None else out
    match value:
        case str() if m := PLACEHOLDER.match(value):
            out.add(m.group(1))
        case list():
            for v in value:
                placeholders(v, out)
        case dict():
            for v in value.values():
                placeholders(v, out)
        case _:
            pass
    return out


def fill(value: Any, values: dict[str, Any]) -> Any:
    """Replace placeholders by values.

    :param value: The query or a part of it.
    :param values: Values by placeholder name.
    :return: The query with the known placeholders replaced."""
    match value:
        case str() if (m := PLACEHOLDER.match(value)) and m.group(1) in values:
            return values[m.group(1)]
        case list():
            out = []
            for v in value:
                # a list value in a list is spliced: select: [run.id, $fields].
                filled = fill(v, values)
                out += filled if isinstance(v, str) and isinstance(filled, list) else [filled]
            return out
        case dict():
            return {k: fill(v, values) for k, v in value.items()}
        case _:
            return value
