"""The built-in default view: an ``m.View`` made from what a group or run logged, compiled like any
authored view, and written out as one when a draft starts from it."""

from typing import Any

from beamtime.format.ids import is_run_id
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.views import model as m

ESSENTIAL = 4
SEED_GROUPING_ABOVE = 8
TABLE_LIMIT = 100
RECENT = 10
NOTES = 3
LOWER_IS_BETTER = ("loss", "err", "ppl", "perplexity", "nll", "mse", "mae", "wer", "cer")
EVAL_PREFIXES = ("val", "valid", "eval", "test")
# the SDK's system metrics: their own collapsed section, never a headline chart.
SYSTEM = "sys/"
EMPTY = (
    "No runs here yet. Runs appear once a script calls beamtime.init() with this group as its dir."
)


def default_view(ctx: Context, path: str) -> m.View:
    """Build the default view of a group or run.

    :param ctx: The operation context.
    :param path: The group below the log dir (``.`` for the log dir), or a run's path.
    :return: The view."""
    if is_run_id(path.rsplit("/", 1)[-1]):
        return m.View(body=run_body(ctx, path))
    return m.View(body=group_body(ctx, path))


def group_body(ctx: Context, path: str) -> list[m.Block]:
    """Build the default view of a group: what it shows, concisely.

    :param ctx: The operation context.
    :param path: The group below the log dir.
    :return: The body."""
    runs, direct = counts(ctx, path)
    # the header states the proposal and its predictions; the body starts with the data.
    if not runs:
        return [m.Note(id="empty", text=EMPTY), *record(run=False)]
    body: list[m.Block] = []
    if direct < runs:
        body.append(m.Groups(id="subgroups", title="Groups"))
    keys = call("keys", {"from": path}, ctx)
    varying = varying_config(keys)
    main = (essential(ordered_metrics(keys)) or [None])[0]
    if direct:
        # curves show only the group's own runs; runs in subgroups belong to their groups.
        own = direct < runs
        own_keys = call("keys", {"from": path, "depth": 1}, ctx) if own else keys
        many = "config.seed" in varying and direct > SEED_GROUPING_ABOVE
        body += curves(ordered_metrics(own_keys), "config.seed" if many else None, own)
        columns = ["run.name", "run.status", *varying, *([f"metric.{main}.last"] if main else [])]
        table = m.Table(id="runs", title="Runs", columns=columns, limit=TABLE_LIMIT, sparkline=main)
        body.append(table)
    else:
        # runs from different experiments share no config or metric: say where and when instead.
        columns = ["run.name", "run.status", "run.group", "run.created_at"]
        body.append(m.Table(id="runs", title="Recent runs", columns=columns, limit=RECENT))
    return [*body, *record(run=False)]


def record(*, run: bool) -> list[m.Block]:
    """Make the notes and memory blocks every page has, so they look the same at every level.

    :param run: Whether the page is a run's, which has notes but no memory.
    :return: The blocks."""
    notes = m.Notes(id="notes", title="Notes", limit=NOTES)
    return [notes] if run else [m.Memory(id="memory", title="Memory"), notes]


def run_body(ctx: Context, path: str) -> list[m.Block]:
    """Build the default view of a run.

    :param ctx: The operation context.
    :param path: The run's path below the log dir.
    :return: The body."""
    run_id = path.rsplit("/", 1)[-1]
    keys = call("keys", {"from": run_id}, ctx)
    metrics = ordered_metrics(keys)
    status = next(iter(keys["status"]), None)
    body = curves(metrics, None, False)
    for key, kind, _, _ in keys["data"]["rows"]:
        match kind:
            case "image":
                body.append(m.Images(id=f"images-{m.slug(key)}", title=key, key=key))
            case "text":
                body.append(m.Text(id=f"text-{m.slug(key)}", title=key, key=key))
            case _:
                continue
    body += record(run=True)
    opened = status in ("failed", "killed", "lost") or not metrics
    body.append(m.Output(id="output", title="Output", open=opened))
    return body


