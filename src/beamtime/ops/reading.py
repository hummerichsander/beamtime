"""The reading operations, shared by the CLI and MCP."""

import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.run import (
    derived_status,
    read_card,
    read_config,
    read_events,
    read_output,
    read_run_info,
    run_status,
)
from beamtime.format.times import iso
from beamtime.index.cache import daemon_status
from beamtime.index.index import Index
from beamtime.ops import registry as r
from beamtime.ops.budget import MAX_CHARS, cut, offset_of
from beamtime.ops.context import Context, OpError
from beamtime.query import QueryError
from beamtime.query import run as run_query
from beamtime.query.aggregate import spread
from beamtime.query.distinguish import distinguishing, flatten, is_seed, signature
from beamtime.query.kinds import describe_event
from beamtime.query.progress import progress
from beamtime.query.select import Columns
from beamtime.record.check import rounded
from beamtime.record.stats import mean

RECENT_EVENTS = 10
COMPARE_METRICS = 20
DIGEST_NOTES = 5
DIGEST_VALUES = 8
DIGEST_KEYS = 3
LOG_WIDTH = 300


def ask(ctx: Context, query: dict[str, Any], cursor: str | None = None) -> dict[str, Any]:
    """Answer a query for the context's log dir, with the caller's defaults and budget.

    :param ctx: The operation context.
    :param query: The query in its object form.
    :param cursor: A cursor from an earlier, cut answer.
    :return: The answer."""
    return page(ctx, evaluate(ctx, query), cursor)


def evaluate(ctx: Context, query: dict[str, Any]) -> dict[str, Any]:
    """Answer a query for the context's log dir, whole, without the token budget.

    :param ctx: The operation context.
    :param query: The query in its object form.
    :return: The answer."""
    if not ctx.logdir.is_dir():
        raise OpError(
            f"no log dir at {ctx.logdir}; runs appear there once a script calls "
            "beamtime.init() (or set BEAMTIME_LOGDIR, or `beamtime init` to set up)",
            code=4,
        )
    try:
        answer = run_query(query, logdir=ctx.logdir, caller=ctx.caller, now=ctx.now)
    except QueryError as e:
        raise OpError(str(e), code=4 if e.code == "not_found" else 2) from None
    answer["meta"] = {k: v for k, v in answer["meta"].items() if v is not None}
    return answer


def page(ctx: Context, answer: dict[str, Any], cursor: str | None) -> dict[str, Any]:
    """Cut an answer at the token budget, except for the web UI.

    :param ctx: The operation context.
    :param answer: The answer with one item list.
    :param cursor: A cursor from an earlier, cut answer.
    :return: The answer, with ``meta.next`` when items were left out."""
    offset = offset_of(cursor)
    return answer if ctx.caller == "view" else cut(answer, offset)


def selection(p: r.Selection) -> dict[str, Any]:
    """Turn the shared selection parameters into query fields.

    :param p: The parameters.
    :return: ``from``, ``where`` and ``depth``."""
    return {"from": p.from_, "where": p.where, "depth": p.depth}


def keys(ctx: Context, p: r.KeysParams) -> dict[str, Any]:
    """List metrics, config keys, data keys and tags.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    return ask(ctx, {"keys": selection(p)})


def groups(ctx: Context, p: r.GroupsParams) -> dict[str, Any]:
    """Show the group tree with proposals and run counts.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    return ask(ctx, {"groups": selection(p)}, p.cursor)


def runs(ctx: Context, p: r.RunsParams) -> dict[str, Any]:
    """Answer a run table.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {
        "select": p.select,
        "sort": p.sort,
        "limit": p.limit,
        "seeds": p.seeds,
    }
    return ask(ctx, {"runs": q}, p.cursor)


def series(ctx: Context, p: r.SeriesParams) -> dict[str, Any]:
    """Answer curves.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {
        "y": p.y,
        "x": p.x,
        "steps": p.steps,
        "points": p.points,
        "by": p.by,
        "seeds": p.seeds,
        "band": p.band,
        "smooth": {"ema": p.smooth} if p.smooth is not None else None,
    }
    return ask(ctx, {"series": q}, p.cursor)


