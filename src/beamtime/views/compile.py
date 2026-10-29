"""Compiling views to block trees, and writing block trees and viewer settings back as views.

``compile_view`` turns an authored view into the tree the built-in default produces
(``{block, id, props, data, children}``), so the frontend renders both alike. ``from_tree`` goes
the other way for the default view, and ``apply_prefs`` folds a viewer's chart settings into a
view's body for "Save as view"."""

import posixpath
from typing import Any

from beamtime.format.ids import is_run_id
from beamtime.views import model as m
from beamtime.views.defaults import api, lower_is_better, node

RUNS_LIMIT = 10000


class Compiler:
    """Compiles one view for one page."""

    def __init__(self, *, view: m.View, path: str, draft: str | None = None) -> None:
        """Prepare compiling.

        :param view: The view.
        :param path: The page: a group below the log dir, or a run's path.
        :param draft: The draft's name when compiling a draft, so data files come from it."""
        self.view = view
        self.path = path
        self.draft = draft
        leaf = path.rsplit("/", 1)[-1]
        self.run = leaf if is_run_id(leaf) else None
        self.addable = False

    def tree(self) -> dict[str, Any]:
        """Compile the whole view.

        :return: The root node."""
        return node("section", "root", children=[self.compile(n) for n in self.view.body])

    def compile(self, n: m.Node) -> dict[str, Any]:
        """Compile one node and its children.

        :param n: The node.
        :return: The tree node."""
        common = {k: v for k, v in (("title", n.title), ("caption", n.caption)) if v is not None}
        if n.span != 1:
            common["span"] = n.span
        sel = self.selection(n)
        scope = self.scope_of(n.from_)
        match n:
            case m.Line():
                ys = [n.y] if isinstance(n.y, str) else n.y
                return self.line(n, ys, sel, common)
            case m.Scatter():
                fields = [n.x, n.y, *([n.color] if n.color else [])]
                call = api(
                    "runs",
                    sel
                    | {"select": fields, "limit": RUNS_LIMIT}
                    | ({"seeds": n.seeds} if n.seeds else {}),
                    scope,
                )
                return node(
                    "scatter",
                    n.id,
                    data={"main": call},
                    x=n.x,
                    y=n.y,
                    color=n.color,
                    x_scale=n.x_scale,
                    y_scale=n.y_scale,
                    fit=n.fit,
                    seeds=n.seeds,
                    **common,
                )
            case m.Bar():
                fields = [n.x, n.y, *([n.by] if n.by else [])]
                call = api("runs", sel | {"select": fields, "limit": RUNS_LIMIT}, scope)
                return node(
                    "bar",
                    n.id,
                    data={"main": call},
                    x=n.x,
                    y=n.y,
                    by=n.by,
                    error=n.error,
                    sort=n.sort,
                    **common,
                )
            case m.Histogram():
                call = api("data", sel | {"key": n.key, "step": n.step}, scope)
                return node("histogram", n.id, data={"main": call}, key=n.key, **common)
            case m.Stat():
                select = [*([n.field] if n.field else []), "run.status"]
                call = api("runs", sel | {"select": select, "limit": RUNS_LIMIT}, scope)
                return node(
                    "stat",
                    n.id,
                    data={"main": call},
                    field=n.field,
                    aggregate=n.aggregate,
                    lower=self.lower(n.field),
                    **common,
                )
            case m.Table():
                params = sel | {"sort": n.sort or ["-run.created_at"], "limit": n.limit}
                if n.columns:
                    params["select"] = n.columns
                data = {"main": api("runs", params, scope)}
                if n.sparkline:
                    data["spark"] = api("series", sel | {"y": [n.sparkline], "points": 48}, scope)
                return node(
                    "table",
                    n.id,
                    data=data,
                    columns=n.columns,
                    sparkline=n.sparkline,
                    highlight_best=n.highlight_best,
                    **common,
                )
            case m.DataTable():
                if n.file is not None:
                    params = {"view": self.path, "path": n.file}
                    call = api(
                        "file", params | ({"draft": self.draft} if self.draft else {}), scope
                    )
                else:
                    call = api(
                        "data", sel | {"key": n.key, "step": n.step, "limit": n.limit}, scope
                    )
                return node("data_table", n.id, data={"main": call}, limit=n.limit, **common)
            case m.Images() | m.Text():
                call = api("data", sel | {"key": n.key, "step": n.step}, scope)
                return node(m.block_of(n), n.id, data={"main": call}, **common)
            case m.Proposal():
                group = self.scope_of(n.of)
                data = {
                    "proposal": api("proposal_show", {"group": group}, group),
                    "check": api("check", {"group": group}, group),
                }
                return node("proposal", n.id, data=data, of=n.of, **common)
            case m.Memory():
                group = self.scope_of(n.of)
                call = api("memory_show", {"group": group}, group)
                return node("memory", n.id, data={"main": call}, **common)
            case m.Groups():
                call = api("groups", {"from": scope, "depth": 1}, scope)
                return node("groups", n.id, data={"main": call}, **common)
            case m.Timeline():
                params = sel | {"limit": n.limit} | ({"types": n.types} if n.types else {})
                return node(
                    "timeline", n.id, data={"main": api("timeline", params, scope)}, **common
                )
            case m.Notes():
                params = {"from": scope, "limit": n.limit, "full": True, "current": True}
                params |= {"types": n.types} if n.types else {}
                return node("notes", n.id, data={"main": api("notes", params, scope)}, **common)
            case m.Note():
                return node("note", n.id, text=n.text, kind=n.kind, **common)
            case m.Output():
                if (run := n.run or self.run) is None:
                    return node(
                        "note", n.id, kind="warning", text="output: name a run (run: <id>)."
                    )
                call = api("output", {"run": run, "tail": n.lines, "rank": n.rank}, self.path)
                return node("output", n.id, data={"main": call}, open=True, **common)
            case m.Custom():
                return node("custom", n.id, code=n.code, **common)
            case m.Section():
                kids = [self.compile(k) for k in n.children]
                return node("section", n.id, children=kids, open=n.open, **common)
            case m.Row():
                return node("row", n.id, children=[self.compile(k) for k in n.children], **common)
            case m.Grid():
                kids = [self.compile(k) for k in n.children]
                out = node(
                    "grid", n.id, children=kids, columns=n.columns, min_width=n.min_width, **common
                )
                # viewers add charts to the first grid of curves; new charts copy its first call.
                if not self.addable and (
                    first := next((k for k in kids if k["block"] == "line"), None)
                ):
                    self.addable = True
                    template = {
                        **first["data"]["main"],
                        "params": dict(first["data"]["main"]["params"]),
                    }
                    template["params"].pop("y")
                    out["props"] |= {"addable": True, "template": template}
                return out
            case m.Tabs():
                return node("tabs", n.id, children=[self.compile(k) for k in n.children], **common)
            case _:
                raise ValueError(f"no compiler for block {m.block_of(n)!r}")

    def line(
        self, n: m.Line, ys: list[str], sel: dict[str, Any], common: dict[str, Any]
    ) -> dict[str, Any]:
        """Compile a ``line`` block.

        :param n: The node.
        :param ys: Its metrics.
        :param sel: The selection parameters.
        :param common: The common props.
        :return: The tree node."""
        scope = self.scope_of(n.from_)
        params = sel | {"y": ys, "x": n.x, "points": 300, "band": n.band}
        if n.seeds:
            params["seeds"] = n.seeds
        if n.by:
            params["by"] = [n.by] if isinstance(n.by, str) else n.by
        if n.steps:
            params["steps"] = n.steps
        data = {"main": api("series", params, scope)}
        if n.color:
            data["colors"] = api("runs", sel | {"select": [n.color], "limit": RUNS_LIMIT}, scope)
        info = self.view.metrics.get(ys[0])
        guess = "log" if lower_is_better(ys[0]) and "loss" in ys[0] else "linear"
        scale = n.scale or (info.scale if info and info.scale else guess)
        return node(
            "line",
            n.id,
            data=data,
            y=ys[0] if len(ys) == 1 else ys,
            scale=scale,
            smooth=n.smooth or None,
            x=n.x if n.x != "_step" else None,
            outliers=n.outliers or None,
            color=n.color,
            **common,
        )

    def selection(self, n: m.Node) -> dict[str, Any]:
        """Make the parameters that pick a block's runs.

        :param n: The node.
        :return: ``from``, and ``where`` and ``depth`` when set."""
        where = self.view.filters | n.where
        return (
            {"from": self.scope_of(n.from_)}
            | ({"where": where} if where else {})
            | ({"depth": 1} if n.depth == 1 else {})
        )

    def scope_of(self, target: str) -> str:
        """Resolve ``from`` against the page.

        :param target: ``.``, a group relative to the page, ``/`` plus a group below the log dir,
            or a run id.
        :return: The group or run path, or the run id."""
        if target in (".", ""):
            return self.path
        if is_run_id(target.rstrip("/").rsplit("/", 1)[-1]):
            return target
        if target.startswith("/"):
            return target.strip("/") or "."
        return posixpath.normpath(posixpath.join(self.path, target))

    def lower(self, field: str | None) -> bool:
        """Tell whether lower values of a field are better.

        :param field: E.g. ``metric.val/loss.min``.
        :return: From the view's ``metrics``, else guessed from the name."""
        if not field:
            return False
        metric = field.removeprefix("metric.").rsplit(".", 1)[0]
        info = self.view.metrics.get(metric)
        if info is not None and info.higher_is_better is not None:
            return not info.higher_is_better
        return lower_is_better(metric)


