"""The agent guide: how to build views, disclosed in parts, with five examples.

Examples are YAML templates with ``{{name}}`` placeholders, filled with a group's metrics and
config; nodes whose data the group doesn't have are left out."""

import re
from importlib.resources import files
from typing import Any

from beamtime.ops import call
from beamtime.ops import registry as r
from beamtime.ops.context import Context, OpError
from beamtime.remote import answer as remote_answer

EXAMPLES = ("sweep", "ablation", "run", "direction", "custom")
ESSENTIAL = ("key", "x", "y", "field", "file")
GENERIC = {
    "group": "my-sweep",
    "main": "val/acc",
    "higher": "true",
    "stat": "max",
    "sort": "-metric.val/acc.max",
    "loss": "train/loss",
    "main_prefix": "val",
    "loss_prefix": "train",
    "swept": "config.lr",
    "swept2": "config.weight_decay",
    "swept_scale": "log",
    "change": "config.optimizer",
    "seeds": "config.seed",
    "hist": "grads/layer3",
    "image": "samples",
    "table": "val/per_class",
}


def guide(ctx: Context, p: r.GuideParams) -> dict[str, Any]:
    """Answer a part of the guide.

    :param ctx: The operation context.
    :param p: The parameters.
    :return: ``{kind, part, text}``."""
    match p.part:
        case None:
            text = read("overview.md")
            if p.group is not None:
                text += "\n" + about(ctx, p.group)
        case "examples":
            text = example(p.name, ctx, p.group) if p.name else examples()
        case "blocks":
            text = block(p.name) if p.name else catalog()
        case "queries" | "checklist" | "anti-patterns" | "kit":
            text = read(f"{p.part}.md")
        case other:
            raise ValueError(f"no guide part {other!r}")
    return {"kind": "guide", "part": p.part or "overview", "text": text}


def read(name: str) -> str:
    """Read a part of the guide.

    :param name: The file in ``parts/``.
    :return: Its Markdown."""
    return (files(__package__) / "parts" / name).read_text()


def examples() -> str:
    """List the examples with their commentary.

    :return: Markdown."""
    out = [
        "# Examples",
        "",
        "Each is a complete view; `view_new <group> --from <name>` starts a "
        "draft from it, filled with the group's keys.",
        "",
    ]
    for name in EXAMPLES:
        text = (files(__package__) / "examples" / f"{name}.yaml").read_text()
        comment = " ".join(line.lstrip("# ") for line in text.splitlines() if line.startswith("#"))
        out.append(f"- **{name}**: {comment.split(': ', 1)[-1]}")
    out += ["", "`guide examples <name>` shows one; add `group` to fill it with a group's keys."]
    return "\n".join(out)


def example(name: str | None, ctx: Context, group: str | None) -> str:
    """Fill an example with a group's keys, leaving out blocks without data there.

    :param name: The example.
    :param ctx: The operation context.
    :param group: The group (or run) whose keys fill it; generic names without.
    :return: The view YAML, commentary first."""
    import yaml

    from beamtime.views.model import dump

    if name not in EXAMPLES:
        raise OpError(f"no example {name!r}; examples: {', '.join(EXAMPLES)}", code=4)
    template = (files(__package__) / "examples" / f"{name}.yaml").read_text()
    values = GENERIC if group is None else values_of(ctx, group)
    text = re.sub(r"\{\{(\w+)\}\}", lambda mt: values.get(mt.group(1), ""), template)
    data = yaml.safe_load(text)
    data["body"] = prune(data.get("body") or [])
    comment = "".join(line + "\n" for line in text.splitlines() if line.startswith("#"))
    return comment + dump(data)


def example_file(ref: str) -> bytes | None:
    """Read a file an example refers to, such as its custom block's code.

    :param ref: The reference in the example, e.g. ``code/phase-map.js``.
    :return: The content, or ``None`` if the examples have no such file."""
    file = files(__package__) / "examples" / ref
    return file.read_bytes() if file.is_file() else None


