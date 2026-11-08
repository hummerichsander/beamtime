"""The view operations: drafts, validation, rendering, saving, and a view's versions.

Drafts live in ``.beamtime/drafts/<name>/``; saving writes a new version into the page's
``view/``, with data files copied under content hashes, and never changes an existing file."""

import hashlib
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.ids import id_time
from beamtime.format.io import write_created
from beamtime.format.schema import SchemaError
from beamtime.ops import registry as r
from beamtime.ops.authored import author_of, save, target_of, written
from beamtime.ops.context import Context, OpError
from beamtime.views import model as m
from beamtime.views import store

BUNDLE_LIMIT = 16 << 20


def new(ctx: Context, p: r.ViewNewParams) -> dict[str, Any]:
    """Start a draft: from an example, else from the page's current view, local or on another
    source. The draft itself always stays here.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The draft's name and file."""
    remote = p.group.startswith("@")
    if p.from_ is not None:
        from beamtime.guide import example, example_file

        if remote:
            path = p.group
        else:
            with target_of(ctx, p.group) as target:
                path = target.rel
        text, origin = example(p.from_, ctx, path), f"the {p.from_!r} example"
        return write_draft_files(ctx, p, path, text, origin, example_file)
    if remote:
        from beamtime.remote import answer as remote_answer

        shown = remote_answer("view show", {"group": p.group}, ctx)
        path = shown["group"]
        if shown.get("yaml") is not None:
            text, origin = shown["yaml"], f"version {shown['version']} of {path}"
        else:
            text = m.dump({"schema": 1, "title": None, "finding": None, "body": []})
            origin = f"a blank view ({path} has no saved view yet; --from starts from an example)"

        def fetch(ref: str) -> bytes | None:
            return fetch_view_file(ctx, path, ref)
    else:
        with target_of(ctx, p.group) as target:
            path = target.rel
        text, origin = current_yaml(ctx, path)
        view_folder = store.view_dir(ctx, path)

        def fetch(ref: str) -> bytes | None:
            source = view_folder / ref
            return source.read_bytes() if source.is_file() else None

    return write_draft_files(ctx, p, path, text, origin, fetch)


def write_draft_files(
    ctx: Context,
    p: r.ViewNewParams,
    path: str,
    text: str,
    origin: str,
    fetch: Callable[[str], bytes | None],
) -> dict[str, Any]:
    """Write a new draft's folder: its ``view.yaml``, the files it references, and
    ``_draft.json``.

    :param ctx: The operation context.
    :param p: The parameters.
    :param path: The group or run path, ``@source/...`` for another source.
    :param text: The view's YAML.
    :param origin: Where it came from, for the answer.
    :param fetch: Reads one referenced data or code file; ``None`` where there is none.
    :return: The draft's name and file."""
    name = store.check_name(p.name or default_name(path), new=True)
    folder = store.drafts(ctx) / name
    if folder.exists():
        raise OpError(
            f"draft {name!r} exists at {folder}; continue it by editing its view.yaml, "
            "or start another with --name",
            code=1,
        )
    (folder / "data").mkdir(parents=True)
    (folder / store.VIEW_FILE).write_text(text)
    for ref in data_refs(text):
        if (content := fetch(ref)) is not None:
            write_created(folder / ref, content)
    store.write_draft_meta(folder, group=path, origin=p.from_ or "current")
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
    """Find the data and code files a view's YAML refers to.

    :param text: The YAML.
    :return: The ``data/...`` and ``code/...`` references."""
    import yaml

    from beamtime.views.model import yaml_walk

    try:
        body = (yaml.safe_load(text) or {}).get("body") or []
        files = {"data_table": "file", "custom": "code"}
        return [
            props[files[b]]
            for b, props in yaml_walk(body)
            if b in files and isinstance(props.get(files[b]), str)
        ]
    except (yaml.YAMLError, AttributeError, ValueError):
        return []


def default_name(path: str) -> str:
    """Name a draft after its page.

    :param path: The group or run path.
    :return: E.g. ``lr-sweep``, or ``root`` for the log dir."""
    return m.slug(path.rsplit("/", 1)[-1]) if path != "." else "root"


