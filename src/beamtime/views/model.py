"""The view format: one msgspec struct per block in a tagged union, and the view around them.

In YAML a node is a one-key mapping from the block name to its props (``- line: {y: val/loss}``);
layouts take their children as a list or as ``children``. ``parse`` normalizes that form to the
union, fills in ids and reports errors with the node they are in."""

import re
from typing import Annotated, Any, Literal

import msgspec

from beamtime.format.schema import SchemaError

Field = Annotated[str, msgspec.Meta(description="e.g. config.lr, metric.val/acc.max, run.status")]
Metric = Annotated[str, msgspec.Meta(description="a metric key, e.g. val/loss")]
Scale = Literal["linear", "log", "symlog"]
Step = Literal["last"] | int


class Node(
    msgspec.Struct, kw_only=True, forbid_unknown_fields=True, omit_defaults=True, tag_field="block"
):
    """Props every block has."""

    id: str | None = None
    title: str | None = None
    caption: Annotated[
        str | None, msgspec.Meta(description="one or two sentences; required on charts")
    ] = None
    span: Literal[1, 2, "full"] = 1
    from_: Annotated[str, msgspec.Meta(description="a group relative to the page, or a run id")] = (
        msgspec.field(default=".", name="from")
    )
    where: dict[str, Any] = msgspec.field(default_factory=dict)
    depth: Annotated[
        Literal[1, "all"], msgspec.Meta(description="1: only the runs directly in the group")
    ] = "all"


class Line(Node, tag="line"):
    """Metric curves over steps, one per run; use for how training went."""

    y: Metric | list[Metric]
    x: Annotated[str, msgspec.Meta(description="_step, _t, _elapsed or a metric key")] = "_step"
    color: Annotated[Field | None, msgspec.Meta(description="color curves by this field")] = None
    by: Annotated[
        Field | list[Field] | None, msgspec.Meta(description="mean and band per value")
    ] = None
    band: Literal["minmax", "std", "stderr", "none"] = "minmax"
    seeds: Annotated[Field | None, msgspec.Meta(description="e.g. config.seed")] = None
    smooth: Annotated[float, msgspec.Meta(ge=0, lt=1, description="EMA weight")] = 0.0
    scale: Annotated[
        Scale | None,
        msgspec.Meta(
            description="default: the view's metrics, else log for losses, else linear; symlog "
            "is linear near zero and logarithmic beyond"
        ),
    ] = None
    steps: Annotated[list[int | None] | None, msgspec.Meta(description="[first, last] step")] = None
    ymin: float | None = None
    ymax: float | None = None
    outliers: Annotated[bool, msgspec.Meta(description="y range ignores outliers")] = False
    raw: Annotated[bool, msgspec.Meta(description="when smoothing, the raw curve faintly")] = True
    legend: bool = True


class Scatter(Node, tag="scatter"):
    """Two fields against each other, one point per run; use for a metric over a hyperparameter."""

    x: Field
    y: Field
    color: Field | None = None
    x_scale: Scale = "linear"
    y_scale: Scale = "linear"
    fit: Literal["linear", "log", "power"] | None = None
    seeds: Field | None = None


class Bar(Node, tag="bar"):
    """A field per category, mean with error bars; use when a change is compared."""

    x: Annotated[
        Field, msgspec.Meta(description="the category, e.g. config.optimizer; numbers too")
    ]
    y: Field
    by: Annotated[Field | None, msgspec.Meta(description="a second field: grouped bars")] = None
    error: Literal["std", "stderr", "minmax", "none"] = "std"
    sort: Literal["x", "y", "-y"] = "x"


class Histogram(Node, tag="histogram"):
    """A logged distribution (a table with bin_start, bin_end, count), one outline per run."""

    key: str
    step: Step = "last"


class Stat(Node, tag="stat"):
    """One number: a count, the best, mean or last value of a field."""

    field: Field | None = None
    aggregate: Literal["best", "mean", "last", "count", "min", "max"] = "count"