def data(ctx: Context, p: r.DataParams) -> dict[str, Any]:
    """Answer logged tables, images and text.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {"key": p.key, "step": p.step, "limit": p.limit}
    return ask(ctx, {"data": q}, p.cursor)


def file(ctx: Context, p: r.FileParams) -> dict[str, Any]:
    """Answer a data file stored with a view.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    if p.draft is None:
        return ask(ctx, {"file": {"view": p.view, "path": p.path}})
    from beamtime.query.files import read_table
    from beamtime.views.store import draft

    folder = draft(ctx, p.draft).dir.resolve()
    path = (folder / p.path).resolve()
    if folder not in path.parents or not path.is_file():
        raise OpError(f"no file {p.path!r} in draft {p.draft!r}", code=4)
    try:
        columns, rows = read_table(path)
    except QueryError as e:
        raise OpError(str(e), code=2) from None
    return {"kind": "file", "draft": p.draft, "path": p.path, "columns": columns, "rows": rows,
            "meta": {"matched": len(rows)}}  # fmt: skip


def timeline(ctx: Context, p: r.TimelineParams) -> dict[str, Any]:
    """Answer notes and run events in time order.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    q = selection(p) | {
        "types": p.types,
        "since": p.since,
        "limit": p.limit,
        "full": p.full,
    }
    return ask(ctx, {"timeline": q}, p.cursor)


def query(ctx: Context, p: r.QueryParams) -> dict[str, Any]:
    """Answer any query in its object form.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    return ask(ctx, p.query, p.cursor)


def members(
    ctx: Context, target: str, where: dict[str, Any] | None = None, depth: Any = "all"
) -> list[dict[str, Any]]:
    """List the runs of a group or the one run a target names, whole and without a budget.

    :param ctx: The operation context.
    :param target: A group below the log dir, or a run id.
    :param where: A condition the runs must meet.
    :param depth: How many group levels below the target to look into.
    :return: Per run: ``id``, ``name``, ``status``, ``code`` and ``dir``."""
    fields = ["run.name", "run.status", "run.code", "run.path"]
    query = {"from": target, "select": fields, "limit": 10**6, "where": where or {}, "depth": depth}
    table = evaluate(ctx, {"runs": query})
    return [
        {"id": row[0], "name": row[1], "status": row[2], "code": row[3], "dir": ctx.logdir / row[4]}
        for row in table["rows"]
    ]


def compare(ctx: Context, p: r.CompareParams) -> dict[str, Any]:
    """Compare runs or groups: what differs in config, whether the code is the same, how the
    metrics end up.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: Per target its status and code; the config keys that differ with their values;
        a metric table (last values; the mean over a group's runs) with the difference of two."""
    if len(p.targets) < 2:
        raise OpError("compare takes at least two runs or groups", code=2)
    entities = []
    for target in p.targets:
        if not (runs_ := members(ctx, target)):
            raise OpError(f"{target!r} holds no runs to compare", code=4)
        entities.append((target, runs_))

    configs = [entity_config(runs_) for _, runs_ in entities]
    aliases = distinguishing(configs).aliases
    differences = [
        {
            "key": f"config.{key}",
            "values": [cfg.get(key) for cfg in configs],
            "same_split_as": aliases.get(f"config.{key}"),
        }
        for key in sorted({k for cfg in configs for k in cfg})
        if len(set(signature(configs, key))) > 1
    ]

    lasts = [[last_values(m["dir"]) for m in runs_] for _, runs_ in entities]
    found = sorted({k for per_run in lasts for last in per_run for k in last})
    keys = p.metrics or found[:COMPARE_METRICS]
    rows = []
    for key in keys:
        cells = [cell([last[key] for last in per_run if key in last]) for per_run in lasts]
        delta = None
        if len(cells) == 2 and all(isinstance(c_, (int, float)) for c_ in map(center, cells)):
            delta = center(cells[1]) - center(cells[0])
        rows.append({"metric": key, "values": cells, "delta": delta})

    codes = [sorted({m["code"] for m in runs_ if m["code"]}) for _, runs_ in entities]
    answer = {
        "kind": "compare",
        "targets": [
            {
                "target": target,
                "runs": len(runs_),
                "status": dict(Counter(m["status"] for m in runs_)),
                "code": codes[i],
            }
            for i, (target, runs_) in enumerate(entities)
        ],
        "same_code": len({tuple(code) for code in codes}) == 1
        and all(len(c_) == 1 for c_ in codes),
        "differences": differences,
        "rows": rows,
        "meta": {"matched": len(rows)},
    }
    if not p.metrics and len(found) > len(keys):
        answer["meta"]["hint"] = f"{len(found)} metrics logged; name them with metrics"
    return page(ctx, answer, p.cursor)


