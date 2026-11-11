"""What an answer from a source needs before it is ours: its places, and merging listings.

Pure dicts in and out. ``placed`` gives an answer's paths their source's prefix back; ``merged``
combines one listing's answers from several sources. Every answer kind has its own ``Answer``;
answers without a ``kind`` go through the generic walk of ``DEFAULT``."""

from collections.abc import Callable
from typing import Any, ClassVar

from beamtime.format.place import Place
from beamtime.ops import budget

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


def label(source: str) -> str:
    """Name a source the way every answer does: ``.`` for this machine, ``@name`` for a remote.

    :param source: The source's name; ``local`` is this machine.
    :return: ``.`` or ``@name``."""
    return "." if source == "local" else f"@{source}"


def place_keys(
    d: dict[str, Any], keys: tuple[str, ...], at: Callable[[str], str]
) -> dict[str, Any]:
    """Place the named keys of a dict; the others pass through.

    :param d: A dict of an answer.
    :param keys: The keys that hold places.
    :param at: Puts a source's prefix on one path.
    :return: A copy with those keys placed."""
    return {k: at(v) if k in keys and isinstance(v, str) else v for k, v in d.items()}


def place_table(
    table: dict[str, Any], columns: tuple[str, ...], at: Callable[[str], str]
) -> dict[str, Any]:
    """Place the named columns of a table; the other columns pass through.

    :param table: A dict with ``columns`` and ``rows``.
    :param columns: The columns that hold places.
    :param at: Puts a source's prefix on one path.
    :return: A copy with those columns placed."""
    cols = {i for i, c in enumerate(table.get("columns", [])) if c in columns}
    rows = [[at(v) if i in cols else v for i, v in enumerate(r)] for r in table.get("rows", [])]
    return {**table, "rows": rows} if "rows" in table else table


def place_meta(answer: dict[str, Any], at: Callable[[str], str]) -> dict[str, Any]:
    """Place the source and the scope an answer says it came from.

    :param answer: An answer.
    :param at: Puts a source's prefix on one path.
    :return: A copy whose ``meta.source`` and ``meta.from`` name the remote."""
    if not isinstance(meta := answer.get("meta"), dict):
        return answer
    meta = place_keys(meta, ("from",), at)
    if meta.get("source") in ("local", "."):
        meta["source"] = at(".")
    return {**answer, "meta": meta}


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
                elif k == "source" and v in ("local", "."):
                    out[k] = at(".")
                else:
                    out[k] = walk(v)
            if isinstance(x.get("columns"), list) and isinstance(x.get("rows"), list):
                cols = [i for i, c in enumerate(x["columns"]) if c in PATH_COLUMNS]
                out["rows"] = [
                    [at(v) if i in cols else v for i, v in enumerate(r)] for r in x["rows"]
                ]
            return out

        return walk(answer)

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Combine this kind's answers from several sources.

        :param answers: ``(source, answer)`` pairs, this machine first.
        :param params: The call's parameters.
        :param caller: Who asks (``cli``, ``mcp``, ``web``), for its default limits.
        :return: The merged answer, without ``meta``.
        :raises ValueError: For a kind that doesn't federate."""
        raise ValueError(f"no merge for {self.kind!r}")


DEFAULT = Answer()


class Bare(Answer):
    """An answer with no place of its own: only its meta names the source."""

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place the meta.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``meta.source`` and ``meta.from`` placed."""
        return place_meta(answer, at)


class Tabled(Bare):
    """A table whose path columns are places."""

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place the path columns and the meta.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``@source/...`` paths."""
        return place_meta(place_table(answer, PATH_COLUMNS, at), at)


class Grouped(Bare):
    """An answer about one group: its ``group``, the ``group`` of each item in ``lists`` and the
    table columns named in ``columns``."""

    lists: ClassVar[tuple[str, ...]] = ()
    columns: ClassVar[tuple[str, ...]] = ()

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place the group, the groups of the items and the meta.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``@source/...`` groups."""
        out = place_keys(answer, ("group",), at)
        for key in self.lists:
            out[key] = [place_keys(item, ("group",), at) for item in out.get(key, [])]
        return place_meta(place_table(out, self.columns, at), at)


class Card(Bare):
    """One run: its path and the groups of its proposals."""

    kind = "card"

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place the run's path, its proposals' groups and the meta.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``@source/...`` paths."""
        run = place_keys(answer["run"], ("path",), at)
        proposals = [place_keys(p, ("group",), at) for p in answer.get("proposals", [])]
        return place_meta({**answer, "run": run, "proposals": proposals}, at)