class Table(Node, tag="table"):
    """Runs as rows, fields as columns; use for which setting is best."""

    columns: list[Field] | None = None
    sort: Annotated[list[str], msgspec.Meta(description="a leading - sorts descending")] = (
        msgspec.field(default_factory=list)
    )
    limit: int = 100
    highlight_best: bool = True
    sparkline: Metric | None = None


class DataTable(Node, tag="data_table"):
    """A logged table (key) or a data file stored with the view (file)."""

    key: str | None = None
    step: Step = "last"
    file: Annotated[str | None, msgspec.Meta(description="e.g. data/fit.csv")] = None
    limit: int = 50


class Images(Node, tag="images"):
    """Logged images of a key."""

    key: str
    step: Step = "last"


class Text(Node, tag="text"):
    """Logged text of a key."""

    key: str
    step: Step = "last"


class Proposal(Node, tag="proposal"):
    """A group's proposal: predictions with results, effects and intervals."""

    of: str = "."


class Memory(Node, tag="memory"):
    """A group's memory."""

    of: str = "."


class Groups(Node, tag="groups"):
    """The child groups with status, check, verdict and run counts."""


class Timeline(Node, tag="timeline"):
    """Notes and run events in time order."""

    types: list[str] | None = None
    limit: int = 30


class Note(Node, tag="note"):
    """A short text, optionally a callout."""

    text: str
    kind: Literal["info", "warning", "success"] = "info"


class Notes(Node, tag="notes"):
    """The newest notes, current versions only."""

    types: list[str] | None = None
    limit: int = 3


class Output(Node, tag="output"):
    """The tail of a run's captured output."""

    run: Annotated[str | None, msgspec.Meta(description="default: the page's run")] = None
    lines: int = 40
    rank: int = 0


class Custom(Node, tag="custom"):
    """Agent code in a sandbox (custom blocks arrive in M7)."""

    code: str
    kit: int = 1
    libs: list[str] = msgspec.field(default_factory=list)
    queries: dict[str, dict[str, Any]] = msgspec.field(default_factory=dict)


class Section(Node, tag="section"):
    """A titled group of blocks that can be collapsed."""

    children: list["Block"] = msgspec.field(default_factory=list)
    open: bool = True


class Row(Node, tag="row"):
    """Blocks side by side, wrapping."""

    children: list["Block"] = msgspec.field(default_factory=list)


class Grid(Node, tag="grid"):
    """Blocks in an auto-fitting grid, or in fixed columns."""

    children: list["Block"] = msgspec.field(default_factory=list)
    columns: int | None = None
    min_width: int = 420


class Tabs(Node, tag="tabs"):
    """Sections as tabs, named by their titles; not nested."""

    children: list[Section] = msgspec.field(default_factory=list)


Block = (
    Line
    | Scatter
    | Bar
    | Histogram
    | Stat
    | Table
    | DataTable
    | Images
    | Text
    | Proposal
    | Memory
    | Groups
    | Timeline
    | Note
    | Notes
    | Output
    | Custom
    | Section
    | Row
    | Grid
    | Tabs
)
BLOCKS: dict[str, type[Node]] = {
    cls.__struct_config__.tag: cls  # type: ignore[misc]
    for cls in Block.__args__  # type: ignore[attr-defined]
}
LAYOUTS = ("section", "row", "grid", "tabs")
CHARTS = ("line", "scatter", "bar", "histogram")
# the prop an id is made from when a node has none: line-val-loss, table-1.
MAIN_PROP = {
    "line": "y",
    "scatter": "y",
    "bar": "y",
    "histogram": "key",
    "stat": "field",
    "data_table": "key",
    "images": "key",
    "text": "key",
    "section": "title",
}


class MetricInfo(msgspec.Struct, kw_only=True, forbid_unknown_fields=True, omit_defaults=True):
    """How a metric is shown: label, unit, scale and direction."""

    label: str | None = None
    unit: str | None = None
    scale: Scale | None = None
    higher_is_better: bool | None = None


