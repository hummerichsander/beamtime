"""The automatic check: select, reduce, merge seeds and test every prediction."""

import json
import math
from typing import Any

from beamtime.query.kinds import group_by, seed_groups
from beamtime.query.models import QueryError
from beamtime.query.where import fields_of, matches
from beamtime.record.plans import progress
from beamtime.record.proposals import Prediction, Proposal, RecordError, Target, load
from beamtime.record.stats import Interval, mean, mean_interval, paired_interval, welch_interval

ORDER = ("inconclusive", "insufficient", "pending")
VERDICT_RESULT = {"confirmed": "pass", "refuted": "fail", "inconclusive": "inconclusive"}
ADD_SEEDS = "too few repetitions for an interval; add seeds, or set significance: none"


def combine(results: list[str]) -> str:
    """Combine results: any fail fails, all pass pass, else the most informative.

    :param results: The results of predictions or points.
    :return: The combined result."""
    if "fail" in results:
        return "fail"
    if results and all(r == "pass" for r in results):
        return "pass"
    return next((r for r in ORDER if r in results), "pending")


def decide(op: str, iv: Interval, threshold: float) -> str:
    """Judge an interval against a claim ``estimate op threshold``.

    :param op: ``<``, ``<=``, ``>`` or ``>=``.
    :param iv: The interval; equal ends when no uncertainty is taken into account.
    :param threshold: What the estimate is compared with.
    :return: ``pass`` if the whole interval satisfies the claim, ``fail`` if the whole
        interval violates it, else ``inconclusive``."""
    lo, hi = iv.lo - threshold, iv.hi - threshold
    match op:
        case ">":
            return "pass" if lo > 0 else "fail" if hi <= 0 else "inconclusive"
        case ">=":
            return "pass" if lo >= 0 else "fail" if hi < 0 else "inconclusive"
        case "<":
            return "pass" if hi < 0 else "fail" if lo >= 0 else "inconclusive"
        case "<=":
            return "pass" if hi <= 0 else "fail" if lo > 0 else "inconclusive"
        case _:
            raise ValueError(f"unknown op {op!r}")


def threshold_of(op: str, margin: float) -> float:
    """Turn a margin into the threshold of the claim; the op gives its direction.

    :param op: The comparison.
    :param margin: The margin, not negative.
    :return: ``+margin`` for ``>``/``>=``, ``-margin`` for ``<``/``<=``."""
    return margin if op in (">", ">=") else -margin


def rounded(x: float | None) -> float | None:
    """Round for answers and snapshots, keeping six significant digits.

    :param x: The number.
    :return: The rounded number."""
    return None if x is None else float(f"{x:.6g}")


def evaluate(target: Target, version: str, proposal: Proposal | None = None) -> dict[str, Any]:
    """Check a proposal version against the runs that recorded it.

    :param target: The group or run.
    :param version: The version id.
    :param proposal: The version, if already read.
    :return: The check: result, provisional, progress and one entry per prediction."""
    out: dict[str, Any] = {"group": target.rel, "version": version}
    members = target.members(version)
    try:
        proposal = proposal or load(target.dir, version)
    except RecordError as e:
        return out | {"result": "invalid", "problem": str(e), "predictions": []}
    if problem := target.hash_problem(version, members):
        return out | {"result": "invalid", "problem": problem, "predictions": []}
    plan = progress(target, version, proposal, members)
    verdict = newest_verdict(target, version)
    verdicts = (verdict or {}).get("verdicts") or {}
    predictions = []
    for pr in proposal.predictions:
        entry = (
            predict(target, version, pr, proposal.level)
            if pr.kind == "auto"
            else manual(pr, verdicts.get(pr.name))
        )
        entry["cited_by"] = cited_by(target, f"{target.rel}#{pr.name}")
        predictions.append(entry)
    results = [p["result"] for p in predictions]
    return out | {
        "result": combine(results) if results else None,
        "provisional": not plan["complete"],
        "level": proposal.level,
        "progress": plan,
        "predictions": predictions,
    }


def manual(pr: Prediction, verdict: str | None) -> dict[str, Any]:
    """Report a manual prediction: pending until a verdict note decides it.

    :param pr: The prediction.
    :param verdict: The newest verdict's judgement of it, if any.
    :return: The entry."""
    entry = {"name": pr.name, "kind": "manual", "description": pr.description}
    if verdict is None:
        return entry | {"result": "pending", "detail": "manual; waits for a verdict note"}
    return entry | {"result": VERDICT_RESULT.get(verdict, "pending"), "verdict": verdict}