def entity_config(runs_: list[dict[str, Any]]) -> dict[str, Any]:
    """Flatten the configs of one compared target: a run's own, a group's with differing values
    listed.

    :param runs_: The target's runs, as ``members`` lists them.
    :return: Dotted key to its value, or to ``{"varies": [...]}`` when the runs disagree."""
    per_run = [
        flatten(read_config(m["dir"])) if (m["dir"] / c.CONFIG).exists() else {} for m in runs_
    ]
    out = {}
    for key in {k for cfg in per_run for k in cfg}:
        seen = {json.dumps(cfg.get(key), sort_keys=True): cfg.get(key) for cfg in per_run}
        out[key] = next(iter(seen.values())) if len(seen) == 1 else {"varies": list(seen.values())}
    return out


def last_values(run_dir: Path) -> dict[str, float]:
    """Read the last value of every metric of a run from its card.

    :param run_dir: The run directory.
    :return: Metric key to last value; metrics without a finite value are left out."""
    if not (run_dir / c.CARD).exists():
        return {}
    return {k: m.last for k, m in read_card(run_dir).metrics.items() if m.last is not None}


def cell(values: list[float]) -> Any:
    """Summarize one metric over a target's runs.

    :param values: The runs' last values.
    :return: ``None`` without values, the value for one run, else ``{mean, std, n}``."""
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    mu, std = spread(values)
    return {"mean": mu, "std": std, "n": len(values)}


def center(value: Any) -> Any:
    """Give the number a metric cell stands for.

    :param value: A cell from ``cell``.
    :return: The value, or a group's mean."""
    return value["mean"] if isinstance(value, dict) else value


def digest(ctx: Context, p: r.DigestParams) -> dict[str, Any]:
    """Summarize a group on one page: runs by status, the proposal's check, the best value per
    varying setting, failures by signature, the newest notes and what the plan still lacks.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The digest."""
    from beamtime.ops.authored import target_of
    from beamtime.record.check import evaluate
    from beamtime.record.notes import listing
    from beamtime.record.proposals import current, load

    runs_ = members(ctx, p.group)
    with target_of(ctx, p.group) as target:
        version = current(target.dir)
        proposal = load(target.dir, version) if version else None
        check_ = evaluate(target, version, proposal) if proposal else None
        plan = plan_points(target, version, proposal) if proposal else None
        newest = listing(target, types=None, only_open=False, full=False, only_current=True)
        questions = listing(target, types=None, only_open=True, full=False, only_current=True)

    reduce = (
        next((pr.reduce for pr in proposal.predictions if pr.reduce), None) if proposal else None
    )
    metric = p.metric or (reduce.metric if reduce else None)
    stat = reduce.stat if reduce and reduce.metric == metric else "last"
    return {
        "kind": "digest",
        "group": p.group,
        "runs": dict(Counter(m["status"] for m in runs_)),
        "proposal": None
        if proposal is None
        else {
            "version": version,
            "statement": proposal.statement,
            "result": check_["result"],
            "provisional": check_["provisional"],
            "progress": check_["progress"]["text"],
        },
        "predictions": [
            {k: pr.get(k) for k in ("name", "test", "result", "effect", "ci", "detail")}
            for pr in (check_["predictions"] if check_ else [])
        ],
        "best": best_per_setting(runs_, metric, stat),
        "failures": failures(runs_),
        "missing": plan,
        "open_questions": [note_row(n) for n in questions[:DIGEST_NOTES]],
        "notes": [note_row(n) for n in newest[:DIGEST_NOTES]],
        "meta": {},
    }


