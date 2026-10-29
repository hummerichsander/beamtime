"""The view operations: drafts, validation, rendering, saving, and a view's versions.

Drafts live in ``.beamtime/drafts/<name>/``; saving writes a new version into the page's
``view/``, with data files copied under content hashes, and never changes an existing file."""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from beamtime.format.ids import id_time
from beamtime.format.io import write_created
from beamtime.format.schema import SchemaError
from beamtime.ops import registry as r
from beamtime.ops.context import Context, OpError
from beamtime.ops.record import author_of, save, target_of, written
from beamtime.views import model as m
from beamtime.views import store


def new(ctx: Context, p: r.ViewNewParams) -> dict[str, Any]:
    """Start a draft: from an example, else from the page's current view.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The draft's name and file."""
    with target_of(ctx, p.group) as target:
        path = target.rel
    name = store.check_name(p.name or default_name(path))
    folder = store.drafts(ctx) / name
    if folder.exists():
        raise OpError(
            f"draft {name!r} exists at {folder}; edit its view.yaml, or start another with --name",
            code=1,
        )
    if p.from_ is not None:
        from beamtime.guide import example

        text, origin = example(p.from_, ctx, path), f"the {p.from_!r} example"
    else:
        text, origin = current_yaml(ctx, path)
    (folder / "data").mkdir(parents=True)
    (folder / store.VIEW_FILE).write_text(text)
    for ref in data_refs(text):
        if (source := store.view_dir(ctx, path) / ref).is_file():
            write_created(folder / ref, source.read_bytes())
    meta = {"schema": 1, "group": path, "from": p.from_ or "current", "created": time.time()}
    (folder / store.DRAFT_META).write_text(json.dumps(meta) + "\n")
    file = folder / store.VIEW_FILE
    return {
        "kind": "view new",
        "draft": name,
        "group": path,
        "file": str(file),
        "lines": [
            f"wrote {file} from {origin}",
            f"data files go in {folder / 'data'} (data_table: {{file: data/<name>.csv}})",
            f"next: edit it, then `beamtime view validate {name}` and `view render {name}`",
        ],
        "meta": {},
    }


def data_refs(text: str) -> list[str]:
    """Find the data files a view's YAML refers to.

    :param text: The YAML.
    :return: The ``data/...`` references."""
    import yaml

    from beamtime.views.compile import yaml_walk

    try:
        body = (yaml.safe_load(text) or {}).get("body") or []
        return [
            props["file"]
            for b, props in yaml_walk(body)
            if b == "data_table" and isinstance(props.get("file"), str)
        ]
    except (yaml.YAMLError, AttributeError, ValueError):
        return []


def default_name(path: str) -> str:
    """Name a draft after its page.

    :param path: The group or run path.
    :return: E.g. ``lr-sweep``, or ``root`` for the log dir."""
    return m.slug(path.rsplit("/", 1)[-1]) if path != "." else "root"


def current_yaml(ctx: Context, path: str) -> tuple[str, str]:
    """Write the page's current view as draft YAML: its newest version, else the default.

    :param ctx: The operation context.
    :param path: The group or run path.
    :return: The YAML text, and where it came from."""
    from beamtime.views.compile import from_tree
    from beamtime.views.defaults import default_view

    if files := store.saved(ctx, path):
        try:
            view = store.read(files[-1], source=files[-1].name)
        except SchemaError:
            return files[-1].read_text(), f"version {files[-1].stem} (invalid)"
        data = m.to_yaml_form(view)
        for k in ("author", "user", "message", "uses"):
            data.pop(k, None)
        return m.dump(data), f"version {files[-1].stem}"
    body = from_tree(default_view(ctx, path), path=path)
    data = {"schema": 1, "title": None, "finding": None, "body": body}
    return m.dump(data), "the built-in default view"


def validate(ctx: Context, p: r.ViewValidateParams) -> dict[str, Any]:
    """Validate a draft: statically, then with one render where a browser exists.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The findings and whether it rendered."""
    d = store.draft(ctx, p.draft)
    view, findings = check(ctx, d)
    answer: dict[str, Any] = {"kind": "view validate", "draft": d.name, "group": d.group}
    if view is not None and p.render and not any(f["level"] == "error" for f in findings):
        from beamtime.views.render import render_draft

        result = render_draft(ctx, d, shots=False)
        findings += result.pop("findings", [])
        answer["render"] = result
    errors = sum(f["level"] == "error" for f in findings)
    answer |= {
        "ok": errors == 0,
        "findings": findings,
        "lines": summary(findings, answer.get("render")),
        "meta": {},
    }
    return answer