def page_yaml(ctx: Context, path: str, pins: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Read the page's current view in YAML form, for a change made in the web UI.

    :param ctx: The operation context.
    :param path: The group or run path.
    :param pins: The viewer's pins, which the default view takes into its Main section.
    :return: The view as a mapping.
    :raises OpError: If the saved version is broken; the UI then says how to repair it."""
    import yaml

    text, origin = current_yaml(ctx, path, pins)
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        data = None
    if not isinstance(data, dict) or "(invalid)" in origin:
        raise OpError(
            f"the view of {path} ({origin}) is broken, so it can't be changed here; repair it in "
            f"a draft: `beamtime view new {path}`",
            code=3,
        )
    return data


def current_yaml(
    ctx: Context, path: str, pins: list[dict[str, Any]] | None = None
) -> tuple[str, str]:
    """Write the page's current view as draft YAML: its newest version, else the default.

    :param ctx: The operation context.
    :param path: The group or run path.
    :param pins: The viewer's pins for the default view; ``None`` for the default pins.
    :return: The YAML text, and where it came from."""
    from beamtime.views.defaults import default_view

    if files := store.saved(ctx, path):
        try:
            view = store.read(files[-1], source=files[-1].name)
        except SchemaError:
            return files[-1].read_text(), f"version {files[-1].stem} (invalid)"
        data = m.to_yaml_form(view)
        # pins stay, so editing a view never upgrades its library blocks unasked.
        for k in ("author", "user", "message"):
            data.pop(k, None)
        return m.dump(data), f"version {files[-1].stem}"
    data = {"schema": 1, "title": None, "finding": None} | m.to_yaml_form(
        default_view(ctx, path, pins)
    )
    return m.dump(data), "the built-in default view"


def validate(ctx: Context, p: r.ViewValidateParams) -> dict[str, Any]:
    """Validate a draft: statically (on the source its group is on), then with one render where
    a browser exists.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The findings and whether it rendered."""
    d = store.draft(ctx, p.draft)
    if d.group.startswith("@"):
        from beamtime.remote.route import on_source

        ok, findings = True, on_source("view_check", d.group, ctx, bundle(ctx, d))["findings"]
    else:
        view, findings = check(ctx, d)
        ok = view is not None
    answer: dict[str, Any] = {"kind": "view validate", "draft": d.name, "group": d.group}
    if ok and p.render and not any(f["level"] == "error" for f in findings):
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
    """Validate a draft statically, against its own (local) group.

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
        ctx, d.group, data, source=f"draft {d.name}", draft=d.name, data_dir=d.dir, blocks=d.blocks
    )
    return view, [f.to_dict() for f in findings]


def bundle(ctx: Context, d: store.Draft) -> dict[str, Any]:
    """Pack a draft's view, the files it references and the block drafts it uses, to send to
    another source.

    :param ctx: The operation context.
    :param d: The draft.
    :return: ``{draft, yaml, files, blocks}``; files are base64 by their path in the draft."""
    text = d.file.read_text()
    files = packed(d.dir, [ref for ref in data_refs(text) if (d.dir / ref).is_file()])
    return {"draft": d.name, "yaml": text, "files": files, "blocks": bundle_blocks(ctx, d.blocks)}


def bundle_blocks(ctx: Context, blocks: dict[str, str]) -> dict[str, dict[str, Any]]:
    """Pack block drafts, every file of each, to send to another source.

    :param ctx: The operation context.
    :param blocks: Block names to their drafts' names.
    :return: ``{name: {draft, files}}``."""
    from beamtime.views.library import drafts_dir

    out = {}
    for name, draft in blocks.items():
        folder = drafts_dir(ctx) / store.check_name(draft)
        refs = [
            f.relative_to(folder).as_posix()
            for f in sorted(folder.rglob("*"))
            if f.is_file() and f.name != store.DRAFT_META
        ]
        out[name] = {"draft": draft, "files": packed(folder, refs)}
    return out


def packed(folder: Path, refs: list[str]) -> dict[str, str]:
    """Read files of a draft as base64.

    :param folder: The draft's folder.
    :param refs: Their paths in it.
    :return: Each path to its content."""
    import base64

    return {ref: base64.b64encode((folder / ref).read_bytes()).decode() for ref in refs}


def check_size(body: dict[str, Any]) -> None:
    """Refuse a bundle above the 16 MB a remote save accepts, before or after it travels.

    :param body: The bundle.
    :raises OpError: If it is too large."""
    blocks = (body.get("blocks") or {}).values()
    files = [*(body.get("files") or {}).values()]
    files += [v for b in blocks if isinstance(b, dict) for v in (b.get("files") or {}).values()]
    size = len(str(body.get("yaml") or "").encode()) + sum(len(v) for v in files) * 3 // 4
    if size > BUNDLE_LIMIT:
        raise OpError(
            f"the draft is {size / (1 << 20):.1f} MB, over the 16 MB a remote save accepts; "
            "put large data in the group's own data files instead of the draft's",
            code=2,
        )