class View(msgspec.Struct, kw_only=True, forbid_unknown_fields=True, omit_defaults=True):
    """A view: what a group or run page shows."""

    schema: int = 1
    title: str | None = None
    finding: Annotated[str | None, msgspec.Meta(description="the key result, one sentence")] = None
    author: str | None = None
    user: str | None = None
    message: Annotated[str | None, msgspec.Meta(description="what this version changed")] = None
    filters: dict[str, Any] = msgspec.field(default_factory=dict)
    metrics: dict[str, MetricInfo] = msgspec.field(default_factory=dict)
    body: list[Block] = msgspec.field(default_factory=list)
    uses: dict[str, str] = msgspec.field(default_factory=dict)


def parse(data: Any, *, source: str = "view") -> View:
    """Read a view from its YAML form.

    :param data: The parsed YAML.
    :param source: Where it came from, for messages.
    :return: The view, with every node's id filled in."""
    if not isinstance(data, dict):
        raise SchemaError(f"{source}: a view is a mapping with schema, title, finding and body")
    raw = dict(data)
    if (schema := raw.get("schema", 1)) != 1:
        raise SchemaError(f"{source}: no reader for view schema {schema}")
    raw["body"] = [normalize(n, f"body[{i}]", source) for i, n in enumerate(raw.get("body") or [])]
    try:
        view = msgspec.convert(raw, View)
    except msgspec.ValidationError as e:
        raise SchemaError(f"{source}: {located(str(e), raw)}") from None
    assign_ids(view.body)
    return view


def normalize(node: Any, where: str, source: str) -> dict[str, Any]:
    """Turn a YAML node (``{name: props}``) into the union's form (``{block: name, **props}``).

    :param node: The node.
    :param where: Its path in the view, for messages.
    :param source: Where the view came from.
    :return: The normalized node, children included."""
    if isinstance(node, dict) and "block" in node:
        name, props = node["block"], {k: v for k, v in node.items() if k != "block"}
    elif isinstance(node, dict) and len(node) == 1:
        name, props = next(iter(node.items()))
    else:
        raise SchemaError(
            f"{source}: {where}: a node is one block name with its props, e.g. "
            "'- line: {y: val/loss}'"
        )
    if name not in BLOCKS:
        known = ", ".join(sorted(BLOCKS))
        raise SchemaError(
            f"{source}: {where}: no block {name!r}; the blocks are {known} "
            "(library blocks arrive in M7)"
        )
    match props:
        case None:
            props = {}
        case list() if name in LAYOUTS:
            props = {"children": props}
        case dict():
            props = dict(props)
        case _:
            raise SchemaError(f"{source}: {where}.{name}: give props as a mapping")
    if name in LAYOUTS:
        kids = props.get("children") or []
        if not isinstance(kids, list):
            raise SchemaError(f"{source}: {where}.{name}.children: give a list of nodes")
        props["children"] = [
            normalize(k, f"{where}.{name}.children[{i}]", source) for i, k in enumerate(kids)
        ]
        if name == "tabs":
            for i, k in enumerate(props["children"]):
                if k["block"] != "section":
                    raise SchemaError(
                        f"{source}: {where}.tabs.children[{i}]: each tab is a section with a title"
                    )
                if any(g["block"] == "tabs" for g in k.get("children", [])):
                    raise SchemaError(f"{source}: {where}.tabs: tabs are not nested")
    return {"block": name, **props}


def located(message: str, raw: dict[str, Any]) -> str:
    """Rewrite msgspec's ``- at `$.body[0].children[1].y``` with the block names on the way.

    :param message: msgspec's message.
    :param raw: The normalized view.
    :return: E.g. ``body[0].grid.children[1].line.y: Expected `str`, got `int```."""
    if (m := re.search(r" - at `\$\.?(.*)`$", message)) is None:
        return message
    text, path = message[: m.start()], m.group(1)
    out, node = [], raw
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        out.append(part)
        node = node[int(part[1:-1])] if part.startswith("[") else node.get(part)
        if part.startswith("[") and isinstance(node, dict) and "block" in node:
            out.append(f".{node['block']}")
        elif not isinstance(node, (dict, list)):
            node = {}
    joined = "".join(p if p.startswith("[") or p.startswith(".") else f".{p}" for p in out)
    return f"{joined.lstrip('.')}: {text}"


