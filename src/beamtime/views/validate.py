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
from beamtime.views.compile import compile_view

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
) -> tuple[m.View | None, list[Finding]]:
    """Validate a view for a page without a browser.

    :param ctx: The operation context.
    :param path: The page: a group below the log dir, or a run's path.
    :param data: The view as parsed YAML.
    :param source: How to name the view in messages.
    :param draft: The draft's name, so data files are read from it.
    :param data_dir: Where the view's data files are, to check ``file`` references.
    :return: The view, if it parses, and the findings."""
    try:
        view = m.parse(data, source=source)
    except SchemaError as e:
        return None, [Finding(level="error", message=str(e), fix="see `beamtime guide blocks`")]
    findings = structure(view, data_dir)
    if any(f.level == "error" for f in findings):
        return view, findings
    ctx = dataclasses.replace(ctx, caller="view")
    tree = compile_view(view, path=path, draft=draft)
    nodes = {n.id: n for n in m.walk(view.body)}
    keys: dict[str, dict[str, Any]] = {}
    for t in tree_walk(tree):
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
                out.append(
                    Finding(
                        level="warning",
                        **at,
                        message="custom blocks arrive in M7; it shows a notice",
                    )
                )
            case m.Line() if n.by and n.seeds:
                out.append(Finding(level="error", **at, message="use by or seeds, not both"))
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
        try:
            answer = call(BY_TOOL[c["method"]].name, c["params"], ctx)
        except OpError as e:
            out.append(Finding(level="error", **at, message=f"{name}: {e}"))
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


def tree_walk(t: dict[str, Any]) -> list[dict[str, Any]]:
    """List a block tree's nodes, depth first.

    :param t: The root.
    :return: Every node."""
    return [t, *(x for k in t.get("children", []) for x in tree_walk(k))]
