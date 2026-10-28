import math

import pytest

from beamtime.record.stats import (
    betainc,
    mean_interval,
    paired_interval,
    t_pdf,
    t_quantile,
    welch_interval,
)

# scipy.stats.t.ppf, to ten decimals.
REFERENCE = {
    (0.95, 1): 6.3137515147,
    (0.95, 2): 2.9199855804,
    (0.95, 10): 1.8124611228,
    (0.95, 30): 1.6972608866,
    (0.975, 1): 12.7062047362,
    (0.975, 2): 4.3026527297,
    (0.975, 3): 3.1824463053,
    (0.975, 4): 2.7764451052,
    (0.975, 10): 2.228138852,
    (0.975, 30): 2.0422724563,
    (0.975, 1000): 1.9623390808,
    (0.975, 2.5): 3.574654842,
    (0.975, 7.3): 2.3450667365,
    (0.995, 1): 63.6567411629,
    (0.995, 2): 9.9248432009,
    (0.995, 3): 5.8409093097,
    (0.995, 30): 2.7499956536,
    (0.995, 2.5): 7.1637281389,
}


@pytest.mark.parametrize("p, df", list(REFERENCE))
def test_t_quantile_matches_reference(p: float, df: float) -> None:
    """Quantiles agree with SciPy to ten decimals, also for fractional df."""
    assert t_quantile(p, df) == pytest.approx(REFERENCE[(p, df)], abs=1e-9)


def test_t_quantile_properties() -> None:
    """The quantile is odd around 0.5, rises with p, and falls with df."""
    assert t_quantile(0.5, 3) == 0.0
    assert t_quantile(0.025, 4) == pytest.approx(-t_quantile(0.975, 4))
    qs = [t_quantile(p, 5) for p in (0.6, 0.8, 0.9, 0.99)]
    assert qs == sorted(qs)
    by_df = [t_quantile(0.975, df) for df in (1, 2, 5, 50, 500)]
    assert by_df == sorted(by_df, reverse=True)
    with pytest.raises(ValueError):
        t_quantile(1.0, 3)


def test_cdf_by_integration() -> None:
    """The quantile inverts the density, checked with Simpson's rule independently of
    the incomplete beta function."""
    df, p = 3.7, 0.9
    t = t_quantile(p, df)
    n = 2000
    h = t / n
    s = t_pdf(0, df) + t_pdf(t, df) + sum((4 if i % 2 else 2) * t_pdf(i * h, df) for i in range(1, n))
    assert 0.5 + s * h / 3 == pytest.approx(p, abs=1e-10)
    assert betainc(2.0, 3.0, 0.0) == 0.0 and betainc(2.0, 3.0, 1.0) == 1.0


def test_intervals() -> None:
    """Mean, Welch and paired intervals against hand-computed cases."""
    iv = mean_interval([1.0, 2.0, 3.0], 0.95)
    half = 4.302652729749464 * 1.0 / math.sqrt(3)
    assert (iv.estimate, iv.lo, iv.hi, iv.n, iv.df) == pytest.approx((2.0, 2 - half, 2 + half, 3, 2))
    direct = mean_interval([1.0, 2.0, 3.0], None)
    assert direct.lo == direct.hi == 2.0
    w = welch_interval([1.0, 2.0, 3.0], [1.0, 1.5, 2.0, 2.5], 0.95)
    va, vb = 1.0 / 3, (5 / 12) / 4
    df = (va + vb) ** 2 / (va**2 / 2 + vb**2 / 3)
    assert w.estimate == pytest.approx(0.25) and w.df == pytest.approx(df)
    assert w.hi - w.estimate == pytest.approx(t_quantile(0.975, df) * math.sqrt(va + vb))
    same = welch_interval([1.0, 1.0], [0.0, 0.0], 0.95)
    assert same.lo == same.hi == 1.0
    paired = paired_interval([2.0, 3.0, 4.0], [1.0, 2.5, 3.0], 0.95)
    assert paired.estimate == pytest.approx(mean_interval([1.0, 0.5, 1.0], 0.95).estimate)
