"""The beamtime command line interface (layer 8)."""

import argparse
import json
import sys
import types
from pathlib import Path
from typing import Annotated, Any, Literal, Union, get_args, get_origin

EXAMPLES = """examples:
  beamtime runs scaling/lr-sweep --where 'config.lr<1e-3' --sort -metric.val/acc.max
  beamtime series . -y train/loss --steps 0:5000 --points 50
  beamtime card 20261024-101532-k3m9xq2a
  beamtime query '{"keys": {"from": "."}}'
"""


def unwrap(tp: Any) -> tuple[Any, ...]:
    """List the non-None members of a type.

    :param tp: A type annotation.
    :return: Its members, without ``None``."""
    if get_origin(tp) is Annotated:
        tp = get_args(tp)[0]
    if get_origin(tp) in (Union, types.UnionType):
        return tuple(a for a in get_args(tp) if a is not type(None))
    return (tp,)


def scalar(text: str) -> Any:
    """Read a flag value that may be a number or a word.

    :param text: The value as typed.
    :return: An int if it is one, else the text."""
    try:
        return int(text)
    except ValueError:
        return text


def step_value(text: str) -> Any:
    """Read ``--step``: ``last``, ``all``, a step, or ``first:last``.

    :param text: The value as typed.
    :return: The value in the object form."""
    if ":" in text:
        a, b = text.split(":", 1)
        return [int(a), int(b)]
    return scalar(text)


def add_field(parser: argparse.ArgumentParser, field: Any, positional: bool) -> None:
    """Add one parameter of an operation as a flag or positional argument.

    :param parser: The command's parser.
    :param field: The msgspec field info.
    :param positional: Whether it is positional.
    :return: None."""
    import msgspec

    name = field.encode_name
    required = field.required
    dest = field.name
    if positional:
        if required:
            parser.add_argument(dest, metavar=name)
        else:
            parser.add_argument(dest, metavar=name, nargs="?", default=field.default)
        return
    flag = f"--{name.replace('_', '-')}"
    flags = [flag, "-y"] if name == "y" else [flag]
    members = unwrap(field.type)
    kw: dict[str, Any] = {"dest": dest, "required": required}
    if not required:
        default = field.default
        if (
            default is msgspec.NODEFAULT
            and field.default_factory is not msgspec.NODEFAULT
        ):
            default = field.default_factory()
        kw["default"] = default
    match name:
        case "where":
            kw |= {"action": "append", "default": [], "metavar": "CONDITION"}
            kw["help"] = "e.g. 'config.lr<1e-3', 'run.status=finished' (repeatable)"
        case "steps":
            kw |= {
                "metavar": "FIRST:LAST",
                "type": lambda t: [scalar(v) or None for v in t.split(":")],
            }
        case "step":
            kw |= {"metavar": "last|all|STEP|FIRST:LAST", "type": step_value}
        case "depth":
            kw |= {"type": scalar, "metavar": "all|N"}
        case _ if members == (bool,):
            kw["action"] = "store_true"
            kw.pop("required")
        case _ if get_origin(members[0]) is list:
            kw |= {"type": lambda t: t.split(","), "metavar": "A,B"}
        case _ if get_origin(members[0]) is Literal:
            kw["choices"] = get_args(members[0])
        case _ if members[0] in (int, float):
            kw["type"] = members[0]
        case _:
            pass
    parser.add_argument(*flags, **kw)


class Version(argparse.Action):
    """Print the version; looked up only when asked, since that costs import time."""

    def __call__(self, parser: Any, namespace: Any, values: Any, option: Any = None):
        """Print the version and exit.

        :param parser: The parser.
        :param namespace: Ignored.
        :param values: Ignored.
        :param option: Ignored."""
        from beamtime import __version__

        print(f"beamtime {__version__}")
        parser.exit()


