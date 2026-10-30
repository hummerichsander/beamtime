"""The research-record operations: notes, proposals, checks and memory.

The writes are additive: each creates a new file named by a fresh version id."""

import posixpath
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.authored import split_frontmatter
from beamtime.format.ids import is_run_id, new_version_id
from beamtime.format.io import write_created
from beamtime.format.schema import SchemaError
from beamtime.format.tree import is_reserved, is_run
from beamtime.index.index import Index
from beamtime.ops import registry as r
from beamtime.ops.budget import cut, offset_of
from beamtime.ops.context import Context, OpError
from beamtime.query.kinds import known_keys, resolve_from
from beamtime.query.models import QueryError
from beamtime.record import memory as mem
from beamtime.record.check import evaluate
from beamtime.record.notes import build, listing
from beamtime.record.proposals import (
    Proposal,
    RecordError,
    Target,
    all_versions,
    current,
    load,
    parse,
)
from beamtime.record.status import research_status


@contextmanager
def target_of(ctx: Context, group: str, *, create: bool = False) -> Iterator[Target]:
    """Open the index, catch up, and resolve a group or run.

    :param ctx: The operation context.
    :param group: A group below the log dir, or a run id.
    :param create: Whether a missing group is created, for writes before the first run.
    :return: The target, while the index is open."""
    if create:
        make_group(ctx, group)
    if not ctx.logdir.is_dir():
        raise OpError(f"no log dir at {ctx.logdir}; `beamtime init` sets one up", code=4)
    index = Index(logdir=ctx.logdir)
    try:
        index.catch_up(".", 0.2)
        try:
            rel, run_id = resolve_from(index, ".", group)
        except QueryError as e:
            raise OpError(str(e), code=4 if e.code == "not_found" else 2) from None
        try:
            yield Target(index=index, rel=rel, run_id=run_id)
        except RecordError as e:
            raise OpError(str(e), code=3) from None
    finally:
        index.close()


def make_group(ctx: Context, group: str) -> None:
    """Create a missing group below the log dir, refusing reserved names and runs.

    :param ctx: The operation context.
    :param group: The group relative to the log dir, or a run id."""
    rel = posixpath.normpath(group.strip("/") or ".")
    if is_run_id(rel.rsplit("/", 1)[-1]) or rel == ".":
        return
    if rel.startswith(".."):
        raise OpError(f"{group!r} leaves the log dir", code=2)
    path = ctx.logdir / rel
    if path.is_dir():
        return
    if any(is_reserved(part) for part in rel.split("/")):
        raise OpError(f"{group!r}: names starting with _ or . and {sorted(c.AUTHORED)} are "
                      "reserved; choose another group name", code=2)  # fmt: skip
    if any(is_run(parent) for parent in path.parents):
        raise OpError(f"{group!r} is inside a run; give the run id instead", code=2)
    path.mkdir(parents=True)


def author_of(ctx: Context, author: str | None) -> tuple[str, str]:
    """Name who writes a file and the account it is written for.

    :param ctx: The operation context.
    :param author: The given author, if any.
    :return: ``(author, user)``."""
    from beamtime.sdk.env import user

    account = user()
    return author or (account if ctx.caller in ("cli", "view") else "agent"), account


def save(folder: Path, suffix: str, text: str) -> Path:
    """Write a new version of an authored file.

    :param group: The authored group, e.g. ``<group>/notes``.
    :param suffix: ``.md`` or ``.yaml``.
    :param text: The content.
    :return: The new file."""
    from beamtime.format.authored import newest

    # the newest version counts, so a save must sort after it, also within the same second.
    latest = (newest(folder) or Path("")).stem
    path = folder / f"{new_version_id()}{suffix}"
    while path.exists() or path.stem <= latest:
        time.sleep(0.01)
        path = folder / f"{new_version_id()}{suffix}"
    write_created(path, text.encode())
    return path


def dump(fields: dict[str, Any]) -> str:
    """Write YAML in the order given.

    :param fields: The fields.
    :return: The YAML text."""
    import yaml

    return yaml.safe_dump(fields, sort_keys=False, allow_unicode=True)


