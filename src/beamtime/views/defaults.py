"""The built-in default view: an ``m.View`` made from what a group or run logged, compiled like any
authored view, and written out as one when a draft starts from it."""

from collections import Counter
from typing import Any

from beamtime.format.ids import is_run_id
from beamtime.ops import call
from beamtime.ops.context import Context
from beamtime.views import model as m

OPEN_SECTIONS = 2
SEED_GROUPING_ABOVE = 8
TABLE_LIMIT = 100
RECENT = 10
NOTES = 3
LOWER_IS_BETTER = ("loss", "err", "ppl", "perplexity", "nll", "mse", "mae", "wer", "cer")
EVAL_PREFIXES = ("val", "valid", "eval", "test", "validation")
TRAIN_PREFIXES = ("train", "training")
# the SDK's system metrics: their own collapsed section, last.
SYSTEM = "sys"
CLOCKS = ("epoch", "global_step", "trainer/global_step")
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
    main = main_metric(ctx, path, keys)
    if direct:
        # curves show only the group's own runs; runs in subgroups belong to their groups.
        own = direct < runs
        own_keys = call("keys", {"from": path, "depth": 1}, ctx) if own else keys
        many = "config.seed" in varying and direct > SEED_GROUPING_ABOVE
        body += curves(ordered_metrics(own_keys), "config.seed" if many else None, own, main)
        if varying:
            body.append(m.Config(id="hyperparameters", title="Hyperparameters"))
        code = ["run.code"] if keys.get("codes") else []
        clock = ["run.progress"] if "epoch" in ordered_metrics(own_keys) else []
        columns = [
            "run.name",
            "run.status",
            *clock,
            *varying,
            *code,
            *([f"metric.{main}.last"] if main else []),
        ]
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
    body = curves(metrics, None, False, main_metric(ctx, path, keys))
    for key, kind, _, _ in keys["data"]["rows"]:
        match kind:
            case "image":
                body.append(m.Images(id=f"images-{m.slug(key)}", title=key, key=key))
            case "text":
                body.append(m.Text(id=f"text-{m.slug(key)}", title=key, key=key))
            case _:
                continue
    body.append(m.Config(id="config", title="Config", open=False))
    body += record(run=True)
    opened = status in ("failed", "killed", "lost") or not metrics
    body.append(m.Output(id="output", title="Output", open=opened))
    return body


def summary(
    ctx: Context, path: str, lead: tuple[str, bool, str | None] | None = None
) -> dict[str, Any] | None:
    """Find the main metric and its best run, for the header's facts line.

    :param ctx: The operation context.
    :param path: A group or run path.
    :param lead: The shown view's lead metric, whether lower is better and its label; guessed
        without.
    :return: ``{metric, label, stat, value, run, name, config}``, or ``None`` without metrics or
        for a group without runs of its own."""
    run_id = path.rsplit("/", 1)[-1]
    scope = run_id if is_run_id(run_id) else path
    # a group whose runs all sit in subgroups mixes experiments; no single best there.
    if scope == path and not counts(ctx, path)[1]:
        return None
    keys = call("keys", {"from": scope}, ctx)
    if lead is not None and lead[0] in ordered_metrics(keys):
        main, lower, label = lead
    else:
        main, label = main_metric(ctx, path, keys), None
        lower = main is not None and lower_is_better(main)
    if main is None:
        return None
    stat = "min" if lower else "max"
    field = f"metric.{main}.{stat}"
    varying = [k for k in varying_config(keys) if k != "config.seed"][:3]
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
        "label": label,
        "stat": stat,
        "value": best[field],
        "run": best["run.id"],
        "name": best["run.name"],
        "config": {k.removeprefix("config."): best[k] for k in varying if best.get(k) is not None},
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