def compile_view(view: m.View, *, path: str, draft: str | None = None) -> dict[str, Any]:
    """Compile a view for a page.

    :param view: The view.
    :param path: A group below the log dir, or a run's path.
    :param draft: The draft's name when compiling a draft.
    :return: The root node of the block tree."""
    return Compiler(view=view, path=path, draft=draft).tree()


def from_tree(tree: dict[str, Any], *, path: str) -> list[dict[str, Any]]:
    """Write the built-in default's block tree as a view body in YAML form.

    :param tree: The root node of a default view.
    :param path: The page it was built for.
    :return: The body's nodes, ``{block: props}``."""
    return [n for k in tree.get("children", []) if (n := yaml_node(k, path)) is not None]


def yaml_node(t: dict[str, Any], path: str) -> dict[str, Any] | None:
    """Write one default node in YAML form.

    :param t: The tree node.
    :param path: The page.
    :return: The node, or ``None`` for nodes without a YAML form."""
    p, block = t.get("props", {}), t["block"]
    params = t.get("data", {}).get("main", {}).get("params", {})
    out: dict[str, Any] = {"id": t["id"]}
    out |= {k: p[k] for k in ("title", "caption") if p.get(k) is not None}
    if params.get("depth") == 1:
        out["depth"] = 1
    match block:
        case "section" | "row" | "grid":
            if block == "section" and p.get("open") is False:
                out["open"] = False
            if block == "grid":
                out |= {k: p[k] for k in ("columns", "min_width") if p.get(k) is not None}
            kids = [n for k in t.get("children", []) if (n := yaml_node(k, path)) is not None]
            out["children"] = kids
        case "line":
            out["y"] = p["y"]
            out |= {k: params[k] for k in ("seeds", "by", "band") if params.get(k)}
            if out.get("band") == "minmax":
                del out["band"]
            if p.get("scale") == "log":
                out["scale"] = "log"
        case "table":
            out |= {"columns": p.get("columns"), "limit": params.get("limit", 100)}
            out |= {"sparkline": p["sparkline"]} if p.get("sparkline") else {}
            if (sort := params.get("sort")) and sort != ["-run.created_at"]:
                out["sort"] = sort
        case "images" | "text":
            out |= {"key": params["key"]} | (
                {"step": params["step"]} if params.get("step") != "last" else {}
            )
        case "notes":
            out["limit"] = params.get("limit", 3)
        case "output":
            out["lines"] = params.get("tail", 40)
        case "note":
            out |= {"text": p.get("text", ""), "kind": p.get("kind", "info")}
        case "memory" | "groups":
            pass
        case _:
            return None
    return {block: out}


