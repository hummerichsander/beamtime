"""Vector PDF figures of charts, drawn with matplotlib in the scienceplots style.

The web UI sends what a chart shows (its curves, points, bars or histograms, already smoothed,
filtered and colored in the light theme); this module only draws. It needs the ``figures`` extra."""

import io
import math
from typing import Any, Literal

import msgspec

from beamtime.ops.context import OpError

SIZE = (3.3, 2.5)
LEGEND_MAX = 12
Scale = Literal["linear", "log", "symlog"]


class Figure(msgspec.Struct, kw_only=True):
    """What the UI asks to draw."""

    kind: Literal["line", "scatter", "bar", "histogram"]
    title: str | None = None
    xlabel: str | None = None
    ylabel: str | None = None
    xscale: Scale = "linear"
    yscale: Scale = "linear"
    ylim: list[float | None] | None = None
    series: list[dict[str, Any]] = msgspec.field(default_factory=list)
    categories: list[str] = msgspec.field(default_factory=list)
    groups: list[dict[str, Any]] = msgspec.field(default_factory=list)
    fit: dict[str, Any] | None = None


def pdf(data: dict[str, Any]) -> bytes:
    """Draw a chart as a PDF.

    :param data: The figure as the UI sends it.
    :return: The PDF."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import scienceplots  # noqa: F401
    except ImportError:
        raise OpError(
            "PDF figures need matplotlib and scienceplots: install beamtime with the figures "
            "extra, e.g. `uv add 'beamtime[figures]'`",
            code=3,
        ) from None
    try:
        fig_spec = msgspec.convert(data, Figure)
    except msgspec.ValidationError as e:
        raise OpError(f"figure: {e}", code=2) from None
    with plt.style.context(["science", "nature", "no-latex"]):
        fig, ax = plt.subplots(figsize=SIZE)
        match fig_spec.kind:
            case "line":
                line(ax, fig_spec)
            case "scatter":
                scatter(ax, fig_spec)
            case "bar":
                bar(ax, fig_spec)
            case "histogram":
                histogram(ax, fig_spec)
            case other:
                raise ValueError(f"no figure kind {other!r}")
        axes(ax, fig_spec)
        out = io.BytesIO()
        fig.savefig(out, format="pdf", bbox_inches="tight")
        plt.close(fig)
    return out.getvalue()


def line(ax: Any, f: Figure) -> None:
    """Draw curves, with their bands where given.

    :param ax: The axes.
    :param f: The figure."""
    for s in f.series:
        x = s["x"]
        ax.plot(x, nums(s["y"]), color=s.get("color"), label=s.get("label"))
        if s.get("lo") and s.get("hi"):
            ax.fill_between(x, nums(s["lo"]), nums(s["hi"]), color=s.get("color"), alpha=0.2, lw=0)


def scatter(ax: Any, f: Figure) -> None:
    """Draw points with error bars, and the fit.

    :param ax: The axes.
    :param f: The figure."""
    for s in f.series:
        err = s.get("err") or []
        yerr = [e or 0 for e in err] if any(err) else None
        ax.errorbar(s["x"], s["y"], yerr=yerr, fmt="o", color=s.get("color"), label=s.get("label"))
    if f.fit:
        ax.plot(f.fit["x"], f.fit["y"], ls="--", color="0.5")


def bar(ax: Any, f: Figure) -> None:
    """Draw grouped bars with error bars.

    :param ax: The axes.
    :param f: The figure."""
    n = max(1, len(f.groups))
    width = 0.8 / n
    for j, g in enumerate(f.groups):
        xs = [i - 0.4 + (j + 0.5) * width for i in range(len(f.categories))]
        values = nums(g["value"])
        lo, hi = nums(g.get("lo") or []), nums(g.get("hi") or [])
        yerr = None
        if lo and hi and not all(math.isnan(v) for v in lo):
            # matplotlib wants distances below and above each bar; gaps draw no error bar.
            below = [v - a for v, a in zip(values, lo, strict=True)]
            above = [b - v for v, b in zip(values, hi, strict=True)]
            yerr = [[0.0 if math.isnan(e) else max(0.0, e) for e in row] for row in (below, above)]
        ax.bar(xs, values, width * 0.9, yerr=yerr, color=g.get("colors"), label=g.get("label"))
    ax.set_xticks(range(len(f.categories)), f.categories)


def histogram(ax: Any, f: Figure) -> None:
    """Draw histograms as outlines with a light fill.

    :param ax: The axes.
    :param f: The figure."""
    for s in f.series:
        edges = [*s["start"], s["end"][-1]]
        alpha = 0.25 if len(f.series) == 1 else 0.1
        ax.stairs(s["count"], edges, color=s.get("color"), label=s.get("label"))
        ax.stairs(s["count"], edges, color=s.get("color"), fill=True, alpha=alpha)


def axes(ax: Any, f: Figure) -> None:
    """Label and scale the axes, and add a legend where it helps.

    :param ax: The axes.
    :param f: The figure."""
    if f.xlabel:
        ax.set_xlabel(f.xlabel)
    if f.ylabel:
        ax.set_ylabel(f.ylabel)
    for axis, scale, values in (("x", f.xscale, xvalues(f)), ("y", f.yscale, yvalues(f))):
        setter = ax.set_xscale if axis == "x" else ax.set_yscale
        match scale:
            case "log":
                setter("log")
            case "symlog":
                setter("symlog", linthresh=linthresh(values))
            case "linear":
                pass
            case other:
                raise ValueError(f"no scale {other!r}")
    if f.ylim and any(v is not None for v in f.ylim):
        ax.set_ylim(*f.ylim)
    labels = [h for h in ax.get_legend_handles_labels()[1] if h]
    if 2 <= len(labels) <= LEGEND_MAX:
        ax.legend()


def nums(values: list[Any]) -> list[float]:
    """Turn gaps into NaN, which matplotlib leaves out.

    :param values: Numbers and ``None``.
    :return: Floats."""
    return [math.nan if v is None else float(v) for v in values]


def xvalues(f: Figure) -> list[float]:
    """Collect the figure's x values.

    :param f: The figure.
    :return: The values."""
    return [v for s in f.series for v in s.get("x", []) if v is not None]


def yvalues(f: Figure) -> list[float]:
    """Collect the figure's y values.

    :param f: The figure.
    :return: The values."""
    out = [v for s in f.series for v in s.get("y", []) or [] if v is not None]
    return out + [v for g in f.groups for v in g.get("value", []) if v is not None]


def linthresh(values: list[float]) -> float:
    """Pick a symlog threshold like the web UI does.

    :param values: The values on the axis.
    :return: The power of ten at about the smallest tenth of the absolute values."""
    small = sorted(abs(v) for v in values if v and math.isfinite(v))
    if not small:
        return 1.0
    return 10 ** math.floor(math.log10(small[len(small) // 10]))