def written(ctx: Context, kind: str, path: Path, lines: list[str]) -> dict[str, Any]:
    """Build the answer of a write.

    :param ctx: The operation context.
    :param kind: The operation.
    :param path: The new file.
    :param lines: What else to say.
    :return: The answer."""
    rel = path.relative_to(ctx.logdir).as_posix()
    return {
        "kind": kind,
        "lines": [f"wrote {rel}", *lines],
        "path": rel,
        "version": path.stem,
        "meta": {},
    }


def notes(ctx: Context, p: r.NotesParams) -> dict[str, Any]:
    """List notes at or below a group, newest first.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer: ``entries`` with id, type, description and state."""
    with target_of(ctx, p.from_) as target:
        entries = listing(
            target, types=p.types, only_open=p.open, full=p.full, only_current=p.current
        )
    total = len(entries)
    if p.before is not None:
        # ids sort by time, so older notes have smaller ids.
        entries = [e for e in entries if e["id"] < p.before]
    limit = p.limit if p.limit is not None else 30
    more = len(entries) > limit
    answer = {
        "kind": "notes",
        "group": target.rel,
        "entries": entries[:limit],
        "more": more,
        "meta": {"matched": total},
    }
    if more:
        older = entries[limit - 1]["id"] if limit else p.before
        answer["meta"] |= {"cut": True, "hint": f"older notes: before={older}"}
    return answer if ctx.caller == "view" else cut(answer, offset_of(p.cursor))


def proposal_show(ctx: Context, p: r.GroupParams) -> dict[str, Any]:
    """Show the current proposal, its earlier versions and their checks.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    import yaml

    with target_of(ctx, p.group) as target:
        versions = all_versions(target.dir)
        if not versions:
            raise OpError(
                f"{target.rel} has no proposal; write one with `beamtime proposal set "
                f"{target.rel} <file>`",
                code=4,
            )
        status = research_status(target)
        history = []
        for version in reversed(versions):
            members = target.members(version)
            try:
                proposal = load(target.dir, version)
                check = evaluate(target, version, proposal)["result"]
                statement, supersedes = proposal.statement, proposal.supersedes
            except RecordError as e:
                check, statement, supersedes = "invalid", str(e), None
            history.append(
                {
                    "version": version,
                    "statement": statement,
                    "runs": len(members),
                    "frozen": bool(members) or target.run_id is not None,
                    "check": check,
                    "supersedes": supersedes.version if supersedes else None,
                    "reason": supersedes.reason if supersedes else None,
                }
            )
        text = (target.dir / c.PROPOSAL / f"{versions[-1]}.yaml").read_text()
    return {
        "kind": "proposal",
        "group": target.rel,
        "version": versions[-1],
        "status": status["status"],
        "progress": status["progress_text"],
        "proposal": yaml.safe_load(text),
        "versions": history,
        "meta": {},
    }


def check(ctx: Context, p: r.CheckParams) -> dict[str, Any]:
    """Check a proposal version against its runs.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The check."""
    with target_of(ctx, p.group) as target:
        version = p.version or current(target.dir)
        if version is None:
            raise OpError(f"{target.rel} has no proposal to check", code=4)
        if version not in all_versions(target.dir):
            raise OpError(f"no proposal version {version!r} in {target.rel}", code=4)
        result = evaluate(target, version)
    return {"kind": "check"} | result | {"meta": {}}


def memory_show(ctx: Context, p: r.GroupParams) -> dict[str, Any]:
    """Show the memory of a group and every group above it, root first.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer: ``chain`` with each memory and its staleness."""
    with target_of(ctx, p.group) as target:
        chain = mem.chain(target)
        unread = mem.notes_since(target, target.rel, None) if not chain else 0
    hints = [
        f"{m['group']}: {m['notes_since']} note(s) since the last update; "
        f"update with `beamtime memory update {m['group']}`"
        for m in chain
        if m.get("notes_since")
    ]
    if not chain:
        hints.append(f"no memory yet; {unread} note(s) in scope")
    return {
        "kind": "memory",
        "group": target.rel,
        "chain": chain,
        "budget": mem.BUDGET_CHARS,
        "meta": {"hints": hints},
    }


def note_add(ctx: Context, p: r.NoteAddParams) -> dict[str, Any]:
    """Add a note to a group or run.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new note's path and id."""
    author, user = author_of(ctx, p.author)
    with target_of(ctx, p.group, create=True) as target:
        meta = build(
            target,
            type=p.type,
            description=p.description,
            resolves=p.resolves,
            supersedes=p.supersedes,
            completes=p.completes,
            evidence=p.evidence,
            proposal=p.proposal,
            verdicts=p.verdict,
            overall=p.overall,
        )
        front = dump({"schema": 1, **meta, "author": author, "user": user})
        body = (p.body or "").strip()
        path = save(target.dir / c.NOTES, ".md", f"---\n{front}---\n\n{body}\n")
        lines = []
        if p.type == "verdict":
            results = ", ".join(f"{k} {v['result']}" for k, v in meta["check"].items())
            lines.append(f"check at the time of writing: {results or 'no automatic predictions'}")
        if p.type in ("verdict", "decision"):
            lines.append(f"next: update the memory (`beamtime memory update {target.rel}`)")
    return written(ctx, "note add", path, lines)


