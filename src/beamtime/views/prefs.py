"""Folding a viewer's chart settings, added and removed charts, order and spans into a view body,
for "Save as view" in the web UI."""

from typing import Any

from beamtime.views import model as m
from beamtime.views.defaults import lower_is_better
from beamtime.views.model import yaml_walk


def apply_pins(data: dict[str, Any], pins: list[dict[str, Any]]) -> None:
    """Write the viewer's pins into a view's YAML form: ``main_metrics`` in order, and the
    direction under ``metrics`` where it differs from the name's guess. Other entries stay.

    :param data: The view in YAML form, changed in place.
    :param pins: ``{y, higher}`` per main metric, ``[]`` for none."""
    metrics = dict(data.get("metrics") or {})
    for pin in pins:
        info = dict(metrics.get(pin["y"]) or {})
        if pin["higher"] == (not lower_is_better(pin["y"])):
            info.pop("higher_is_better", None)
        else:
            info["higher_is_better"] = pin["higher"]
        if info:
            metrics[pin["y"]] = info
        else:
            metrics.pop(pin["y"], None)
    data["main_metrics"] = [pin["y"] for pin in pins]
    if metrics:
        data["metrics"] = metrics
    else:
        data.pop("metrics", None)


def apply_prefs(body: list[dict[str, Any]], prefs: dict[str, Any]) -> list[dict[str, Any]]:
    """Fold a viewer's chart settings and added and removed charts into a view body.

    :param body: The body in YAML form; changed in place.
    :param prefs: ``{charts, added, removed, order, spans}`` as the web UI keeps them per page.
    :return: The body."""
    removed = set(prefs.get("removed") or [])
    body[:] = without(body, removed)
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
    for b, props in yaml_walk(body):
        if b in ("scatter", "bar"):
            settle_colormap(props, shared | clean(charts.get(props.get("id"), {})))
    shown = {
        y for props in lines for y in ([props["y"]] if isinstance(props["y"], str) else props["y"])
    }
    added = [
        mt for mt in prefs.get("added") or [] if mt not in shown and f"added-{mt}" not in removed
    ]
    if added:
        new = []
        for mt in added:
            props = {"id": f"added-{m.slug(mt)}", "y": mt}
            settle(props, shared | clean(charts.get(f"added-{mt}", {})))
            new.append({"line": props})
        grid = next((p for b, p in yaml_walk(body) if b == "grid" and p.get("id") == "added"), None)
        if grid is not None:
            grid.setdefault("children", []).extend(new)
        else:
            # after the page's charts, where the web UI shows them.
            charted = [
                i for i, kid in enumerate(body) if any(b == "line" for b, _ in yaml_walk([kid]))
            ]
            body.insert(
                (charted[-1] + 1) if charted else len(body),
                {"grid": {"id": "added", "children": new}},
            )
    return body


def without(kids: list[dict[str, Any]], removed: set[str]) -> list[dict[str, Any]]:
    """Drop the removed blocks, and layouts left empty by it.

    :param kids: Nodes in YAML form.
    :param removed: Ids of the blocks to drop.
    :return: The nodes kept, in their order."""
    out = []
    for kid in kids:
        ((name, props),) = kid.items()
        if isinstance(props, dict) and props.get("id") in removed:
            continue
        if name in m.LAYOUTS:
            inner = props if isinstance(props, list) else props.get("children") or []
            kept = without(inner, removed)
            if inner and not kept:
                continue
            if isinstance(props, list):
                kid[name] = kept
            else:
                props["children"] = kept
        out.append(kid)
    return out


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
    # an axis title written for the old x or metrics would be wrong for the new ones.
    for key, title in (("x", "xlabel"), ("y", "ylabel")):
        if key in settings:
            props.pop(title, None)
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
            case "color" | "colormap":
                if value:
                    props[key] = value
                else:
                    props.pop(key, None)
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


def settle_colormap(props: dict[str, Any], settings: dict[str, Any]) -> None:
    """Write the colormap setting into a ``scatter`` or ``bar`` node's props.

    :param props: The node's props; changed in place.
    :param settings: The settings, as the web UI names them."""
    if "colormap" in settings:
        if settings["colormap"]:
            props["colormap"] = settings["colormap"]
        else:
            props.pop("colormap", None)


def clean(settings: dict[str, Any]) -> dict[str, Any]:
    """Drop unset settings.

    :param settings: The settings.
    :return: Those with a value, and ``by`` when set to none."""
    # by: null is a choice (each run, even where the view aggregates); so are cleared limits,
    # no color field and the default colormap.
    keep = ("by", "ymin", "ymax", "steps", "color", "colormap")
    return {k: v for k, v in settings.items() if v is not None or k in keep}
