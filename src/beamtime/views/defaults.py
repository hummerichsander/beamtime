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


def default_view(ctx: Context, path: str, pins: list[dict[str, Any]] | None = None) -> m.View:
    """Build the default view of a group or run.

    :param ctx: The operation context.
    :param path: The group below the log dir (``.`` for the log dir), or a run's path.
    :param pins: The main metrics as resolved by ``pins_of``; the default pins without.
    :return: The view."""
    if pins is None:
        pins = pins_of(ctx, path)
    if is_run_id(path.rsplit("/", 1)[-1]):
        return m.View(body=run_body(ctx, path, pins))
    return m.View(body=group_body(ctx, path, pins))


def pins_of(
    ctx: Context, path: str, given: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    """Resolve a page's main metrics: the viewer's pins, else the proposal's predicted metrics.

    :param ctx: The operation context.
    :param path: A group or run path.
    :param given: The viewer's pins ``{y, higher}`` (``[]`` for none); ``None`` for the defaults.
    :return: The pins the page logs, in order, without clocks or repeats."""
    from beamtime.guide import predicted

    run_id = path.rsplit("/", 1)[-1]
    keys = call("keys", {"from": run_id if is_run_id(run_id) else path}, ctx)
    metrics = [k for k in ordered_metrics(keys) if k not in CLOCKS]
    if given is None:
        group = (path.rsplit("/", 1)[0] if "/" in path else ".") if is_run_id(run_id) else path
        given = [{"y": y, "higher": not lower_is_better(y)} for y in predicted(ctx, group, metrics)]
    out: dict[str, dict[str, Any]] = {}
    for pin in given:
        if pin["y"] in metrics:
            out.setdefault(pin["y"], {"y": pin["y"], "higher": bool(pin["higher"])})
    return list(out.values())


def group_body(ctx: Context, path: str, pins: list[dict[str, Any]]) -> list[m.Block]:
    """Build the default view of a group: what it shows, concisely.

    :param ctx: The operation context.
    :param path: The group below the log dir.
    :param pins: The main metrics.
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
    if direct:
        # curves show only the group's own runs; runs in subgroups belong to their groups.
        own = direct < runs
        own_keys = call("keys", {"from": path, "depth": 1}, ctx) if own else keys
        many = "config.seed" in varying and direct > SEED_GROUPING_ABOVE
        metrics = ordered_metrics(own_keys)
        main = [p["y"] for p in pins if p["y"] in metrics]
        body += curves(metrics, "config.seed" if many else None, own, main)
        if varying:
            body.append(m.Config(id="hyperparameters", title="Hyperparameters"))
        code = ["run.code"] if keys.get("codes") else []
        clock = ["run.progress"] if "epoch" in metrics else []
        columns = [
            "run.name",
            "run.status",
            *clock,
            *varying,
            *code,
            *[f"metric.{y}.last" for y in main],
        ]
        table = m.Table(
            id="runs",
            title="Runs",
            columns=columns,
            limit=TABLE_LIMIT,
            sparkline=(main or [None])[0],
        )
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


def run_body(ctx: Context, path: str, pins: list[dict[str, Any]]) -> list[m.Block]:
    """Build the default view of a run.

    :param ctx: The operation context.
    :param path: The run's path below the log dir.
    :param pins: The main metrics.
    :return: The body."""
    run_id = path.rsplit("/", 1)[-1]
    keys = call("keys", {"from": run_id}, ctx)
    metrics = ordered_metrics(keys)
    status = next(iter(keys["status"]), None)
    body = curves(metrics, None, False, [p["y"] for p in pins if p["y"] in metrics])
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
    ctx: Context, path: str, lead: tuple[str, bool, str | None] | None
) -> dict[str, Any] | None:
    """Find the best run of the lead metric, for the header's facts line.

    :param ctx: The operation context.
    :param path: A group or run path.
    :param lead: The lead metric, whether lower is better and its label; ``None`` for no pin.
    :return: ``{metric, label, stat, value, run, name, config}``, or ``None`` without a lead or
        metric, or for a group without runs of its own."""
    if lead is None:
        return None
    run_id = path.rsplit("/", 1)[-1]
    scope = run_id if is_run_id(run_id) else path
    # a group whose runs all sit in subgroups mixes experiments; no single best there.
    if scope == path and not counts(ctx, path)[1]:
        return None
    keys = call("keys", {"from": scope}, ctx)
    main, lower, label = lead
    if main not in ordered_metrics(keys):
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


def curves(metrics: list[str], seeds: str | None, own: bool, main: list[str]) -> list[m.Block]:
    """Make one chart per metric, in sections by metric prefix.

    :param metrics: The metrics, ordered.
    :param seeds: ``config.seed`` to average over seeds, or ``None``.
    :param own: Whether to show only the runs directly in the group.
    :param main: The pinned metrics, in order.
    :return: The sections: ``Main`` (the pinned metrics again, open; their charts there are
        ``pin-<metric>``), evaluation, training, the other prefixes, ``Other`` (unprefixed metrics
        and prefixes of one metric), then ``System``; the first two of those open. A single
        section without pins is a plain grid. Clocks (``epoch``) get no chart: they are an x
        axis and a progress fact."""
    metrics = [k for k in metrics if k not in CLOCKS]
    pinned = [k for k in main if k in metrics]
    sizes = Counter(prefix(k) for k in metrics)
    groups: dict[str, list[str]] = {}
    for k in metrics:
        name = prefix(k) if sizes[prefix(k)] > 1 or prefix(k) == SYSTEM else ""
        groups.setdefault(name, []).append(k)
    order = sorted(groups, key=section_rank)
    # system metrics are per machine, never averaged over seeds.
    if len(order) == 1 and not pinned:
        by = None if order == [SYSTEM] else seeds
        return [m.Grid(id="curves", children=[line(k, by, own) for k in metrics])]
    # Main's ids start with neither ``charts-`` nor ``line-``, so no metric or prefix can collide.
    sections = []
    if pinned:
        charts = [
            line(k, seeds if prefix(k) != SYSTEM else None, own, f"pin-{m.slug(k)}") for k in pinned
        ]
        sections.append(("Main", "main", charts, True))
    for i, name in enumerate(order):
        title = {"": "Other", SYSTEM: "System"}.get(name, name)
        by = None if name == SYSTEM else seeds
        charts = [line(k, by, own) for k in groups[name]]
        opened = i < OPEN_SECTIONS and name != SYSTEM
        sections.append((title, f"charts-{m.slug(name or 'unprefixed')}", charts, opened))
    out: list[m.Block] = []
    for title, id_, charts, opened in sections:
        grid = m.Grid(id=f"{id_}-curves", children=charts)
        out.append(
            m.Section(id=id_, title=f"{title} ({len(charts)})", open=opened, children=[grid])
        )
    return out


def section_rank(name: str) -> int:
    """Rank a chart section: evaluation, training, other prefixes, Other, System.

    :param name: The section's prefix; empty for ``Other``.
    :return: The rank; lower comes first."""
    if name == SYSTEM:
        return 4
    if not name:
        return 3
    return 0 if name in EVAL_PREFIXES else 1 if name in TRAIN_PREFIXES else 2


def line(metric: str, seeds: str | None, own: bool, id_: str | None = None) -> m.Line:
    """Make the line block of one metric.

    :param metric: The metric key.
    :param seeds: ``config.seed`` to average over seeds, or ``None`` for one curve per run.
    :param own: Whether to show only the runs directly in the group.
    :param id_: The block's id; ``line-<metric>`` without.
    :return: The block."""
    return m.Line(
        id=id_ or f"line-{m.slug(metric)}", y=metric, seeds=seeds, depth=1 if own else "all"
    )


def ordered_metrics(keys: dict[str, Any]) -> list[str]:
    """Order a group's metrics for display: validation and test first, then the rest.

    :param keys: The ``keys`` answer.
    :return: The metric keys."""
    names = [r[0] for r in keys["metrics"]["rows"]]
    rank = {"val": 0, "valid": 0, "eval": 0, "validation": 0, "test": 1, "train": 2, "training": 2}
    return sorted(names, key=lambda k: (rank.get(k.split("/", 1)[0], 3) if "/" in k else 4, k))


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
