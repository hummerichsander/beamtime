"""The built-in default view, built as a block tree from what a group or run logged.

A block tree node is ``{block, id, props, data, children}``; ``data`` maps names to API
calls ``{method, params, scope}``, where ``scope`` is the group or run path whose
changes make the call stale. Authored views (M6) compile to the same tree."""

from typing import Any

from beamtime.format.ids import is_run_id
from beamtime.ops import call
from beamtime.ops.context import Context

ESSENTIAL = 4
SEED_GROUPING_ABOVE = 8
TABLE_LIMIT = 100
RECENT = 10
NOTES = 3
LOWER_IS_BETTER = ("loss", "err", "ppl", "perplexity", "nll", "mse", "mae", "wer", "cer")
EVAL_PREFIXES = ("val", "valid", "eval", "test")


def default_view(ctx: Context, path: str) -> dict[str, Any]:
    """Build the default view of a group or run.

    :param ctx: The operation context.
    :param path: The group below the log dir (``.`` for the log dir), or a run's path.
    :return: The root node of the block tree."""
    if is_run_id(path.rsplit("/", 1)[-1]):
        return run_view(ctx, path)
    return group_view(ctx, path)


def group_view(ctx: Context, path: str) -> dict[str, Any]:
    """Build the default view of a group: what it shows, concisely.

    :param ctx: The operation context.
    :param path: The group below the log dir.
    :return: The root node."""
    group = call("groups", {"from": path, "depth": 0}, ctx)
    row = dict(zip(group["columns"], group["rows"][0], strict=True)) if group["rows"] else {}
    # the header states the proposal and its predictions; the body starts with the data.
    children: list[dict[str, Any]] = []
    if not row.get("runs"):
        children.append(node("note", "empty", text=EMPTY, kind="info"))
        return node("section", "root", children=children)
    direct = row.get("direct", 0)
    if direct < row["runs"]:
        children.append(
            node(
                "groups",
                "subgroups",
                title="Groups",
                data={"main": api("groups", {"from": path, "depth": 1}, path)},
            )
        )
    keys = call("keys", {"from": path}, ctx)
    varying = varying_config(keys)
    main = (essential(ordered_metrics(keys)) or [None])[0]
    if direct:
        # curves show only the group's own runs; runs in subgroups belong to their groups.
        own = direct < row["runs"]
        own_keys = call("keys", {"from": path, "depth": 1}, ctx) if own else keys
        many = "config.seed" in varying and direct > SEED_GROUPING_ABOVE
        children += curves(path, ordered_metrics(own_keys), "config.seed" if many else None, own)
    if direct:
        select = ["run.name", "run.status", *varying, *([f"metric.{main}.last"] if main else [])]
    else:
        # runs from different experiments share no config or metric: say where and when instead.
        select = ["run.name", "run.status", "run.group", "run.created_at"]
        main = None
    limit = TABLE_LIMIT if direct else RECENT
    children.append(
        node(
            "table",
            "runs",
            title="Runs" if direct else "Recent runs",
            columns=select,
            sparkline=main,
            data={
                "main": api("runs", {"from": path, "select": select, "sort": ["-run.created_at"],
                                     "limit": limit}, path),
                **({"spark": api("series", {"from": path, "y": [main], "points": 48}, path)}
                   if main else {}),
            },
        )
    )  # fmt: skip
    chain = call("memory show", {"group": path}, ctx)["chain"]
    if any(m["group"] == path for m in chain):
        children.append(
            node(
                "memory",
                "memory",
                title="Memory",
                data={"main": api("memory_show", {"group": path}, path)},
            )
        )
    notes = call("notes", {"from": path, "limit": 1}, ctx)
    if notes["meta"]["matched"]:
        latest = api("notes", {"from": path, "limit": NOTES, "full": True}, path)
        children.append(node("notes", "notes", title="Notes", data={"main": latest}))
    return node("section", "root", children=children)


def run_view(ctx: Context, path: str) -> dict[str, Any]:
    """Build the default view of a run.

    :param ctx: The operation context.
    :param path: The run's path below the log dir.
    :return: The root node."""
    run_id = path.rsplit("/", 1)[-1]
    keys = call("keys", {"from": run_id}, ctx)
    metrics = ordered_metrics(keys)
    status = next(iter(keys["status"]), None)
    children = curves(path, metrics, None, False)
    for key, kind, _, _ in keys["data"]["rows"]:
        params = {"from": run_id, "key": key, "step": "last"}
        match kind:
            case "image":
                block = "images"
            case "text":
                block = "text"
            case _:
                continue
        children.append(node(block, f"{block}-{slug(key)}", title=key,
                             data={"main": api("data", params, path)}))  # fmt: skip
    children.append(
        node(
            "output",
            "output",
            title="Output",
            open=status in ("failed", "killed", "lost") or not metrics,
            data={"main": api("output", {"run": run_id, "tail": 40}, path)},
        )
    )
    return node("section", "root", children=children)