def note_row(note: dict[str, Any]) -> dict[str, Any]:
    """Shorten a note listing entry for a digest.

    :param note: An entry of ``record.notes.listing``.
    :return: Its id, type and description."""
    return {k: note[k] for k in ("id", "type", "description")}


def best_per_setting(
    runs_: list[dict[str, Any]], metric: str | None, stat: str
) -> dict[str, Any] | None:
    """Tabulate a metric of the finished runs per value of each config key that varies.

    :param runs_: The group's runs, as ``members`` lists them.
    :param metric: The metric key, or ``None`` for no table.
    :param stat: The statistic of the metric that stands for a run.
    :return: ``metric``, ``stat`` and per varying key (never a seed) its values with the number
        of runs and the mean, min and max; ``None`` without a metric or finished runs."""
    done = [m for m in runs_ if m["status"] == "finished" and (m["dir"] / c.CARD).exists()]
    values = [
        getattr(card.metrics.get(metric), stat, None)
        for card in (read_card(m["dir"]) for m in done)
    ]
    kept = [(m, v) for m, v in zip(done, values, strict=True) if v is not None]
    if metric is None or not kept:
        return None
    configs = [flatten(read_config(m["dir"])) for m, _ in kept]
    keys = [k for k in distinguishing(configs).varying if not is_seed(k)][:DIGEST_KEYS]
    by_key = {}
    for key in keys:
        groups: dict[str, list[float]] = {}
        for cfg, (_, v) in zip(configs, kept, strict=True):
            groups.setdefault(json.dumps(cfg.get(key.removeprefix("config."))), []).append(v)
        by_key[key] = [
            {
                "value": json.loads(label),
                "runs": len(vs),
                "mean": rounded(mean(vs)),
                "min": rounded(min(vs)),
                "max": rounded(max(vs)),
            }
            for label, vs in list(groups.items())[:DIGEST_VALUES]
        ]
    return {"metric": metric, "stat": stat, "runs": len(kept), "by": by_key}


