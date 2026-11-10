"""What an answer from a source needs before it is ours: its places, and merging listings.

Pure dicts in and out. ``placed`` gives an answer's paths their source's prefix back; ``merged``
combines one listing's answers from several sources. Every answer kind has its own ``Answer``;
answers without a ``kind`` go through the generic walk of ``DEFAULT``."""

from collections.abc import Callable
from typing import Any, ClassVar

from beamtime.format.place import Place

PATH_KEYS = ("group", "from", "scope", "folder")
# what users wrote or logged: its keys may be called group or path, and it is never a place.
USER_CONTENT = (
    "config",
    "proposal",
    "where",
    "a",
    "b",
    "plan",
    "by",
    "fields",
    "body",
    "columns",
    "text",
    "description",
    "values",
    "tags",
)
PATH_COLUMNS = ("path", "run.group", "run.path")


class Answer:
    """The generic answer: every place found by key name, no merge."""

    kind: ClassVar[str] = ""

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Give the paths in an answer their source's prefix back.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``@source/...`` paths."""

        def walk(x: Any) -> Any:
            if isinstance(x, list):
                return [walk(v) for v in x]
            if not isinstance(x, dict):
                return x
            # a file reference: its path is relative to the view, block or logged run it names.
            entry = isinstance(x.get("run"), str) and "step" in x
            ref = isinstance(x.get("view"), str) or "block" in x or "block_draft" in x or entry
            out = {}
            for k, v in x.items():
                # a block's call sits under a user-content key like ``proposal``, but it is a place.
                if k in USER_CONTENT and not is_call(v):
                    out[k] = v
                elif k in PATH_KEYS or (k == "path" and not ref) or (k == "view" and ref):
                    out[k] = at(v)
                elif k == "source" and v == "local":
                    out[k] = at(".")
                else:
                    out[k] = walk(v)
            if isinstance(x.get("columns"), list) and isinstance(x.get("rows"), list):
                cols = [i for i, c in enumerate(x["columns"]) if c in PATH_COLUMNS]
                out["rows"] = [
                    [at(v) if i in cols else v for i, v in enumerate(r)] for r in x["rows"]
                ]
            return out

        out = walk(answer)
        # a write says what it wrote, or where it copied to; the file is on the source.
        if isinstance(answer, dict) and isinstance(path := answer.get("path"), str):
            out["lines"] = [
                line.replace(f"wrote {path}", f"wrote {at(path)}").replace(
                    f"to {path} ", f"to {at(path)} "
                )
                for line in out.get("lines", [])
            ]
        return out

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Combine this kind's answers from several sources.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``.
        :raises ValueError: For a kind that doesn't federate."""
        raise ValueError(f"no merge for {self.kind!r}")


DEFAULT = Answer()


class Groups(Answer):
    """The group tree: rows of every source."""

    kind = "groups"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Join the rows of every source.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``."""
        first = dict(answers[0][1])
        first["rows"] = [x for _, a in answers for x in a.get("rows", [])]
        return first


class Data(Answer):
    """The data entries of the runs."""

    kind = "data"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Join the entries of every source.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``."""
        first = dict(answers[0][1])
        first["entries"] = [x for _, a in answers for x in a.get("entries", [])]
        return first


class Runs(Answer):
    """A run table."""

    kind = "runs"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Union the columns, sort again and cut to the limit.

        Each source returned its top rows by the same sort, so the merged top rows are exact.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``."""
        from beamtime.query.aggregate import sort_rows
        from beamtime.query.select import DEFAULTS

        first = dict(answers[0][1])
        tables = [a for _, a in answers]
        limit = params.get("limit") or DEFAULTS[caller]["rows"]
        columns: list[str] = []
        for a in tables:
            columns += [c for c in a.get("columns", []) if c not in columns]
        rows = [
            dict(zip(a.get("columns", []), r, strict=False))
            for a in tables
            for r in a.get("rows", [])
        ]
        sort = list(params.get("sort") or ["-run.created_at"])
        # a run id starts with its creation time, so it sorts like run.created_at.
        sort = [
            s.replace("run.created_at", "run.id") if s.lstrip("-") not in columns else s
            for s in sort
        ]
        sort_rows(rows, sort)
        first["columns"] = columns
        first["rows"] = [[r.get(c) for c in columns] for r in rows[:limit]]
        return first


class Series(Answer):
    """Curves of metrics."""

    kind = "series"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Join the curves; with several sources' curves, each group says its source.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``."""
        first = dict(answers[0][1])
        several = sum(1 for _, a in answers if a.get("curves")) > 1
        first["curves"] = [
            (
                {**c, "by": {"source": src, **c["by"]}}
                if several and isinstance(c.get("by"), dict)
                else c
            )
            for src, a in answers
            for c in a.get("curves", [])
        ]
        return first