def summary(ctx: Context, path: str) -> dict[str, Any] | None:
    """Find the main metric and its best run, for the header's facts line.

    :param ctx: The operation context.
    :param path: A group or run path.
    :return: ``{metric, stat, value, run, name, config}``, or ``None`` without metrics or for
        a group without runs of its own."""
    run_id = path.rsplit("/", 1)[-1]
    scope = run_id if is_run_id(run_id) else path
    if scope == path:
        # a group whose runs all sit in subgroups mixes experiments; no single best there.
        group = call("groups", {"from": path, "depth": 0}, ctx)
        direct = group["columns"].index("direct")
        if not group["rows"] or not group["rows"][0][direct]:
            return None
    keys = call("keys", {"from": scope}, ctx)
    main = (essential(ordered_metrics(keys)) or [None])[0]
    if main is None:
        return None
    stat = "min" if lower_is_better(main) else "max"
    field = f"metric.{main}.{stat}"
    varying = varying_config(keys)
    query = {
        "from": scope,
        "select": ["run.name", field, *varying],
        "where": {field: {"exists": True}},
        "sort": [field if stat == "min" else f"-{field}"],
        "limit": 1,
    }
    answer = call("runs", query, ctx)
    if not answer["rows"]:
        return None
    best = dict(zip(answer["columns"], answer["rows"][0], strict=True))
    return {
        "metric": main,
        "stat": stat,
        "value": best[field],
        "run": best["run.id"],
        "name": best["run.name"],
        "config": {
            k.removeprefix("config."): best[k]
            for k in varying
            if k != "config.seed" and best.get(k) is not None
        },
    }


def curves(path: str, metrics: list[str], seeds: str | None, own: bool) -> list[dict[str, Any]]:
    """Make the essential charts, and the rest in a collapsed section.

    :param path: The group or run path.
    :param metrics: The metrics, ordered.
    :param seeds: ``config.seed`` to average over seeds, or ``None``.
    :param own: Whether to show only the runs directly in the group.
    :return: The nodes: a grid, and a section with more."""
    first = essential(metrics)
    rest = [m for m in metrics if m not in first]
    out = []
    if first:
        out.append(node("grid", "curves", children=[line(path, m, seeds, own) for m in first],
                        min_width=420))  # fmt: skip
    if rest:
        grid = node("grid", "more-curves", children=[line(path, m, seeds, own) for m in rest],
                    min_width=420)  # fmt: skip
        out.append(node("section", "more", title=f"More metrics ({len(rest)})", open=False,
                        children=[grid]))  # fmt: skip
    return out


EMPTY = (
    "No runs here yet. Runs appear once a script calls beamtime.init() with this group as its dir."
)


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


def line(path: str, metric: str, seeds: str | None, own: bool = False) -> dict[str, Any]:
    """Make the line block of one metric.

    :param path: The group or run path.
    :param metric: The metric key.
    :param seeds: ``config.seed`` to average over seeds, or ``None`` for one curve per run.
    :param own: Whether to show only the runs directly in the group.
    :return: The node."""
    params: dict[str, Any] = {"from": path, "y": [metric], "points": 300}
    if own:
        params["depth"] = 1
    if seeds:
        params |= {"seeds": seeds, "band": "minmax"}
    scale = "log" if lower_is_better(metric) and "loss" in metric else "linear"
    note = ", ".join([*(["seed mean and range"] if seeds else []), *(["own runs"] if own else [])])
    return node(
        "line",
        f"line-{slug(metric)}",
        y=metric,
        scale=scale,
        note=note or None,
        data={"main": api("series", params, path)},
    )


def ordered_metrics(keys: dict[str, Any]) -> list[str]:
    """Order a group's metrics for display: validation and test first, then the rest.

    :param keys: The ``keys`` answer.
    :return: The metric keys."""
    names = [r[0] for r in keys["metrics"]["rows"]]
    rank = {"val": 0, "valid": 0, "eval": 0, "test": 1, "train": 2}
    return sorted(names, key=lambda k: (rank.get(k.split("/", 1)[0], 3) if "/" in k else 4, k))


def essential(metrics: list[str]) -> list[str]:
    """Pick the metrics worth a chart up front: evaluation metrics, then training losses.

    :param metrics: The metrics, ordered.
    :return: At most four; schedules and diagnostics (lr, grad norms) are left for "more"."""
    prefix = lambda m: m.split("/", 1)[0] if "/" in m else ""  # noqa: E731
    evals = [m for m in metrics if prefix(m) in EVAL_PREFIXES]
    losses = [m for m in metrics if prefix(m) == "train" and "loss" in m]
    plain = [m for m in metrics if not prefix(m) and lower_is_better(m) or m in ("acc", "accuracy")]
    picked = list(dict.fromkeys([*evals, *losses, *plain]))
    return picked[:ESSENTIAL] or metrics[:ESSENTIAL]


def varying_config(keys: dict[str, Any]) -> list[str]:
    """List the config keys whose values differ between runs.

    :param keys: The ``keys`` answer.
    :return: The fields, e.g. ``config.lr``."""
    rows = keys["config"]["rows"]
    return [k for k, _, values in rows if isinstance(values, list) and len(values) > 1]


def lower_is_better(metric: str) -> bool:
    """Guess a metric's direction from its name.

    :param metric: The metric key.
    :return: Whether lower values are better."""
    leaf = metric.rsplit("/", 1)[-1].lower()
    return any(word in leaf for word in LOWER_IS_BETTER)


def slug(key: str) -> str:
    """Turn a key into an id.

    :param key: E.g. ``val/acc``.
    :return: E.g. ``val-acc``."""
    return "".join(ch if ch.isalnum() else "-" for ch in key).strip("-")
