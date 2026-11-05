"""Compiling views, authored or the built-in default, to the block tree the frontend renders.

A block tree node is ``{block, id, props, data, children}``; ``data`` maps names to API calls
``{method, params, scope}``, where ``scope`` is the group or run path whose changes make the call
stale."""

import posixpath
from typing import TYPE_CHECKING, Any

from beamtime.format.ids import is_run_id
from beamtime.format.schema import SchemaError
from beamtime.views import model as m
from beamtime.views.defaults import lower_is_better

if TYPE_CHECKING:
    from beamtime.views.library import Library

RUNS_LIMIT = 10000


def node(block: str, id: str, *, children: list | None = None, data: dict | None = None,
         **props: Any) -> dict[str, Any]:  # fmt: skip
    """Make a block tree node.

    :param block: The block name, e.g. ``line``.
    :param id: The block's id.
    :param children: Child nodes of a layout block.
    :param data: Named API calls.
    :param props: The block's props.
    :return: The node."""
    out: dict[str, Any] = {"block": block, "id": id, "props": props}
    if children is not None:
        out["children"] = children
    if data is not None:
        out["data"] = data
    return out


def api(method: str, params: dict[str, Any], scope: str) -> dict[str, Any]:
    """Describe an API call a block makes.

    :param method: The API method (an MCP tool name).
    :param params: Its parameters.
    :param scope: The group or run path whose changes make the answer stale.
    :return: The call."""
    return {"method": method, "params": params, "scope": scope}


class Compiler:
    """Compiles one view for one page."""

    def __init__(
        self, *, view: m.View, path: str, draft: str | None = None, library: "Library | None" = None
    ) -> None:
        """Prepare compiling.

        :param view: The view.
        :param path: The page: a group below the log dir, or a run's path.
        :param draft: The draft's name when compiling a draft, so data files come from it.
        :param library: The page's library blocks, for views that use them."""
        self.view = view
        self.path = path
        self.draft = draft
        self.library = library
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
            case m.Markdown():
                return node("markdown", n.id, text=n.text, **common)
            case m.Note():
                return node("note", n.id, text=n.text, kind=n.kind, **common)
            case m.Output():
                if (run := n.run or self.run) is None:
                    return node(
                        "note", n.id, kind="warning", text="output: name a run (run: <id>)."
                    )
                call = api("output", {"run": run, "tail": n.lines, "rank": n.rank}, self.path)
                return node("output", n.id, data={"main": call}, open=n.open, **common)
            case m.Config():
                if (run := n.run or self.run) is not None:
                    group = self.path.rsplit("/", 1)[0] if "/" in self.path else "."
                    data = {
                        "main": api("card", {"run": run}, self.path),
                        "keys": api("keys", {"from": group}, group),
                    }
                    return node("config", n.id, data=data, mode="run", open=n.open, **common)
                data = {"main": api("keys", {"from": scope}, scope)}
                return node("config", n.id, data=data, mode="group", open=n.open, **common)
            case m.Custom():
                data = {name: self.declared(q, n) for name, q in n.queries.items()}
                code = {"view": self.path, "path": n.code} | (
                    {"draft": self.draft} if self.draft else {}
                )
                return node("custom", n.id, data=data, code=code, libs=n.libs, kit=n.kit, **common)
            case m.Use():
                return self.use(n, common)
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
        note = [
            *(["seed mean and range"] if n.seeds else []),
            *(["own runs"] if n.depth == 1 else []),
        ]
        return node(
            "line",
            n.id,
            data=data,
            y=ys[0] if len(ys) == 1 else ys,
            scale=scale,
            smooth=n.smooth or None,
            x=n.x if n.x != "_step" else None,
            outliers=n.outliers or None,
            ymin=n.ymin,
            ymax=n.ymax,
            raw=None if n.raw else False,
            legend=None if n.legend else False,
            color=n.color,
            note=", ".join(note) or None,
            **common,
        )

    def use(self, n: m.Use, common: dict[str, Any]) -> dict[str, Any]:
        """Compile a library block's use to a custom block with its params filled in.

        :param n: The node.
        :param common: Its title, caption and span.
        :return: The tree node.
        :raises SchemaError: If the page has no such block or the params don't fit."""
        from beamtime.views import library

        if self.library is None:
            raise SchemaError(f"{n.id}: library block {n.name!r} needs the page's library")
        found = self.library.get(n.name, self.view.uses.get(n.name))
        if errors := library.problems(found.block, n.params):
            raise SchemaError(f"{n.id}: " + "; ".join(errors))
        queries = library.queries_for(found.block, n.params)
        data = {name: self.declared(q, n) for name, q in queries.items()}
        b = found.block
        lib = {"name": n.name, "version": found.version}
        params = {k: n.params.get(k, p.default) for k, p in b.params.items()}
        return node(
            "custom",
            n.id,
            data=data,
            code=found.code_ref,
            libs=b.libs,
            kit=b.kit,
            library=lib,
            params=params,
            **common,
        )

    def declared(self, query: dict[str, Any], n: m.Node) -> dict[str, Any]:
        """Compile a custom block's declared query to an API call.

        ``$name`` placeholders stay in the parameters; the frame fills them at runtime.

        :param query: One kind and its parameters, e.g. ``{"runs": {"select": [...]}}``.
        :param n: The node, for its ``from`` and ``where``.
        :return: The call."""
        ((kind, params),) = query.items()
        params = dict(params or {})
        if kind == "file":
            draft = {"draft": self.draft} if self.draft else {}
            return api("file", {"view": self.path, "path": params["path"]} | draft, self.path)
        sel = self.selection(n)
        target = params.pop("from", None)
        if isinstance(target, str) and not target.startswith("$"):
            sel["from"] = self.scope_of(target)
        elif target is not None:
            sel["from"] = target
        if where := params.pop("where", None):
            sel["where"] = sel.get("where", {}) | where
        return api(kind, sel | params, self.path)

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


def compile_view(
    view: m.View, *, path: str, draft: str | None = None, library: "Library | None" = None
) -> dict[str, Any]:
    """Compile a view for a page.

    :param view: The view.
    :param path: A group below the log dir, or a run's path.
    :param draft: The draft's name when compiling a draft.
    :param library: The page's library blocks.
    :return: The root node of the block tree.
    :raises SchemaError: If a library block is missing or its params don't fit."""
    return Compiler(view=view, path=path, draft=draft, library=library).tree()


def walk_tree(t: dict[str, Any]) -> list[dict[str, Any]]:
    """List a block tree's nodes, depth first.

    :param t: The root.
    :return: Every node."""
    return [t, *(x for k in t.get("children", []) for x in walk_tree(k))]
