"""Where views and drafts live, and which view a page shows.

Saved versions are ``view/<version>.yaml`` in the group or run; drafts are
``.beamtime/drafts/<name>/`` in the project root, with ``view.yaml``, ``data/`` and
``_draft.json`` naming the draft's group."""

import dataclasses
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import msgspec

from beamtime.format import constants as c
from beamtime.format.authored import versions
from beamtime.format.schema import SchemaError
from beamtime.ops.context import Context, OpError
from beamtime.views import model as m

DRAFT_NAME = re.compile(r"[a-z0-9][a-z0-9._-]{0,63}")
VIEW_FILE = "view.yaml"
DRAFT_META = "_draft.json"
# view drafts a block draft's examples render in; users' drafts can't take these names.
EXAMPLES = "block-"


def view_dir(ctx: Context, path: str) -> Path:
    """Locate a page's ``view/`` folder.

    :param ctx: The operation context.
    :param path: A group below the log dir, or a run's path.
    :return: The folder; it may not exist."""
    return ctx.logdir / path / c.VIEW


def saved(ctx: Context, path: str) -> list[Path]:
    """List a page's saved view versions, oldest first.

    :param ctx: The operation context.
    :param path: A group or run path.
    :return: The version files."""
    return [p for p in versions(view_dir(ctx, path)) if p.suffix == ".yaml"]


def read(file: Path, *, source: str) -> m.View:
    """Read a view file.

    :param file: A saved version or a draft's ``view.yaml``.
    :param source: How to name it in messages.
    :return: The view."""
    import yaml

    try:
        data = yaml.safe_load(file.read_text())
    except yaml.YAMLError as e:
        raise SchemaError(f"{source}: not valid YAML: {e}") from None
    return m.parse(data, source=source)


def drafts(ctx: Context) -> Path:
    """Locate the drafts folder, creating ``.beamtime/`` with its own ``.gitignore``.

    :param ctx: The operation context.
    :return: ``<root>/.beamtime/drafts``."""
    base = ctx.root / ".beamtime"
    if not (ignore := base / ".gitignore").exists():
        base.mkdir(parents=True, exist_ok=True)
        ignore.write_text("# Beamtime's drafts and renders; not part of the project.\n*\n")
    return base / "drafts"


@dataclass(kw_only=True)
class Draft:
    """A view draft: its folder and the group it is for."""

    name: str
    dir: Path
    group: str
    # block drafts standing in for library blocks of the same name (to render a block's examples).
    blocks: dict[str, str] = dataclasses.field(default_factory=dict)

    @property
    def file(self) -> Path:
        """The draft's ``view.yaml``."""
        return self.dir / VIEW_FILE

    def view(self) -> m.View:
        """Read the draft.

        :return: The view."""
        return read(self.file, source=f"draft {self.name}")


def draft(ctx: Context, name: str) -> Draft:
    """Open an existing draft.

    :param ctx: The operation context.
    :param name: The draft's name.
    :return: The draft."""
    folder = drafts(ctx) / check_name(name)
    if not (folder / DRAFT_META).is_file() or not (folder / VIEW_FILE).is_file():
        known = sorted(p.name for p in drafts(ctx).glob("*") if (p / DRAFT_META).is_file())
        hint = f"; drafts: {', '.join(known)}" if known else ""
        raise OpError(
            f"no draft {name!r}; start one with `beamtime view new <group>`{hint}", code=4
        )
    meta = draft_meta(folder)
    return Draft(name=name, dir=folder, group=meta["group"], blocks=meta.get("blocks") or {})


def write_draft_meta(
    folder: Path, *, group: str, origin: str, blocks: dict[str, str] | None = None
) -> None:
    """Record what a view or block draft is for, in its ``_draft.json``.

    :param folder: The draft's folder.
    :param group: The group it is for, or checked against.
    :param origin: Where it started from, e.g. ``current`` or an example's name.
    :param blocks: Block drafts standing in for library blocks of the same name."""
    meta = {"schema": 1, "group": group, "from": origin, "created": time.time()}
    if blocks:
        meta["blocks"] = blocks
    (folder / DRAFT_META).write_text(json.dumps(meta) + "\n")


def draft_meta(folder: Path) -> dict[str, Any]:
    """Read a draft's ``_draft.json``.

    :param folder: The draft's folder.
    :return: ``{group, from, created}``, and ``blocks`` for an examples draft."""
    return json.loads((folder / DRAFT_META).read_text())


def check_name(name: str, *, new: bool = False) -> str:
    """Refuse draft names that aren't plain folder names.

    :param name: The name.
    :param new: Whether a user's view draft starts under it, which can't take reserved names.
    :return: The name."""
    if not DRAFT_NAME.fullmatch(name):
        raise OpError(f"draft name {name!r}: use lowercase letters, digits, '.', '-', '_'", code=2)
    if name == c.BLOCKS:
        raise OpError(f"draft name {name!r} is taken by the block drafts", code=2)
    if new and name.startswith(EXAMPLES):
        raise OpError(
            f"draft name {name!r}: names starting with {EXAMPLES} are kept for block examples; "
            "pass another --name",
            code=2,
        )
    return name