def name(ctx: Context, p: r.NameParams) -> dict[str, Any]:
    """Give a run a display name, as a new version in its ``name/`` folder.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new version."""
    if not p.name.strip() or "\n" in p.name:
        raise OpError("a name is one non-empty line", code=2)
    author, user = author_of(ctx, p.author)
    with target_of(ctx, p.run) as target:
        if target.run_id is None:
            raise OpError(f"{p.run!r} is a group; groups are renamed with `beamtime mv`", code=2)
        fields = {"schema": 1, "name": p.name.strip(), "author": author, "user": user}
        path = save(target.dir / c.NAME, ".yaml", dump(fields))
    return written(ctx, "name", path, [f"{target.run_id} is now shown as {p.name.strip()!r}"])


def note_rm(ctx: Context, p: r.NoteRmParams) -> dict[str, Any]:
    """Move a note into the trash, with the versions it superseded, so it is gone everywhere.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What moved where."""
    import json
    import shutil
    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    lines = []
    with target_of(ctx, ".") as target:
        db = target.index.store.db
        rows = {i: (path, json.loads(meta or "{}")) for path, i, meta in db.execute(
            "SELECT path, id, meta FROM notes")}  # fmt: skip
        if p.note not in rows:
            raise OpError(f"no note {p.note!r}; `beamtime notes` lists them", code=4)
        chain, note = [], p.note
        while note in rows and note not in chain:
            chain.append(note)
            note = rows[note][1].get("supersedes")
        for note in chain:
            rel = Path(rows[note][0])
            dest = ctx.logdir / c.TRASH / stamp / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(ctx.logdir / rel), str(dest))
            lines.append(f"moved {rel.as_posix()} to {dest.relative_to(ctx.logdir).as_posix()}")
    lines.append("`beamtime gc --yes` deletes the trash for good")
    return {"kind": "note rm", "lines": lines, "notes": chain, "meta": {}}


def proposal_set(ctx: Context, p: r.ProposalSetParams) -> dict[str, Any]:
    """Save a new proposal version, refusing to silently replace a frozen one.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new version and any warnings."""
    data, source = read_input(p.file, p.proposal, "proposal", yaml_text=True)
    if isinstance(data, dict) and p.reason and "supersedes" not in data:
        data = data | {"supersedes": {"version": None, "reason": p.reason}}
    with target_of(ctx, p.group, create=True) as target:
        latest = current(target.dir)
        if isinstance(data, dict) and isinstance(data.get("supersedes"), dict):
            data["supersedes"].setdefault("version", None)
            data["supersedes"]["version"] = data["supersedes"]["version"] or latest
        proposal = parse(data, source=source)
        if not proposal.statement:
            raise RecordError(f"{source}: statement is required: what the runs should show")
        lines = superseding(target, proposal, latest)
        author, user = author_of(ctx, p.author)
        fields = {k: v for k, v in data.items() if k not in ("schema", "author", "user")}
        path = save(
            target.dir / c.PROPOSAL,
            ".yaml",
            dump({"schema": 1, **fields, "author": author, "user": user}),
        )
        lines += metric_warnings(target, proposal)
        lines.append("runs started from now on record this version")
    return written(ctx, "proposal set", path, lines)


