"""Routing calls to the source their target names, and merging what several sources answer.

A target naming ``@x/...`` sends the call to ``x`` with the prefix stripped; paths in the answer get
it back. Listings over ``.`` ask every source of the running serve and merge. A run id the local
log dir doesn't know is looked for on the remotes, since run ids are unique everywhere."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from beamtime.format.ids import is_run_id
from beamtime.format.place import Place
from beamtime.ops import answers
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import OPS
from beamtime.remote import TARGETS, places

# from the registry: listings merge across sources, drafts stay in this project, snapshots refuse
# writes (and the web UI's own writes), writes that take an author get this machine's.
LISTINGS = {op.tool for op in OPS if op.listing}
DRAFTS = {op.tool for op in OPS if op.drafts}
WRITES = {op.tool for op in OPS if op.writes} | {"view_text", "save_view"}
AUTHORED = {op.tool for op in OPS if "author" in op.params.__struct_fields__}
# a listing waits this long for a remote before it answers without it.
LISTING_S = 20.0

Local = Callable[[dict[str, Any]], Any]


def routed(method: str, params: dict[str, Any], ctx: Context, local: Local) -> Any:
    """Answer a call where it belongs: on the source its target names, merged over every source
    for listings of ``.``, else here.

    :param method: The API method: an operation's MCP name or a page method (``view``, ...).
    :param params: Its parameters.
    :param ctx: The operation context.
    :param local: Answers the call here.
    :return: The answer."""
    from beamtime.remote.client import Unreachable
    from beamtime.remote.sources import client_for

    params = strip(params, None)
    if method in ("cp", "compare"):
        check_one_source(method, params, ctx)
    source = source_of(params)
    fans = method in LISTINGS and ctx.sources is not None and ctx.merge and fans_out(params)
    if source is None and fans:
        return federate(method, params, ctx, local)
    if source is None and (source := ctx.default_source) is not None:
        params = with_default(method, params, source)
    if source is not None:
        # the draft stays with the agent; the op itself fetches from, or pushes to, the source.
        if method in DRAFTS:
            return local(params)
        stripped = with_author(method, strip(params, source), ctx)
        try:
            answer = client_for(ctx, source).request(method, stripped, caller=ctx.caller)
        except Unreachable as e:
            return from_snapshot(method, strip(params, source), ctx, source, e)
        return answers.placed(answer, source)
    try:
        return local(params)
    except OpError as e:
        if e.code != 4 or ctx.sources is None or (run := run_target(params)) is None:
            raise
        return elsewhere(method, params, ctx, run, e)


def check_one_source(method: str, params: dict[str, Any], ctx: Context) -> None:
    """Refuse a call whose targets are not all on the same machine.

    :param method: ``cp`` or ``compare``.
    :param params: The parameters.
    :param ctx: The operation context, for the default source a bare path means.
    :raises OpError: If the targets name different sources."""
    keys = ("source", "dest") if method == "cp" else ("targets",)
    named = {
        source_of({"from": v}) or ctx.default_source
        for key in keys
        for v in places({key: params.get(key)})
    }
    if len(named) > 1:
        then = "`beamtime pull` copies across sources" if method == "cp" else "pull one first"
        raise OpError(f"{method} works within one source for now; {then}", code=2)


def with_default(method: str, params: dict[str, Any], source: str) -> dict[str, Any]:
    """Name the default source in a draft op's group, since the op runs here and decides by the
    ``@`` prefix where its check and write go.

    :param method: The API method.
    :param params: Its parameters, without a source.
    :param source: The default source.
    :return: The parameters."""
    if method not in DRAFTS or not isinstance(group := params.get("group"), str):
        return params
    bare = group.strip("/")
    return params | {"group": f"@{source}/{bare}" if bare not in ("", ".") else f"@{source}"}


def with_author(method: str, params: dict[str, Any], ctx: Context) -> dict[str, Any]:
    """Name this machine's author on a write that goes to a remote.

    :param method: The API method.
    :param params: Its parameters.
    :param ctx: The operation context.
    :return: The parameters; ``user`` is still the account the remote runs as."""
    if method not in AUTHORED:
        return params
    from beamtime.ops.authored import author_of

    return params | {"author": params.get("author") or author_of(ctx, None)[0]}


def from_snapshot(
    method: str, params: dict[str, Any], ctx: Context, source: str, unreachable: OpError
) -> Any:
    """Answer for an unreachable remote from its pulled snapshot, at the snapshot's time.

    :param method: The API method.
    :param params: Its parameters, without the source's prefix.
    :param ctx: The operation context.
    :param source: The remote.
    :param unreachable: Why the remote can't answer, raised again without a snapshot.
    :return: The answer, marked with the snapshot's time."""
    import dataclasses
    import time

    from beamtime.ops import call
    from beamtime.ops.registry import BY_TOOL
    from beamtime.remote.pull import snapshot_of
    from beamtime.serve.api import dispatch_here

    if (found := snapshot_of(ctx, source)) is None:
        raise unreachable
    folder, record = found
    when = time.strftime("%Y-%m-%d %H:%M", time.localtime(record["at"]))
    if method in WRITES:
        raise OpError(f"{unreachable}; its snapshot of {when} is read-only", code=1)
    here = dataclasses.replace(ctx, logdir=folder, now=record["at"], merge=False)
    if (op := BY_TOOL.get(method)) is not None:
        answer = call(op.name, params, here)
    else:
        answer = dispatch_here(here, method, params)
    answer = answers.placed(answer, source)
    if isinstance(answer, dict):
        answer["meta"] = {**answer.get("meta", {}), "snapshot": record["at"], "snapshot_of": when}
    return answer