def build_parser() -> argparse.ArgumentParser:
    """Build the parser from the operation registry.

    :return: The parser."""
    import msgspec

    from beamtime.ops.registry import OPS

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root", default=argparse.SUPPRESS, help="another project's root"
    )
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="the canonical answer",
    )
    common.add_argument("--quiet", action="store_true", default=argparse.SUPPRESS)
    parser = argparse.ArgumentParser(
        prog="beamtime",
        description="Agents-first experiment logging.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action=Version, nargs=0, help="show the version")
    parser.add_argument("--root", default=None, help="another project's root")
    parser.add_argument(
        "--json", action="store_true", help="the canonical answer as JSON"
    )
    parser.add_argument("--quiet", action="store_true", help="print nothing on success")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")
    mcp = commands.add_parser(
        "mcp", parents=[common], help="the MCP server over stdio (for agent clients)"
    )
    mcp_commands = mcp.add_subparsers(dest="mcp_command")
    for op in OPS:
        if op.name == "query":
            sub = commands.add_parser(op.name, parents=[common], help=op.summary)
            sub.add_argument(
                "query", metavar="FILE_OR_JSON", help="a YAML/JSON file or {…}"
            )
            sub.add_argument("--cursor", default=None)
            sub.set_defaults(op=op.name)
            continue
        where = mcp_commands if op.name.startswith("mcp ") else commands
        name = op.name.split(" ", 1)[1] if op.name.startswith("mcp ") else op.name
        label = op.summary + (" (user only)" if op.user_only else "")
        sub = where.add_parser(
            name, parents=[common], help=label, description=op.summary
        )
        for field in msgspec.structs.fields(op.params):
            add_field(sub, field, field.name in op.positional)
        sub.set_defaults(op=op.name)
    return parser


def params_of(op_name: str, args: argparse.Namespace) -> dict[str, Any]:
    """Collect an operation's parameters from parsed arguments.

    :param op_name: The operation.
    :param args: The parsed arguments.
    :return: Parameters by encoded name."""
    import msgspec

    from beamtime.cli.conditions import parse_where
    from beamtime.ops.registry import BY_NAME

    op = BY_NAME[op_name]
    if op_name == "query":
        return {"query": read_query(args.query), "cursor": args.cursor}
    out = {}
    for field in msgspec.structs.fields(op.params):
        value = getattr(args, field.name)
        if field.name == "where":
            value = parse_where(value)
        out[field.encode_name] = value
    return out


def read_query(text: str) -> Any:
    """Read a query from inline JSON/YAML or a file.

    :param text: ``{…}`` or a path.
    :return: The query object."""
    import yaml

    if not text.lstrip().startswith("{"):
        path = Path(text)
        if not path.is_file():
            raise ValueError(
                f"no query file {text!r}; pass a file or an object like {{runs: {{}}}}"
            )
        text = path.read_text()
    return (
        yaml.safe_load(text)
        if not text.lstrip().startswith("{")
        else json_or_yaml(text)
    )


def json_or_yaml(text: str) -> Any:
    """Parse JSON, or YAML's flow style for hand-typed objects.

    :param text: The text.
    :return: The object."""
    import yaml

    try:
        return json.loads(text)
    except ValueError:
        return yaml.safe_load(text)


def join_sort(argv: list[str]) -> list[str]:
    """Keep ``--sort -field`` together; argparse would read ``-field`` as a flag.

    :param argv: The arguments.
    :return: The arguments with ``--sort=-field``."""
    out: list[str] = []
    for arg in argv:
        if out and out[-1] == "--sort" and arg.startswith("-"):
            out[-1] = f"--sort={arg}"
        else:
            out.append(arg)
    return out


def main(argv: list[str] | None = None) -> None:
    """Run the beamtime command line interface.

    :param argv: The arguments; ``sys.argv[1:]`` by default."""
    if sys.version_info < (3, 11):
        found = ".".join(map(str, sys.version_info[:3]))
        sys.exit(
            f"beamtime: the command line needs Python 3.11 or newer, found {found}. "
            "The SDK (import beamtime) works on 3.10."
        )
    parser = build_parser()
    args = parser.parse_args(join_sort(sys.argv[1:] if argv is None else argv))
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    if args.command == "mcp" and args.mcp_command is None:
        from beamtime.mcp import serve

        sys.exit(serve(root=args.root))
    from beamtime.ops import call
    from beamtime.ops.context import Context, OpError

    try:
        params = params_of(args.op, args)
    except ValueError as e:
        parser.exit(2, f"beamtime: {e}\n")
    try:
        context = Context.make(root=args.root, caller="cli")
        answer = call(args.op, params, context)
    except OpError as e:
        print(f"beamtime: {e}", file=sys.stderr)
        sys.exit(e.code)
    if args.json:
        print(json.dumps(answer, indent=1, default=str))
    elif not args.quiet:
        from beamtime.cli.format import render

        print(render(answer))
    if answer.get("meta", {}).get("failed"):
        sys.exit(1)