def superseding(target: Target, proposal: Proposal, latest: str | None) -> list[str]:
    """Apply the superseding rules: frozen versions are superseded with a reason.

    :param target: The group or run.
    :param proposal: The new version.
    :param latest: The current version, if any.
    :return: Lines for the answer."""
    if proposal.supersedes is not None:
        if proposal.supersedes.version not in all_versions(target.dir):
            raise RecordError(f"supersedes: no version {proposal.supersedes.version!r}")
        if not proposal.supersedes.reason.strip():
            raise RecordError("supersedes: give the reason")
        return [f"supersedes {proposal.supersedes.version}: {proposal.supersedes.reason}"]
    if latest is None:
        return []
    n = len(target.members(latest))
    if n or target.run_id is not None:
        raise RecordError(
            f"the current version {latest} is frozen ({n} run(s) recorded it); say why it is "
            f"replaced: --reason '...' or supersedes: {{version: {latest}, reason: ...}}"
        )
    return [f"replaces {latest}, which no run had recorded"]


def metric_warnings(target: Target, proposal: Proposal) -> list[str]:
    """Warn about predictions on metrics no run in scope has logged yet.

    :param target: The group or run.
    :param proposal: The proposal.
    :return: One line per unknown metric."""
    from beamtime.query.kinds import Context as QueryContext

    ctx = QueryContext(
        index=target.index, caller="cli", scope=target.rel, run_id=target.run_id, now=time.time()
    )
    known = known_keys(ctx, "metrics")
    if not known:
        return []
    metrics = {pr.reduce.metric for pr in proposal.predictions if pr.reduce is not None}
    return [
        f"warning: no run in {target.rel} has logged {m!r} yet; check the key name"
        for m in sorted(metrics - known)
    ]


def memory_update(ctx: Context, p: r.MemoryUpdateParams) -> dict[str, Any]:
    """Save a new memory version for a group.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new version and any warnings."""
    text, source = read_input(p.file, p.body, "body")
    meta: dict[str, Any] = {}
    if text.lstrip().startswith("---"):
        try:
            meta, text = split_frontmatter(text.lstrip(), source=source)
        except SchemaError as e:
            raise OpError(str(e), code=3) from None
        meta = meta or {}
    body = text.strip()
    if not body:
        raise OpError("memory update: the memory is empty", code=3)
    author, user = author_of(ctx, p.author or meta.get("author"))
    with target_of(ctx, p.group, create=True) as target:
        covers = p.covers_until or meta.get("covers_until")
        if covers is not None and mem.to_time(covers) is None:
            raise OpError(
                f"covers_until {covers!r} is not a time like 2026-10-25T14:00:00Z", code=3
            )
        t = mem.to_time(covers) if covers is not None else mem.newest_note_time(target)
        fields = {"schema": 1, "covers_until": mem.iso(t or time.time())}
        path = save(
            target.dir / c.MEMORY,
            ".md",
            f"---\n{dump(fields | {'author': author, 'user': user})}---\n\n{body}\n",
        )
    lines = [f"covers notes until {fields['covers_until']}"]
    if len(body) > mem.BUDGET_CHARS:
        lines.append(
            f"warning: {len(body)} characters, beyond the budget of about {mem.BUDGET_CHARS} "
            "(1.5k tokens); compress: fold concluded work into single lines"
        )
    return written(ctx, "memory update", path, lines)


def read_input(
    file: str | None, given: Any, name: str, *, yaml_text: bool = False
) -> tuple[Any, str]:
    """Read what a write saves, from a file or a parameter.

    :param file: A path, from the CLI or an agent.
    :param given: The parameter's value: text, or an object.
    :param name: The parameter's name, for messages.
    :param yaml_text: Whether text is parsed as YAML.
    :return: The content and where it came from."""
    parse_text: Callable[[str], Any] = yaml_load if yaml_text else str
    if file is not None:
        path = Path(file).expanduser()
        if not path.is_file():
            raise OpError(f"no file {file!r}", code=4)
        return parse_text(path.read_text()), path.name
    if given is None:
        raise OpError(f"give a file, or {name} (on the command line, stdin works too)", code=2)
    return (parse_text(given) if isinstance(given, str) else given), name


def yaml_load(text: str) -> Any:
    """Parse YAML, with errors that say where.

    :param text: The text.
    :return: The value."""
    import yaml

    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise OpError(f"not valid YAML: {e}", code=3) from None