def check(ctx: Context, d: store.Draft) -> tuple[m.View | None, list[dict[str, Any]]]:
    """Validate a draft statically.

    :param ctx: The operation context.
    :param d: The draft.
    :return: The view, if it parses, and the findings as dicts."""
    import yaml

    from beamtime.views.validate import static

    try:
        data = yaml.safe_load(d.file.read_text())
    except yaml.YAMLError as e:
        return None, [{"level": "error", "message": f"draft {d.name}: not valid YAML: {e}"}]
    view, findings = static(
        ctx, d.group, data, source=f"draft {d.name}", draft=d.name, data_dir=d.dir
    )
    return view, [f.to_dict() for f in findings]


def summary(findings: list[dict[str, Any]], render: dict[str, Any] | None) -> list[str]:
    """Say what validation found, one line per finding.

    :param findings: The findings.
    :param render: The render's result, if one ran.
    :return: The lines."""
    lines = []
    for f in findings:
        where = f" [{f['id']}]" if f.get("id") else ""
        fix = f" → {f['fix']}" if f.get("fix") else ""
        lines.append(f"{f['level']}{where}: {f['message']}{fix}")
    errors = sum(f["level"] == "error" for f in findings)
    lines.append(f"{errors} error(s), {len(findings) - errors} warning(s)")
    if render is not None and not render.get("rendered"):
        lines.append(f"render skipped: {render.get('reason')}")
    return lines


def render(ctx: Context, p: r.ViewRenderParams) -> dict[str, Any]:
    """Render a draft headless and take screenshots of the page or one block.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The screenshot files and what the render found."""
    from beamtime.views.render import render_draft

    d = store.draft(ctx, p.draft)
    result = render_draft(ctx, d, shots=True, block=p.block, theme=p.theme, width=p.width)
    lines = [f"wrote {s['file']}" for s in result.get("shots", [])]
    if not result.get("rendered"):
        lines.append(f"not rendered: {result.get('reason')}")
    if result.get("rendered"):
        lines += summary(result.get("findings", []), None)
    return {
        "kind": "view render",
        "draft": d.name,
        "group": d.group,
        **result,
        "lines": lines,
        "meta": {},
    }


def save_draft(ctx: Context, p: r.ViewSaveParams) -> dict[str, Any]:
    """Save a draft as a new view version, refusing one with errors.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new version."""
    d = store.draft(ctx, p.draft)
    view, findings = check(ctx, d)
    errors = [f for f in findings if f["level"] == "error"]
    if view is None or errors:
        raise OpError(
            "the draft has errors; fix them and save again:\n" + "\n".join(summary(errors, None)),
            code=3,
        )
    path = write_version(ctx, d.group, view, p.author, p.message, data_dir=d.dir)
    warnings = summary(findings, None)[:-1]
    return written(ctx, "view save", path, [*warnings, f"the page {d.group} shows it now"])


def write_version(
    ctx: Context,
    group: str,
    view: m.View,
    author: str | None,
    message: str | None,
    *,
    data_dir: Path | None = None,
) -> Path:
    """Write a view as a new version, copying data files under content hashes.

    :param ctx: The operation context.
    :param group: The group or run path.
    :param view: The view.
    :param author: Who saves it; default the local account (or ``agent`` over MCP).
    :param message: What this version changed.
    :param data_dir: The draft folder its ``data/...`` references are relative to.
    :return: The new file."""
    view.author, view.user = author_of(ctx, author)
    view.message = message
    folder = store.view_dir(ctx, group)
    for n in m.walk(view.body):
        if isinstance(n, m.DataTable) and n.file is not None and data_dir is not None:
            n.file = copy_data(data_dir / n.file, folder)
    return save(folder, ".yaml", m.dump(m.to_yaml_form(view)))


def copy_data(source: Path, folder: Path) -> str:
    """Store a data file next to the view, named by its content hash.

    :param source: The draft's file.
    :param folder: The page's ``view/`` folder.
    :return: The reference relative to ``view/``: ``data/<sha8>-<name>``."""
    content = source.read_bytes()
    # a file copied from a saved version already carries a hash prefix.
    stem = re.sub(r"^[0-9a-f]{8}-", "", source.name)
    ref = f"data/{hashlib.sha256(content).hexdigest()[:8]}-{stem}"
    if not (folder / ref).exists():
        write_created(folder / ref, content)
    return ref


