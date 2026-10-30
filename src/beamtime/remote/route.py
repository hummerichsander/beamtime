"""Routing calls to the source their target names, and merging what several sources answer.

A target naming ``@x/...`` sends the call to ``x`` with the prefix stripped; paths in the answer get
it back. Listings over ``.`` ask every source of the running serve and merge. A run id the local
log dir doesn't know is looked for on the remotes, since run ids are unique everywhere."""

from collections.abc import Callable
from typing import Any

from beamtime import remote
from beamtime.format.ids import is_run_id
from beamtime.ops.context import Context, OpError

# parameters that name a place: a group, a run, a page.
TARGETS = ("group", "from", "run", "path", "view", "source", "to", "target")
# listings over "." that merge across sources.
LISTINGS = ("groups", "runs", "series", "data", "timeline", "notes", "keys")
# work on drafts in this project's .beamtime/, which a remote group can't use (yet).
DRAFTS = (
    "view_new",
    "view_validate",
    "view_render",
    "view_save",
    "block_promote",
    "block_fork",
    "block_validate",
    "block_save",
)
PATH_KEYS = ("group", "from", "scope", "folder")
PATH_COLUMNS = ("path", "run.group", "run.path")

Local = Callable[[dict[str, Any]], Any]


def routed(method: str, params: dict[str, Any], ctx: Context, local: Local) -> Any:
    """Answer a call where it belongs: on the source its target names, merged over every source
    for listings of ``.``, else here.

    :param method: The API method: an operation's MCP name or a page method (``view``, ...).
    :param params: Its parameters.
    :param ctx: The operation context.
    :param local: Answers the call here.
    :return: The answer."""
    from beamtime.remote.sources import client_for

    if (source := source_of(params)) is not None:
        if method in DRAFTS:
            raise OpError(
                f"{method.replace('_', ' ')} works on drafts in this project; for a group on "
                f"@{source}, run it there (ssh), or pull the group first",
                code=2,
            )
        stripped = strip(params, source)
        if "author" in stripped or method in AUTHORED:
            from beamtime.ops.record import author_of

            # the laptop's author goes along; `user` is the account the remote runs as.
            stripped["author"] = stripped.get("author") or author_of(ctx, None)[0]
        answer = client_for(ctx, source).request(method, stripped, caller=ctx.caller)
        return prefix(answer, source)
    if method in LISTINGS and remote.active is not None and ctx.merge and fans_out(params):
        return federate(method, params, ctx, local)
    try:
        return local(params)
    except OpError as e:
        if e.code != 4 or remote.active is None or (run := run_target(params)) is None:
            raise
        return elsewhere(method, params, ctx, run, e)


# writes whose author the laptop names.
AUTHORED = ("note_add", "proposal_set", "memory_update", "view_upgrade", "name")


def source_of(params: dict[str, Any]) -> str | None:
    """Find the source a call's target names.

    :param params: The parameters.
    :return: The source's name without ``@``, or ``None`` for this machine."""
    for key in TARGETS:
        if isinstance(v := params.get(key), str) and v.startswith("@"):
            return v[1:].split("/", 1)[0]
    if isinstance(query := params.get("query"), dict):
        for inner in query.values():
            if isinstance(inner, dict) and str(inner.get("from", "")).startswith("@"):
                return str(inner["from"])[1:].split("/", 1)[0]
    return None


def strip(params: dict[str, Any], source: str) -> dict[str, Any]:
    """Take the source's prefix off every target.

    :param params: The parameters.
    :param source: The source's name.
    :return: The parameters as the remote reads them."""

    def bare(v: Any) -> Any:
        if not isinstance(v, str) or not v.startswith(f"@{source}"):
            return v
        rest = v[len(source) + 1 :].lstrip("/")
        return rest or "."

    out = {k: bare(v) if k in TARGETS else v for k, v in params.items()}
    if isinstance(query := out.get("query"), dict):
        out["query"] = {
            k: {**v, "from": bare(v.get("from"))} if isinstance(v, dict) else v
            for k, v in query.items()
        }
    return out