def prune(nodes: list[Any]) -> list[Any]:
    """Drop empty props, and nodes that are incomplete without them.

    :param nodes: Nodes in YAML form.
    :return: The nodes kept."""
    import msgspec

    from beamtime.views import model as m

    out = []
    for n in nodes:
        ((name, props),) = n.items()
        props = {"children": props} if isinstance(props, list) else props or {}
        # a block whose data names came out empty has nothing to show in this group.
        if any(props.get(k) == "" for k in ESSENTIAL):
            continue
        props = {k: v for k, v in props.items() if v not in ("", [""], None)}
        if isinstance(props.get("columns"), list):
            props["columns"] = [c for c in props["columns"] if c]
        if isinstance(props.get("sort"), list):
            props["sort"] = [c for c in props["sort"] if c] or None
            props = {k: v for k, v in props.items() if v is not None}
        if name in m.LAYOUTS:
            props["children"] = prune(props.get("children") or [])
            if not props["children"]:
                continue
        else:
            try:
                msgspec.convert({"block": name, **props}, m.BLOCKS[name])
            except msgspec.ValidationError:
                continue
        out.append({name: props})
    return out


def values_of(ctx: Context, group: str) -> dict[str, str]:
    """Pick a group's names for the example placeholders.

    :param ctx: The operation context.
    :param group: A group or run.
    :return: Placeholder values; empty where the group has nothing fitting."""
    from beamtime.views.defaults import (
        CLOCKS,
        EVAL_PREFIXES,
        lower_is_better,
        ordered_metrics,
        prefix,
        varying_config,
    )

    keys = remote_answer("keys", {"from": group}, ctx)
    metrics = ordered_metrics(keys)
    plain = [k for k in metrics if k not in CLOCKS]
    evals = [k for k in plain if prefix(k) in EVAL_PREFIXES]
    main = proposed(ctx, group, metrics) or (evals or plain or [""])[0]
    lower = lower_is_better(main)
    stat = "min" if lower else "max"
    losses = [k for k in metrics if "loss" in k and k != main]
    config = {k: v for k, _, v in keys["config"]["rows"]}
    varying = [k for k in varying_config(keys) if k != "config.seed"]
    swept = varying[0] if varying else ""
    texts = [k for k in varying if any(isinstance(v, str) for v in config.get(k) or [])]
    data = {
        kind: [k for k, kd, *_ in keys["data"]["rows"] if kd == kind]
        for kind in ("table", "image", "text")
    }
    hists = [k for k in data["table"] if re.search(r"hist|grad|weight|activ", k)]
    return {
        "group": group,
        "main": main,
        "higher": "false" if lower else "true",
        "stat": stat,
        "sort": f"{'' if lower else '-'}metric.{main}.{stat}" if main else "",
        "loss": (loss := losses[0] if losses else (metrics[1] if len(metrics) > 1 else main)),
        "main_prefix": prefix(main),
        "loss_prefix": prefix(loss),
        "swept": swept,
        # a second axis: another swept field, else the seed, else the first again.
        "swept2": varying[1]
        if len(varying) > 1
        else ("config.seed" if "config.seed" in config else swept),
        "swept_scale": scale_of(config.get(swept)),
        "change": texts[0] if texts else swept,
        "seeds": "config.seed" if "config.seed" in config else "",
        "hist": hists[0] if hists else "",
        "image": data["image"][0] if data["image"] else "",
        "table": next((k for k in data["table"] if k not in hists), ""),
    }


def proposed(ctx: Context, group: str, metrics: list[str]) -> str | None:
    """Find the metric the group's proposal makes its first prediction about.

    :param ctx: The operation context.
    :param group: The group.
    :param metrics: The metrics the group logs.
    :return: The first predicted metric that is logged, or ``None``."""
    return next(iter(predicted(ctx, group, metrics)), None)


def predicted(ctx: Context, group: str, metrics: list[str]) -> list[str]:
    """List the metrics the group's proposal makes predictions about.

    :param ctx: The operation context.
    :param group: The group.
    :param metrics: The metrics the group logs.
    :return: The predicted metrics that are logged, in prediction order, without repeats."""
    try:
        shown = remote_answer("proposal show", {"group": group}, ctx)
    except OpError:
        return []
    found = (
        (prediction.get("reduce") or {}).get("metric")
        for prediction in shown["proposal"].get("predictions") or []
    )
    return list(dict.fromkeys(metric for metric in found if metric in metrics))


