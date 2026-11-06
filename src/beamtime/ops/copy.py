"""``beamtime cp``: copy a run or group, keeping checkpoint references valid.

Additive, so agents may use it: it never modifies the source, and a crash leaves only a
temporary directory with a reserved name, which ``gc`` removes."""

import os
import shutil
import time
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.authored import file_hash, newest
from beamtime.format.ids import new_run_id
from beamtime.format.io import append_lines, json_line, read_json, write_replaced
from beamtime.format.run import Artifact, read_artifacts
from beamtime.format.times import iso
from beamtime.format.tree import is_run, iter_runs
from beamtime.index.index import Index
from beamtime.ops import registry as r
from beamtime.ops.admin import answer, inside, refuse_running
from beamtime.ops.context import Context, OpError

# the reserved prefix of a copy's hidden working directory, so discovery ignores it mid-copy.
TEMP_PREFIX = "_cp-"


def cp(ctx: Context, p: r.CpParams) -> dict[str, Any]:
    """Copy a run or group into another group, under new run ids.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was copied."""
    from beamtime.ops.reading import find_run

    if p.source.startswith("@") or p.dest.startswith("@"):
        raise OpError(
            "cp works within one source for now; `beamtime pull` copies across sources", code=2
        )
    dest_group = inside(ctx, p.dest)
    if any((parent / c.RUN).exists() for parent in (dest_group, *dest_group.parents)):
        raise OpError(f"{p.dest!r} is inside a run; choose a group", code=2)
    source = (ctx.logdir / p.source.strip("/")).resolve()
    if source.is_dir() and ctx.logdir in source.parents and not is_run(source):
        return copy_group(ctx, source, dest_group, p)
    run_dir = find_run(ctx, p.source)
    info = copy_run_core(ctx, run_dir, dest_group, name=p.name, with_checkpoints=p.with_checkpoints)
    lines = [f"copied {run_dir.relative_to(ctx.logdir)} to {info['path']}"]
    lines += skip_lines(info["skipped"])
    return answer("cp", lines, path=info["path"], id=info["id"], checkpoints=info["checkpoints"])


def skip_lines(skipped: list[str]) -> list[str]:
    """Report checkpoints a copy could not find.

    :param skipped: Their names.
    :return: One line per missing checkpoint."""
    return [f"skipped {name}: the checkpoint file is missing" for name in skipped]


def copy_run_core(
    ctx: Context, run_dir: Path, dest_group: Path, *, name: str | None, with_checkpoints: bool
) -> dict[str, Any]:
    """Copy one run into a destination group, under a new id.

    :param ctx: The operation context.
    :param run_dir: The source run directory.
    :param dest_group: Where the copy goes; created if missing.
    :param name: A new display name for the copy, or ``None`` to keep the source's.
    :param with_checkpoints: Whether to copy checkpoint files in, instead of referencing them.
    :return: ``id``, ``path`` (relative to the log dir), ``size`` in bytes, the resolved
        ``checkpoints`` rows, and ``skipped`` checkpoint names."""
    refuse_running(run_dir, "copy")
    dest_group.mkdir(parents=True, exist_ok=True)
    new_id = new_run_id()
    temp = dest_group / f"{TEMP_PREFIX}{new_id}"
    if temp.exists():
        raise OpError(f"{temp} already exists; try again", code=1)
    ignore = None if with_checkpoints else shutil.ignore_patterns("checkpoints")
    shutil.copytree(run_dir, temp, ignore=ignore)
    source_id = read_json(run_dir / c.RUN)["id"]
    checkpoints_, skipped = rewrite_artifacts(
        ctx, run_dir, temp, source_id, with_checkpoints=with_checkpoints
    )
    rewrite_run_info(ctx, run_dir, temp, dest_group, new_id, name)
    append_lines(temp / c.EVENTS, [{"_t": time.time(), "kind": "copied", "from": source_id}])
    final = dest_group / new_id
    os.replace(temp, final)
    size = sum(f.stat().st_size for f in final.rglob("*") if f.is_file())
    return {
        "id": new_id,
        "path": final.relative_to(ctx.logdir).as_posix(),
        "size": size,
        "checkpoints": checkpoints_,
        "skipped": skipped,
    }