def bundle_group(ctx: Context, group: str) -> str:
    """Resolve the group a bundle names on this machine, so it can't leave the log dir.

    :param ctx: The operation context.
    :param group: The group or run, as the other source sent it.
    :return: Its path relative to the log dir."""
    with target_of(ctx, group) as target:
        return target.rel


@contextmanager
def bundled(ctx: Context, group: str, body: dict[str, Any]) -> Iterator[Context]:
    """Unpack a bundle as real drafts, under the sender's draft names, in a root of their own
    inside this project's ``.beamtime/``, so their file, code and block lookups work as the
    sender's do and two bundles never meet.

    :param ctx: The operation context.
    :param group: The group the drafts are for.
    :param body: ``{draft, yaml, files}`` for a view draft (optional) and ``blocks``.
    :return: The context whose drafts are the bundle's, while it lasts.
    :raises OpError: Above 16 MB, or for a file outside its draft."""
    import dataclasses
    import secrets
    import shutil

    from beamtime.views.library import drafts_dir

    check_size(body)
    base = (store.drafts(ctx).parent / "bundles" / secrets.token_hex(8)).resolve()
    here = dataclasses.replace(ctx, root=base)
    blocks = {n: str(b["draft"]) for n, b in (body.get("blocks") or {}).items()}
    try:
        if (text := body.get("yaml")) is not None:
            folder = store.drafts(here) / store.check_name(str(body["draft"]))
            unpack(folder, body.get("files") or {})
            (folder / "data").mkdir(exist_ok=True)
            (folder / store.VIEW_FILE).write_text(str(text))
            store.write_draft_meta(folder, group=group, origin="a bundle", blocks=blocks)
        for name, b in (body.get("blocks") or {}).items():
            folder = drafts_dir(here) / store.check_name(blocks[name])
            unpack(folder, b.get("files") or {})
            store.write_draft_meta(folder, group=group, origin="a bundle")
        yield here
    finally:
        shutil.rmtree(base, ignore_errors=True)


def unpack(folder: Path, files: dict[str, str]) -> None:
    """Write a bundle's files into a draft's folder, refusing any that would land outside it.

    :param folder: The draft's folder, created here.
    :param files: Paths in it to base64 content."""
    import base64

    folder.mkdir(parents=True)
    root = folder.resolve()
    for ref, content in files.items():
        dest = (root / ref).resolve()
        if root not in dest.parents:
            raise OpError(f"{ref!r} leaves the bundle", code=2)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(base64.b64decode(content))


def view_check(ctx: Context, body: dict[str, Any]) -> dict[str, Any]:
    """Validate a bundled draft against this machine's own group (API-only: what a remote call
    to ``view validate`` turns into).

    :param ctx: The operation context.
    :param body: ``{group, draft, yaml, files, blocks}``.
    :return: The findings."""
    group = bundle_group(ctx, str(body["group"]))
    with bundled(ctx, group, body) as here:
        _, findings = check(here, store.draft(here, str(body["draft"])))
    return {"kind": "view check", "findings": findings, "meta": {}}


def view_put(ctx: Context, body: dict[str, Any]) -> dict[str, Any]:
    """Validate a bundled draft and, without errors, save it as a new version (API-only: what a
    remote call to ``view save`` turns into).

    :param ctx: The operation context.
    :param body: ``{group, draft, yaml, files, blocks, author, message}``.
    :return: What ``view save`` returns."""
    group = bundle_group(ctx, str(body["group"]))
    with bundled(ctx, group, body) as here:
        d = store.draft(here, str(body["draft"]))
        return save_checked(here, d, body.get("author"), body.get("message"))


def view_compile(ctx: Context, body: dict[str, Any]) -> dict[str, Any]:
    """Compile a bundled draft on this machine, for rendering a draft of a group here on the
    sender's machine (API-only). The compiled tree names the sender's drafts, which answer its
    code and file calls there.

    :param ctx: The operation context.
    :param body: ``{group, draft, yaml, files, blocks}``.
    :return: What ``store.shown`` returns for a draft."""
    group = bundle_group(ctx, str(body["group"]))
    with bundled(ctx, group, body) as here:
        return store.shown(here, group, draft_name=str(body["draft"]))


def view_files(ctx: Context, body: dict[str, Any]) -> dict[str, Any]:
    """Read one of a page's view data or code files (API-only: for starting a draft from
    another source's current view).

    :param ctx: The operation context.
    :param body: ``{group, ref}``, ``ref`` being ``data/<hash>-<name>`` or ``code/<hash>-<name>``.
    :return: ``{content}``, base64, or ``None`` if there is no such file."""
    import base64

    group, ref = bundle_group(ctx, str(body["group"])), str(body["ref"])
    folder = store.view_dir(ctx, group).resolve()
    file = (folder / ref).resolve()
    if folder not in file.parents or ref.split("/", 1)[0] not in ("data", "code"):
        raise OpError(f"no view file {ref!r}", code=2)
    content = base64.b64encode(file.read_bytes()).decode() if file.is_file() else None
    return {"kind": "view files", "content": content}


