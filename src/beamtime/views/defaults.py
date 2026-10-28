"""The built-in default view, built as a block tree from what a folder or run logged.

A block tree node is ``{block, id, props, data, children}``; ``data`` maps names to API
calls ``{method, params, scope}``, where ``scope`` is the folder or run path whose
changes make the call stale. Authored views (M6) compile to the same tree."""

from typing import Any

from beamtime.format.ids import is_run_id
from beamtime.ops import call
from beamtime.ops.context import Context

MAX_LINES = 8
SEED_GROUPING_ABOVE = 8
TABLE_LIMIT = 100
LOWER_IS_BETTER = ("loss", "err", "ppl", "perplexity", "nll", "mse", "mae", "wer", "cer")


def default_view(ctx: Context, path: str) -> dict[str, Any]:
    """Build the default view of a folder or run.

    :param ctx: The operation context.
    :param path: The folder below the log dir (``.`` for the log dir), or a run's path.
    :return: The root node of the block tree."""
    if is_run_id(path.rsplit("/", 1)[-1]):
        return run_view(ctx, path)
    return folder_view(ctx, path)


def folder_view(ctx: Context, path: str) -> dict[str, Any]:
    """Build the default view of a folder.

    :param ctx: The operation context.
    :param path: The folder below the log dir.
    :return: The root node."""
    folder = call("folders", {"from": path, "depth": 0}, ctx)
    row = dict(zip(folder["columns"], folder["rows"][0], strict=True)) if folder["rows"] else {}
    children: list[dict[str, Any]] = []
    if row.get("proposal"):
        children.append(proposal_block(path))
    if not row.get("runs"):
        children.append(node("note", "empty", text=EMPTY, kind="info"))
        return node("section", "root", children=children)
    if row.get("direct", 0) < row["runs"]:
        children.append(
            node(
                "folders",
                "subfolders",
                title="Folders",
                data={"main": api("folders", {"from": path, "depth": 1}, path)},
            )
        )
    keys = call("keys", {"from": path}, ctx)
    metrics = ordered_metrics(keys)
    varying = [
        k for k, _, values in keys["config"]["rows"] if isinstance(values, list) and len(values) > 1
    ]
    main = metrics[0] if metrics else None
    children.append(stats(path, main, row["runs"]))
    if direct := row.get("direct", 0):
        # curves show only the folder's own runs; runs in subfolders belong to their folders.
        own = direct < row["runs"]
        if own:
            keys = call("keys", {"from": path, "depth": 1}, ctx)
            metrics = ordered_metrics(keys)
        many = "config.seed" in varying and direct > SEED_GROUPING_ABOVE
        seeds = "config.seed" if many else None
        lines = [line(path, m, seeds, own) for m in metrics[:MAX_LINES]]
        if lines:
            children.append(node("grid", "curves", children=lines, min_width=360))
    select = ["run.name", "run.status", *varying, *[f"metric.{m}.last" for m in metrics[:4]]]
    children.append(
        node(
            "table",
            "runs",
            title="Runs",
            columns=select,
            data={
                "main": api(
                    "runs",
                    {
                        "from": path,
                        "select": select,
                        "sort": ["-run.created_at"],
                        "limit": TABLE_LIMIT,
                    },
                    path,
                )
            },  # fmt: skip
        )
    )
    chain = call("memory show", {"folder": path}, ctx)["chain"]
    if any(m["folder"] == path for m in chain):
        children.append(
            node(
                "memory",
                "memory",
                title="Memory",
                data={"main": api("memory_show", {"folder": path}, path)},
            )
        )
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
    children = [stats(path, metrics[0] if metrics else None, 1)]
    if metrics:
        children.append(
            node("grid", "curves", children=[line(path, m, None) for m in metrics], min_width=360)
        )
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


EMPTY = (
    "No runs here yet. Runs appear once a script calls beamtime.init() with this folder as its dir."
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
    :param scope: The folder or run path whose changes make the answer stale.
    :return: The call."""
    return {"method": method, "params": params, "scope": scope}


def proposal_block(path: str) -> dict[str, Any]:
    """Make the proposal block of a folder.

    :param path: The folder.
    :return: The node."""
    return node(
        "proposal",
        "proposal",
        data={
            "proposal": api("proposal_show", {"folder": path}, path),
            "check": api("check", {"folder": path}, path),
        },
    )


def stats(path: str, main: str | None, runs: int) -> dict[str, Any]:
    """Make the row of stat tiles: run counts and the best value of the main metric.

    :param path: The folder or run path.
    :param main: The main metric, if any.
    :param runs: How many runs are in scope.
    :return: The row node."""
    best = "min" if main and lower_is_better(main) else "max"
    select = ["run.status", *([f"metric.{main}.{best}"] if main else [])]
    source = {"main": api("runs", {"from": path, "select": select, "limit": 10_000}, path)}
    tiles = []
    if runs > 1:
        tiles += [
            node("stat", "runs", title="Runs", aggregate="count", data=source),
            node("stat", "running", title="Running", aggregate="count",
                 where={"run.status": "running"}, data=source),
            node("stat", "failed", title="Failed, killed or lost", aggregate="count",
                 where={"run.status": ["failed", "killed", "lost"]}, data=source),
        ]  # fmt: skip
    else:
        tiles.append(node("stat", "status", title="Status", field="run.status",
                          aggregate="last", data=source))  # fmt: skip
    if main:
        tiles.append(node("stat", "best", title=f"{best} {main}", field=f"metric.{main}.{best}",
                          aggregate="min" if best == "min" else "max", data=source))  # fmt: skip
    return node("row", "stats", children=tiles)


def line(path: str, metric: str, seeds: str | None, own: bool = False) -> dict[str, Any]:
    """Make the line block of one metric.

    :param path: The folder or run path.
    :param metric: The metric key.
    :param seeds: ``config.seed`` to average over seeds, or ``None`` for one curve per run.
    :param own: Whether to show only the runs directly in the folder.
    :return: The node."""
    params: dict[str, Any] = {"from": path, "y": [metric], "points": 300}
    if own:
        params["depth"] = 1
    if seeds:
        params |= {"seeds": seeds, "band": "minmax"}
    scale = "log" if lower_is_better(metric) and "loss" in metric else "linear"
    caption = f"{metric} over steps" + (", mean and range over seeds" if seeds else "")
    caption += ", runs directly in this folder" if own else ""
    return node(
        "line",
        f"line-{slug(metric)}",
        y=metric,
        scale=scale,
        caption=caption,
        data={"main": api("series", params, path)},
    )


def ordered_metrics(keys: dict[str, Any]) -> list[str]:
    """Order a folder's metrics for display: validation and test first, then the rest.

    :param keys: The ``keys`` answer.
    :return: The metric keys."""
    names = [r[0] for r in keys["metrics"]["rows"]]
    rank = {"val": 0, "valid": 0, "eval": 0, "test": 1, "train": 2}
    return sorted(names, key=lambda k: (rank.get(k.split("/", 1)[0], 3) if "/" in k else 4, k))


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
