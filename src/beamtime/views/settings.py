"""The settings of a ``line`` chart, owned by ``m.Line``: their names, defaults and how a viewer's
settings fold into a node's props."""

import json
from typing import Any

import msgspec

from beamtime.format.schema import SchemaError
from beamtime.views import model as m

SEEDS_FIELD = "config.seed"

# seeds folds into by; the axis titles are authored, not settings.
AUTHORED = ("seeds", "xlabel", "ylabel")

_NODE = {f.name for f in msgspec.structs.fields(m.Node)}

SETTINGS = ("y",) + tuple(
    f.name for f in msgspec.structs.fields(m.Line) if f.name not in _NODE | {"y", *AUTHORED}
)


def line_defaults() -> dict[str, Any]:
    """The default of every setting that has one.

    :return: Setting name to its default in ``m.Line``, as it appears on the wire."""
    fields = {f.name: f for f in msgspec.structs.fields(m.Line)}
    return {
        key: fields[key].default for key in SETTINGS if fields[key].default is not msgspec.NODEFAULT
    }


def settle(props: dict[str, Any], settings: dict[str, Any]) -> None:
    """Write chart settings into a ``line`` node's props, leaving out what is at its default.

    :param props: The node's props in YAML form; changed in place.
    :param settings: The settings, as the web UI names them; unknown keys are dropped.
    :raises SchemaError: When a value is not valid for the setting."""
    merged = dict(props)
    # an axis title written for the old x or metrics would be wrong for the new ones.
    for key, title in (("x", "xlabel"), ("y", "ylabel")):
        if key in settings:
            merged.pop(title, None)
    for key in SETTINGS:
        if key not in settings:
            continue
        value = settings[key]
        match key:
            case "y":
                if value:
                    merged["y"] = value[0] if len(value) == 1 else list(value)
            case "by":
                merged.pop("seeds", None)
                merged.pop("by", None)
                if value == "seeds":
                    merged["seeds"] = SEEDS_FIELD
                elif value:
                    merged["by"] = [value]
            case "color" | "colormap":
                if value:
                    merged[key] = value
                else:
                    merged.pop(key, None)
            case "steps":
                if value and any(v is not None for v in value):
                    merged["steps"] = list(value)
                else:
                    merged.pop("steps", None)
            case _:
                merged[key] = value
    raw = {"block": "line", **merged}
    try:
        line = msgspec.convert(raw, m.Line)
    except msgspec.ValidationError as e:
        raise SchemaError(m.located(str(e), raw)) from None
    # msgspec's omit_defaults compares floats by identity, so a smooth of 0 would stay.
    defaults = line_defaults()
    settled = {
        k: v
        for k, v in msgspec.to_builtins(line).items()
        if k != "block" and not (k in defaults and v == defaults[k])
    }
    props.clear()
    props.update(settled)


def generated_ts() -> str:
    """Write the defaults as a TypeScript module for the web UI.

    :return: The source of ``web/src/bt/chart-defaults.ts``."""
    items = sorted(line_defaults().items())
    line = ",\n".join(f"    {key}: {json.dumps(value)}" for key, value in items)
    return (
        "// Beamtime: generated from views/settings.py by scripts/build-chart-defaults. "
        "Do not edit by hand.\n"
        f"export const SEEDS_FIELD = {json.dumps(SEEDS_FIELD)};\n"
        f"export const DEFAULTS = {{\n  line: {{\n{line},\n  }},\n}} as const;\n"
    )