def curves(
    metrics: list[str], seeds: str | None, own: bool, lead: str | None = None
) -> list[m.Block]:
    """Make one chart per metric, in sections by metric prefix.

    :param metrics: The metrics, ordered.
    :param seeds: ``config.seed`` to average over seeds, or ``None``.
    :param own: Whether to show only the runs directly in the group.
    :param lead: The main metric; its prefix comes first.
    :return: The sections: the lead's prefix, evaluation, training, the other prefixes, ``Other``
        (unprefixed metrics and prefixes of one metric), then ``System``; the first two open. A
        single section is a plain grid. Clocks (``epoch``) get no chart: they are an x axis and a
        progress fact."""
    metrics = [k for k in metrics if k not in CLOCKS]
    sizes = Counter(prefix(k) for k in metrics)
    groups: dict[str, list[str]] = {}
    for k in metrics:
        name = prefix(k) if sizes[prefix(k)] > 1 or prefix(k) == SYSTEM else ""
        groups.setdefault(name, []).append(k)
    order = sorted(groups, key=lambda name: section_rank(name, prefix(lead or "")))
    if len(order) == 1:
        return [m.Grid(id="curves", children=[line(k, seeds, own) for k in metrics])]
    out: list[m.Block] = []
    for i, name in enumerate(order):
        title = {"": "Other", SYSTEM: "System"}.get(name, name)
        id_ = f"charts-{m.slug(name or 'unprefixed')}"
        grid = m.Grid(id=f"{id_}-curves", children=[line(k, seeds, own) for k in groups[name]])
        opened = i < OPEN_SECTIONS and name != SYSTEM
        section = m.Section(
            id=id_, title=f"{title} ({len(groups[name])})", open=opened, children=[grid]
        )
        out.append(section)
    return out


def section_rank(name: str, lead: str) -> int:
    """Rank a chart section: the lead's, evaluation, training, other prefixes, Other, System.

    :param name: The section's prefix; empty for ``Other``.
    :param lead: The prefix of the main metric.
    :return: The rank; lower comes first."""
    if name == SYSTEM:
        return 5
    if not name:
        return 4
    if name == lead:
        return 0
    return 1 if name in EVAL_PREFIXES else 2 if name in TRAIN_PREFIXES else 3


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
    rank = {"val": 0, "valid": 0, "eval": 0, "validation": 0, "test": 1, "train": 2, "training": 2}
    return sorted(names, key=lambda k: (rank.get(k.split("/", 1)[0], 3) if "/" in k else 4, k))


def leading(metrics: list[str]) -> list[str]:
    """Pick the metrics fit to lead a page: evaluation metrics, training losses, plain losses.

    :param metrics: The metrics, ordered.
    :return: Those metrics in that order; system metrics never lead."""
    metrics = [k for k in metrics if not k.startswith(f"{SYSTEM}/")]
    evals = [k for k in metrics if prefix(k) in EVAL_PREFIXES]
    losses = [k for k in metrics if prefix(k) in TRAIN_PREFIXES and "loss" in k]
    plain = [k for k in metrics if not prefix(k) and lower_is_better(k) or k in ("acc", "accuracy")]
    return list(dict.fromkeys([*evals, *losses, *plain]))


def main_metric(ctx: Context, path: str, keys: dict[str, Any]) -> str | None:
    """Pick the leading metric: the group's prediction, else the best-ranked non-constant one.

    :param ctx: The operation context.
    :param path: A group or run path.
    :param keys: The ``keys`` answer for that path.
    :return: The metric key, or ``None`` without metrics."""
    from beamtime.guide import proposed

    metrics = ordered_metrics(keys)
    if not metrics:
        return None
    run_id = path.rsplit("/", 1)[-1]
    if is_run_id(run_id):
        group = path.rsplit("/", 1)[0] if "/" in path else "."
    else:
        group = path
    if (main := proposed(ctx, group, metrics)) is not None:
        return main
    constant = metric_column(keys, "constant")
    points = metric_column(keys, "points")
    # a metric logged once (a final evaluation) leads only where no curve of its kind does.
    live = sorted(
        (k for k in metrics if k not in CLOCKS and not constant.get(k)),
        key=lambda k: (points.get(k) or 2) <= 1,
    )
    return (leading(live) or live or metrics)[0]


def metric_column(keys: dict[str, Any], column: str) -> dict[str, Any]:
    """Read one column of the ``keys`` answer's metrics table by metric.

    :param keys: The ``keys`` answer.
    :param column: The column, e.g. ``constant``.
    :return: Metric key to value; empty when the column is missing (an older remote)."""
    table = keys["metrics"]
    if column not in table["columns"]:
        return {}
    i = table["columns"].index(column)
    return {row[0]: row[i] for row in table["rows"] if i < len(row)}


def varying_config(keys: dict[str, Any]) -> list[str]:
    """List the config keys that distinguish runs: real splits, not aliases or path noise.

    :param keys: The ``keys`` answer.
    :return: The fields, e.g. ``config.lr``."""
    return keys["config"]["varying"]


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