def save_page(
    ctx: Context, path: str, prefs: dict[str, Any], title: str | None, finding: str | None
) -> dict[str, Any]:
    """Save what a page shows with a viewer's chart settings as a new version (the web UI).

    :param ctx: The operation context, with caller ``view``.
    :param path: The group or run path.
    :param prefs: The viewer's ``{view, charts, added}`` for the page.
    :param title: The view's title.
    :param finding: The view's finding.
    :return: The new version."""
    import yaml

    from beamtime.views.compile import apply_prefs

    text, _ = current_yaml(ctx, path)
    data = yaml.safe_load(text)
    data["body"] = apply_prefs(data.get("body") or [], prefs)
    data["title"], data["finding"] = title or None, finding or None
    try:
        view = m.parse(data, source="the page")
    except SchemaError as e:
        raise OpError(str(e), code=3) from None
    file = write_version(ctx, path, view, None, "saved from the web UI")
    return written(ctx, "view save", file, [])


def show(ctx: Context, p: r.ViewShowParams) -> dict[str, Any]:
    """Show a page's view: its YAML, version and author.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    with target_of(ctx, p.group) as target:
        path = target.rel
    files = store.saved(ctx, path)
    if not files:
        return {
            "kind": "view show",
            "group": path,
            "version": None,
            "lines": [
                f"{path} has no saved view; it shows the built-in default",
                f"`beamtime view new {path}` writes the default out as a draft to edit",
            ],
            "meta": {},
        }
    file = files[-1] if p.version is None else store.view_dir(ctx, path) / f"{p.version}.yaml"
    if file not in files:
        raise OpError(f"no view version {p.version!r} in {path}", code=4)
    text = file.read_text()
    return {
        "kind": "view show",
        "group": path,
        "version": file.stem,
        "current": file == files[-1],
        "yaml": text,
        "meta": {},
    }


def history(ctx: Context, p: r.ViewHistoryParams) -> dict[str, Any]:
    """List a page's view versions, newest first.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: ``entries`` with version, time, author, title and message."""
    import yaml

    with target_of(ctx, p.group) as target:
        path = target.rel
    entries = []
    for file in reversed(store.saved(ctx, path)):
        try:
            data = yaml.safe_load(file.read_text()) or {}
        except yaml.YAMLError:
            data = {}
        entries.append(
            {
                "version": file.stem,
                "time": id_time(file.stem).isoformat(),
                "author": data.get("author"),
                "user": data.get("user"),
                "title": data.get("title"),
                "message": data.get("message"),
            }
        )
    return {"kind": "view history", "group": path, "entries": entries, "meta": {}}


def edit_text(ctx: Context, path: str, node_id: str | None, text: str) -> dict[str, Any]:
    """Add, change or remove a text panel of a page's view (the web UI), as a new version.

    :param ctx: The operation context, with caller ``view``.
    :param path: The group or run path.
    :param node_id: The ``markdown`` block to change, or ``None`` to add one at the top.
    :param text: Its Markdown; empty removes the block.
    :return: The new version."""
    import yaml

    from beamtime.views.compile import yaml_walk

    data = yaml.safe_load(current_yaml(ctx, path)[0])
    body = data.get("body") or []
    if node_id is None:
        taken = {props.get("id") for _, props in yaml_walk(body)}
        body.insert(0, {"markdown": {"id": m.unique("text", taken), "text": text or "Write here."}})
        message = "added a text panel in the web UI"
    elif not drop_or_set(body, node_id, text.strip()):
        raise OpError(f"no text panel {node_id!r} in the view of {path}", code=4)
    else:
        message = f"{'edited' if text.strip() else 'removed'} a text panel in the web UI"
    data["body"] = body
    try:
        view = m.parse(data, source="the page")
    except SchemaError as e:
        raise OpError(str(e), code=3) from None
    return written(ctx, "view save", write_version(ctx, path, view, None, message), [])


def drop_or_set(nodes: list[Any], node_id: str, text: str) -> bool:
    """Set a ``markdown`` block's text, or remove the block when the text is empty.

    :param nodes: Nodes in YAML form; changed in place.
    :param node_id: The block's id.
    :param text: The new text.
    :return: Whether the block was found."""
    for i, n in enumerate(nodes):
        ((block, props),) = n.items()
        if block == "markdown" and isinstance(props, dict) and props.get("id") == node_id:
            if text:
                props["text"] = text
            else:
                del nodes[i]
            return True
        kids = props if isinstance(props, list) else (props or {}).get("children")
        if kids and drop_or_set(kids, node_id, text):
            return True
    return False
