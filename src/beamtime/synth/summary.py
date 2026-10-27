"""Exact run cards and previews computed from a whole series.

The SDK computes both incrementally in constant memory; these batch versions are the
reference its property tests compare against."""

import math
from collections.abc import Iterable
from typing import Any

from beamtime.format import constants as c


def series(rows: Iterable[dict[str, Any]]) -> dict[str, list[tuple[int, float]]]:
    """Split effective metric records into one series per key.

    :param rows: Effective records with ``_step`` and ``_t``, sorted by step.
    :return: Per key, its ``(step, value)`` points in order."""
    out: dict[str, list[tuple[int, float]]] = {}
    for r in rows:
        for k, v in r.items():
            if not k.startswith("_"):
                out.setdefault(k, []).append((r["_step"], v))
    return out


def bucket_width(first_step: int, last_step: int) -> int:
    """Find the smallest power-of-two bucket width giving at most 512 buckets.

    :param first_step: The metric's first step.
    :param last_step: The metric's last step.
    :return: The bucket width."""
    w = 1
    while last_step // w - first_step // w + 1 > c.MAX_BUCKETS:
        w *= 2
    return w


def metric_preview(points: list[tuple[int, float]]) -> dict[str, Any] | None:
    """Downsample one metric into fixed buckets over its finite values.

    :param points: The metric's ``(step, value)`` points, sorted by step.
    :return: The preview entry, or ``None`` if no value is finite."""
    finite = [(s, v) for s, v in points if math.isfinite(v)]
    if not finite:
        return None
    w = bucket_width(finite[0][0], finite[-1][0])
    first = finite[0][0] // w
    n = finite[-1][0] // w - first + 1
    buckets: list[list[float]] = [[] for _ in range(n)]
    for s, v in finite:
        buckets[s // w - first].append(v)
    return {
        "bucket_width": w,
        "first_bucket": first,
        "min": [min(b) if b else None for b in buckets],
        "max": [max(b) if b else None for b in buckets],
        "last": [b[-1] if b else None for b in buckets],
        "mean": [math.fsum(b) / len(b) if b else None for b in buckets],
        "count": [len(b) if b else None for b in buckets],
    }


def slope_last10pct(preview: dict[str, Any], first_step: int, last_step: int) -> float | None:
    """Fit a line to the bucket means of the last 10 % of a metric's steps.

    :param preview: The metric's preview entry.
    :param first_step: The metric's first step.
    :param last_step: The metric's last step.
    :return: The slope per step, or ``None`` with fewer than two buckets."""
    w, first = preview["bucket_width"], preview["first_bucket"]
    start = last_step - 0.1 * (last_step - first_step)
    xs, ys = [], []
    for i, m in enumerate(preview["mean"]):
        if m is not None and (first + i) * w >= start:
            xs.append((first + i) * w + (w - 1) / 2)
            ys.append(m)
    if len(xs) < 2:
        return None
    mx, my = math.fsum(xs) / len(xs), math.fsum(ys) / len(ys)
    sxx = math.fsum((x - mx) ** 2 for x in xs)
    return math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True)) / sxx


def metric_summary(
    points: list[tuple[int, float]], preview: dict[str, Any] | None
) -> dict[str, Any]:
    """Summarize one metric for the run card; statistics cover finite values only.

    :param points: The metric's ``(step, value)`` points, sorted by step.
    :param preview: The metric's preview entry, for the slope.
    :return: The card entry."""
    finite = [(s, v) for s, v in points if math.isfinite(v)]
    out: dict[str, Any] = {
        "count": len(finite),
        "nonfinite": len(points) - len(finite),
        "last_step": points[-1][0],
    }
    if not finite:
        return out
    ema = finite[0][1]
    for _, v in finite:
        ema = c.EMA_SMOOTHING * ema + (1 - c.EMA_SMOOTHING) * v
    lo = min(finite, key=lambda p: p[1])
    hi = max(finite, key=lambda p: p[1])
    return out | {
        "first": finite[0][1],
        "last": finite[-1][1],
        "ema_last": ema,
        "min": lo[1],
        "min_step": lo[0],
        "max": hi[1],
        "max_step": hi[0],
        "mean": math.fsum(v for _, v in finite) / len(finite),
        "slope_last10pct": slope_last10pct(preview, finite[0][0], finite[-1][0])
        if preview
        else None,
    }


def card_and_preview(
    rows: list[dict[str, Any]],
    *,
    status: str,
    duration_s: float,
    error: str | None = None,
    warnings: int = 0,
    values: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute a run's ``_run_card.json`` and ``_preview.json`` from its records.

    :param rows: The effective metric records, sorted by step.
    :param status: The run status.
    :param duration_s: The run's wall-clock duration.
    :param error: The last exception line of a failed run.
    :param warnings: The number of SDK warnings.
    :param values: Values set explicitly on the card.
    :return: The card and the preview."""
    previews, metrics = {}, {}
    for key, points in series(rows).items():
        if (p := metric_preview(points)) is not None:
            previews[key] = p
        metrics[key] = metric_summary(points, p)
    steps = rows[-1]["_step"] if rows else 0
    card = {
        "schema": 1,
        "status": status,
        "duration_s": round(duration_s, 3),
        "steps": steps,
        "steps_per_s": round(steps / duration_s, 3) if duration_s > 0 else None,
        "error": error,
        "warnings": warnings,
        "metrics": metrics,
        "values": values or {},
    }
    return card, {"schema": 1, "metrics": previews}