def source_of(params: dict[str, Any]) -> str | None:
    """Find the source a call's target names.

    :param params: The parameters.
    :return: The source's name without ``@``, or ``None`` for this machine."""
    for v in places(params):
        if (source := Place.parse(v).source) is not None:
            return source
    if isinstance(query := params.get("query"), dict):
        for inner in query.values():
            if isinstance(inner, dict) and (
                source := Place.parse(str(inner.get("from", ""))).source
            ):
                return source
    return None


def strip(params: dict[str, Any], source: str | None) -> dict[str, Any]:
    """Take the source's prefix off every target.

    :param params: The parameters.
    :param source: The source's name, or ``None`` to take an explicit ``@local`` off.
    :return: The parameters as the remote reads them."""

    def bare(v: Any) -> Any:
        if isinstance(v, list):
            return [bare(x) for x in v]
        if not isinstance(v, str) or (place := Place.parse(v)).source != source or v == place.path:
            return v
        return place.path

    out = {k: bare(v) if k in TARGETS else v for k, v in params.items()}
    if isinstance(query := out.get("query"), dict):
        out["query"] = {
            k: {**v, "from": bare(v.get("from"))} if isinstance(v, dict) else v
            for k, v in query.items()
        }
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
    assert ctx.sources is not None
    params = with_author(method, params, ctx)
    for name, client in ctx.sources.clients.items():
        try:
            return answers.placed(client.request(method, params, caller=ctx.caller), name)
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
    assert ctx.sources is not None
    clients = list(ctx.sources.clients.items())

    def ask(name: str, client: Any) -> tuple[dict | None, dict[str, Any]]:
        scoped = params | {"from": client.spec.scope}
        try:
            answer = client.request(method, scoped, caller=ctx.caller, timeout=LISTING_S)
            return answers.placed(answer, name), {"name": f"@{name}", "state": "connected"}
        except OpError as e:
            try:
                snap = from_snapshot(method, scoped, ctx, name, e)
                return snap, {"name": f"@{name}", "state": "snapshot", "error": str(e)}
            except OpError:
                return None, {"name": f"@{name}", "state": "unreachable", "error": str(e)}

    # every remote at once: a page waits for the slowest, not for the sum of them.
    with ThreadPoolExecutor(max(1, len(clients))) as pool:
        asked = [pool.submit(ask, name, client) for name, client in clients]
        # a source is a named log dir; without local runs, local isn't one and is left out.
        collected = [("local", local(params))] if ctx.has_local else []
        states = [{"name": "local", "state": "connected"}] if ctx.has_local else []
        for (name, _), future in zip(clients, asked, strict=True):
            answer, state = future.result()
            states.append(state)
            if answer is not None:
                collected.append((name, answer))
    if not collected and method == "groups":
        # the tree still has a root per source, each saying why it can't answer.
        meta = {"source": ".", "matched": 0, "sources": states}
        return {"kind": "groups", "columns": ["path"], "rows": [], "meta": meta}
    if not collected:
        reasons = "; ".join(f"{s['name']}: {s.get('error') or s['state']}" for s in states)
        raise OpError(f"no source could answer {method}: {reasons}", code=1)
    merged = answers.merged(method, collected, params, ctx.caller)
    merged["meta"] = {
        **collected[0][1].get("meta", {}),
        **merged.get("meta", {}),
        "sources": states,
    }
    return merged


FILE_LIMIT = 64 << 20


def remote_file(ctx: Context, run: str, rel: str, source: str | None = None) -> bytes | None:
    """Fetch a file of a run that lives on a remote, such as a logged image.

    :param ctx: The operation context, with the serve's sources.
    :param run: The run id.
    :param rel: The file's path inside the run.
    :param source: The remote it is on, if known; else every remote is asked.
    :return: Its content, or ``None`` if no remote has it."""
    import base64

    if ctx.sources is None:
        return None
    clients = ctx.sources.clients
    for client in [clients[source]] if source in clients else clients.values():
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


def on_source(method: str, target: str, ctx: Context, body: dict[str, Any]) -> Any:
    """Send an API-only bundle method (``view_check``, ``view_put``, ``view_compile``,
    ``view_files``, ``block_check`` or ``block_put``) to the source a group names, and give the
    answer's paths that source's prefix back.

    :param method: The API-only method.
    :param target: The group the bundle is for, ``@source/bare``.
    :param ctx: The operation context.
    :param body: The rest of the body: the bundle, and for a save ``author`` and ``message``.
    :return: The remote's answer.
    :raises OpError: If the remote can't be reached, or is too old for the method."""
    from beamtime.ops.views import check_size
    from beamtime.remote.client import RemoteError
    from beamtime.remote.sources import client_for

    check_size(body)
    place = Place.parse(target)
    source = place.source
    client = client_for(ctx, source)
    try:
        answer = client.request(method, {"group": place.path, **body}, caller=ctx.caller)
    except RemoteError as e:
        if e.code == 4 and "no API method" in e.reason:
            raise OpError(
                f"@{source} runs beamtime {client.info.get('version', '?')}; this needs a newer "
                f"version for {method.replace('_', ' ')}: `uv pip install -U beamtime` there",
                code=2,
            ) from None
        raise
    return answers.placed(answer, source)