class Output(Bare):
    """A run's output lines."""

    kind = "output"


class Resume(Bare):
    """How to resume a run; its cwd and checkpoint are paths on the remote machine."""

    kind = "resume"


class Status(Bare):
    """The log dir and the daemon of a source."""

    kind = "status"


class Logs(Bare):
    """Output lines and tracebacks, by run id."""

    kind = "logs"


class Diagnose(Bare):
    """What looks wrong in runs, by run id."""

    kind = "diagnose"


class Digest(Grouped):
    """The digest of a group."""

    kind = "digest"


class PlanMissing(Grouped):
    """The runs a group's plan still lacks."""

    kind = "plan missing"


class Check(Grouped):
    """The check of a proposal version."""

    kind = "check"


class Proposal(Grouped):
    """A group's proposal and its versions; the proposal text is the user's."""

    kind = "proposal"


class Memory(Grouped):
    """The memory of a group and of the groups above it."""

    kind = "memory"
    lists = ("chain",)


class Note(Grouped):
    """One note: its group; the text is the user's."""

    kind = "note"


class File(Bare):
    """A data file of a view: its group; its path is relative to the view."""

    kind = "file"

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place the group and the meta.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``@source/...`` group."""
        return place_meta(place_keys(answer, ("group",), at), at)


class Groups(Tabled):
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


class Data(Bare):
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


class Runs(Tabled):
    """A run table."""

    kind = "runs"

    def merged(self, answers: list[tuple[str, dict]], params: dict, caller: str) -> dict:
        """Union the columns, sort again and cut to the limit.

        Each source returned its top rows by the same sort, so the merged top rows are exact. Rows
        aggregated by ``by`` or ``seeds`` keep each source's order and name their source.

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
        aggregated = bool(params.get("by") or params.get("seeds"))
        labelled = aggregated and len(answers) > 1 and "runs" in columns
        if labelled:
            columns.insert(columns.index("runs") + 1, "source")
        rows = [
            dict(zip(a.get("columns", []), r, strict=False))
            | ({"source": label(src)} if labelled else {})
            for src, a in answers
            for r in a.get("rows", [])
        ]
        sort = list(params.get("sort") or ([] if aggregated else ["-run.created_at"]))
        # a run id starts with its creation time, so it sorts like run.created_at.
        sort = [
            s.replace("run.created_at", "run.id") if s.lstrip("-") not in columns else s
            for s in sort
        ]
        sort_rows(rows, sort)
        first["columns"] = columns
        first["rows"] = [[r.get(c) for c in columns] for r in rows[:limit]]
        first["meta"] = {**first.get("meta", {}), "shown": len(first["rows"])}
        if len(rows) > limit:
            first["meta"] |= {"cut": True, "hint": "raise limit to see more"}
        return first


class Series(Bare):
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
                {**c, "by": {"source": label(src), **c["by"]}}
                if several and isinstance(c.get("by"), dict)
                else c
            )
            for src, a in answers
            for c in a.get("curves", [])
        ]
        return first


class Timeline(Grouped):
    """The events and notes of a time range; a note names its group."""

    kind = "timeline"
    lists = ("entries",)

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


class Notes(Grouped):
    """The notes of a target."""

    kind = "notes"
    lists = ("entries",)

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


class Keys(Bare):
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


class WaitAnswer(Answer):
    """What a wait saw: run ids and statuses, so only a group is a place."""

    kind = "wait"

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place the group, if present; ``changed`` passes through untouched.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with its group placed."""
        out = dict(answer)
        if isinstance(out.get("group"), str):
            out["group"] = at(out["group"])
        return out


class CompareAnswer(Answer):
    """The comparison of runs or groups: only its targets are places."""

    kind = "compare"

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place each target; the rest of the shape is unprefixed.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``@source/...`` targets."""
        out = dict(answer)
        out["targets"] = [{**t, "target": at(t["target"])} for t in out.get("targets", [])]
        return out


class Written(Grouped):
    """A write: the file it made, in ``path`` and in the line ``wrote <path>``."""

    def placed(self, answer: Any, at: Callable[[str], str]) -> Any:
        """Place the file, the lines that name it, the group and the meta.

        :param answer: The remote's answer.
        :param at: Puts a source's prefix on one path.
        :return: The answer with ``@source/...`` paths."""
        out = super().placed(place_keys(answer, ("path",), at), at)
        if isinstance(path := answer.get("path"), str):
            out["lines"] = [
                line.replace(f"wrote {path}", f"wrote {at(path)}").replace(
                    f"to {path} ", f"to {at(path)} "
                )
                for line in out.get("lines", [])
            ]
        return out


