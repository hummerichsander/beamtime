"""The one read path: windows, statistics and downsampling over columns and previews.

Every number a query, a view or a prediction check shows comes from these functions,
in pure Python with ``math.fsum``, so no two callers can disagree. Statistics and
downsampled buckets cover finite values only, like the run card and the preview."""

import math
from bisect import bisect_left, bisect_right
from collections.abc import Sequence
from typing import Any

from beamtime.format.run import MetricPreview


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
