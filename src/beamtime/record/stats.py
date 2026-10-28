"""Student-t quantiles and the intervals of the check, in pure Python."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

TINY = 1e-300
EPS = 1e-15


def betacf(a: float, b: float, x: float) -> float:
    """Evaluate the continued fraction of the incomplete beta function (modified Lentz).

    :param a: The first shape parameter.
    :param b: The second shape parameter.
    :param x: The point, in (0, 1).
    :return: The continued fraction's value."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > TINY else TINY)
    h = d
    for m in range(1, 10_000):
        m2 = 2 * m
        for aa in (
            m * (b - m) * x / ((qam + m2) * (a + m2)),
            -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2)),
        ):
            d = 1.0 + aa * d
            d = 1.0 / (d if abs(d) > TINY else TINY)
            c = 1.0 + aa / c
            c = c if abs(c) > TINY else TINY
            h *= d * c
        if abs(d * c - 1.0) < EPS:
            break
    return h


def betainc(a: float, b: float, x: float) -> float:
    """Compute the regularized incomplete beta function I_x(a, b).

    :param a: The first shape parameter, positive.
    :param b: The second shape parameter, positive.
    :param x: The point, in [0, 1].
    :return: The value, in [0, 1]."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * betacf(a, b, x) / a
    return 1.0 - front * betacf(b, a, 1.0 - x) / b


def t_tail(t: float, df: float) -> float:
    """Compute the upper tail P(T > t) of Student's t distribution, for t >= 0.

    :param t: The point.
    :param df: The degrees of freedom, positive and possibly fractional.
    :return: The tail probability."""
    return 0.5 * betainc(df / 2.0, 0.5, df / (df + t * t))


def t_pdf(t: float, df: float) -> float:
    """Compute the density of Student's t distribution.

    :param t: The point.
    :param df: The degrees of freedom.
    :return: The density."""
    log_norm = math.lgamma((df + 1) / 2) - math.lgamma(df / 2) - 0.5 * math.log(df * math.pi)
    return math.exp(log_norm - (df + 1) / 2 * math.log1p(t * t / df))


def t_quantile(p: float, df: float) -> float:
    """Invert Student's t distribution: Newton steps on the upper tail, kept in a bracket.

    :param p: The probability, in (0, 1).
    :param df: The degrees of freedom, positive and possibly fractional.
    :return: The t with P(T <= t) = p."""
    if not 0.0 < p < 1.0 or not df > 0:
        raise ValueError(f"t_quantile needs 0 < p < 1 and df > 0, got p={p}, df={df}")
    if p < 0.5:
        return -t_quantile(1.0 - p, df)
    if p == 0.5:
        return 0.0
    # the upper tail keeps full relative precision where p is close to 1.
    q = 1.0 - p
    lo, hi = 0.0, 1.0
    while t_tail(hi, df) > q:
        lo, hi = hi, hi * 2.0
    t = (lo + hi) / 2.0
    for _ in range(200):
        f = t_tail(t, df) - q
        if f > 0:
            lo = t
        else:
            hi = t
        nxt = t + f / t_pdf(t, df)
        if not lo < nxt < hi:
            nxt = (lo + hi) / 2.0
        if abs(nxt - t) <= 1e-13 * max(1.0, abs(t)):
            return nxt
        t = nxt
    return t


@dataclass(kw_only=True, frozen=True)
class Interval:
    """An estimate with its interval and the number of values behind it."""

    estimate: float
    lo: float
    hi: float
    n: int
    df: float | None = None

    def shift(self, by: float) -> "Interval":
        """Move the estimate and both ends.

        :param by: The amount to subtract.
        :return: The shifted interval."""
        return Interval(
            estimate=self.estimate - by, lo=self.lo - by, hi=self.hi - by, n=self.n, df=self.df
        )


def mean(xs: Sequence[float]) -> float:
    """Average exactly.

    :param xs: The values, at least one.
    :return: The mean."""
    return math.fsum(xs) / len(xs)


def variance(xs: Sequence[float]) -> float:
    """Compute the sample variance.

    :param xs: The values, at least two.
    :return: The variance with n - 1 in the denominator."""
    m = mean(xs)
    return math.fsum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def mean_interval(xs: Sequence[float], level: float | None) -> Interval:
    """Give a t-interval for a mean, or the mean alone without a level.

    :param xs: The values; at least two when a level is given.
    :param level: The confidence level, e.g. 0.95; ``None`` takes no uncertainty into account.
    :return: The interval."""
    m = mean(xs)
    if level is None:
        return Interval(estimate=m, lo=m, hi=m, n=len(xs))
    n = len(xs)
    half = t_quantile((1 + level) / 2, n - 1) * math.sqrt(variance(xs) / n)
    return Interval(estimate=m, lo=m - half, hi=m + half, n=n, df=n - 1)


def welch_interval(a: Sequence[float], b: Sequence[float], level: float | None) -> Interval:
    """Give a Welch t-interval for the difference of two means.

    :param a: The first sample; at least two values when a level is given.
    :param b: The second sample; likewise.
    :param level: The confidence level; ``None`` takes no uncertainty into account.
    :return: The interval of mean(a) - mean(b)."""
    d = mean(a) - mean(b)
    n = len(a) + len(b)
    if level is None:
        return Interval(estimate=d, lo=d, hi=d, n=n)
    va, vb = variance(a) / len(a), variance(b) / len(b)
    if va + vb == 0:
        return Interval(estimate=d, lo=d, hi=d, n=n)
    df = (va + vb) ** 2 / (va**2 / (len(a) - 1) + vb**2 / (len(b) - 1))
    half = t_quantile((1 + level) / 2, df) * math.sqrt(va + vb)
    return Interval(estimate=d, lo=d - half, hi=d + half, n=n, df=df)


def paired_interval(a: Sequence[float], b: Sequence[float], level: float | None) -> Interval:
    """Give a paired t-interval for the mean difference.

    :param a: The first values.
    :param b: Their partners, in the same order.
    :param level: The confidence level; ``None`` takes no uncertainty into account.
    :return: The interval of mean(a - b)."""
    return mean_interval([x - y for x, y in zip(a, b, strict=True)], level)