def fetch_view_file(ctx: Context, path: str, ref: str) -> bytes | None:
    """Read one of a view's data or code files on another source.

    :param ctx: The operation context.
    :param path: The group, ``@source/bare``.
    :param ref: ``data/<hash>-<name>`` or ``code/<hash>-<name>``.
    :return: Its content, or ``None`` if there is no such file."""
    import base64

    from beamtime.remote.route import on_source

    content = on_source("view_files", path, ctx, {"ref": ref}).get("content")
    return base64.b64decode(content) if content is not None else None


def draft_view(ctx: Context, path: str, draft_name: str) -> dict[str, Any]:
    """Compile a draft whose group is on another source, on that source, for the page it is
    being rendered on.

    :param ctx: The operation context.
    :param path: The group, ``@source/bare``.
    :param draft_name: The local draft's name.
    :return: What ``store.shown`` returns."""
    from beamtime.remote.route import on_source

    return on_source("view_compile", path, ctx, bundle(ctx, store.draft(ctx, draft_name)))


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
    if cut := result.get("cut"):
        below = ", ".join(cut["blocks_below"])
        lines.append(
            f"the page is {cut['page_height']} px; the shot shows the top {cut['shown_height']}; "
            f"below it: {below}; `view render {d.name} --block <id>` shows one"
        )
    return {
        "kind": "view render",
        "draft": d.name,
        "group": d.group,
        **result,
        "lines": lines,
        "meta": {},
    }


def save_draft(ctx: Context, p: r.ViewSaveParams) -> dict[str, Any]:
    """Save a draft as a new view version, refusing one with errors. On another source, the
    check and the write happen there.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new version."""
    d = store.draft(ctx, p.draft)
    if d.group.startswith("@"):
        from beamtime.remote.route import on_source

        author = p.author or author_of(ctx, None)[0]
        body = bundle(ctx, d) | {"author": author, "message": p.message}
        return on_source("view_put", d.group, ctx, body)
    return save_checked(ctx, d, p.author, p.message)


def save_checked(
    ctx: Context, d: store.Draft, author: str | None, message: str | None
) -> dict[str, Any]:
    """Check a draft against its group here and save it as a new version, refusing one with
    errors.

    :param ctx: The operation context.
    :param d: The draft.
    :param author: Who saves it.
    :param message: What this version changed.
    :return: The new version."""
    view, findings = check(ctx, d)
    errors = [f for f in findings if f["level"] == "error"]
    if view is None or errors:
        raise OpError(
            "the draft has errors; fix them and save again:\n" + "\n".join(summary(errors, None)),
            code=3,
        )
    path = write_version(ctx, d.group, view, author, message, data_dir=d.dir)
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
    from beamtime.views.library import Library

    view.author, view.user = author_of(ctx, author)
    view.message = message
    library = Library(ctx=ctx, path=group)
    used = sorted({n.name for n in m.walk(view.body) if isinstance(n, m.Use)})
    view.uses = {name: view.uses.get(name) or library.newest(name) or "" for name in used}
    folder = store.view_dir(ctx, group)
    for n in m.walk(view.body):
        if isinstance(n, m.DataTable) and n.file is not None and data_dir is not None:
            n.file = copy_data(data_dir / n.file, folder)
        if isinstance(n, m.Custom) and data_dir is not None:
            n.code = copy_data(data_dir / n.code, folder, "code")
    return save(folder, ".yaml", m.dump(m.to_yaml_form(view)))


def copy_data(source: Path, folder: Path, sub: str = "data") -> str:
    """Store a data or code file next to the view, named by its content hash.

    :param source: The draft's file.
    :param folder: The page's ``view/`` folder.
    :param sub: ``data`` or ``code``.
    :return: The reference relative to ``view/``: ``<sub>/<sha8>-<name>``."""
    content = source.read_bytes()
    # a file copied from a saved version already carries a hash prefix.
    stem = re.sub(r"^[0-9a-f]{8}-", "", source.name)
    ref = f"{sub}/{hashlib.sha256(content).hexdigest()[:8]}-{stem}"
    if not (folder / ref).exists():
        write_created(folder / ref, content)
    return ref


