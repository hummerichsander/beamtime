"""Where views and drafts live, and which view a page shows.

Saved versions are ``view/<version>.yaml`` in the group or run; drafts are
``.beamtime/drafts/<name>/`` in the project root, with ``view.yaml``, ``data/`` and
``_draft.json`` naming the draft's group."""

import json
import re
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
    group = json.loads((folder / DRAFT_META).read_text())["group"]
    return Draft(name=name, dir=folder, group=group)


def check_name(name: str) -> str:
    """Refuse draft names that aren't plain folder names.

    :param name: The name.
    :return: The name."""
    if not DRAFT_NAME.fullmatch(name):
        raise OpError(f"draft name {name!r}: use lowercase letters, digits, '.', '-', '_'", code=2)
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
    from beamtime.views.compile import compile_view
    from beamtime.views.defaults import default_view, node

    files = saved(ctx, path)
    out: dict[str, Any] = {"source": "default", "version": None, "versions": len(files)}
    try:
        if draft_name is not None:
            d = draft(ctx, draft_name)
            view, out["source"], out["draft"] = d.view(), "draft", draft_name
        elif files:
            file = files[-1]
            if version is not None:
                if (file := view_dir(ctx, path) / f"{version}.yaml") not in files:
                    raise OpError(f"no view version {version!r} in {path}", code=4)
            view = read(file, source=f"{path}/view/{file.name}")
            out |= {"source": "view", "version": file.stem}
        else:
            return out | {"view": default_view(ctx, path)}
    except SchemaError as e:
        # a broken version never breaks the page: the default shows, with what is wrong.
        tree = default_view(ctx, path)
        notice = node("note", "invalid-view", kind="warning", text=f"{e} Showing the default view.")
        tree["children"].insert(0, notice)
        return out | {"view": tree, "source": "default", "invalid": str(e)}
    return out | {
        "view": compile_view(view, path=path, draft=draft_name),
        "author": view.author,
        "user": view.user,
        "title": view.title,
        "finding": view.finding,
        "metrics": msgspec.to_builtins(view.metrics),
    }


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