class BlockList(Grouped):
    """The library blocks of a group; each row names the group that holds the block."""

    kind = "block list"
    columns = ("group",)


class ViewOutdated(Grouped):
    """The views that pin an old block version, one row per block and group."""

    kind = "view outdated"
    columns = ("group",)


WRITES = (
    "view save", "view upgrade", "name", "note add", "proposal set", "memory update",
    "block save", "cp",
)  # fmt: skip
# kinds whose answer names a group (and nothing else is a place).
GROUPED = (
    "view new", "view validate", "view render", "view show", "view history", "block show",
    "block validate", "block promote", "block fork",
)  # fmt: skip
# what a source says about its own machine, or about names and text: nothing in it is a place.
BARE = (
    "view check", "view files", "block check", "block export", "block import", "note rm",
    "settings", "doctor", "source list", "export", "pull", "init", "set", "source add",
    "source rm", "reindex", "rm", "mv", "gc", "mcp install", "serve", "guide",
)  # fmt: skip
# the page methods' kinds: trees (a view's blocks) with places under any key, so the generic walk
# serves them on purpose; a remote's page answers pass through ``placed`` with it.
PAGES = ("hello", "files", "meta", "view", "summary", "code", "diff")

ANSWERS: dict[str, Answer] = (
    {
        a.kind: a
        for a in (
            Groups(),
            Runs(),
            Series(),
            Data(),
            Timeline(),
            Notes(),
            Keys(),
            WaitAnswer(),
            CompareAnswer(),
            Card(),
            Output(),
            Resume(),
            Status(),
            Logs(),
            Diagnose(),
            Digest(),
            PlanMissing(),
            Check(),
            Proposal(),
            Memory(),
            Note(),
            File(),
            BlockList(),
            ViewOutdated(),
        )
    }
    | {k: Written() for k in WRITES}
    | {k: Grouped() for k in GROUPED}
    | {k: Bare() for k in BARE}
    | {k: DEFAULT for k in PAGES}
)


def placed(answer: Any, source: str) -> Any:
    """Give the paths in a remote's answer their source's prefix.

    :param answer: The remote's answer.
    :param source: The source's name.
    :return: The answer with ``@source/...`` paths."""

    def at(v: Any) -> Any:
        if not isinstance(v, str) or (place := Place.parse(v)).source is not None:
            return v
        if v.startswith("/") or "://" in v:
            return v
        return place.on(source).text

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
    counts = {
        key: sum(a.get("meta", {}).get(key) or 0 for _, a in answers)
        for key in ("matched", "groups", "means")
        if key == "matched" or any(a.get("meta", {}).get(key) is not None for _, a in answers)
    }
    out["meta"] = {**out.get("meta", {}), **counts, "source": "."}
    return out


def paged(answer: dict, cursor: str | None) -> dict:
    """Cut a merged listing once, at the token budget, from the cursor on.

    :param answer: The merged answer.
    :param cursor: A cursor from an earlier page, or ``None`` for the first.
    :return: The answer, with ``meta.next`` when items were left out; curves carry the envelope
        only, since a merged listing is for the CLI and MCP.
    :raises OpError: If the cursor is not one Beamtime gave out."""
    return budget.cut(budget.envelope_only(answer), budget.offset_of(cursor))


def flagged(answer: dict) -> dict:
    """Show at the top that a source cut its own answer, unless a cursor already leads to the rest.

    :param answer: A merged answer with ``meta.sources``.
    :return: The answer; ``meta.cut`` and ``meta.hint`` name the sources whose items are missing."""
    meta = answer.get("meta", {})
    if "next" not in meta and (
        names := [s["name"] for s in meta.get("sources", []) if s.get("cut")]
    ):
        meta |= {"cut": True, "hint": f"narrow from or where to see all of {', '.join(names)}"}
    return answer


def is_call(v: Any) -> bool:
    """Tell whether a value is a call a block makes, as ``views/compile.py:api`` builds it.

    :param v: Any value.
    :return: Whether it has a ``method`` and ``params``."""
    return isinstance(v, dict) and isinstance(v.get("method"), str) and "params" in v
