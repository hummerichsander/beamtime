"""Static validation of a view: the schema, then every block's queries run once against its scope.

Running the declared queries checks that they parse, that fields and keys exist (with the query
layer's suggestions) and that blocks get data, with the same code the page uses."""

import dataclasses
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from beamtime.format.schema import SchemaError
from beamtime.ops import call
from beamtime.ops.context import Context, OpError
from beamtime.ops.registry import BY_TOOL
from beamtime.views import model as m
from beamtime.views.compile import compile_view, walk_tree

MAX_CURVES = 8


@dataclasses.dataclass(kw_only=True)
class Finding:
    """One problem: an error stops saving, a warning doesn't."""

    level: Literal["error", "warning"]
    message: str
    id: str | None = None
    block: str | None = None
    fix: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Describe the finding.

        :return: Its fields, without empty ones."""
        return {k: v for k, v in dataclasses.asdict(self).items() if v is not None}


def static(
    ctx: Context,
    path: str,
    data: Any,
    *,
    source: str,
    draft: str | None = None,
    data_dir: Path | None = None,
    blocks: dict[str, str] | None = None,
) -> tuple[m.View | None, list[Finding]]:
    """Validate a view for a page without a browser.

    :param ctx: The operation context.
    :param path: The page: a group below the log dir, or a run's path.
    :param data: The view as parsed YAML.
    :param source: How to name the view in messages.
    :param draft: The draft's name, so data files are read from it.
    :param data_dir: Where the view's data files are, to check ``file`` references.
    :param blocks: Block drafts standing in for library blocks of the same name.
    :return: The view, if it parses, and the findings."""
    from beamtime.views.library import Library

    try:
        view = m.parse(data, source=source)
    except SchemaError as e:
        return None, [Finding(level="error", message=str(e), fix="see `beamtime guide blocks`")]
    library = Library(ctx=ctx, path=path, drafts=blocks)
    findings = structure(view, data_dir) + uses(view, library)
    if any(f.level == "error" for f in findings):
        return view, findings
    ctx = dataclasses.replace(ctx, caller="view")
    tree = compile_view(view, path=path, draft=draft, library=library)
    nodes = {n.id: n for n in m.walk(view.body)}
    keys: dict[str, dict[str, Any]] = {}
    for t in walk_tree(tree):
        if (n := nodes.get(t["id"])) is not None:
            findings += queries(ctx, n, t, keys)
    return view, findings


def structure(view: m.View, data_dir: Path | None) -> list[Finding]:
    """Check what the schema can't: unique ids, captions, data files, custom blocks.

    :param view: The view.
    :param data_dir: Where its data files are.
    :return: The findings."""
    out = []
    if not view.finding or "TODO" in view.finding:
        out.append(
            Finding(
                level="warning",
                message="no finding",
                fix="state the key result in one sentence: finding: ...",
            )
        )
    for id_, n in Counter(m.ids(view.body)).items():
        if n > 1:
            out.append(
                Finding(
                    level="error",
                    id=id_,
                    message=f"id {id_!r} is used {n} times",
                    fix="give every node its own id",
                )
            )
    for n in m.walk(view.body):
        block = m.block_of(n)
        at = {"id": n.id, "block": block}
        if block in m.CHARTS and not n.caption:
            out.append(
                Finding(
                    level="warning",
                    **at,
                    message="a chart without caption",
                    fix="caption: what it shows, what varies, how many runs",
                )
            )
        match n:
            case m.DataTable() if (n.key is None) == (n.file is None):
                out.append(Finding(level="error", **at, message="give either key or file"))
            case m.DataTable() if n.file is not None and data_dir is not None:
                if not (data_dir / n.file).is_file():
                    out.append(
                        Finding(
                            level="error",
                            **at,
                            message=f"no data file {n.file!r}",
                            fix=f"put it in {data_dir}",
                        )
                    )
            case m.Custom():
                out += custom_checks(n, at, data_dir)
            case m.Line() if n.by and n.seeds:
                out.append(Finding(level="error", **at, message="use by or seeds, not both"))
    return out


def uses(view: m.View, library: Any) -> list[Finding]:
    """Check that every library block a view uses exists here and gets fitting params.

    :param view: The view.
    :param library: The page's library.
    :return: The findings."""
    from beamtime.views.library import problems

    out = []
    for n in m.walk(view.body):
        if not isinstance(n, m.Use):
            continue
        at = {"id": n.id, "block": n.name}
        try:
            found = library.get(n.name, view.uses.get(n.name))
        except SchemaError as e:
            out.append(Finding(level="error", **at, message=str(e), fix="`block_list` names them"))
            continue
        for message in problems(found.block, n.params):
            out.append(Finding(level="error", **at, message=message, fix=f"`block_show {n.name}`"))
    return out


def custom_checks(n: m.Custom, at: dict[str, Any], data_dir: Path | None) -> list[Finding]:
    """Check a custom block: its kit, libraries, declared queries and code.

    :param n: The node.
    :param at: Its id and block, for findings.
    :param data_dir: Where its code file is, if known.
    :return: The findings."""
    from beamtime.views import code

    out = []
    if n.kit not in code.KITS:
        out.append(Finding(level="error", **at, message=f"no kit {n.kit}", fix="kit: 1"))
    for lib in n.libs:
        if lib not in code.LIBS:
            out.append(
                Finding(
                    level="error",
                    **at,
                    message=f"no library {lib!r}",
                    fix=f"libs from {', '.join(code.LIBS)}",
                )
            )
    for name, q in n.queries.items():
        if len(q) != 1 or next(iter(q)) not in code.KINDS:
            out.append(
                Finding(
                    level="error",
                    **at,
                    message=f"query {name!r} must name one kind",
                    fix=f"{name}: {{runs: {{...}}}}; kinds: {', '.join(code.KINDS)}",
                )
            )
    if data_dir is None:
        return out
    if not (file := data_dir / n.code).is_file():
        missing = Finding(
            level="error", **at, message=f"no code file {n.code!r}", fix=f"put it in {data_dir}"
        )
        return [*out, missing]
    for message, fix in code.problems(file.read_text()):
        out.append(Finding(level="error", **at, message=f"{n.code}: {message}", fix=fix))
    return out


def queries(
    ctx: Context, n: m.Node, t: dict[str, Any], keys: dict[str, dict[str, Any]]
) -> list[Finding]:
    """Run a block's declared queries once and check what comes back.

    :param ctx: The operation context, with caller ``view``.
    :param n: The view node.
    :param t: Its compiled tree node.
    :param keys: ``keys`` answers by scope, shared between blocks.
    :return: The findings."""
    out = []
    at = {"id": n.id, "block": m.block_of(n)}
    for name, c in (t.get("data") or {}).items():
        params = c["params"]
        if isinstance(n, (m.Custom, m.Use)) and placeholders_of(params):
            params, rest = example_values(ctx, c["scope"], params)
            if rest:
                out.append(
                    Finding(
                        level="warning",
                        **at,
                        message=f"{name}: not run, nothing to fill {', '.join(rest)} with",
                        fix="check this query in `view render`, where the page fills it",
                    )
                )
                continue
        try:
            answer = call(BY_TOOL[c["method"]].name, params, ctx)
        except OpError as e:
            # a group without a proposal yet is a state the block shows, not a broken view.
            missing = e.code == 4 and c["method"] in ("proposal_show", "check")
            out.append(
                Finding(level="warning" if missing else "error", **at, message=f"{name}: {e}")
            )
            continue
        if name == "main":
            out += answer_checks(ctx, n, at, answer, c["params"], keys)
    return out


def answer_checks(
    ctx: Context,
    n: m.Node,
    at: dict[str, Any],
    answer: dict[str, Any],
    params: dict[str, Any],
    keys: dict[str, dict[str, Any]],
) -> list[Finding]:
    """Check a block's main answer: empty data, too many curves, unsound aggregates.

    :param ctx: The operation context.
    :param n: The view node.
    :param at: The node's id and block, for findings.
    :param answer: The answer.
    :param params: The call's parameters.
    :param keys: ``keys`` answers by scope.
    :return: The findings."""
    out = []
    match n:
        case m.Line():
            curves = answer.get("curves", [])
            if not curves:
                out.append(Finding(level="warning", **at, message=f"no run in scope logs {n.y}"))
            elif not (n.by or n.seeds or n.color) and len(curves) > MAX_CURVES:
                out.append(
                    Finding(
                        level="warning",
                        **at,
                        message=f"{len(curves)} curves",
                        fix="color: <field>, by: [<field>] or seeds: config.seed",
                    )
                )
            if n.by:
                scope = params["from"]
                if scope not in keys:
                    keys[scope] = call("keys", {"from": scope}, ctx)
                rows = keys[scope]["config"]["rows"]
                varying = {k for k, _, v in rows if isinstance(v, list) and len(v) > 1}
                by = {n.by} if isinstance(n.by, str) else set(n.by)
                other = sorted(varying - by - {"config.seed"})
                if other:
                    out.append(
                        Finding(
                            level="warning",
                            **at,
                            message=f"runs aggregated by {sorted(by)} also differ in "
                            f"{', '.join(other)}",
                            fix="add them to by, or narrow with where",
                        )
                    )
        case m.Scatter() | m.Bar() if len(answer.get("rows", [])) < 2:
            out.append(Finding(level="warning", **at, message="fewer than two runs to compare"))
        case m.Table() | m.Stat() if not answer.get("rows"):
            out.append(Finding(level="warning", **at, message="no runs in scope"))
        case m.Histogram() | m.Images() | m.Text() | m.DataTable():
            if not answer.get("entries") and not answer.get("rows"):
                out.append(Finding(level="warning", **at, message="no data in scope"))
    return out


def placeholders_of(params: dict[str, Any]) -> list[str]:
    """Name a query's open placeholders.

    :param params: The call's parameters.
    :return: E.g. ``["$run"]``."""
    from beamtime.views.code import placeholders

    return sorted(f"${p}" for p in placeholders(params))


def example_values(
    ctx: Context, scope: str, params: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Fill a query's placeholders to run it once: a ``from`` placeholder with the page's first run.

    :param ctx: The operation context.
    :param scope: The page, whose first run stands in for a ``from`` placeholder.
    :param params: The call's parameters.
    :return: The filled parameters, and the placeholders left open."""
    from beamtime.views.code import fill, placeholders

    values: dict[str, Any] = {}
    target = params.get("from")
    if isinstance(target, str) and target.startswith("$"):
        page = {k: v for k, v in params.items() if k in ("where", "depth")}
        answer = call("runs", {"from": scope, "select": ["run.id"], "limit": 1} | page, ctx)
        if answer["rows"]:
            values[target[1:]] = answer["rows"][0][0]
    filled = fill(params, values)
    return filled, sorted(f"${p}" for p in placeholders(filled))