class Timeline(Answer):
    """The events of a time range."""

    kind = "timeline"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Sort the entries by time and keep the latest ones.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``."""
        from beamtime.query.select import DEFAULTS

        first = dict(answers[0][1])
        entries = sorted(
            (e for _, a in answers for e in a.get("entries", [])), key=lambda e: e.get("t") or ""
        )
        first["entries"] = entries[-(params.get("limit") or DEFAULTS[caller]["entries"]) :]
        return first


class Notes(Answer):
    """The notes of a target."""

    kind = "notes"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Sort the entries newest first and keep one page.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``."""
        from beamtime.ops.record import NOTES_PAGE

        first = dict(answers[0][1])
        limit = NOTES_PAGE if params.get("limit") is None else params["limit"]
        entries = sorted(
            (e for _, a in answers for e in a.get("entries", [])),
            key=lambda e: e["id"],
            reverse=True,
        )
        first["entries"] = entries[:limit]
        first["more"] = len(entries) > limit or any(a.get("more") for _, a in answers)
        return first


class Keys(Answer):
    """The keys of the runs: metrics, config and data."""

    kind = "keys"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Unite names, add run counts and join value lists.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``."""
        first = dict(answers[0][1])
        tables_of = [a for _, a in answers]
        first["runs"] = sum(a.get("runs", 0) for a in tables_of)
        status: dict[str, int] = {}
        for a in tables_of:
            for k, n in (a.get("status") or {}).items():
                status[k] = status.get(k, 0) + n
        first["status"] = status
        for table in ("metrics", "config", "data"):
            tables = [a[table] for a in tables_of if isinstance(a.get(table), dict)]
            if not tables:
                continue
            columns = tables[0]["columns"]
            rows: dict[str, list] = {}
            for t in tables:
                for r in t["rows"]:
                    if r[0] not in rows:
                        rows[r[0]] = list(r)
                        continue
                    kept = rows[r[0]]
                    for i, c in enumerate(columns):
                        match c:
                            case "runs" | "entries":
                                kept[i] = (kept[i] or 0) + (r[i] or 0)
                            case "last_step" | "points":
                                steps = [x for x in (kept[i], r[i]) if x is not None]
                                kept[i] = max(steps) if steps else None
                            case "values" if isinstance(kept[i], list) and isinstance(r[i], list):
                                kept[i] = kept[i] + [v for v in r[i] if v not in kept[i]]
                            case "constant":
                                kept[i] = kept[i] and r[i]
                            case _:
                                pass
            first[table] = {"columns": columns, "rows": sorted(rows.values(), key=lambda r: r[0])}
            if table == "config":
                varying: list[str] = []
                aliases: dict[str, str] = {}
                for t in tables:
                    varying += [k for k in t.get("varying") or [] if k not in varying]
                    aliases.update(t.get("aliases") or {})
                first[table]["varying"] = sorted(varying)
                first[table]["aliases"] = aliases
        return first


ANSWERS: dict[str, Answer] = {
    a.kind: a for a in (Groups(), Runs(), Series(), Data(), Timeline(), Notes(), Keys())
}


def placed(answer: Any, source: str) -> Any:
    """Give the paths in a remote's answer their source's prefix.

    :param answer: The remote's answer.
    :param source: The source's name.
    :return: The answer with ``@source/...`` paths."""

    def at(v: Any) -> Any:
        if (
            not isinstance(v, str)
            or Place.parse(v).source is not None
            or v.startswith("/")
            or "://" in v
        ):
            return v
        return f"@{source}" if v in (".", "") else f"@{source}/{v}"

    kind = answer.get("kind") if isinstance(answer, dict) else None
    return ANSWERS.get(kind, DEFAULT).placed(answer, at)


def merged(method: str, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
    """Combine one listing's answers from several sources.

    :param method: The listing method, which is its answer kind.
    :param answers: ``(source, answer)`` pairs, this machine first.
    :param params: The call's parameters.
    :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
    :return: The merged answer.
    :raises ValueError: If the method's answers don't merge."""
    if (merger := ANSWERS.get(method)) is None:
        raise ValueError(f"no merge for {method!r}")
    out = merger.merged(answers, params, caller)
    matched = sum(a.get("meta", {}).get("matched", 0) or 0 for _, a in answers)
    out["meta"] = {**out.get("meta", {}), "matched": matched, "source": "."}
    return out


def is_call(v: Any) -> bool:
    """Tell whether a value is a call a block makes, as ``views/compile.py:api`` builds it.

    :param v: Any value.
    :return: Whether it has a ``method`` and ``params``."""
    return isinstance(v, dict) and isinstance(v.get("method"), str) and "params" in v
