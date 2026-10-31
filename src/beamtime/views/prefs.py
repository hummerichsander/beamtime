"""Folding a viewer's chart settings, added charts, order and spans into a view body, for "Save as
view" in the web UI."""

from typing import Any

from beamtime.views import model as m
from beamtime.views.model import yaml_walk


def apply_prefs(body: list[dict[str, Any]], prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fold a viewer's chart settings and added charts into a view body.

    :param body: The body in YAML form; changed in place.
    :param prefs: ``{charts, added, order, spans}`` as the web UI keeps them per page.
    :return: The body."""
    for _, props in yaml_walk(body):
        if (order := (prefs.get("order") or {}).get(props.get("id"))) and props.get("children"):
            props["children"] = reorder(props["children"], order)
        if (span := (prefs.get("spans") or {}).get(props.get("id"))) is not None:
            if span == 1:
                props.pop("span", None)
            else:
                props["span"] = span
    shared = clean(prefs.get("view") or {})
    charts = prefs.get("charts") or {}
    lines = [props for b, props in yaml_walk(body) if b == "line"]
    for props in lines:
        settings = shared | clean(charts.get(props.get("id"), {}))
        settle(props, settings)
    shown = {
        y for props in lines for y in ([props["y"]] if isinstance(props["y"], str) else props["y"])
    }
    added = [mt for mt in prefs.get("added") or [] if mt not in shown]
    if added:
        grid = next(
            (
                props
                for b, props in yaml_walk(body)
                if b == "grid" and any("line" in k for k in props.get("children", []))
            ),
            None,
        )
        new = []
        for mt in added:
            props = {"id": f"added-{m.slug(mt)}", "y": mt}
            settle(props, shared | clean(charts.get(f"added-{mt}", {})))
            new.append({"line": props})
        if grid is not None:
            grid.setdefault("children", []).extend(new)
        else:
            body.append({"grid": {"id": "added", "children": new}})
    return body


def reorder(kids: list[dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    """Put a layout's children in the viewer's order.

    :param kids: The children in YAML form.
    :param order: Ids in the wanted order; children not listed keep theirs, after them.
    :return: The children reordered."""
    at = {id_: i for i, id_ in enumerate(order)}
    ranked = [
        (at.get(next(iter(k.values())).get("id"), len(order) + i), k) for i, k in enumerate(kids)
    ]
    return [k for _, k in sorted(ranked, key=lambda r: r[0])]


def settle(props: dict[str, Any], settings: dict[str, Any]) -> None:
    """Write chart settings into a ``line`` node's props.

    :param props: The node's props; changed in place.
    :param settings: The settings, as the web UI names them."""
    for key, value in settings.items():
        match key:
            case "y":
                if value:
                    props["y"] = value[0] if len(value) == 1 else list(value)
            case "by":
                props.pop("seeds", None)
                props.pop("by", None)
                if value == "seeds":
                    props["seeds"] = "config.seed"
                elif value:
                    props["by"] = [value]
            case "scale":
                # explicit, since a loss without a scale is drawn on a log axis.
                props["scale"] = value
            case "steps":
                if value and any(v is not None for v in value):
                    props["steps"] = list(value)
                else:
                    props.pop("steps", None)
            case "x" | "smooth" | "band" | "outliers" | "raw" | "legend" | "ymin" | "ymax":
                default = {
                    "x": "_step",
                    "smooth": 0,
                    "band": "minmax",
                    "outliers": False,
                    "raw": True,
                    "legend": True,
                    "ymin": None,
                    "ymax": None,
                }[key]
                if value == default:
                    props.pop(key, None)
                else:
                    props[key] = value
            case _:
                pass


def clean(settings: dict[str, Any]) -> dict[str, Any]:
    """Drop unset settings.

    :param settings: The settings.
    :return: Those with a value, and ``by`` when set to none."""
    # by: null is a choice (each run, even where the view aggregates); so are cleared limits.
    return {
        k: v for k, v in settings.items() if v is not None or k in ("by", "ymin", "ymax", "steps")
    }
