"""The one read path: windows, statistics and downsampling over columns and previews.

Every number a query, a view or a prediction check shows comes from these functions,
in pure Python with ``math.fsum``, so no two callers can disagree. Statistics and
downsampled buckets cover finite values only, like the run card and the preview."""

import math
from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from beamtime.format.run import MetricPreview
from beamtime.index.columns import TIME_KEY

if TYPE_CHECKING:
    from beamtime.query.select import Columns


def finite(values: Sequence[float]) -> Sequence[float]:
    """Drop NaN and infinite values.

    :param values: The values.
    :return: The finite values."""
    return [v for v in values if math.isfinite(v)]


def window_stat(
    steps: Sequence[int],
    values: Sequence[float],
    window: tuple[int | None, int | None],
    stat: str,
    *,
    nonfinite: bool = True,
) -> float | int | None:
    """Compute a statistic over a step window exactly.

    :param steps: The sorted steps.
    :param values: The values.
    :param window: ``(first step, last step)``, inclusive; ``None`` for open ends.
    :param stat: ``first``, ``last``, ``min``, ``max``, ``mean`` or ``count``.
    :param nonfinite: Whether the values may contain NaN or infinities.
    :return: The statistic, or ``None`` without finite values in the window."""
    lo, hi = window
    i = 0 if lo is None else bisect_left(steps, lo)
    j = len(steps) if hi is None else bisect_right(steps, hi)
    vals = values[i:j]
    if nonfinite:
        vals = finite(vals)
    if stat == "count":
        return len(vals)
    if not len(vals):
        return None
    match stat:
        case "first":
            return vals[0]
        case "last":
            return vals[-1]
        case "min":
            return min(vals)
        case "max":
            return max(vals)
        case "mean":
            return math.fsum(vals) / len(vals)
        case _:
            raise ValueError(f"unknown window statistic {stat!r}")


def width_for(lo: int, hi: int, points: int) -> int:
    """Find the bucket width for a step range: the smallest power of two giving at
    most ``points`` buckets, with edges at multiples of it so live curves don't jitter.

    :param lo: The first step.
    :param hi: The last step.
    :param points: The most buckets wanted.
    :return: The width."""
    w = 1
    while hi // w - lo // w + 1 > points:
        w *= 2
    return w


def finite_range(
    steps: Sequence[int], values: Sequence[float], i: int, j: int, nonfinite: bool
) -> tuple[int, int]:
    """Narrow an index range to its first and last finite value.

    :param steps: The steps.
    :param values: The values.
    :param i: The start index.
    :param j: The end index.
    :param nonfinite: Whether the values may contain NaN or infinities.
    :return: The narrowed range; empty if nothing is finite."""
    if not nonfinite:
        return i, j
    while i < j and not math.isfinite(values[i]):
        i += 1
    while j > i and not math.isfinite(values[j - 1]):
        j -= 1
    return i, j


