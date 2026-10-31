"""The block operations: library blocks to list and show, drafts to promote, fork, check and save.

A block draft is ``.beamtime/drafts/blocks/<name>/`` with ``block.yaml`` and ``code/<name>.js``;
saving writes a new version into ``blocks/<name>/`` of the log dir root or a group, its code under
a content hash, and never changes an existing file."""

import json
import re
import time
from pathlib import Path
from typing import Any

import msgspec

from beamtime.format import constants as c
from beamtime.format.io import write_created
from beamtime.format.schema import SchemaError
from beamtime.ops import call
from beamtime.ops import registry as r
from beamtime.ops.authored import author_of, save, target_of, written
from beamtime.ops.context import Context, OpError
from beamtime.views import code, store
from beamtime.views import model as m
from beamtime.views.library import (
    BLOCK_FILE,
    BlockDef,
    Library,
    drafts_dir,
    problems,
    read_def,
)
from beamtime.views.validate import Finding

MIN_EXAMPLES = 2


def listing(ctx: Context, p: r.BlockListParams) -> dict[str, Any]:
    """List the library blocks a group can use.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: One row per block: name, newest version, where it lives, params, description."""
    with target_of(ctx, p.group) as target:
        path = target.rel
    library = Library(ctx=ctx, path=path)
    rows = []
    for name in library.names:
        found = library.get(name)
        params = ", ".join(
            f"{k}: {v.kind}" + (f" = {v.default}" if v.default is not None else "")
            for k, v in found.block.params.items()
        )
        rows.append([name, found.version, found.group, params, found.block.description.strip()])
    lines = [f"{n} ({v}, in {g}): {d} [{ps}]" for n, v, g, ps, d in rows]
    return {
        "kind": "block list",
        "group": path,
        "columns": ["name", "version", "group", "params", "description"],
        "rows": rows,
        "lines": lines or ["no library blocks here; `block promote` makes one from a custom block"],
        "meta": {"matched": len(rows)},
    }


def show(ctx: Context, p: r.BlockShowParams) -> dict[str, Any]:
    """Show a library block's definition and code.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The YAML, the code and the version."""
    with target_of(ctx, p.group) as target:
        path = target.rel
    try:
        found = Library(ctx=ctx, path=path).get(p.name, p.version)
    except SchemaError as e:
        raise OpError(str(e), code=4) from None
    text = (found.folder / f"{found.version}.yaml").read_text()
    source = (found.folder / found.block.code).read_text()
    return {
        "kind": "block show",
        "name": p.name,
        "version": found.version,
        "group": found.group,
        "yaml": text,
        "code": source,
        "lines": [text.rstrip(), f"--- {found.block.code}", source.rstrip()],
        "meta": {},
    }


def promote(ctx: Context, p: r.BlockPromoteParams) -> dict[str, Any]:
    """Start a block draft from a custom block of a group's saved view.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The draft's files and what to do next."""
    with target_of(ctx, p.group) as target:
        path = target.rel
    if not (files := store.saved(ctx, path)):
        raise OpError(
            f"{path} has no saved view; save the view with the custom block first", code=4
        )
    view = store.read(files[-1], source=files[-1].name)
    node = next((n for n in m.walk(view.body) if n.id == p.block_id), None)
    if not isinstance(node, m.Custom):
        customs = [n.id for n in m.walk(view.body) if isinstance(n, m.Custom)]
        raise OpError(
            f"no custom block {p.block_id!r} in the view of {path}; "
            f"its custom blocks: {', '.join(customs) or 'none'}",
            code=4,
        )
    block = BlockDef(
        name=p.name,
        description="TODO: what it shows. Use for ...; not for ...",
        queries=node.queries,
        code=f"code/{p.name}.js",
        kit=node.kit,
        libs=node.libs,
    )
    source = (store.view_dir(ctx, path) / node.code).read_bytes()
    folder = new_draft(ctx, p.name, path, block, source, origin=f"{path}#{p.block_id}")
    return drafted(
        "block promote",
        folder,
        p.name,
        [
            "make it general: replace the fields in queries with $params and declare them "
            "under params (kind: field, fields, metric, metrics, number, string or bool)",
            "in the code, read field names from the query's columns, param values from bt.params",
            f"add a description (when to use, when not) and {MIN_EXAMPLES}+ examples (params each)",
        ],
    )