def prefix(answer: Any, source: str) -> Any:
    """Give the paths in an answer their source's prefix back.

    :param answer: The remote's answer.
    :param source: The source's name.
    :return: The answer with ``@source/...`` paths."""

    def p(v: Any) -> Any:
        if not isinstance(v, str) or v.startswith(("@", "/")) or "://" in v:
            return v
        return f"@{source}" if v in (".", "") else f"@{source}/{v}"

    def walk(x: Any) -> Any:
        if isinstance(x, list):
            return [walk(v) for v in x]
        if not isinstance(x, dict):
            return x
        # a file reference: its path is relative to the view or block it names.
        ref = isinstance(x.get("view"), str) or "block" in x or "block_draft" in x
        out = {}
        for k, v in x.items():
            if k in PATH_KEYS or (k == "path" and not ref) or (k == "view" and ref):
                out[k] = p(v)
            elif k == "source" and v == "local":
                out[k] = f"@{source}"
            else:
                out[k] = walk(v)
        if isinstance(x.get("columns"), list) and isinstance(x.get("rows"), list):
            at = [i for i, c in enumerate(x["columns"]) if c in PATH_COLUMNS]
            out["rows"] = [[p(v) if i in at else v for i, v in enumerate(r)] for r in x["rows"]]
        return out

    out = walk(answer)
    # a write says what it wrote; the file is on the source.
    if isinstance(answer, dict) and isinstance(path := answer.get("path"), str):
        out["lines"] = [
            line.replace(f"wrote {path}", f"wrote {p(path)}") for line in out.get("lines", [])
        ]
    return out


def fans_out(params: dict[str, Any]) -> bool:
    """Tell whether a listing covers everything: ``from`` is ``.`` or left out.

    :param params: The parameters.
    :return: Whether every source answers it."""
    return params.get("from", ".") in (".", "", None)


def run_target(params: dict[str, Any]) -> str | None:
    """Find a run id a call targets.

    :param params: The parameters.
    :return: The id, or ``None``."""
    for key in ("run", "path"):
        if isinstance(v := params.get(key), str) and is_run_id(v.rstrip("/").rsplit("/", 1)[-1]):
            return v
    return None


def elsewhere(method: str, params: dict[str, Any], ctx: Context, run: str, missing: OpError) -> Any:
    """Look for a run on the remotes after this machine didn't know it.

    :param method: The API method.
    :param params: Its parameters.
    :param ctx: The operation context.
    :param run: The run id the call targets.
    :param missing: The local not-found error, raised again if no remote knows the run.
    :return: The answer of the remote that has the run."""
    assert remote.active is not None
    for name, client in remote.active.clients.items():
        try:
            return prefix(client.request(method, params, caller=ctx.caller), name)
        except OpError:
            continue
    raise missing


def federate(method: str, params: dict[str, Any], ctx: Context, local: Local) -> dict[str, Any]:
    """Ask this machine and every source, and merge the answers.

    :param method: A listing method.
    :param params: Its parameters (``from`` is ``.``).
    :param ctx: The operation context.
    :param local: Answers the call here.
    :return: The merged answer; ``meta.sources`` says which source answered."""
    assert remote.active is not None
    answers = [("local", local(params))]
    states = [{"name": "local", "state": "connected"}]
    for name, client in remote.active.clients.items():
        scoped = params | {"from": client.spec.scope}
        try:
            answers.append((name, prefix(client.request(method, scoped, caller=ctx.caller), name)))
            states.append({"name": f"@{name}", "state": "connected"})
        except OpError as e:
            states.append({"name": f"@{name}", "state": "unreachable", "error": str(e)})
    merged = merge(method, answers, params, ctx)
    merged["meta"] = {**answers[0][1].get("meta", {}), **merged.get("meta", {}), "sources": states}
    return merged