def assign_ids(nodes: list[Node], taken: set[str] | None = None) -> None:
    """Give every node without an id one from its block and main prop, unique in the view.

    :param nodes: The nodes, changed in place, children included.
    :param taken: Ids already used."""
    taken = taken if taken is not None else set(ids(nodes))
    for n in nodes:
        if n.id is None:
            main = getattr(n, MAIN_PROP.get(block_of(n), ""), None)
            main = main[0] if isinstance(main, list) and main else main
            base = f"{block_of(n)}-{slug(str(main))}" if isinstance(main, str) else block_of(n)
            n.id = base if base not in taken and main else unique(base, taken)
            taken.add(n.id)
        if (kids := getattr(n, "children", None)) is not None:
            assign_ids(kids, taken)


def ids(nodes: list[Node]) -> list[str]:
    """List the given ids of nodes and their children, in order.

    :param nodes: The nodes.
    :return: The ids, repeats included."""
    out = []
    for n in nodes:
        if n.id is not None:
            out.append(n.id)
        out += ids(getattr(n, "children", None) or [])
    return out


def walk(nodes: list[Node]) -> list[Node]:
    """List nodes and their children, depth first.

    :param nodes: The nodes.
    :return: Every node."""
    out = []
    for n in nodes:
        out.append(n)
        out += walk(getattr(n, "children", None) or [])
    return out


def unique(base: str, taken: set[str]) -> str:
    """Number an id until it is free.

    :param base: E.g. ``table``.
    :param taken: Ids in use.
    :return: E.g. ``table-2``."""
    i = 1
    while f"{base}-{i}" in taken:
        i += 1
    return f"{base}-{i}"


def block_of(node: Node) -> str:
    """Name a node's block.

    :param node: The node.
    :return: E.g. ``line``."""
    return node.__struct_config__.tag  # type: ignore[return-value]


def slug(key: str) -> str:
    """Turn a key into an id.

    :param key: E.g. ``val/acc``.
    :return: E.g. ``val-acc``."""
    return re.sub(r"[^a-z0-9]+", "-", key.lower()).strip("-") or "x"


def to_yaml_form(view: View) -> dict[str, Any]:
    """Write a view in its YAML form, leaving out defaults.

    :param view: The view.
    :return: A mapping ready for ``yaml.safe_dump``."""
    data = msgspec.to_builtins(view)
    data["body"] = [denormalize(n) for n in data.get("body", [])]
    return {"schema": 1, **{k: v for k, v in data.items() if k != "schema"}}


def denormalize(node: dict[str, Any]) -> dict[str, Any]:
    """Turn ``{block: name, **props}`` back into ``{name: props}``.

    :param node: The node as builtins.
    :return: The YAML form."""
    name = node.pop("block")
    kids = [denormalize(k) for k in node.pop("children", [])]
    # id first and children last read best.
    props = {k: node[k] for k in ("id", "title") if k in node} | node
    if kids:
        props["children"] = kids
    return {name: props or None}


def json_schema() -> dict[str, Any]:
    """Describe the view format for agents.

    :return: The JSON schema of ``View``, blocks in the union form (``block: <name>``)."""
    return msgspec.json.schema(View)


def dump(data: dict[str, Any]) -> str:
    """Write a view's YAML form as people write it: short leaves and lists of names inline.

    :param data: The YAML form.
    :return: The text."""
    import yaml

    class Dumper(yaml.SafeDumper):
        pass

    def scalar(v: Any) -> bool:
        return not isinstance(v, (dict, list))

    def mapping(dumper: yaml.SafeDumper, d: dict[str, Any]) -> Any:
        short = all(scalar(v) for v in d.values()) and len(str(d)) <= 72
        return dumper.represent_mapping("tag:yaml.org,2002:map", d, flow_style=short)

    def sequence(dumper: yaml.SafeDumper, items: list[Any]) -> Any:
        short = all(scalar(v) for v in items) and len(str(items)) <= 80
        return dumper.represent_sequence("tag:yaml.org,2002:seq", items, flow_style=short)

    Dumper.add_representer(dict, mapping)
    Dumper.add_representer(list, sequence)
    return yaml.dump(data, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=100)
