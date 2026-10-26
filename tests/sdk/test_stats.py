import math
import random

import pytest

from beamtime.sdk.stats import MetricStats
from beamtime.synth.summary import metric_preview, metric_summary


def random_series(rng: random.Random, n: int) -> list[tuple[int, float]]:
    """Make a sparse series with repeated steps, gaps, NaN and Infinity.

    :param rng: The random source.
    :param n: Number of points.
    :return: ``(step, value)`` points with non-decreasing steps."""
    step, out = rng.randrange(0, 5000), []
    for _ in range(n):
        step += rng.choice([0, 1, 1, 1, 3, 17, rng.randrange(1, 4000)])
        u = rng.random()
        v = math.nan if u < 0.02 else math.inf if u < 0.03 else rng.gauss(0, 10)
        out.append((step, v))
    return out


def same(a: object, b: object) -> bool:
    """Compare JSON-like values with a relative tolerance for floats.

    :param a: One value.
    :param b: The other.
    :return: Whether they agree."""
    if isinstance(a, float) and isinstance(b, float):
        return a == pytest.approx(b, rel=1e-9, abs=1e-9)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    return a == b


@pytest.mark.parametrize("seed", range(40))
def test_incremental_matches_exact(seed: int) -> None:
    """Card and preview built step by step equal the exact batch reference."""
    rng = random.Random(seed)
    points = random_series(rng, rng.choice([1, 2, 50, 600, 5000]))
    stats = MetricStats()
    for s, v in points:
        stats.add(s, v)
    preview = metric_preview(points)
    assert same(stats.preview(), preview)
    assert same(stats.card(), metric_summary(points, preview))


def test_long_dense_series_has_256_to_512_buckets() -> None:
    """A long dense metric keeps between 256 and 512 buckets."""
    stats = MetricStats()
    for s in range(100_000):
        stats.add(s, float(s))
    p = stats.preview()
    assert 256 < len(p["count"]) <= 512 and sum(p["count"]) == 100_000
    assert stats.card()["slope_last10pct"] == pytest.approx(1.0, rel=1e-2)


def test_only_nonfinite() -> None:
    """A metric without finite values has no preview and a short card entry."""
    stats = MetricStats()
    stats.add(3, math.nan)
    assert stats.preview() is None
    assert stats.card() == {"count": 0, "nonfinite": 1, "last_step": 3}