def rewrite_run_info(
    ctx: Context, run_dir: Path, temp: Path, dest_group: Path, new_id: str, name: str | None
) -> None:
    """Rewrite a copy's ``_run.json``: new id, fresh proposal membership, ``copied_from``.

    ``created_at`` and ``attempts`` stay, since that is when the data was made; the run's own
    proposal entry (``.``) stays too, naming the version file copytree already carried over.

    :param ctx: The operation context.
    :param run_dir: The source run directory.
    :param temp: The copy's (still hidden) directory.
    :param dest_group: The destination group the copy lands in.
    :param new_id: The copy's new run id.
    :param name: A new display name, or ``None`` to keep the source's."""
    d = read_json(temp / c.RUN)
    source_id, source_path = d["id"], run_dir.relative_to(ctx.logdir).as_posix()
    own = (d.get("proposals") or {}).get(".")
    proposals = {".": own} if own else {}
    hashes = {".": (d.get("proposal_hashes") or {}).get(".")} if own else {}
    rel = dest_group.relative_to(ctx.logdir)
    parts = rel.parts
    for i in range(1, len(parts) + 1):
        group = "/".join(parts[:i])
        if (path := newest(ctx.logdir / group / c.PROPOSAL)) is not None:
            proposals[group] = path.stem
            hashes[group] = file_hash(path)
    d["id"] = new_id
    d["proposals"] = proposals
    d["proposal_hashes"] = hashes
    d["copied_from"] = {"id": source_id, "path": source_path, "at": iso(time.time(), ms=True)}
    if name:
        d["name"] = name
        shutil.rmtree(temp / c.NAME, ignore_errors=True)
    write_replaced(temp / c.RUN, d, sync=True)


def artifact_dict(a: Artifact) -> dict[str, Any]:
    """Turn an artifact back into its stored JSON shape.

    :param a: The artifact.
    :return: The fields it was read with, dropping the ones that are ``None``."""
    return {
        k: v
        for k, v in (
            ("name", a.name),
            ("size", a.size),
            ("kind", a.kind),
            ("path", a.path),
            ("uri", a.uri),
            ("origin", a.origin),
            ("score", a.score),
            ("monitor", a.monitor),
        )
        if v is not None
    }