def apply_prefs(body: list[dict[str, Any]], prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fold a viewer's chart settings and added charts into a view body.

    :param body: The body in YAML form; changed in place.
    :param prefs: ``{view, charts, added}`` as the web UI keeps them per page.
    :return: The body."""
    shared = clean(prefs.get("view") or {})
    charts = prefs.get("charts") or {}
    lines = [props for b, props in yaml_walk(body) if b == "line"]
    for props in lines:
        settings = shared | clean(charts.get(props.get("id"), {}))
        settle(props, settings)
    shown = {
        y for props in lines for y in ([props["y"]] if isinstance(props["y"], str) else props["y"])
    }
    added = [mt for mt in prefs.get("added") or [] if mt not in shown]
    if added:
        grid = next(
            (
                props
                for b, props in yaml_walk(body)
                if b == "grid" and any("line" in k for k in props.get("children", []))
            ),
            None,
        )
        new = []
        for mt in added:
            props = {"id": f"added-{m.slug(mt)}", "y": mt}
            settle(props, shared | clean(charts.get(f"added-{mt}", {})))
            new.append({"line": props})
        if grid is not None:
            grid.setdefault("children", []).extend(new)
        else:
            body.append({"grid": {"id": "added", "children": new}})
    return body


def settle(props: dict[str, Any], settings: dict[str, Any]) -> None:
    """Write chart settings into a ``line`` node's props.

    :param props: The node's props; changed in place.
    :param settings: The settings, as the web UI names them."""
    for key, value in settings.items():
        match key:
            case "y":
                if value:
                    props["y"] = value[0] if len(value) == 1 else list(value)
            case "by":
                props.pop("seeds", None)
                props.pop("by", None)
                if value == "seeds":
                    props["seeds"] = "config.seed"
                elif value:
                    props["by"] = [value]
            case "scale":
                # explicit, since a loss without a scale is drawn on a log axis.
                props["scale"] = value
            case "x" | "smooth" | "band" | "outliers":
                default = {"x": "_step", "smooth": 0, "band": "minmax", "outliers": False}[key]
                if value == default:
                    props.pop(key, None)
                else:
                    props[key] = value
            case _:
                pass


def clean(settings: dict[str, Any]) -> dict[str, Any]:
    """Drop unset settings.

    :param settings: The settings.
    :return: Those with a value, and ``by`` when set to none."""
    # by: null is a choice: each run, even where the view aggregates.
    return {k: v for k, v in settings.items() if v is not None or k == "by"}


def yaml_walk(body: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """List the nodes of a body in YAML form, depth first.

    :param body: The nodes.
    :return: ``(block, props)`` pairs; props are the nodes' own dicts."""
    out = []
    for n in body:
        ((block, props),) = n.items()
        if not isinstance(props, dict):
            props = {"children": props} if isinstance(props, list) else {}
            n[block] = props
        out.append((block, props))
        out += yaml_walk(props.get("children") or [])
    return out
