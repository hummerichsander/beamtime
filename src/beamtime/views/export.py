"""Static exports of a page: a folder that opens from disk with the page's answers frozen, and each
block as a figure at paper sizes.

Both are taken by the headless renderer: the project is served for the call and the page opened in
an installed browser, which records every call the page makes (``--html``) or hands over each
block's downloads (``--figures``)."""

import json
import shutil
import time
from base64 import b64encode
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote, unquote, urlsplit

from beamtime.ops.context import Context, OpError
from beamtime.views.render import launch, serving, settle, skipped

MARKER = "_export.json"
# sparklines ask for fewer points than this; the points an export asks for are for charts.
SPARK = 100
# placeholder queries are answered for at most this many runs of the page.
PLACEHOLDER_RUNS = 200
# methods the page sends that are about the live server, not the page's content.
LIVE = ("watch",)


def export_html(ctx: Context, path: str, out: Path, points: int | Literal["all"]) -> dict[str, Any]:
    """Write a page as a folder that opens from disk: the frontend, every answer it loaded, and
    the files it showed.

    :param ctx: The operation context, with caller ``view``.
    :param path: The group or run path.
    :param out: The folder; empty, missing, or an earlier export.
    :param points: Points per curve, or ``all``.
    :return: What was written, or why it was skipped."""
    folder_for(out)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return skipped("Playwright is not installed; it comes with beamtime's serve extra")
    calls: list[dict[str, Any]] = []
    shown: dict[str, bytes] = {}
    findings: list[str] = []
    with serving(ctx) as (base, token), sync_playwright() as p:
        if (browser := launch(p)) is None:
            return skipped("no installed Chromium, Chrome or Edge was found")
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900}, color_scheme="light")
            page.on("pageerror", lambda e: findings.append(f"page error: {e}"))
            page.route("**/api/**", lambda r, q: record(r, q, points, calls, shown))
            page.goto(f"{base}/f/local?token={token}&render=1")
            page.goto(f"{base}{page_url(path)}?render=1&record=1&theme=light")
            if not settle(page):
                findings.append("the page didn't finish loading; the snapshot may miss answers")
        finally:
            browser.close()
    calls += placeholder_calls(ctx, calls, points)
    write(out, path, calls, shown, points)
    lines = [f"wrote {out / 'index.html'}: {len(calls)} answers, {len(shown)} files"]
    lines += findings
    lines.append("open it from disk or send the folder; it needs no server")
    return {"kind": "export", "lines": lines, "dir": str(out), "answers": len(calls), "meta": {}}


# paper sizes in inches: a single column and both columns of a two-column paper.
SIZES = {"single": (3.3, 2.5), "double": (6.9, 2.5)}
# CSS pixels per inch, and how many device pixels each of them gets in a PNG.
DPI_CSS = 96
SCALE = 4


def export_figures(
    ctx: Context, path: str, out: Path, size: Literal["single", "double"]
) -> dict[str, Any]:
    """Write each block of a page as a figure at a paper size: PNG (or SVG for custom blocks that
    draw SVG), its data as CSV, and a vector PDF in the project's figure style.

    :param ctx: The operation context, with caller ``view``.
    :param path: The group or run path.
    :param out: The folder; created if missing, files of the same names replaced.
    :param size: ``single`` or ``double`` column.
    :return: What was written, or why it was skipped."""
    import base64
    from urllib.parse import unquote_to_bytes

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return skipped("Playwright is not installed; it comes with beamtime's serve extra")
    width, height = (round(x * DPI_CSS) for x in SIZES[size])
    taken: dict[str, dict[str, Any]] = {}
    with serving(ctx) as (base, token), sync_playwright() as p:
        if (browser := launch(p)) is None:
            return skipped("no installed Chromium, Chrome or Edge was found")
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900}, color_scheme="light",
                                    device_scale_factor=SCALE)  # fmt: skip
            page.goto(f"{base}/f/local?token={token}&render=1")
            page.goto(f"{base}{page_url(path)}?render=1&record=1&figures=1&theme=light")
            settle(page)
            for id_ in page.evaluate("() => window.__btFigures()"):
                got = page.evaluate(
                    "([id, w, h]) => window.__btFigure(id, {width: w, height: h})",
                    [id_, width, height],
                )
                if got:
                    taken[id_] = got
        finally:
            browser.close()
    out.mkdir(parents=True, exist_ok=True)
    lines, pdfs = [], 0
    for id_, got in taken.items():
        for kind in ("png", "svg", "csv"):
            if not (href := got.get(kind)):
                continue
            head, _, data = href.partition(",")
            content = base64.b64decode(data) if head.endswith(";base64") else unquote_to_bytes(data)
            (out / f"{id_}.{kind}").write_bytes(content)
        if (spec := got.get("pdf")) is not None:
            try:
                (out / f"{id_}.pdf").write_bytes(figure_pdf(ctx, spec))
                pdfs += 1
            except OpError as e:
                lines.append(f"{id_}.pdf: {e}")
    lines.insert(0, f"wrote {len(taken)} figures to {out} at {size} column ({SIZES[size][0]} x "
                    f"{SIZES[size][1]} in), {pdfs} of them also as PDF")  # fmt: skip
    return {"kind": "export", "lines": lines, "dir": str(out), "figures": sorted(taken), "meta": {}}