def summary(ctx: Context, path: str, lead: tuple[str, bool] | None = None) -> dict[str, Any] | None:
    """Find the main metric and its best run, for the header's facts line.

    :param ctx: The operation context.
    :param path: A group or run path.
    :param lead: The shown view's lead metric and whether lower is better; guessed without.
    :return: ``{metric, stat, value, run, name, config}``, or ``None`` without metrics or for
        a group without runs of its own."""
    run_id = path.rsplit("/", 1)[-1]
    scope = run_id if is_run_id(run_id) else path
    # a group whose runs all sit in subgroups mixes experiments; no single best there.
    if scope == path and not counts(ctx, path)[1]:
        return None
    keys = call("keys", {"from": scope}, ctx)
    logged = ordered_metrics(keys)
    if lead is not None and lead[0] in logged:
        main, lower = lead
    else:
        main = (essential(logged) or [None])[0]
        lower = main is not None and lower_is_better(main)
    if main is None:
        return None
    stat = "min" if lower else "max"
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


def counts(ctx: Context, path: str) -> tuple[int, int]:
    """Count a group's runs, all and its own, without computing its research status.

    :param ctx: The operation context.
    :param path: The group.
    :return: Runs at or below the group, and runs directly in it."""
    return count(ctx, path, "all"), count(ctx, path, 1)


def count(ctx: Context, path: str, depth: Any) -> int:
    """Count a group's runs to some depth.

    :param ctx: The operation context.
    :param path: The group.
    :param depth: ``all``, or 1 for the group's own runs.
    :return: The number of runs."""
    query = {"from": path, "depth": depth, "select": ["run.status"], "limit": 1}
    return call("runs", query, ctx)["meta"]["matched"]


def curves(metrics: list[str], seeds: str | None, own: bool) -> list[m.Block]:
    """Make the essential charts, and the rest and the system metrics in collapsed sections.

    :param metrics: The metrics, ordered.
    :param seeds: ``config.seed`` to average over seeds, or ``None``.
    :param own: Whether to show only the runs directly in the group.
    :return: The blocks: a grid, and sections with more."""
    first = essential(metrics)
    system = [k for k in metrics if k.startswith(SYSTEM)]
    rest = [k for k in metrics if k not in first and k not in system]
    out: list[m.Block] = []
    if first:
        # the first grid of curves is where viewers add charts.
        out.append(m.Grid(id="curves", children=[line(k, seeds, own) for k in first]))
    for id_, title, shown, by in (
        ("more", "More metrics", rest, seeds),
        ("system", "System", system, None),
    ):
        if shown:
            grid = m.Grid(id=f"{id_}-curves", children=[line(k, by, own) for k in shown])
            out.append(
                m.Section(id=id_, title=f"{title} ({len(shown)})", open=False, children=[grid])
            )
    return out


def line(metric: str, seeds: str | None, own: bool) -> m.Line:
    """Make the line block of one metric.

    :param metric: The metric key.
    :param seeds: ``config.seed`` to average over seeds, or ``None`` for one curve per run.
    :param own: Whether to show only the runs directly in the group.
    :return: The block."""
    return m.Line(id=f"line-{m.slug(metric)}", y=metric, seeds=seeds, depth=1 if own else "all")


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
    metrics = [k for k in metrics if not k.startswith(SYSTEM)]
    evals = [k for k in metrics if prefix(k) in EVAL_PREFIXES]
    losses = [k for k in metrics if prefix(k) == "train" and "loss" in k]
    plain = [k for k in metrics if not prefix(k) and lower_is_better(k) or k in ("acc", "accuracy")]
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


def prefix(metric: str) -> str:
    """Name a metric's namespace.

    :param metric: E.g. ``val/acc``.
    :return: E.g. ``val``; empty without one."""
    return metric.split("/", 1)[0] if "/" in metric else ""
