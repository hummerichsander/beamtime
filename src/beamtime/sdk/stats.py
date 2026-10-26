"""Run card statistics and preview buckets, kept in constant memory per metric."""

import math
from typing import Any

from beamtime.format import constants as c


class MetricStats:
    """Running statistics and preview buckets of one scalar metric."""

    def __init__(self) -> None:
        """Start with no values."""
        self.count = 0
        self.nonfinite = 0
        self.total = 0.0
        self.first: float | None = None
        self.last: float | None = None
        self.ema: float | None = None
        self.min: float | None = None
        self.min_step: int | None = None
        self.max: float | None = None
        self.max_step: int | None = None
        self.first_step: int | None = None
        self.last_finite_step: int | None = None
        self.last_step: int | None = None
        self.width = 1
        self.first_bucket = 0
        # per bucket [min, max, last, sum, count], or None while empty.
        self.buckets: list[list[float] | None] = []

    def add(self, step: int, value: float) -> None:
        """Add one logged value; non-finite values are only counted.

        :param step: The step, not lower than the previous one.
        :param value: The value."""
        self.last_step = step
        if not math.isfinite(value):
            self.nonfinite += 1
            return
        self.count += 1
        self.total += value
        if self.first is None:
            self.first, self.ema, self.first_step = value, value, step
        self.ema = c.EMA_SMOOTHING * self.ema + (1 - c.EMA_SMOOTHING) * value
        self.last, self.last_finite_step = value, step
        if self.min is None or value < self.min:
            self.min, self.min_step = value, step
        if self.max is None or value > self.max:
            self.max, self.max_step = value, step
        self.add_to_bucket(step, value)

    def add_to_bucket(self, step: int, value: float) -> None:
        """Put a finite value into its bucket, widening buckets when there are too many.

        :param step: The step.
        :param value: The value."""
        if not self.buckets:
            self.first_bucket = step // self.width
        while step // self.width - self.first_bucket + 1 > c.MAX_BUCKETS:
            self.merge()
        i = step // self.width - self.first_bucket
        self.buckets.extend([None] * (i + 1 - len(self.buckets)))
        if (b := self.buckets[i]) is None:
            self.buckets[i] = [value, value, value, value, 1]
        else:
            b[0], b[1], b[2] = min(b[0], value), max(b[1], value), value
            b[3] += value
            b[4] += 1

    def merge(self) -> None:
        """Double the bucket width, merging neighbouring buckets with fixed edges."""
        first = self.first_bucket // 2
        merged: list[list[float] | None] = [None] * (
            (self.first_bucket + len(self.buckets) - 1) // 2 - first + 1
        )
        for i, b in enumerate(self.buckets):
            if b is None:
                continue
            j = (self.first_bucket + i) // 2 - first
            if (m := merged[j]) is None:
                merged[j] = list(b)
            else:
                m[0], m[1], m[2] = min(m[0], b[0]), max(m[1], b[1]), b[2]
                m[3] += b[3]
                m[4] += b[4]
        self.width *= 2
        self.first_bucket = first
        self.buckets = merged

    def preview(self) -> dict[str, Any] | None:
        """Build the metric's ``_preview.json`` entry.

        :return: The entry, or ``None`` without finite values."""
        if not self.count:
            return None
        bs = self.buckets
        return {
            "bucket_width": self.width,
            "first_bucket": self.first_bucket,
            "min": [b[0] if b else None for b in bs],
            "max": [b[1] if b else None for b in bs],
            "last": [b[2] if b else None for b in bs],
            "mean": [b[3] / b[4] if b else None for b in bs],
            "count": [b[4] if b else None for b in bs],
        }

    def slope_last10pct(self) -> float | None:
        """Fit a line to the bucket means of the last 10 % of the metric's steps.

        :return: The slope per step, or ``None`` with fewer than two buckets."""
        if not self.count:
            return None
        start = self.last_finite_step - 0.1 * (self.last_finite_step - self.first_step)
        xs, ys = [], []
        for i, b in enumerate(self.buckets):
            if b is not None and (self.first_bucket + i) * self.width >= start:
                xs.append((self.first_bucket + i) * self.width + (self.width - 1) / 2)
                ys.append(b[3] / b[4])
        if len(xs) < 2:
            return None
        mx, my = math.fsum(xs) / len(xs), math.fsum(ys) / len(ys)
        sxx = math.fsum((x - mx) ** 2 for x in xs)
        sxy = math.fsum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
        return sxy / sxx

    def card(self) -> dict[str, Any]:
        """Build the metric's run card entry.

        :return: The entry; statistics cover finite values only."""
        out: dict[str, Any] = {
            "count": self.count,
            "nonfinite": self.nonfinite,
            "last_step": self.last_step,
        }
        if not self.count:
            return out
        return out | {
            "first": self.first,
            "last": self.last,
            "ema_last": self.ema,
            "min": self.min,
            "min_step": self.min_step,
            "max": self.max,
            "max_step": self.max_step,
            "mean": self.total / self.count,
            "slope_last10pct": self.slope_last10pct(),
        }