def predict(target: Target, version: str, pr: Prediction, level: float | None) -> dict[str, Any]:
    """Evaluate one automatic prediction.

    :param target: The group or run.
    :param version: The version id.
    :param pr: The prediction.
    :param level: The confidence level, or ``None`` for ``significance: none``.
    :return: The entry: result, effect, interval, points and a detail line."""
    head = {"name": pr.name, "kind": "auto", "test": pr.test, "op": pr.op}
    field = pr.reduce.field
    extra = [field, "run.status", *fields_of(pr.a or {}), *fields_of(pr.b or {})]
    try:
        runs = target.select(version, pr.where, [*extra, *(pr.pair_by or [])], seeds=pr.seeds)
    except QueryError as e:
        if e.code == "not_found":
            return head | {"result": "pending", "detail": str(e)}
        raise RecordError(f"prediction {pr.name!r}: {e}") from None
    done = [
        r
        for r in runs
        if r["run.status"] == "finished" and isinstance(r[field], (int, float))
        if math.isfinite(r[field])
    ]
    if not done:
        waiting = sum(r["run.status"] == "running" for r in runs)
        detail = f"no finished run with {pr.reduce.metric} yet" + (
            f"; {waiting} running" if waiting else ""
        )
        return head | {"result": "pending", "detail": detail}
    match pr.test:
        case "each":
            return head | each(target, pr, done, field, level)
        case "compare":
            return head | compare(pr, done, field, level)
        case _:
            raise ValueError(f"unknown test {pr.test!r}")


def each(
    target: Target,
    pr: Prediction,
    runs: list[dict[str, Any]],
    field: str,
    level: float | None,
) -> dict[str, Any]:
    """Test that every point satisfies the comparison.

    :param target: The group or run, for reading a reference run.
    :param pr: The prediction.
    :param runs: The finished runs with a value.
    :param field: The reduced field.
    :param level: The confidence level, or ``None``.
    :return: The entry's result fields."""
    if pr.ref is not None:
        if (base := reference(target, pr.ref["run"], field)) is None:
            return {"result": "pending", "detail": f"ref run {pr.ref['run']} has no {field}"}
    else:
        base = pr.value
    threshold = base + threshold_of(pr.op, pr.margin)
    groups = (
        seed_groups(runs, pr.seeds)
        if pr.seeds
        else [(json.loads(r["_config"] or "{}"), [r]) for r in runs]
    )
    labels = varying([cfg for cfg, _ in groups])
    uncertain = pr.seeds is not None and level is not None
    points = []
    for (_, group), label in zip(groups, labels, strict=True):
        values = [r[field] for r in group]
        if uncertain and len(values) < 2:
            iv, result = mean_interval(values, None), "insufficient"
        else:
            iv = mean_interval(values, level if uncertain else None)
            result = decide(pr.op, iv, threshold)
        points.append((label, [r["_id"] for r in group], iv, result))
    lower = pr.op in (">", ">=")
    _, _, worst, _ = min(points, key=lambda p: p[2].lo if lower else -p[2].hi)
    result = combine([p[3] for p in points])
    return {
        "result": result,
        "effect": rounded(worst.estimate - base),
        "ci": [rounded(worst.lo - base), rounded(worst.hi - base)] if uncertain else None,
        "threshold": rounded(threshold - base),
        "points": len(points),
        "detail": detail(result, uncertain),
        "by_point": [
            {
                "point": label,
                "runs": ids,
                "mean": rounded(iv.estimate),
                "ci": [rounded(iv.lo), rounded(iv.hi)] if uncertain and iv.df else None,
                "result": res,
            }
            for label, ids, iv, res in points
        ],
    }