def shown(
    ctx: Context, path: str, *, version: str | None = None, draft_name: str | None = None
) -> dict[str, Any]:
    """Pick and compile the view a page shows: a draft, a version, its newest, else the default.

    :param ctx: The operation context.
    :param path: A group below the log dir, or a run's path.
    :param version: A saved version to show instead of the newest.
    :param draft_name: A draft to show, for the renderer.
    :return: ``{view, source, version, author, user, title, finding, metrics, versions}``."""
    from beamtime.format.ids import is_run_id
    from beamtime.views.compile import compile_view, walk_tree
    from beamtime.views.defaults import default_view, record
    from beamtime.views.library import Library

    files = saved(ctx, path)
    out: dict[str, Any] = {"source": "default", "version": None, "versions": len(files)}
    library = Library(ctx=ctx, path=path)
    try:
        if draft_name is not None:
            d = draft(ctx, draft_name)
            library = Library(ctx=ctx, path=path, drafts=d.blocks)
            view, out["source"], out["draft"] = d.view(), "draft", draft_name
        elif files:
            file = files[-1]
            if version is not None:
                if (file := view_dir(ctx, path) / f"{version}.yaml") not in files:
                    raise OpError(f"no view version {version!r} in {path}", code=4)
            view = read(file, source=f"{path}/view/{file.name}")
            out |= {"source": "view", "version": file.stem}
        else:
            view = default_view(ctx, path)
        tree = compile_view(view, path=path, draft=draft_name, library=library)
    except SchemaError as e:
        # a broken version never breaks the page: the default shows, with what is wrong.
        view = default_view(ctx, path)
        text = f"{e} Showing the default view."
        view.body.insert(0, m.Note(id="invalid-view", kind="warning", text=text))
        tree = compile_view(view, path=path)
        out |= {"source": "default", "invalid": str(e)}
    # every page shows its notes and memory; a view only decides where, by including them.
    blocks = {n.get("block") for n in walk_tree(tree)}
    missing = [
        b for b in record(run=is_run_id(path.rsplit("/", 1)[-1])) if m.block_of(b) not in blocks
    ]
    tree["children"] += compile_view(m.View(body=missing), path=path)["children"]
    return out | {
        "view": tree,
        "author": view.author,
        "user": view.user,
        "title": view.title,
        "finding": view.finding,
        "metrics": msgspec.to_builtins(view.metrics),
        "outdated": outdated(view, library),
    }


def outdated(view: m.View, library: Any) -> list[dict[str, str]]:
    """List the library blocks a view is pinned to older versions of.

    :param view: The view.
    :param library: The page's library.
    :return: ``{name, pinned, newest}`` per block."""
    out = []
    for name, pinned in sorted(view.uses.items()):
        if (newest := library.newest(name)) is not None and newest > pinned:
            out.append({"name": name, "pinned": pinned, "newest": newest})
    return out


def code_text(ctx: Context, ref: dict[str, Any]) -> dict[str, Any]:
    """Read a custom block's code for the page, which posts it into the block's frame.

    :param ctx: The operation context.
    :param ref: ``{view, path}`` of a saved view, plus ``draft`` for a draft; ``{block, group,
        path}`` of a library block, ``{block_draft, path}`` of a block draft.
    :return: ``{kind, path, code}``."""
    from beamtime.views.library import drafts_dir

    rel = str(ref.get("path") or "")
    if (name := ref.get("block_draft")) is not None:
        folder = (drafts_dir(ctx) / check_name(str(name))).resolve()
    elif (name := ref.get("block")) is not None:
        group = str(ref.get("group") or ".")
        folder = (ctx.logdir / group / c.BLOCKS / check_name(str(name))).resolve()
    elif (name := ref.get("draft")) is not None:
        folder = draft(ctx, str(name)).dir.resolve()
    else:
        folder = view_dir(ctx, str(ref.get("view") or ".")).resolve()
    file = (folder / rel).resolve()
    allowed = (ctx.logdir.resolve(), drafts(ctx).resolve())
    if not any(root in folder.parents for root in allowed):
        raise OpError(f"no code file {rel!r} (code lives in the log dir or the drafts)", code=4)
    if folder / "code" not in file.parents or file.suffix != ".js" or not file.is_file():
        raise OpError(f"no code file {rel!r} (code files are code/<name>.js)", code=4)
    return {"kind": "code", "path": rel, "code": file.read_text()}


def lead(ctx: Context, path: str) -> tuple[str, bool] | None:
    """Find the lead metric of a page's newest view: the first under ``metrics:``.

    :param ctx: The operation context.
    :param path: A group or run path.
    :return: The metric and whether lower is better, or ``None`` without one."""
    from beamtime.views.defaults import lower_is_better

    if not (files := saved(ctx, path)):
        return None
    try:
        view = read(files[-1], source=files[-1].name)
    except SchemaError:
        return None
    for metric, info in view.metrics.items():
        given = info.higher_is_better
        return metric, (lower_is_better(metric) if given is None else not given)
    return None
