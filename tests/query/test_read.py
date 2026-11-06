import math
import random
from array import array

import pytest

from beamtime.format.run import MetricPreview
from beamtime.query.read import (
    bucket_means,
    downsample,
    elapsed_values,
    ema,
    from_preview,
    value_at,
    width_for,
    window_stat,
)
from beamtime.sdk.stats import MetricStats


def random_series(rng: random.Random, n: int, nonfinite: bool) -> tuple[array, array]:
    """Make sorted steps with repeats and gaps, and values with spikes.

    :param rng: The random source.
    :param n: Number of points.
    :param nonfinite: Whether to include NaN and infinities.
    :return: Steps and values."""
    steps, values, s = array("q"), array("d"), rng.randrange(0, 1000)
    for _ in range(n):
        s += rng.choice([0, 1, 1, 1, 2, 50, rng.randrange(1, 5000)])
        v = rng.gauss(0, 1) * (100 if rng.random() < 0.01 else 1)
        if nonfinite and rng.random() < 0.03:
            v = rng.choice([math.nan, math.inf, -math.inf])
        steps.append(s)
        values.append(v)
    return steps, values


def brute_buckets(steps, values, lo, hi, width):
    """Recompute min, max, last and count per bucket the slow way.

    :return: Bucket start to (min, max, last, count)."""
    out: dict[int, list] = {}
    for s, v in zip(steps, values, strict=True):
        if (lo is not None and s < lo) or (hi is not None and s > hi) or not math.isfinite(v):
            continue
        out.setdefault(s // width * width, []).append(v)
    return {b: (min(vs), max(vs), vs[-1], len(vs)) for b, vs in out.items()}


@pytest.mark.parametrize("seed", range(30))
def test_downsample_matches_brute_force(seed: int) -> None:
    """Every bucket's min, max, last and count equal a direct recomputation."""
    rng = random.Random(seed)
    steps, values = random_series(rng, rng.choice([5, 300, 3000]), seed % 2 == 0)
    window = rng.choice([(None, None), (steps[len(steps) // 4], steps[-len(steps) // 4])])
    points = rng.choice([10, 64, 500])
    curve = downsample(steps, values, window=window, points=points)
    lo, hi = window
    if curve["raw"]:
        inside = [
            (s, v)
            for s, v in zip(steps, values)
            if (lo is None or s >= lo) and (hi is None or s <= hi)
        ]
        assert curve["x"] == [s for s, _ in inside]
        assert all(
            (y is None and not math.isfinite(v)) or y == v
            for y, (_, v) in zip(curve["y"], inside, strict=True)
        )
        return
    assert len(curve["x"]) <= points + 1
    expected = brute_buckets(steps, values, lo, hi, curve["width"])
    got = {
        x: (a, b, c, n)
        for x, a, b, c, n in zip(
            curve["x"], curve["min"], curve["max"], curve["last"], curve["count"], strict=True
        )
    }
    assert got == expected


@pytest.mark.parametrize("seed", range(30))
def test_window_stats_match_brute_force(seed: int) -> None:
    """Windowed first, last, min, max, mean and count are exact."""
    rng = random.Random(seed)
    steps, values = random_series(rng, 1000, seed % 2 == 0)
    lo, hi = sorted(rng.sample(range(steps[0], steps[-1] + 1), 2))
    inside = [v for s, v in zip(steps, values) if lo <= s <= hi and math.isfinite(v)]
    for stat, want in (
        ("count", len(inside)),
        ("first", inside[0] if inside else None),
        ("last", inside[-1] if inside else None),
        ("min", min(inside) if inside else None),
        ("max", max(inside) if inside else None),
        ("mean", math.fsum(inside) / len(inside) if inside else None),
    ):
        assert window_stat(steps, values, (lo, hi), stat) == want, stat


@pytest.mark.parametrize("seed", range(30))
def test_preview_answers_equal_column_answers(seed: int) -> None:
    """Whenever the preview answers, it gives exactly what the columns give."""
    rng = random.Random(seed)
    steps, values = random_series(rng, rng.choice([600, 4000, 20000]), seed % 3 == 0)
    stats = MetricStats()
    for s, v in zip(steps, values, strict=True):
        stats.add(s, v)
    p = stats.preview()
    preview = MetricPreview(**p)
    answered = 0
    for points in (8, 30, 100, 300, 1000):
        curve = from_preview(preview, points)
        if curve is None:
            continue
        answered += 1
        columns = downsample(steps, values, points=points)
        assert not columns["raw"] and curve["width"] == columns["width"]
        for k in ("x", "count", "min", "max", "last"):
            if k in ("min", "max", "last"):
                assert curve[k] == pytest.approx(columns[k]), (points, k)
            else:
                assert curve[k] == columns[k], (points, k)
    if len(steps) >= 4000:
        assert answered


def test_width_is_a_power_of_two_with_stable_edges() -> None:
    """Widths are powers of two; growing a range keeps old edges."""
    assert width_for(0, 999, 100) == 16
    assert width_for(0, 99, 100) == 1
    w = width_for(0, 10_000, 100)
    assert w & (w - 1) == 0 and 10_000 // w + 1 <= 100


def test_ema_value_at_and_bucket_means() -> None:
    """Smoothing passes non-finite values; lookups and group means are exact."""
    smoothed = ema([1.0, 3.0, math.nan, 3.0], 0.5)
    assert smoothed[:2] == [1.0, 2.0] and math.isnan(smoothed[2]) and smoothed[3] == 2.5
    assert value_at([0, 10, 20], [1.0, 2.0, 3.0], 15) == 2.0
    assert value_at([5], [1.0], 4) is None
    means = bucket_means([0, 1, 2, 5], [1.0, 3.0, math.nan, 4.0], window=(None, None), width=4)
    assert means == {0: 2.0, 4: 4.0}


def test_elapsed_values_skips_queue_gaps() -> None:
    """Elapsed time subtracts the cumulative gap of every attempt up to a step."""
    steps = [0, 1, 2, 3]
    times = [100.0, 101.0, 2000.0, 2001.0]  # a 1800 s queue wait before step 2
    assert elapsed_values(steps, times, [0, 1, 2, 3], []) == [0.0, 1.0, 1900.0, 1901.0]
    assert elapsed_values(steps, times, [0, 1, 2, 3], [(2, 1899.0)]) == [0.0, 1.0, 1.0, 2.0]
    assert elapsed_values(steps, times, [-1], [(2, 1899.0)]) == [None]
    assert elapsed_values([], [], [0], [(2, 1.0)]) == [None]