def downsample(
    steps: Sequence[int],
    values: Sequence[float],
    *,
    window: tuple[int | None, int | None] = (None, None),
    points: int,
    nonfinite: bool = True,
) -> dict[str, Any]:
    """Return a curve raw if it fits ``points``, else min, max and last per bucket.

    :param steps: The sorted steps.
    :param values: The values.
    :param window: ``(first step, last step)``, inclusive; ``None`` for open ends.
    :param points: The point budget of the curve.
    :param nonfinite: Whether the values may contain NaN or infinities.
    :return: ``{raw: True, x, y}`` (non-finite values as ``None``) or
        ``{raw: False, width, x, first, min, max, last, count}``; ``x`` is the bucket
        start and ``first`` the first step with data in it."""
    lo, hi = window
    i = 0 if lo is None else bisect_left(steps, lo)
    j = len(steps) if hi is None else bisect_right(steps, hi)
    if j - i <= points:
        ys = values[i:j].tolist() if hasattr(values, "tolist") else list(values[i:j])
        if nonfinite:
            ys = [v if math.isfinite(v) else None for v in ys]
        xs = steps[i:j].tolist() if hasattr(steps, "tolist") else list(steps[i:j])
        return {"raw": True, "x": xs, "y": ys}
    a, b = finite_range(steps, values, i, j, nonfinite)
    out: dict[str, Any] = {"raw": False, "width": 1, "x": [], "first": []}
    out |= {"min": [], "max": [], "last": [], "count": []}
    if a >= b:
        return out
    w = width_for(steps[a], steps[b - 1], points)
    out["width"] = w
    for bucket in range(steps[a] // w, steps[b - 1] // w + 1):
        s = bisect_left(steps, bucket * w, a, b)
        e = bisect_left(steps, (bucket + 1) * w, s, b)
        chunk = values[s:e]
        if nonfinite:
            chunk = finite(chunk)
        if not len(chunk):
            continue
        out["x"].append(bucket * w)
        out["first"].append(steps[s])
        out["min"].append(min(chunk))
        out["max"].append(max(chunk))
        out["last"].append(chunk[-1])
        out["count"].append(len(chunk))
    return out


def from_preview(preview: MetricPreview, points: int) -> dict[str, Any] | None:
    """Answer a full-range downsampled curve from a run's preview, if it is fine enough.

    The answer equals ``downsample`` over the column files whenever it is returned,
    except ``first``, which the preview doesn't keep (``None``).

    :param preview: The metric's preview.
    :param points: The point budget of the curve.
    :return: The curve, or ``None`` if the preview is too coarse or the curve is
        small enough to return raw."""
    pw, fb, n = preview.bucket_width, preview.first_bucket, len(preview.count)
    total = sum(c for c in preview.count if c)
    if total <= points or n == 0:
        return None
    last_b = fb + n - 1
    # counts are exact for widths >= pw; at pw / 2 they lie in [2 span, 2 span + 2].
    if last_b - fb + 1 <= points and pw > 1 and 2 * (last_b - fb) <= points:
        return None
    w = pw
    while (last_b * pw) // w - (fb * pw) // w + 1 > points:
        w *= 2
    merged: dict[int, list] = {}
    for k in range(n):
        if preview.count[k] is None:
            continue
        t = (fb + k) * pw // w
        lo, hi, last, cnt = (
            preview.min[k],
            preview.max[k],
            preview.last[k],
            preview.count[k],
        )
        if (m := merged.get(t)) is None:
            merged[t] = [lo, hi, last, cnt]
        else:
            m[0], m[1], m[2], m[3] = min(m[0], lo), max(m[1], hi), last, m[3] + cnt
    keys = sorted(merged)
    return {
        "raw": False,
        "width": w,
        "x": [t * w for t in keys],
        "first": [None] * len(keys),
        "min": [merged[t][0] for t in keys],
        "max": [merged[t][1] for t in keys],
        "last": [merged[t][2] for t in keys],
        "count": [merged[t][3] for t in keys],
    }


def ema(values: Sequence[float], weight: float) -> list[float]:
    """Smooth values exponentially; non-finite values pass through unsmoothed.

    :param values: The values in step order.
    :param weight: The weight of the previous smoothed value, e.g. 0.9.
    :return: The smoothed values."""
    out = []
    s = None
    for v in values:
        if math.isfinite(v):
            s = v if s is None else weight * s + (1 - weight) * v
            out.append(s)
        else:
            out.append(v)
    return out


def value_at(steps: Sequence[int], values: Sequence[float], step: int) -> float | None:
    """Read a series' most recent value at or before a step.

    :param steps: The sorted steps.
    :param values: The values.
    :param step: The step.
    :return: The value, or ``None`` before the first point."""
    i = bisect_right(steps, step) - 1
    return values[i] if i >= 0 else None


def elapsed_values(
    steps: Sequence[int],
    t_values: Sequence[float],
    query_steps: Sequence[int],
    gaps: Sequence[tuple[int, float]],
) -> list[float | None]:
    """Map steps to active elapsed time, skipping the queue wait between attempts.

    A point belongs to the latest attempt whose resume step is at or below it, since every
    attempt drops the points from its resume step on; it loses the gaps of that attempt and
    of every one before it.

    :param steps: The ``_t`` column's sorted steps.
    :param t_values: The ``_t`` column's wall-clock values.
    :param query_steps: The steps to map.
    :param gaps: ``(resume step, gap seconds)`` of every resumed attempt, in the order they ran.
    :return: Elapsed seconds per query step, or ``None`` before the first point."""
    if not len(steps):
        return [None] * len(query_steps)
    t0 = t_values[0]
    cumulative, total = [], 0.0
    for resume_step, gap in gaps:
        total += gap
        cumulative.append((resume_step, total))
    out = []
    for s in query_steps:
        if (t := value_at(steps, t_values, s)) is None:
            out.append(None)
            continue
        sub = 0.0
        for resume_step, running_total in cumulative:
            if s >= resume_step:
                sub = running_total
        out.append(t - t0 - sub)
    return out


def x_values(cols: "Columns", x: str, steps: Sequence[int]) -> list[float | None]:
    """Map steps to another x axis: wall time, active elapsed time or a metric's value.

    A metric that never decreases is a ramp: linear between the steps where its value changes,
    and beyond the last change on the slope of the last segment. Any other metric is read as its
    most recent value at or before the step.

    :param cols: The run's columns.
    :param x: ``_t``, ``_elapsed`` or a metric key.
    :param steps: The steps to map.
    :return: The x values; ``None`` before the axis' first point or if the run lacks it."""
    col = cols.get(TIME_KEY if x in (TIME_KEY, "_elapsed") else x)
    if col is None:
        return [None] * len(steps)
    if x == "_elapsed":
        gaps = [(a[1], a[2]) for a in cols.manifest.attempts if len(a) > 2]
        return elapsed_values(col.steps, col.values, steps, gaps)
    if x == TIME_KEY:
        return [value_at(col.steps, col.values, s) for s in steps]
    at, vs = [], []
    for s, v in zip(col.steps, col.values, strict=True):
        if not math.isfinite(v):
            continue
        if at and s == at[-1]:
            vs[-1] = v
        elif not vs or v != vs[-1]:
            at.append(s)
            vs.append(v)
    if not is_monotone(vs):
        raw = (value_at(col.steps, col.values, s) for s in steps)
        return [v if v is None or math.isfinite(v) else None for v in raw]
    out: list[float | None] = []
    for s in steps:
        if (i := bisect_right(at, s) - 1) < 0:
            out.append(None)
        elif s == at[i] or len(at) == 1:
            out.append(vs[i])
        else:
            j = min(i, len(at) - 2)
            out.append(vs[j] + (vs[j + 1] - vs[j]) * (s - at[j]) / (at[j + 1] - at[j]))
    return out


def is_monotone(values: Sequence[float]) -> bool:
    """Tell whether values never decrease.

    :param values: The values.
    :return: ``True`` for an empty, constant or rising sequence."""
    return all(a <= b for a, b in zip(values, values[1:], strict=False))


def bucket_means(
    steps: Sequence[int],
    values: Sequence[float],
    *,
    window: tuple[int | None, int | None],
    width: int,
    nonfinite: bool = True,
) -> dict[int, float]:
    """Average a curve's finite values per bucket, for grouped curves.

    :param steps: The sorted steps.
    :param values: The values.
    :param window: ``(first step, last step)``, inclusive; ``None`` for open ends.
    :param width: The bucket width.
    :param nonfinite: Whether the values may contain NaN or infinities.
    :return: Bucket start to mean."""
    lo, hi = window
    i = 0 if lo is None else bisect_left(steps, lo)
    j = len(steps) if hi is None else bisect_right(steps, hi)
    out = {}
    while i < j:
        bucket = steps[i] // width
        e = bisect_left(steps, (bucket + 1) * width, i, j)
        chunk = values[i:e]
        if nonfinite:
            chunk = finite(chunk)
        if len(chunk):
            out[bucket * width] = math.fsum(chunk) / len(chunk)
        i = e
    return out


def bucket_means_by_x(
    xs: Sequence[float], values: Sequence[float], *, lo: float, width: float, last: int
) -> dict[int, float]:
    """Average a curve's values per bucket of x, for grouped curves.

    :param xs: The x values, all known.
    :param values: The finite values at those x.
    :param lo: The left edge of the first bucket.
    :param width: The bucket width; zero puts everything in bucket 0.
    :param last: The index of the last bucket, which takes the right edge.
    :return: Bucket index to mean."""
    buckets: dict[int, list[float]] = {}
    for x, v in zip(xs, values, strict=True):
        b = 0 if width == 0 else min(int((x - lo) / width), last)
        buckets.setdefault(b, []).append(v)
    return {b: math.fsum(vs) / len(vs) for b, vs in buckets.items()}