def save_page(
    ctx: Context, path: str, prefs: dict[str, Any], title: str | None, finding: str | None
) -> dict[str, Any]:
    """Save what a page shows with a viewer's chart settings as a new version (the web UI).

    :param ctx: The operation context, with caller ``view``.
    :param path: The group or run path.
    :param prefs: The viewer's ``{view, charts, added, main}`` for the page.
    :param title: The view's title.
    :param finding: The view's finding.
    :return: The new version."""

    from beamtime.views.prefs import apply_pins, apply_prefs

    pins = prefs.get("main")
    data = page_yaml(ctx, path, pins)
    data["body"] = apply_prefs(data.get("body") or [], prefs)
    if pins is not None:
        apply_pins(data, pins)
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

    from beamtime.views.model import yaml_walk

    data = page_yaml(ctx, path)
    body = data.get("body") or []
    if node_id is None:
        taken = {props.get("id") for _, props in yaml_walk(body)}
        node_id = m.unique("text", taken)
        body.insert(0, {"markdown": {"id": node_id, "text": text or "Write here."}})
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
    return written(ctx, "view save", write_version(ctx, path, view, None, message), []) | {
        "id": node_id
    }


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


def outdated(ctx: Context, p: r.ViewOutdatedParams) -> dict[str, Any]:
    """List the views at or below a group pinned to older versions of their library blocks.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: One row per view and block: page, block, pinned and newest version."""
    from beamtime.views.library import Library

    with target_of(ctx, p.group) as target:
        base = ctx.logdir / target.rel
    rows = []
    for folder in sorted(base.rglob(c.VIEW)):
        rel = folder.parent.relative_to(ctx.logdir).as_posix() or "."
        if any(part.startswith((".", "_")) for part in rel.split("/")) or not folder.is_dir():
            continue
        if not (files := store.saved(ctx, rel)):
            continue
        try:
            view = store.read(files[-1], source=files[-1].name)
        except SchemaError:
            continue
        for item in store.outdated(view, Library(ctx=ctx, path=rel)):
            rows.append([rel, item["name"], item["pinned"], item["newest"]])
    lines = [f"{g}: {b} {old} → {new} (`beamtime view upgrade {g}`)" for g, b, old, new in rows]
    return {
        "kind": "view outdated",
        "columns": ["group", "block", "pinned", "newest"],
        "rows": rows,
        "lines": lines or ["every view uses the newest versions of its library blocks"],
        "meta": {"matched": len(rows)},
    }


def upgrade(ctx: Context, p: r.ViewUpgradeParams) -> dict[str, Any]:
    """Re-pin a page's view to the newest versions of its library blocks, as a new version.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The new version, or what keeps the upgrade from validating."""
    from beamtime.views.library import Library
    from beamtime.views.validate import static

    with target_of(ctx, p.group) as target:
        path = target.rel
    if not (files := store.saved(ctx, path)):
        raise OpError(f"{path} has no saved view", code=4)
    view = store.read(files[-1], source=files[-1].name)
    library = Library(ctx=ctx, path=path)
    stale = [o for o in store.outdated(view, library) if p.block in (None, o["name"])]
    if not stale:
        return {"kind": "view upgrade", "group": path, "lines": ["nothing to upgrade"], "meta": {}}
    for item in stale:
        view.uses[item["name"]] = item["newest"]
    data = m.to_yaml_form(view)
    _, findings = static(ctx, path, data, source=f"{path} upgraded")
    errors = [f.to_dict() for f in findings if f.level == "error"]
    if errors:
        raise OpError(
            "the upgraded view has errors; start a draft (`beamtime view new "
            f"{path}`), adjust the uses to the new params, and save it:\n"
            + "\n".join(summary(errors, None)),
            code=3,
        )
    names = ", ".join(f"{o['name']} {o['pinned']} → {o['newest']}" for o in stale)
    file = write_version(ctx, path, view, p.author, f"upgrade {names}")
    return written(ctx, "view upgrade", file, [f"upgraded {names}"])


def export(ctx: Context, p: r.ExportParams) -> dict[str, Any]:
    """Export a page: as a folder that opens from disk, or as one figure per block.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: What was written, or why it was skipped."""
    import dataclasses

    from beamtime.views.export import export_figures, export_html

    if (p.html is None) == (p.figures is None):
        raise OpError(
            "give --html <folder> for the page, or --figures <folder> for its blocks", code=2
        )
    with target_of(ctx, p.group) as target:
        path = target.rel
    view = dataclasses.replace(ctx, caller="view")
    if p.html is not None:
        return export_html(view, path, Path(p.html).expanduser().resolve(), p.points)
    return export_figures(view, path, Path(p.figures or "").expanduser().resolve(), p.size)