def figure_pdf(ctx: Context, spec: dict[str, Any]) -> bytes:
    """Draw a chart as a vector PDF in the project's figure style.

    :param ctx: The operation context.
    :param spec: The figure, as a chart's PDF download sends it.
    :return: The PDF."""
    from beamtime.views.figure import pdf

    # a project's own style files are paths relative to its root.
    styles = [
        str(ctx.root / s) if s.endswith(".mplstyle") else s
        for s in ctx.settings.get("figure_style") or []
    ]
    return pdf(spec, styles)


def record(
    route: Any,
    request: Any,
    points: int | Literal["all"],
    calls: list[dict[str, Any]],
    shown: dict[str, bytes],
) -> None:
    """Pass one API request through to the server and keep its answer.

    :param route: The Playwright route.
    :param request: Its request.
    :param points: Points per chart curve.
    :param calls: The answers so far, ``{method, params, answer}`` or with ``error``.
    :param shown: Run files the page showed, by ``<run>/<path>``."""
    url = urlsplit(request.url).path
    if request.method == "POST" and (method := url.removeprefix("/api/")) not in LIVE:
        params = json.loads(request.post_data or "{}")
        response = route.fetch(post_data=json.dumps(with_points(method, params, points)))
        try:
            body = response.json()
        except ValueError:
            body = None
        if response.ok:
            calls.append({"method": method, "params": params, "answer": body})
        elif isinstance(body, dict):
            calls.append({"method": method, "params": params, "error": body.get("error"),
                          "code": body.get("code")})  # fmt: skip
        route.fulfill(response=response)
    elif url.startswith("/api/file/"):
        response = route.fetch()
        if response.ok:
            shown[unquote(url.removeprefix("/api/file/"))] = response.body()
        route.fulfill(response=response)
    else:
        route.continue_()


def with_points(
    method: str, params: dict[str, Any], points: int | Literal["all"]
) -> dict[str, Any]:
    """Ask a chart's curves at the export's resolution; everything else as the page asked.

    :param method: The API method.
    :param params: Its parameters, as the page sent them.
    :param points: Points per curve, or ``all``.
    :return: The parameters to answer."""
    given = params.get("points")
    if method != "series" or isinstance(given, int) and given < SPARK:
        return params
    return params | {"points": points}


def placeholder_calls(
    ctx: Context, calls: list[dict[str, Any]], points: int | Literal["all"]
) -> list[dict[str, Any]]:
    """Answer custom blocks' placeholder queries for the page's runs, so the frozen page still
    shows what a block shows for a hovered or chosen run.

    :param ctx: The operation context.
    :param calls: The recorded answers.
    :param points: Points per chart curve.
    :return: More answers, one per placeholder query and run."""
    from beamtime.serve.api import dispatch
    from beamtime.views.code import fill, placeholders

    runs = list(dict.fromkeys(run_ids(calls)))[:PLACEHOLDER_RUNS]
    out, seen = [], {(c["method"], json.dumps(c["params"])) for c in calls}
    for call in declared_calls(calls):
        names = placeholders(call["params"])
        if len(names) != 1:
            continue
        (name,) = names
        for run in runs:
            params = fill(call["params"], {name: run})
            if (key := (call["method"], json.dumps(params))) in seen:
                continue
            seen.add(key)
            try:
                answer = dispatch(ctx, call["method"], with_points(call["method"], params, points))
            except OpError:
                continue
            out.append({"method": call["method"], "params": params, "answer": answer})
    return out