def fork(ctx: Context, p: r.BlockForkParams) -> dict[str, Any]:
    """Start a block draft as a copy of a library block.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The draft's files and what to do next."""
    with target_of(ctx, p.group) as target:
        path = target.rel
    try:
        found = Library(ctx=ctx, path=path).get(p.name)
    except SchemaError as e:
        raise OpError(str(e), code=4) from None
    block = msgspec.structs.replace(
        found.block,
        name=p.new_name,
        code=f"code/{p.new_name}.js",
        derived_from=f"{p.name}@{found.version}",
        author=None,
        user=None,
        message=None,
    )
    source = (found.folder / found.block.code).read_bytes()
    folder = new_draft(ctx, p.new_name, path, block, source, origin=f"{p.name}@{found.version}")
    return drafted("block fork", folder, p.new_name, ["change it, then validate and save"])


def new_draft(
    ctx: Context, name: str, group: str, block: BlockDef, source: bytes, *, origin: str
) -> Path:
    """Write a block draft.

    :param ctx: The operation context.
    :param name: The block's name, also the draft's.
    :param group: The group it is checked against.
    :param block: The definition.
    :param source: The code.
    :param origin: Where it came from, for the draft's record.
    :return: The draft's folder."""
    check_block_name(name)
    folder = drafts_dir(ctx) / name
    if folder.exists():
        raise OpError(f"block draft {name!r} exists at {folder}; edit it, or pick another name")
    write_created(folder / block.code, source)
    (folder / BLOCK_FILE).write_text(block_yaml(block))
    meta = {"schema": 1, "group": group, "from": origin, "created": time.time()}
    (folder / store.DRAFT_META).write_text(json.dumps(meta) + "\n")
    return folder


def drafted(kind: str, folder: Path, name: str, steps: list[str]) -> dict[str, Any]:
    """Answer a new block draft.

    :param kind: The operation.
    :param folder: The draft's folder.
    :param name: Its name.
    :param steps: What to do next.
    :return: The answer."""
    return {
        "kind": kind,
        "draft": name,
        "file": str(folder / BLOCK_FILE),
        "lines": [
            f"wrote {folder / BLOCK_FILE} and {folder / 'code' / f'{name}.js'}",
            *steps,
            f"next: `beamtime block validate {name}`, then `block save {name}`",
        ],
        "meta": {},
    }


def validate(ctx: Context, p: r.BlockValidateParams) -> dict[str, Any]:
    """Check a block draft, rendering its examples once where a browser exists.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The findings and whether it rendered."""
    from beamtime.ops.views import summary

    folder, group = open_draft(ctx, p.draft)
    block, findings = check(ctx, p.draft, folder, group)
    answer: dict[str, Any] = {"kind": "block validate", "draft": p.draft, "group": group}
    if block is not None and p.render and not any(f.level == "error" for f in findings):
        from beamtime.views.render import render_draft

        result = render_draft(ctx, examples_draft(ctx, p.draft, group, block), shots=False)
        findings += [Finding(**f) for f in result.pop("findings", [])]
        answer["render"] = result
    found = [f.to_dict() for f in findings]
    errors = sum(f.level == "error" for f in findings)
    lines = summary(found, answer.get("render"))
    if answer.get("render", {}).get("rendered"):
        lines.append(f"`beamtime view render block-{p.draft}` takes screenshots of the examples")
    return answer | {"ok": errors == 0, "findings": found, "lines": lines, "meta": {}}


def save_draft(ctx: Context, p: r.BlockSaveParams) -> dict[str, Any]:
    """Save a block draft as a new version, refusing one with errors.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new version."""
    from beamtime.ops.views import copy_data, summary

    folder, group = open_draft(ctx, p.draft)
    block, findings = check(ctx, p.draft, folder, group)
    found = [f.to_dict() for f in findings]
    if block is None or any(f.level == "error" for f in findings):
        raise OpError(
            "the block draft has errors; fix them and save again:\n"
            + "\n".join(summary(found, None)),
            code=3,
        )
    with target_of(ctx, p.group) as target:
        home = ctx.logdir / target.rel / c.BLOCKS / block.name
    block.code = copy_data(folder / block.code, home, "code")
    block.author, block.user = author_of(ctx, p.author)
    block.message = p.message
    path = save(home, ".yaml", block_yaml(block))
    return written(
        ctx,
        "block save",
        path,
        [*summary(found, None)[:-1], f"views use it as `- {block.name}: {{params}}`"],
    )


