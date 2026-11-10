"""Token budgets: long answers are cut at whole items and carry a cursor to the rest."""

import json
from typing import Any

from beamtime.ops.context import OpError

# about 8k tokens at roughly four characters per token.
MAX_CHARS = 32_000
# what a federating serve takes from one source, about 2 MB.
WHOLE_MAX_CHARS = 64 * MAX_CHARS
LISTS = ("rows", "curves", "entries")


def offset_of(cursor: str | None) -> int:
    """Read the position a cursor points to.

    :param cursor: A cursor from ``meta.next``, or ``None`` for the start.
    :return: The offset into the answer's items."""
    if cursor is None:
        return 0
    try:
        return int(cursor)
    except ValueError:
        raise OpError(f"cursor {cursor!r} is not one Beamtime gave out", code=2) from None


def cut(answer: dict[str, Any], offset: int, *, max_chars: int = MAX_CHARS) -> dict[str, Any]:
    """Page an answer: drop items before the cursor, and items beyond the budget.

    :param answer: An answer with one item list (``rows``, ``curves`` or ``entries``).
    :param offset: The cursor's offset.
    :param max_chars: The budget in characters of JSON.
    :return: The answer; ``meta.next`` is set when items were left out."""
    key = next((k for k in LISTS if k in answer), None)
    if key is None:
        return answer
    items = answer[key][offset:]
    answer[key] = items
    meta = answer.setdefault("meta", {})
    sizes = [len(json.dumps(item, default=str)) for item in items]
    base = len(json.dumps({k: v for k, v in answer.items() if k != key}, default=str))
    keep, total = 0, base
    for size in sizes:
        if keep and total + size > max_chars:
            break
        total += size + 1
        keep += 1
    if keep < len(items):
        answer[key] = items[:keep]
        meta["cut"] = True
        meta["next"] = str(offset + keep)
        meta["hint"] = f"answer cut at about 8k tokens; pass cursor {meta['next']!r} for more"
    if offset:
        meta["offset"] = offset
    return answer


def page(answer: dict[str, Any], cursor: str | None, *, caller: str, whole: bool) -> dict[str, Any]:
    """Page an answer for the one asking: whole for the web UI, near-whole for a federating serve.

    :param answer: An answer with one item list.
    :param cursor: A cursor from an earlier, cut answer, or ``None``.
    :param caller: ``cli``, ``mcp`` or ``view``.
    :param whole: Whether a federating serve asked for everything up to ``WHOLE_MAX_CHARS``.
    :return: The answer; ``meta.next`` is set when items were left out."""
    offset = offset_of(cursor)
    if caller == "view":
        return answer
    if whole:
        return cut(answer, offset, max_chars=WHOLE_MAX_CHARS)
    return cut(answer, offset)