def scale_of(values: Any) -> str:
    """Pick an axis scale for a swept config key.

    :param values: Its values in the group.
    :return: ``log`` for positive numbers spanning more than a decade and a half."""
    nums = [v for v in values or [] if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return "log" if nums and min(nums) > 0 and max(nums) / min(nums) >= 30 else "linear"


def catalog() -> str:
    """List the blocks with their purpose and props.

    :return: Markdown."""
    from beamtime.views import model as m

    common = set(m.Node.__struct_fields__)
    out = [
        "# Blocks",
        "",
        "Common props: id, title, caption (charts), span (1, 2, full), from, where, depth.",
        "",
    ]
    for name, cls in m.BLOCKS.items():
        props = [f for f in cls.__struct_fields__ if f not in common]
        doc = (cls.__doc__ or "").strip()
        out.append(f"- **{name}**: {doc} Props: {', '.join(props) or '–'}.")
    out += [
        "",
        "`guide blocks <name>` gives one block's schema with types and defaults. Library blocks",
        "(`block_list <group>`) are used the same way: `- <name>: {params}`.",
    ]
    return "\n".join(out)


def block(name: str) -> str:
    """Describe one block.

    :param name: The block name.
    :return: Its description and JSON schema."""
    import json

    import msgspec

    from beamtime.views import model as m

    if name not in m.BLOCKS:
        raise OpError(f"no block {name!r}; blocks: {', '.join(m.BLOCKS)}", code=4)
    cls = m.BLOCKS[name]
    full = msgspec.json.schema(cls)
    schema = full["$defs"][full["$ref"].split("/")[-1]]
    required = set(schema.get("required", []))
    lines = [f"# {name}", "", (cls.__doc__ or "").strip(), "", "Props (besides the common ones):"]
    for k, v in schema.get("properties", {}).items():
        if k in ("block", *m.Node.__struct_fields__, "from"):
            continue
        kind = type_of(v)
        extra = "required" if k in required else f"default {json.dumps(v.get('default'))}"
        note = f"; {d}" if (d := v.get("description") or described(v)) else ""
        lines.append(f"- {k}: {kind} ({extra}{note})")
    return "\n".join(lines)


def type_of(schema: dict[str, Any]) -> str:
    """Name a property's type briefly.

    :param schema: The property's JSON schema.
    :return: E.g. ``text or list of text``, ``linear | log``."""
    if "anyOf" in schema:
        kinds = [type_of(s) for s in schema["anyOf"] if s.get("type") != "null"]
        return " or ".join(kinds)
    if "enum" in schema:
        return " | ".join(map(str, schema["enum"]))
    match schema.get("type"):
        case "array":
            return f"list of {type_of(schema.get('items', {}))}"
        case "object":
            return "mapping"
        case "string":
            return "text"
        case "integer":
            return "int"
        case "number":
            return "number"
        case "boolean":
            return "bool"
        case _:
            return "any"


def described(schema: dict[str, Any]) -> str | None:
    """Find a description inside a union's members.

    :param schema: A property's schema.
    :return: The first description found."""
    return next((s["description"] for s in schema.get("anyOf", []) if "description" in s), None)


def about(ctx: Context, group: str) -> str:
    """Describe what a group offers a view.

    :param ctx: The operation context.
    :param group: The group or run.
    :return: Markdown."""
    from beamtime.ops.authored import target_of
    from beamtime.views.defaults import ordered_metrics, varying_config
    from beamtime.views.library import Library
    from beamtime.views.store import outdated, read, saved

    with target_of(ctx, group) as target:
        path = target.rel
    keys = call("keys", {"from": group}, ctx)
    data = [f"{k} ({kind})" for k, kind, *_ in keys["data"]["rows"]]
    shown = saved(ctx, path)
    library = Library(ctx=ctx, path=path)
    stale = outdated(read(shown[-1], source=shown[-1].name), library) if shown else []
    return "\n".join(
        [
            f"## This group: {group}",
            "",
            f"- metrics: {', '.join(ordered_metrics(keys)) or 'none'}",
            f"- varying config: {', '.join(varying_config(keys)) or 'none'}",
            f"- data keys: {', '.join(data) or 'none'}",
            f"- view: {f'version {shown[-1].stem}' if shown else 'the built-in default'}",
            f"- library blocks: {', '.join(library.names) or 'none'} (`block_list` for params)",
            *(
                [f"- outdated pins: {', '.join(o['name'] for o in stale)} (`view_upgrade`)"]
                if stale
                else []
            ),
        ]
    )