def open_draft(ctx: Context, name: str) -> tuple[Path, str]:
    """Open a block draft.

    :param ctx: The operation context.
    :param name: The draft's name.
    :return: Its folder and the group it is checked against."""
    folder = drafts_dir(ctx) / store.check_name(name)
    if not (folder / BLOCK_FILE).is_file():
        known = sorted(d.name for d in drafts_dir(ctx).glob("*") if (d / BLOCK_FILE).is_file())
        hint = f"; block drafts: {', '.join(known)}" if known else ""
        raise OpError(
            f"no block draft {name!r}; start one with `block promote` or `block fork`{hint}", code=4
        )
    meta = json.loads((folder / store.DRAFT_META).read_text())
    return folder, meta["group"]


def check(
    ctx: Context, draft: str, folder: Path, group: str
) -> tuple[BlockDef | None, list[Finding]]:
    """Check a block draft without a browser.

    :param ctx: The operation context.
    :param draft: The draft's name.
    :param folder: Its folder.
    :param group: The group its examples run against.
    :return: The definition, if it reads, and the findings."""
    try:
        block = read_def(folder / BLOCK_FILE, source=f"block draft {draft}")
    except SchemaError as e:
        return None, [Finding(level="error", message=str(e))]
    out = []
    at = {"block": block.name}

    def add(level: str, message: str, fix: str | None = None) -> None:
        out.append(Finding(level=level, message=message, fix=fix, **at))  # type: ignore[arg-type]

    if block.name != draft:
        add("error", f"the block is named {block.name!r} but its draft {draft!r}", f"name: {draft}")
    description = block.description.lower()
    if "todo" in description or not re.search(r"\buse\b", description) or "not" not in description:
        add(
            "error",
            "the description says what it shows, when to use it and when not",
            "description: Heatmap of ... Use for ...; not for ...",
        )
    if len(block.examples) < MIN_EXAMPLES:
        add(
            "error",
            f"{len(block.examples)} example(s); give at least {MIN_EXAMPLES}",
            "examples: [{x: config.lr, ...}, {x: config.wd, ...}]",
        )
    for i, example in enumerate(block.examples):
        for message in problems(block, example):
            add("error", f"examples[{i}]: {message}")
    custom = m.Custom(code=block.code, kit=block.kit, libs=block.libs, queries=block.queries)
    from beamtime.views.validate import custom_checks

    out += [msgspec.structs.replace(f, block=block.name) for f in custom_checks(custom, {}, folder)]
    if (file := folder / block.code).is_file():
        out += hard_coded(ctx, group, file.read_text(), block, at)
    out += duplicates(ctx, group, block, at)
    if not any(f.level == "error" for f in out):
        out += examples_check(ctx, draft, group, block)
    return block, out


def hard_coded(
    ctx: Context, group: str, source: str, block: BlockDef, at: dict[str, Any]
) -> list[Finding]:
    """Find metric and config names written into the code or the queries instead of params.

    :param ctx: The operation context.
    :param group: The group whose keys count.
    :param source: The code.
    :param block: The definition.
    :param at: Where findings point.
    :return: An error per name in the code, a warning per name in the queries."""
    keys = call("keys", {"from": group}, ctx)
    metrics = {row[0] for row in keys["metrics"]["rows"]}
    fields = {row[0] for row in keys["config"]["rows"]}
    known = metrics | fields

    def named(s: str) -> bool:
        return s in known or (s.startswith("metric.") and s[7:].rsplit(".", 1)[0] in metrics)

    out = []
    literals = {s[1:-1] for s in code.STRING.findall(code.COMMENT.sub(" ", source))}
    for s in sorted(filter(named, literals)):
        out.append(
            Finding(
                level="error",
                message=f"{s!r} is hard-coded in the code",
                fix="make it a param, or read it from the query's columns",
                **at,
            )
        )
    strings = re.findall(r"'([^']*)'|\"([^\"]*)\"", json.dumps(block.queries))
    in_queries = {a or b for a, b in strings}
    for s in sorted(filter(named, in_queries)):
        out.append(
            Finding(
                level="warning",
                message=f"{s!r} is fixed in the queries",
                fix="make it a param ($name) unless every use needs it",
                **at,
            )
        )
    return out