def failures(runs_: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group the failed, killed and lost runs by how they ended.

    :param runs_: The group's runs, as ``members`` lists them.
    :return: Per signature: the signature, status, run ids; the biggest group first."""
    groups: dict[tuple[str, str], list[str]] = {}
    for m in runs_:
        if m["status"] in ("failed", "killed", "lost"):
            error = read_card(m["dir"]).error if (m["dir"] / c.CARD).exists() else None
            groups.setdefault((m["status"], failure_signature(error)), []).append(m["id"])
    ordered = sorted(groups.items(), key=lambda item: -len(item[1]))
    return [
        {"status": status, "signature": sig, "count": len(ids), "runs": ids[:DIGEST_NOTES]}
        for (status, sig), ids in ordered
    ]


def failure_signature(text: str | None) -> str:
    """Reduce an error to what runs of one failure share: its last line without numbers.

    :param text: An error message or traceback, or ``None``.
    :return: The signature; empty without an error."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return re.sub(r"0x[0-9a-f]+|\d+(\.\d+)?", "#", lines[-1])[:120] if lines else ""


def plan_points(target: Any, version: str, proposal: Any) -> dict[str, Any]:
    """Find what a version's plan still lacks.

    :param target: The group or run.
    :param version: The version id.
    :param proposal: The version.
    :return: ``form``, ``missing`` (how many) and, for a grid, the ``points`` without a finished
        run with the status counts of the runs at them."""
    import itertools

    from beamtime.query.where import compare as equal
    from beamtime.record.plans import children

    finished = sum(m["status"] == "finished" for m in target.members(version))
    match proposal.plan:
        case {"grid": dict(grid)}:
            fields = list(grid)
            rows = target.select(version, {}, [*fields, "run.status"])
            points = []
            for point in itertools.product(*grid.values()):
                at = [
                    row
                    for row in rows
                    if all(equal("eq", row[f], v) for f, v in zip(fields, point, strict=True))
                ]
                if not any(row["run.status"] == "finished" for row in at):
                    runs_at = dict(Counter(row["run.status"] for row in at))
                    points.append({"point": dict(zip(fields, point, strict=True)), "runs": runs_at})
            return {"form": "grid", "missing": len(points), "points": points}
        case {"runs": int(n)}:
            return {"form": "runs", "missing": max(0, n - finished)}
        case "children":
            done, total = children(target)
            return {"form": "children", "missing": total - done}
        case _:
            return {"form": "none", "missing": None}


def logs(ctx: Context, p: r.LogsParams) -> dict[str, Any]:
    """Show the output of a run or of every run of a group, and group the failed runs'
    last tracebacks by signature.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: ``tracebacks`` (signature, runs, the first run's traceback) and per run ``entries``
        with its last lines, or the lines matching ``grep`` with their context."""
    pattern = None
    if p.grep:
        try:
            pattern = re.compile(p.grep)
        except re.error as e:
            raise OpError(f"grep: {p.grep!r} is not a regular expression: {e}", code=2) from None
    entries, crashes = [], {}
    runs_ = members(ctx, p.from_, p.where, p.depth)
    for m in runs_:
        lines = [
            collapse(line)[:LOG_WIDTH] for line in read_output(m["dir"], rank=p.rank).splitlines()
        ]
        if shown := excerpt(lines, pattern, p.tail, p.context):
            entries.append(
                {"run": m["id"], "name": m["name"], "status": m["status"], "lines": shown}
            )
        if m["status"] == "failed":
            trace = last_traceback(lines)
            error = read_card(m["dir"]).error if (m["dir"] / c.CARD).exists() else None
            sig = failure_signature(trace[-1] if trace else error)
            crash = crashes.setdefault(sig, {"signature": sig, "runs": [], "traceback": trace})
            crash["runs"].append(m["id"])
    answer = {
        "kind": "logs",
        "tracebacks": sorted(crashes.values(), key=lambda crash: -len(crash["runs"])),
        "entries": entries,
        "meta": {"matched": len(runs_), "with_lines": len(entries)},
    }
    return page(ctx, answer, p.cursor)


def excerpt(lines: list[str], pattern: re.Pattern | None, tail: int, context: int) -> list[str]:
    """Pick the lines to show: the last ones, or the last matches with their surroundings.

    :param lines: The run's output lines.
    :param pattern: What to search for, or ``None`` for the last lines.
    :param tail: How many lines, or matching lines, to keep.
    :param context: Lines to show around each match.
    :return: The lines; a match is ``n: line``, its context ``n- line``."""
    if pattern is None:
        return lines[-tail:] if tail else lines
    hits = [i for i, line in enumerate(lines) if pattern.search(line)]
    hits = hits[-tail:] if tail else hits
    keep = sorted(
        {j for i in hits for j in range(max(0, i - context), min(len(lines), i + context + 1))}
    )
    return [f"{j + 1}{':' if j in hits else '-'} {lines[j]}" for j in keep]


def last_traceback(lines: list[str]) -> list[str]:
    """Find the last Python traceback in a run's output.

    :param lines: The output lines.
    :return: The traceback up to and including its exception line; empty without one."""
    starts = [i for i, line in enumerate(lines) if line.startswith("Traceback (most recent call")]
    if not starts:
        return []
    block = lines[starts[-1] :]
    end = next((i for i, line in enumerate(block[1:], 1) if line and not line[0].isspace()), None)
    return block if end is None else block[: end + 1]


def find_run(ctx: Context, run_id: str) -> Path:
    """Find a run by id (or a unique id suffix, or its name) after catching up.

    :param ctx: The operation context.
    :param run_id: The run id.
    :return: The run directory."""
    with Index(logdir=ctx.logdir) as index:
        if (path := index.run_path(run_id)) is None:
            index.catch_up(".", budget_s=0.2)
            path = index.run_path(run_id)
        if path is None:
            hits = index.store.db.execute(
                "SELECT path FROM runs WHERE id LIKE ? OR name = ?", (f"%{run_id}", run_id)
            ).fetchall()
            if len(hits) > 1:
                raise OpError(f"{run_id!r} matches {len(hits)} runs; give the full run id", code=2)
            path = ctx.logdir / hits[0][0] if hits else None
    if path is None:
        raise OpError(f"no run {run_id!r} below {ctx.logdir}; `beamtime runs` lists them", code=4)
    return path


def card(ctx: Context, p: r.CardParams) -> dict[str, Any]:
    """Show one run's card with its identity, config, statistics and recent events.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    from beamtime.index.ingest import given_name
    from beamtime.ops.copy import checkpoints
    from beamtime.record.check import cited_by
    from beamtime.record.proposals import Target

    run_dir = find_run(ctx, p.run)
    run_card = read_card(run_dir) if (run_dir / c.CARD).exists() else None
    config = read_config(run_dir) if (run_dir / c.CONFIG).exists() else {}
    epochs = None
    with Index(logdir=ctx.logdir) as index:
        freshness = index.catch_up(run_dir.relative_to(ctx.logdir).as_posix(), 0.2)
        info = read_run_info(run_dir)
        proposals = run_proposals(index, run_dir, info.proposals)
        cited = cited_by(Target(index=index, rel=".", run_id=None), info.id)
        if run_card is not None and "epoch" in run_card.metrics:
            cols = Columns(index=index, run_id=info.id)
            epochs = progress(cols, config)
            cols.close()
    heartbeat = (run_dir / c.RUN).stat().st_mtime
    status = run_status(info, heartbeat=heartbeat, now=ctx.now or time.time())
    events = read_events(run_dir)
    return {
        "kind": "card",
        "run": {
            "id": info.id,
            # a name given after the run (name/) wins over the one it started with.
            "name": given_name(run_dir) or info.name,
            "path": run_dir.relative_to(ctx.logdir).as_posix(),
            "status": status,
            "created_at": info.created_at,
            "ended_at": info.ended_at,
            "exit": info.exit,
            "tags": info.tags,
            "attempts": len(info.attempts),
            "host": info.host.get("hostname"),
            "scheduler": info.scheduler,
            "git": info.git,
            "proposals": info.proposals,
            "duration_s": run_card.duration_s if run_card else None,
            "steps": run_card.steps if run_card else None,
            "steps_per_s": run_card.steps_per_s if run_card else None,
            "error": run_card.error if run_card else None,
            "warnings": run_card.warnings if run_card else 0,
            "copied_from": info.copied_from,
        },
        "config": config,
        "progress": epochs,
        "metrics": {
            k: {f: v for f, v in m.__dict__.items() if v is not None}
            for k, m in (run_card.metrics if run_card else {}).items()
        },
        "values": run_card.values if run_card else {},
        "proposals": proposals,
        "checkpoints": checkpoints(ctx, run_dir),
        "cited_by": cited,
        "events": [
            {
                "t": iso(e.t),
                "type": e.kind,
                "step": e.step,
                "description": e.message or describe_event(e.kind, e.data),
            }
            for e in events[-RECENT_EVENTS:]
        ],
        "meta": {"source": "local", "freshness": freshness.dump()},
    }


def run_proposals(index: Index, run_dir: Path, recorded: dict[str, str]) -> list[dict[str, Any]]:
    """Summarize the checks and verdicts of the proposal versions a run recorded.

    :param index: The open index.
    :param run_dir: The run directory.
    :param recorded: The run's ``proposals``: group (``.`` for its own) to version.
    :return: Per version: group, version, whether it is current, check and verdict."""
    from beamtime.record.check import evaluate, newest_verdict
    from beamtime.record.proposals import RecordError, Target, current, load

    out = []
    for key, version in recorded.items():
        own = key == "."
        rel = run_dir.relative_to(index.logdir).as_posix() if own else key
        target = Target(index=index, rel=rel, run_id=run_dir.name if own else None)
        try:
            proposal = load(target.dir, version)
        except RecordError as e:
            out.append({"group": key, "version": version, "check": "invalid", "problem": str(e)})
            continue
        if own and proposal.blank:
            continue
        check = evaluate(target, version, proposal)
        verdict = newest_verdict(target, version)
        out.append(
            {
                "group": key,
                "version": version,
                "statement": proposal.statement,
                "current": version == current(target.dir),
                "check": check["result"],
                "provisional": check.get("provisional"),
                "verdict": verdict.get("overall") if verdict else None,
                "note": check.get("note"),
            }
        )
    return out


def output(ctx: Context, p: r.OutputParams) -> dict[str, Any]:
    """Show a run's captured output, as the terminal showed it.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer: ``lines`` and how many there were in total."""
    run_dir = find_run(ctx, p.run)
    lines = [collapse(line) for line in read_output(run_dir, rank=p.rank).splitlines()]
    total = len(lines)
    if p.grep:
        try:
            pattern = re.compile(p.grep)
        except re.error as e:
            raise OpError(f"grep: {p.grep!r} is not a regular expression: {e}", code=2) from None
        lines = [f"{i + 1}: {line}" for i, line in enumerate(lines) if pattern.search(line)]
    shown = lines[-p.tail :] if p.tail else lines
    meta: dict[str, Any] = {
        "total_lines": total,
        "matched": len(lines),
        "shown": len(shown),
    }
    size = sum(len(line) + 1 for line in shown)
    while shown and size > MAX_CHARS:
        size -= len(shown.pop(0)) + 1
    if len(shown) < len(lines):
        meta["cut"] = True
        meta["hint"] = "earlier lines left out; use tail or grep to see them"
    return {
        "kind": "output",
        "run": run_dir.name,
        "rank": p.rank,
        "lines": shown,
        "meta": meta,
    }


def resume(ctx: Context, p: r.ResumeParams) -> dict[str, Any]:
    """Show what's needed to resume a killed or failed run by hand; it runs nothing.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The recorded command, cwd, last step, newest checkpoint and scheduler, and
        the environment variable that continues it."""
    from beamtime.ops.copy import checkpoints, dirpaths_of, shared_dirpath_warning

    run_dir = find_run(ctx, p.run)
    info = read_run_info(run_dir)
    card = read_card(run_dir) if (run_dir / c.CARD).exists() else None
    checkpoints_ = checkpoints(ctx, run_dir)
    checkpoint = checkpoints_[-1] if checkpoints_ else None
    config = read_config(run_dir) if (run_dir / c.CONFIG).exists() else {}
    dirpaths = dirpaths_of(info.command, config, info.cwd)
    return {
        "kind": "resume",
        "run": info.id,
        "name": info.name,
        "status": info.status,
        "command": info.command,
        "cwd": info.cwd,
        "last_step": card.steps if card else None,
        "scheduler": info.scheduler,
        "checkpoint": (
            {"name": checkpoint["name"], "location": checkpoint["location"]} if checkpoint else None
        ),
        "warning": shared_dirpath_warning(dirpaths, checkpoints_),
        "export": f"BEAMTIME_RESUME={info.id}",
        "meta": {},
    }


def collapse(line: str) -> str:
    """Show a line as a terminal would after carriage returns (progress bars).

    :param line: A captured line.
    :return: The text after the last carriage return."""
    return line.rstrip("\r").rsplit("\r", 1)[-1]


def status(ctx: Context, p: r.NoParams) -> dict[str, Any]:
    """Report the daemon, the index and the log dir.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: The answer."""
    with Index(logdir=ctx.logdir) as index:
        freshness = index.catch_up(".", 0.2) if ctx.logdir.is_dir() else None
        now = time.time()
        counts = Counter(
            derived_status(status, heartbeat, now)
            for status, heartbeat in index.store.db.execute("SELECT status, heartbeat FROM runs")
        )
        cache = index.cache
        memory = project_memory(index) if ctx.logdir.is_dir() else None
    daemon = daemon_status(cache)
    return {
        "kind": "status",
        "root": str(ctx.root),
        "root_from": ctx.root_reason,
        "logdir": str(ctx.logdir),
        "logdir_exists": ctx.logdir.is_dir(),
        "cache": str(cache),
        "runs": dict(counts),
        "daemon": daemon,
        "web_ui": f"http://localhost:{daemon['port']}" if daemon and daemon.get("port") else None,
        "remotes": sorted(ctx.settings.get("remotes") or {}),
        "sources": sources(ctx),
        "snapshots": snapshots(ctx),
        "memory": memory,
        "meta": {"freshness": freshness.dump() if freshness else None},
    }


def sources(ctx: Context) -> list[dict[str, Any]]:
    """Describe every source: this machine, when it is one, and the remotes this process holds
    connections to.

    :param ctx: The operation context.
    :return: One entry per source: its name, kind (``local`` or ``remote``), state and log dir;
        for a remote also since when, its last error and its version."""
    out: list[dict[str, Any]] = []
    if ctx.has_local:
        out.append(
            {"name": "local", "kind": "local", "state": "connected", "logdir": str(ctx.logdir)}
        )
    if ctx.sources is not None:
        out += [
            client.describe() | {"kind": "remote", "logdir": client.spec.path}
            for client in ctx.sources.clients.values()
        ]
    return out


def snapshots(ctx: Context) -> list[dict[str, Any]]:
    """List the pulled snapshots of remotes.

    :param ctx: The operation context.
    :return: One entry per remote: name, groups and the time it was pulled."""
    import json

    from beamtime.remote.pull import SNAPSHOT, snapshots_dir

    out = []
    for record in sorted(snapshots_dir(ctx).glob(f"*/{SNAPSHOT}")):
        try:
            data = json.loads(record.read_text())
        except (OSError, ValueError):
            continue
        out.append({"name": f"@{data['source']}", "groups": data["groups"], "at": data["at"]})
    return out


def project_memory(index: Index) -> dict[str, Any] | None:
    """Tell how current the project's memory is.

    :param index: The open index.
    :return: Its version and the notes added since, or ``None`` without memory."""
    from beamtime.format.authored import newest, read_markdown_doc
    from beamtime.record.memory import notes_since, to_time
    from beamtime.record.proposals import Target

    if (path := newest(index.logdir / c.MEMORY)) is None:
        return None
    try:
        covers = to_time(read_markdown_doc(path, kind="memory").meta.get("covers_until"))
    except (ValueError, OSError):
        covers = None
    target = Target(index=index, rel=".", run_id=None)
    return {"version": path.stem, "notes_since": notes_since(target, ".", covers)}