def compare(
    pr: Prediction, runs: list[dict[str, Any]], field: str, level: float | None
) -> dict[str, Any]:
    """Test that the runs of ``a`` beat those of ``b``.

    Without ``pair_by``, the runs of each side are the repetitions of a Welch interval;
    with it, points agreeing on those fields are paired and their mean differences
    are the repetitions.

    :param pr: The prediction.
    :param runs: The finished runs with a value.
    :param field: The reduced field.
    :param level: The confidence level, or ``None``.
    :return: The entry's result fields."""
    side_a = [r for r in runs if matches(pr.a, r)]
    side_b = [r for r in runs if matches(pr.b, r)]
    if not side_a or not side_b:
        return {
            "result": "pending",
            "detail": f"finished runs: {len(side_a)} match a, {len(side_b)} match b",
        }
    threshold = threshold_of(pr.op, pr.margin)
    if pr.pair_by:
        by_a = {json.dumps(k, sort_keys=True): rs for k, rs in group_by(side_a, pr.pair_by)}
        by_b = {json.dumps(k, sort_keys=True): rs for k, rs in group_by(side_b, pr.pair_by)}
        common = sorted(by_a.keys() & by_b.keys())
        if not common:
            return {"result": "pending", "detail": f"no a and b runs agree on {pr.pair_by}"}
        xs = [mean([r[field] for r in by_a[k]]) for k in common]
        ys = [mean([r[field] for r in by_b[k]]) for k in common]
        enough = len(common) >= 2
        iv = paired_interval(xs, ys, level if enough else None)
        n = {"pairs": len(common)}
        points = len(common)
    else:
        xs, ys = [r[field] for r in side_a], [r[field] for r in side_b]
        enough = len(xs) >= 2 and len(ys) >= 2
        iv = welch_interval(xs, ys, level if enough else None)
        n = {"a": len(xs), "b": len(ys)}
        points = len(xs) + len(ys)
    uncertain = level is not None
    if uncertain and not enough:
        result = "insufficient"
    else:
        result = decide(pr.op, iv, threshold)
    return {
        "result": result,
        "effect": rounded(iv.estimate),
        "ci": [rounded(iv.lo), rounded(iv.hi)] if uncertain and enough else None,
        "threshold": rounded(threshold),
        "points": points,
        "n": n,
        "detail": detail(result, uncertain),
    }


def detail(result: str, uncertain: bool) -> str | None:
    """Explain a result in a few words where the result alone could mislead.

    :param result: The result.
    :param uncertain: Whether an interval was used.
    :return: The line, or ``None``."""
    if result == "insufficient":
        return ADD_SEEDS
    if not uncertain:
        return "decided on the values directly; no uncertainty taken into account"
    return None


def varying(configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Label points by the config keys that differ between them.

    :param configs: The configs of the points.
    :return: One label per point."""
    keys = sorted({k for cfg in configs for k in cfg})
    differ = [
        k for k in keys if len({json.dumps(cfg.get(k), sort_keys=True) for cfg in configs}) > 1
    ]
    return [{f"config.{k}": cfg.get(k) for k in differ} for cfg in configs]


def reference(target: Target, run_id: str, field: str) -> float | None:
    """Reduce a reference run named by ``ref``.

    :param target: Any target, for its index.
    :param run_id: The reference run's id.
    :param field: The reduced field.
    :return: Its value, or ``None`` if it is missing."""
    from beamtime.query import models as m
    from beamtime.query.kinds import Context, select_runs

    ctx = Context(index=target.index, caller="cli", scope=".", run_id=None, now=0.0)
    try:
        runs, _ = select_runs(ctx, m.Selection(), [field], restrict=("runs.id = ?", [run_id]))
    except QueryError:
        return None
    value = runs[0][field] if runs else None
    return value if isinstance(value, (int, float)) and math.isfinite(value) else None


def newest_verdict(target: Target, version: str) -> dict[str, Any] | None:
    """Find the newest verdict note on a proposal version.

    :param target: The group or run.
    :param version: The version id.
    :return: Its fields plus ``id``, or ``None``."""
    row = target.index.store.db.execute(
        "SELECT id, meta FROM notes WHERE folder = ? AND type = 'verdict' "
        "AND json_extract(meta, '$.proposal') = ? ORDER BY id DESC LIMIT 1",
        (target.rel, version),
    ).fetchone()
    return None if row is None else json.loads(row[1]) | {"id": row[0]}


def cited_by(target: Target, link: str) -> list[dict[str, Any]]:
    """List the notes that link to something.

    :param target: Any target, for its index.
    :param link: The link target, e.g. ``scaling/warmup#warmup-helps``.
    :return: Id, type and description of each citing note."""
    rows = target.index.store.db.execute(
        "SELECT DISTINCT notes.id, notes.type, notes.description FROM links "
        "JOIN notes ON notes.path = links.source WHERE links.target = ? ORDER BY notes.id",
        (link,),
    )
    return [{"id": r[0], "type": r[1], "description": r[2]} for r in rows]


def snapshot(check: dict[str, Any]) -> dict[str, Any]:
    """Shrink a check to what a verdict note keeps of it.

    :param check: The output of ``evaluate``.
    :return: Per prediction: result, effect, interval and points."""
    out = {}
    for p in check.get("predictions", []):
        out[p["name"]] = {
            k: p[k] for k in ("result", "effect", "ci", "points") if p.get(k) is not None
        }
    return out