def duplicates(ctx: Context, group: str, block: BlockDef, at: dict[str, Any]) -> list[Finding]:
    """Point out a library block that declares the same queries.

    :param ctx: The operation context.
    :param group: The group whose library counts.
    :param block: The definition.
    :param at: Where findings point.
    :return: A warning per such block."""
    library = Library(ctx=ctx, path=group)
    out = []
    for name in library.names:
        other = library.get(name).block
        if name != block.name and other.queries == block.queries:
            out.append(
                Finding(
                    level="warning",
                    message=f"{name} declares the same queries",
                    fix=f"use or fork {name} instead",
                    **at,
                )
            )
    return out


def examples_view(block: BlockDef) -> dict[str, Any]:
    """Write a view that shows a block once per example.

    :param block: The definition.
    :return: The view in YAML form."""
    body = [
        {
            block.name: {
                "id": f"example-{i + 1}",
                "title": f"Example {i + 1}",
                "caption": ", ".join(f"{k}: {v}" for k, v in example.items()),
                **example,
            }
        }
        for i, example in enumerate(block.examples)
    ]
    return {
        "schema": 1,
        "title": f"{block.name}: examples",
        "finding": block.description,
        "body": body,
    }


def examples_check(ctx: Context, draft: str, group: str, block: BlockDef) -> list[Finding]:
    """Run the block's examples statically, as uses in a view of the group.

    :param ctx: The operation context.
    :param draft: The block draft's name.
    :param group: The group.
    :param block: The definition.
    :return: The findings."""
    from beamtime.views.validate import static

    view, findings = static(
        ctx,
        group,
        examples_view(block),
        source=f"block draft {draft} examples",
        blocks={block.name: draft},
    )
    return [f for f in findings if f.message != "no finding"]


def examples_draft(ctx: Context, draft: str, group: str, block: BlockDef) -> store.Draft:
    """Write a view draft with the block's examples, for the renderer.

    :param ctx: The operation context.
    :param draft: The block draft's name.
    :param group: The group.
    :param block: The definition.
    :return: The view draft, named ``block-<name>``."""
    name = f"block-{draft}"
    folder = store.drafts(ctx) / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / store.VIEW_FILE).write_text(m.dump(examples_view(block)))
    meta = {
        "schema": 1,
        "group": group,
        "from": f"block {draft}",
        "created": time.time(),
        "blocks": {block.name: draft},
    }
    (folder / store.DRAFT_META).write_text(json.dumps(meta) + "\n")
    return store.draft(ctx, name)


def block_yaml(block: BlockDef) -> str:
    """Write a block definition as YAML, name and description first.

    :param block: The definition.
    :return: The YAML."""
    data = msgspec.to_builtins(block)
    return m.dump({"schema": 1, **{k: v for k, v in data.items() if k != "schema"}})


def check_block_name(name: str) -> str:
    """Refuse names that can't be blocks.

    :param name: The name.
    :return: The name."""
    if not m.LIBRARY_NAME.fullmatch(name):
        raise OpError(f"block name {name!r}: lowercase letters, digits and '-', from a letter", 2)
    if name in m.BLOCKS:
        raise OpError(f"{name!r} is a built-in block; pick another name", code=2)
    return name


def export(ctx: Context, p: r.BlockExportParams) -> dict[str, Any]:
    """Copy a library block, every version with its code, into ``<to>/blocks/<name>/``.

    Exporting into a git repository makes a library others import with ``block import``.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was copied."""
    with target_of(ctx, p.group) as target:
        path = target.rel
    library = Library(ctx=ctx, path=path)
    if p.name not in library.folders:
        raise OpError(f"no library block {p.name!r} in {path}; `block list {path}` names them", 4)
    _, source = library.folders[p.name]
    dest = Path(p.to).expanduser().resolve() / c.BLOCKS / p.name
    copied = copy_tree(source, dest)
    return {
        "kind": "block export",
        "name": p.name,
        "to": str(dest),
        "lines": [f"copied {len(copied)} file(s) to {dest}" if copied else f"{dest} is up to date"],
        "meta": {},
    }


