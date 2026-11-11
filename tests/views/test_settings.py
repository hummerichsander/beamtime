"""The settings of a line chart: names and defaults from ``m.Line``, and ``settle``."""

from copy import deepcopy
from typing import Any

import pytest

from beamtime.format.schema import SchemaError
from beamtime.views import model as m
from beamtime.views.settings import SEEDS_FIELD, SETTINGS, line_defaults, settle

EVERYTHING: dict[str, Any] = {
    "y": ["val/loss", "val/acc"],
    "x": "_elapsed",
    "color": "config.lr",
    "colormap": "magma",
    "by": "config.arm",
    "band": "std",
    "smooth": 0.6,
    "scale": "symlog",
    "steps": [10, None],
    "ymin": 0.1,
    "ymax": 2.0,
    "outliers": True,
    "raw": False,
    "legend": False,
}


def test_settings_and_defaults_come_from_the_struct() -> None:
    """The settable names are Line's own, without the node props and the authored fields."""
    assert set(SETTINGS) == set(EVERYTHING)
    defaults = line_defaults()
    assert "y" not in defaults and set(defaults) == set(SETTINGS) - {"y"}
    assert defaults["x"] == "_step" and defaults["band"] == "minmax" and defaults["raw"] is True
    assert defaults["scale"] is None and defaults["by"] is None


def test_settle_is_idempotent() -> None:
    """Settling the same settings twice writes what settling once did."""
    props: dict[str, Any] = {"id": "c", "y": "val/loss", "xlabel": "tokens"}
    settle(props, EVERYTHING)
    once = deepcopy(props)
    settle(props, EVERYTHING)
    assert props == once
    assert props["by"] == ["config.arm"] and props["y"] == ["val/loss", "val/acc"]
    assert "xlabel" not in props


def test_default_settings_leave_props_clean() -> None:
    """Settings at their default write nothing, and remove what an earlier choice wrote."""
    props: dict[str, Any] = {"id": "c", "y": "val/loss", "x": "_elapsed", "band": "std"}
    settle(props, {"x": "_step", "band": "minmax", "smooth": 0, "raw": True, "legend": True})
    assert props == {"id": "c", "y": "val/loss"}
    settle(props, {"ymin": None, "ymax": None, "steps": [None, None], "color": None})
    assert props == {"id": "c", "y": "val/loss"}


def test_scale_always_written() -> None:
    """A scale is explicit, even the linear one, since a loss without a scale is drawn log."""
    props: dict[str, Any] = {"id": "c", "y": "val/loss"}
    settle(props, {"scale": "linear"})
    assert props["scale"] == "linear"


def test_seeds_fold() -> None:
    """by seeds is the seeds field, by a key a list of it; each replaces the other."""
    props: dict[str, Any] = {"id": "c", "y": "val/loss"}
    settle(props, {"by": "seeds"})
    assert props["seeds"] == SEEDS_FIELD and "by" not in props
    settle(props, {"by": "config.arm"})
    assert props["by"] == ["config.arm"] and "seeds" not in props
    settle(props, {"by": None})
    assert props == {"id": "c", "y": "val/loss"}


def test_unknown_keys_dropped() -> None:
    """Settings the chart does not know, from old preferences or newer frontends, are ignored."""
    props: dict[str, Any] = {"id": "c", "y": "val/loss"}
    settle(props, {"zoom": [1, 2], "seeds": "config.x", "title": "no", "id": "other"})
    assert props == {"id": "c", "y": "val/loss"}


def test_bad_setting() -> None:
    """A value the chart cannot take raises a schema error naming the setting."""
    props: dict[str, Any] = {"id": "c", "y": "val/loss"}
    with pytest.raises(SchemaError, match="scale"):
        settle(props, {"scale": "cubic"})
    with pytest.raises(SchemaError, match="smooth"):
        settle(props, {"smooth": 1.5})


def test_round_trip_law() -> None:
    """The settled props decode to the defaults with the settings applied."""
    props: dict[str, Any] = {"id": "c", "y": "val/loss"}
    settle(props, EVERYTHING)
    line = m.parse({"body": [{"line": props}]}, source="t").body[0]
    assert isinstance(line, m.Line)
    assert (line.x, line.band, line.smooth, line.scale, line.steps) == (
        "_elapsed",
        "std",
        0.6,
        "symlog",
        [10, None],
    )
    assert line.by == ["config.arm"] and line.raw is False and line.legend is False