def declared_calls(calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """List the calls custom blocks declared, from the recorded page answers.

    :param calls: The recorded answers.
    :return: ``{method, params}`` per declared query with a placeholder."""
    from beamtime.views.code import placeholders
    from beamtime.views.compile import walk_tree

    out = []
    for c in calls:
        if c["method"] != "view" or not isinstance(
            tree := (c.get("answer") or {}).get("view"), dict
        ):
            continue
        for node in walk_tree(tree):
            if node.get("block") != "custom":
                continue
            out += [q for q in (node.get("data") or {}).values() if placeholders(q["params"])]
    return out


def run_ids(calls: list[dict[str, Any]]) -> list[str]:
    """Collect the run ids in the page's run tables.

    :param calls: The recorded answers.
    :return: The ids, in the order the page listed them."""
    out = []
    for c in calls:
        answer = c.get("answer")
        if (
            c["method"] != "runs"
            or not isinstance(answer, dict)
            or "run.id" not in answer.get("columns", [])
        ):
            continue
        i = answer["columns"].index("run.id")
        out += [row[i] for row in answer.get("rows", [])]
    return out


def write(
    out: Path,
    path: str,
    calls: list[dict[str, Any]],
    shown: dict[str, bytes],
    points: int | Literal["all"],
) -> None:
    """Write the export folder.

    :param out: The folder.
    :param path: The page.
    :param calls: The answers.
    :param shown: The run files the page showed.
    :param points: Points per curve, as asked."""
    from importlib.metadata import version

    if out.exists():
        shutil.rmtree(out)
    static = files("beamtime.serve") / "static"
    (out / "static" / "export").mkdir(parents=True)
    for name in ("main.js", "main.css"):
        (out / "static" / "export" / name).write_bytes((static / "export" / name).read_bytes())
    # a custom block's sandboxed frame may load no files from disk: its page carries the kit.
    frame = {
        "kit": (static / "export" / "kit.js").read_text(),
        "css": (static / "export" / "main.css").read_text(),
    }
    (out / "static" / "export" / "frame.js").write_text(
        f"window.__BT_FRAME__ = {json.dumps(frame)};\n"
    )
    for name in ("katex.css", "THIRD_PARTY_LICENSES.txt"):
        (out / "static" / name).write_bytes((static / name).read_bytes())
    (out / "static" / "fonts").mkdir()
    for font in (static / "fonts").iterdir():
        (out / "static" / "fonts" / font.name).write_bytes(font.read_bytes())
    for rel, content in shown.items():
        (target := out / "files" / rel).parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    taken = time.time()
    snapshot = {"path": path, "taken": taken, "points": points, "version": version("beamtime"),
                "calls": calls}  # fmt: skip
    (out / "snapshot.js").write_text(f"window.__BT_SNAPSHOT__ = {json.dumps(snapshot)};\n")
    title = "the log dir" if path == "." else path
    # a file opened from disk has no server to ask for /static/favicon.svg.
    favicon = b64encode((static / "favicon.svg").read_bytes()).decode()
    (out / "index.html").write_text(INDEX.format(title=title, favicon=favicon))
    marker = {"schema": 1, "path": path, "taken": taken, "points": points}
    (out / MARKER).write_text(json.dumps(marker) + "\n")


INDEX = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} · Beamtime snapshot</title>
    <link rel="icon" href="data:image/svg+xml;base64,{favicon}" />
    <link rel="stylesheet" href="static/export/main.css" />
  </head>
  <body class="body">
    <div id="app"></div>
    <script src="snapshot.js"></script>
    <script src="static/export/frame.js"></script>
    <script src="static/export/main.js"></script>
  </body>
</html>
"""


def folder_for(out: Path) -> None:
    """Refuse a folder that holds something other than an earlier export.

    :param out: The export folder."""
    if out.is_file() or (out.is_dir() and any(out.iterdir()) and not (out / MARKER).is_file()):
        raise OpError(f"{out} isn't empty; export into a new folder or an earlier export", code=2)


def page_url(path: str) -> str:
    """Build the URL path of a page.

    :param path: A group or run path below the log dir.
    :return: E.g. ``/f/local/scaling/lr-sweep``."""
    return "/f/local" + "".join(f"/{quote(part)}" for part in path.split("/") if path != ".")