def import_blocks(ctx: Context, p: r.BlockImportParams) -> dict[str, Any]:
    """Copy library blocks from a project, a folder with ``blocks/``, or a git repository.

    Version ids stay, so views pinned to them elsewhere stay valid; the source and commit are
    recorded in ``blocks/<name>/_imported.json``.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The blocks imported and what their checks found."""
    import tempfile

    with target_of(ctx, p.group) as target:
        home = ctx.logdir / target.rel / c.BLOCKS
    with tempfile.TemporaryDirectory(prefix="beamtime-import-") as tmp:
        root, origin = fetch(p.from_, Path(tmp))
        folder = blocks_in(root)
        names = sorted(d.name for d in folder.iterdir() if d.is_dir() and any(d.glob("*.yaml")))
        if p.name is not None:
            if p.name not in names:
                raise OpError(f"no block {p.name!r} in {p.from_}; it has {', '.join(names)}", 4)
            names = [p.name]
        if not names:
            raise OpError(f"no blocks in {folder}", code=4)
        conflicts = [
            f"{name}/{rel}"
            for name in names
            for rel, content in files_of(folder / name).items()
            if (home / name / rel).is_file() and (home / name / rel).read_bytes() != content
        ]
        if conflicts:
            raise OpError(
                "these files exist with other content; nothing was imported:\n"
                + "\n".join(conflicts),
                code=1,
            )
        lines = []
        for name in names:
            check_block_name(name)
            copied = copy_tree(folder / name, home / name)
            record = json.dumps(origin | {"at": time.time()})
            (home / name / "_imported.json").write_text(record + "\n")
            lines.append(f"{name}: {len(copied)} new file(s)")
            for f in sorted(versions_of(home / name)):
                try:
                    read_def(f, source=f"{name}/{f.name}")
                except SchemaError as e:
                    lines.append(f"  warning: {e}")
    return {
        "kind": "block import",
        "blocks": names,
        "lines": [*lines, f"into {home}; views use them as `- <name>: {{params}}`"],
        "meta": {},
    }


def fetch(source: str, tmp: Path) -> tuple[Path, dict[str, Any]]:
    """Locate a block source: a local folder as is, a git URL cloned shallowly.

    :param source: A path, or a git URL with an optional ``@ref`` (branch or tag).
    :param tmp: A folder for the clone.
    :return: The folder, and where it came from for ``_imported.json``."""
    import shutil
    import subprocess

    local = Path(source).expanduser()
    if local.is_dir():
        return local.resolve(), {"schema": 1, "source": str(local.resolve())}
    url, ref = source, None
    # a ref follows the last '@' after the host part: git@github.com:lab/blocks@v1.
    if "@" in source.rsplit("/", 1)[-1]:
        url, ref = source.rsplit("@", 1)
    if shutil.which("git") is None:
        raise OpError(f"{source} is no folder here, and git isn't installed to clone it", 4)
    args = ["git", "clone", "--quiet", "--depth", "1", *(["--branch", ref] if ref else [])]
    done = subprocess.run([*args, url, str(tmp / "repo")], capture_output=True, text=True)
    if done.returncode != 0:
        raise OpError(f"git clone {url} failed: {done.stderr.strip()}", code=4)
    commit = subprocess.run(
        ["git", "-C", str(tmp / "repo"), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    return tmp / "repo", {"schema": 1, "source": url, "ref": ref, "commit": commit}


def blocks_in(root: Path) -> Path:
    """Find the ``blocks/`` folder of a source: at its top, or in its log dir.

    :param root: The source folder.
    :return: The folder holding ``<name>/`` block folders."""
    for candidate in (root / c.BLOCKS, root / "beamtime" / c.BLOCKS):
        if candidate.is_dir():
            return candidate
    raise OpError(f"no blocks/ folder in {root} (nor in {root / 'beamtime'})", code=4)


def files_of(folder: Path) -> dict[str, bytes]:
    """Read a block folder's versions and code, leaving out machine-written files.

    :param folder: ``blocks/<name>/``.
    :return: Contents by path relative to the folder."""
    return {
        f.relative_to(folder).as_posix(): f.read_bytes()
        for f in sorted(folder.rglob("*"))
        if f.is_file() and not f.name.startswith(("_", "."))
    }


def copy_tree(source: Path, dest: Path) -> list[str]:
    """Copy a block folder's files that the destination doesn't have yet.

    :param source: The block folder.
    :param dest: Where it goes.
    :return: The files copied."""
    copied = []
    for rel, content in files_of(source).items():
        if (dest / rel).is_file():
            if (dest / rel).read_bytes() != content:
                raise OpError(f"{dest / rel} exists with other content", code=1)
            continue
        write_created(dest / rel, content)
        copied.append(rel)
    return copied


def versions_of(folder: Path) -> list[Path]:
    """List a block folder's version files.

    :param folder: ``blocks/<name>/``.
    :return: The YAML files."""
    from beamtime.format.authored import versions

    return [f for f in versions(folder) if f.suffix == ".yaml"]