def rewrite_artifacts(
    ctx: Context, run_dir: Path, temp: Path, source_id: str, *, with_checkpoints: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """Rewrite a copy's ``_artifacts.jsonl`` so every checkpoint reference stays resolvable.

    :param ctx: The operation context.
    :param run_dir: The source run directory.
    :param temp: The copy's (still hidden) directory.
    :param source_id: The source run's id.
    :param with_checkpoints: Whether checkpoint files are copied in, severing the reference.
    :return: The resolved checkpoint rows for the answer, and the names of any that were
        missing when ``with_checkpoints`` asked to copy them in."""
    artifacts = read_artifacts(run_dir)
    named = {Path(a.path).name for a in artifacts if a.path}
    named |= {Path(a.uri).name for a in artifacts if a.uri}
    checkpoints_dir = run_dir / "checkpoints"
    if checkpoints_dir.is_dir():
        for f in sorted(checkpoints_dir.iterdir()):
            if f.is_file() and f.name not in named:
                artifacts.append(
                    Artifact(name=f.name, size=f.stat().st_size, kind="checkpoint", uri=str(f))
                )
    records, resolved, skipped, used = [], [], [], set()
    for a in artifacts:
        if a.kind != "checkpoint":
            records.append(artifact_dict(a))
            continue
        record, row, miss = copy_checkpoint(
            ctx, a, run_dir, temp, source_id, with_checkpoints, used
        )
        records.append(record)
        resolved.append(row)
        if miss:
            skipped.append(a.name)
    (temp / c.ARTIFACTS).write_bytes(b"".join(json_line(r) for r in records))
    return resolved, skipped


def copy_checkpoint(
    ctx: Context,
    a: Artifact,
    run_dir: Path,
    temp: Path,
    source_id: str,
    with_checkpoints: bool,
    used: set[str],
) -> tuple[dict[str, Any], dict[str, Any], bool]:
    """Resolve one checkpoint reference, and copy its file in if asked.

    :param ctx: The operation context.
    :param a: The source artifact record.
    :param run_dir: The source run directory.
    :param temp: The copy's directory.
    :param source_id: The source run's id.
    :param with_checkpoints: Whether to copy the file in, leaving no reference to the source.
    :param used: Names already used in the copy's ``checkpoints/``, extended in place.
    :return: The new record, a summary row, and whether the file was missing."""
    location, exists = locate_checkpoint(ctx, run_dir, a)
    if a.path is not None:
        # already travels with the run, inside artifacts/; nothing to do in either mode.
        return artifact_dict(a), summary_row(a, exists=exists), False
    if with_checkpoints:
        if location is None or not exists:
            return artifact_dict(a), summary_row(a, exists=False), True
        if run_dir in (location.parent, *location.parents):
            # copytree already carried this file into the copy, at the same relative path.
            dest = temp / location.relative_to(run_dir)
        else:
            name = unique_name(temp / "checkpoints", location.name, used)
            (temp / "checkpoints").mkdir(exist_ok=True)
            dest = temp / "checkpoints" / name
            shutil.copyfile(location, dest)
        record = {
            "name": a.name,
            "size": dest.stat().st_size,
            "kind": "checkpoint",
            "path": dest.relative_to(temp).as_posix(),
        }
        if a.score is not None:
            record["score"] = a.score
        if a.monitor is not None:
            record["monitor"] = a.monitor
        return record, summary_row(a, exists=True), False
    if a.origin is not None:
        return artifact_dict(a), summary_row(a, exists=exists), False
    if (
        a.uri is not None
        and location is not None
        and run_dir in (location.parent, *location.parents)
    ):
        record = artifact_dict(a)
        record["origin"] = {"run": source_id, "path": location.relative_to(run_dir).as_posix()}
        return record, summary_row(a, exists=exists), False
    return artifact_dict(a), summary_row(a, exists=exists), False


def summary_row(a: Artifact, *, exists: bool) -> dict[str, Any]:
    """Describe one checkpoint for a ``cp`` answer.

    :param a: The artifact.
    :param exists: Whether its file was found.
    :return: Name, score and whether it exists."""
    return {"name": a.name, "score": a.score, "exists": exists}


def unique_name(folder: Path, name: str, used: set[str]) -> str:
    """Pick a file name that collides with neither the folder nor names already placed.

    :param folder: The destination folder.
    :param name: The wanted name.
    :param used: Names already placed there in this call, extended in place.
    :return: A name that is free."""
    stem, suffix, n = Path(name).stem, Path(name).suffix, 1
    candidate = name
    while candidate in used or (folder / candidate).exists():
        candidate, n = f"{stem}-{n}{suffix}", n + 1
    used.add(candidate)
    return candidate


def locate_checkpoint(ctx: Context, run_dir: Path, a: Artifact) -> tuple[Path | None, bool]:
    """Find where a checkpoint artifact's file really is.

    ``path`` is inside the run; ``origin`` is the source run found by id through the index, so
    it follows ``mv``, falling back to ``uri``; otherwise ``uri`` is used directly.

    :param ctx: The operation context.
    :param run_dir: The run directory holding the record.
    :param a: The artifact record.
    :return: Its path, and whether the file exists; ``(None, False)`` if nothing is recorded."""
    if a.path is not None:
        location = run_dir / a.path
        return location, location.is_file()
    if a.origin is not None:
        if (source := locate_run(ctx, a.origin["run"])) is not None:
            location = source / a.origin["path"]
            return location, location.is_file()
        if a.uri is not None:
            location = Path(a.uri)
            return location, location.is_file()
        return None, False
    if a.uri is not None:
        location = Path(a.uri)
        return location, location.is_file()
    return None, False


def locate_run(ctx: Context, run_id: str) -> Path | None:
    """Find a run by id, without raising if it is gone.

    Always catches up first (small files only, so it stays cheap): a cached path from
    before a ``mv`` must not be trusted, since that is exactly when this is asked to follow.

    :param ctx: The operation context.
    :param run_id: The run id.
    :return: The run directory, or ``None``."""
    with Index(logdir=ctx.logdir) as index:
        index.catch_up(".", budget_s=0.2)
        return index.run_path(run_id)


def checkpoints(ctx: Context, run_dir: Path) -> list[dict[str, Any]]:
    """Resolve every checkpoint a run references, wherever the file really is.

    :param ctx: The operation context.
    :param run_dir: The run directory.
    :return: ``{name, kind, score, location, exists, via}`` per checkpoint artifact."""
    out = []
    for a in read_artifacts(run_dir):
        if a.kind != "checkpoint":
            continue
        location, exists = locate_checkpoint(ctx, run_dir, a)
        via = "path" if a.path is not None else "origin" if a.origin is not None else "uri"
        out.append(
            {
                "name": a.name,
                "kind": a.kind,
                "score": a.score,
                "location": str(location) if location is not None else None,
                "exists": exists,
                "via": via,
            }
        )
    return out


def dirpath_of(command: list[str]) -> str | None:
    """Pull a Lightning ``--dirpath`` value out of a recorded command, if any.

    :param command: The run's recorded command.
    :return: The directory, or ``None``."""
    for i, arg in enumerate(command):
        if arg == "--dirpath" and i + 1 < len(command):
            return command[i + 1]
        if arg.startswith("--dirpath="):
            return arg.split("=", 1)[1]
    return None


def shared_dirpath_warning(command: list[str], checkpoints_: list[dict[str, Any]]) -> str | None:
    """Warn when a resumed run would save checkpoints where a referenced one already lives.

    :param command: The run's recorded command.
    :param checkpoints_: Its resolved checkpoints, from :func:`checkpoints`.
    :return: The warning, or ``None``."""
    if (dirpath := dirpath_of(command)) is None:
        return None
    for row in checkpoints_:
        if row["exists"] and row["via"] != "path" and str(Path(row["location"]).parent) == dirpath:
            return (
                f"the recorded command saves checkpoints to {dirpath}, where the source's "
                "are; set another dirpath"
            )
    return None


def copy_group(ctx: Context, source: Path, dest_group: Path, p: "r.CpParams") -> dict[str, Any]:
    """Copy every run below a group into a destination group, keeping subfolders.

    :param ctx: The operation context.
    :param source: The source group.
    :param dest_group: The destination's parent group.
    :param p: The parameters.
    :return: What was copied."""
    name = p.name or source.name
    dest_root = dest_group / name
    if dest_root.exists():
        raise OpError(f"{dest_root.relative_to(ctx.logdir)} exists; choose another --name", code=2)
    runs = list(iter_runs(source))
    if not runs:
        raise OpError(f"no runs below {source.relative_to(ctx.logdir)}", code=4)
    ids, size, skipped = [], 0, []
    for run_dir in runs:
        rel = run_dir.parent.relative_to(source)
        dest_subgroup = dest_root if rel == Path(".") else dest_root / rel
        info = copy_run_core(
            ctx, run_dir, dest_subgroup, name=None, with_checkpoints=p.with_checkpoints
        )
        ids.append(info["id"])
        size += info["size"]
        skipped += info["skipped"]
    lines = [
        f"copied {len(ids)} run(s) from {source.relative_to(ctx.logdir)} to "
        f"{dest_root.relative_to(ctx.logdir)} ({size} bytes)",
    ]
    lines += skip_lines(skipped)
    if p.with_record:
        copied_dirs = copy_authored_dirs(source, runs, dest_root)
        lines += [f"copied {d} (still citing the original run ids)" for d in copied_dirs]
    return answer("cp", lines, path=dest_root.relative_to(ctx.logdir).as_posix(), runs=ids)


def copy_authored_dirs(source: Path, runs: list[Path], dest_root: Path) -> list[str]:
    """Copy every group-level ``proposal/``, ``notes/``, ``view/``, ``memory/`` and ``blocks/``
    folder below a source group into the mirrored destination, unchanged.

    :param source: The source group.
    :param runs: Its runs, to find every group level between them and the source.
    :param dest_root: The destination's root (what the source group was copied as).
    :return: The destination paths copied into, relative to the log dir."""
    groups = {source}
    for run_dir in runs:
        d = run_dir.parent
        while source in (d, *d.parents):
            groups.add(d)
            if d == source:
                break
            d = d.parent
    copied = []
    for group in groups:
        dest_group = dest_root if group == source else dest_root / group.relative_to(source)
        for folder in c.AUTHORED:
            src_folder = group / folder
            if src_folder.is_dir():
                shutil.copytree(src_folder, dest_group / folder)
                copied.append((dest_group / folder).relative_to(dest_root.parent).as_posix())
    return sorted(copied)