def merge(
    method: str, answers: list[tuple[str, dict]], params: dict[str, Any], ctx: Context
) -> dict:
    """Combine one listing's answers from several sources.

    :param method: The listing method.
    :param answers: ``(source, answer)`` pairs, this machine first.
    :param params: The call's parameters.
    :param ctx: The operation context, for its caller's default limits.
    :return: The merged answer."""
    from beamtime.query.kinds import DEFAULTS

    first = dict(answers[0][1])
    defaults = DEFAULTS[ctx.caller]
    matched = sum(a.get("meta", {}).get("matched", 0) or 0 for _, a in answers)
    match method:
        case "groups" | "data":
            key = "rows" if method == "groups" else "entries"
            first[key] = [x for _, a in answers for x in a.get(key, [])]
        case "runs":
            first |= merge_runs(
                [a for _, a in answers], params, params.get("limit") or defaults["rows"]
            )
        case "series":
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
        case "timeline":
            entries = sorted(
                (e for _, a in answers for e in a.get("entries", [])),
                key=lambda e: e.get("t") or "",
            )
            first["entries"] = entries[-(params.get("limit") or defaults["entries"]) :]
        case "notes":
            limit = params.get("limit") or 30
            entries = sorted(
                (e for _, a in answers for e in a.get("entries", [])),
                key=lambda e: e["id"],
                reverse=True,
            )
            first["entries"] = entries[:limit]
            first["more"] = len(entries) > limit or any(a.get("more") for _, a in answers)
        case "keys":
            first |= merge_keys([a for _, a in answers])
        case other:
            raise ValueError(f"no merge for {other!r}")
    first["meta"] = {**first.get("meta", {}), "matched": matched, "source": "."}
    return first


def merge_runs(answers: list[dict], params: dict[str, Any], limit: int) -> dict[str, Any]:
    """Merge run tables: union of columns, sorted again, cut to the limit.

    Each source returned its top rows by the same sort, so the merged top rows are exact.

    :param answers: The tables.
    :param params: The call's parameters (``sort``).
    :param limit: How many rows to keep.
    :return: ``columns`` and ``rows``."""
    from beamtime.query.kinds import sort_rows

    columns: list[str] = []
    for a in answers:
        columns += [c for c in a.get("columns", []) if c not in columns]
    rows = [
        dict(zip(a.get("columns", []), r, strict=False)) for a in answers for r in a.get("rows", [])
    ]
    sort = list(params.get("sort") or ["-run.created_at"])
    # a run id starts with its creation time, so it sorts like run.created_at.
    sort = [
        s.replace("run.created_at", "run.id") if s.lstrip("-") not in columns else s for s in sort
    ]
    sort_rows(rows, sort)
    return {"columns": columns, "rows": [[r.get(c) for c in columns] for r in rows[:limit]]}


def merge_keys(answers: list[dict]) -> dict[str, Any]:
    """Merge key listings: names united, run counts added, value lists joined.

    :param answers: The listings.
    :return: ``runs``, ``status`` and the merged tables."""
    out: dict[str, Any] = {"runs": sum(a.get("runs", 0) for a in answers)}
    status: dict[str, int] = {}
    for a in answers:
        for k, n in (a.get("status") or {}).items():
            status[k] = status.get(k, 0) + n
    out["status"] = status
    for table in ("metrics", "config", "data"):
        tables = [a[table] for a in answers if isinstance(a.get(table), dict)]
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
                        case "last_step":
                            steps = [x for x in (kept[i], r[i]) if x is not None]
                            kept[i] = max(steps) if steps else None
                        case "values" if isinstance(kept[i], list) and isinstance(r[i], list):
                            kept[i] = kept[i] + [v for v in r[i] if v not in kept[i]]
                        case _:
                            pass
        out[table] = {"columns": columns, "rows": sorted(rows.values(), key=lambda r: r[0])}
    return out


FILE_LIMIT = 64 << 20


def remote_file(run: str, rel: str) -> bytes | None:
    """Fetch a file of a run that lives on a remote, such as a logged image.

    :param run: The run id.
    :param rel: The file's path inside the run.
    :return: Its content, or ``None`` if no remote has it."""
    import base64

    if remote.active is None:
        return None
    for client in remote.active.clients.values():
        try:
            base = client.request("card", {"run": run})["run"]["path"]
            out, offset = bytearray(), 0
            while len(out) < FILE_LIMIT:
                part = client.request("files", {"read": f"{base}/{rel}", "offset": offset})
                out += base64.b64decode(part["data"])
                offset = len(out)
                if part["eof"]:
                    return bytes(out)
            return None
        except (OpError, KeyError, TypeError):
            continue
    return None
