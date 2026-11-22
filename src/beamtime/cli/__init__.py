"""The beamtime command line interface (layer 8)."""

import argparse
import json
import sys
import types
from pathlib import Path
from typing import Annotated, Any, Literal, NoReturn, Union, get_args, get_origin

EXAMPLES = """examples:
  beamtime runs scaling/lr-sweep --where 'config.lr<1e-3' --sort -metric.val/acc.max
  beamtime series . -y train/loss --steps 0:5000 --points 50
  beamtime card 20261024-101532-k3m9xq2a
  beamtime check scaling/lr-sweep
  echo 'Spike gone in all seeds.' | beamtime note add scaling/lr-sweep --type observation \\
      --description 'No loss spike with warmup'
  beamtime query '{"keys": {"from": "."}}'
"""


GROUPS = {
    "mcp": "the MCP server over stdio (for agent clients)",
    "note": "add a note to a group or run, or remove one",
    "proposal": "show or save a group's proposal",
    "plan": "what a proposal's plan still lacks",
    "memory": "show or update a group's memory",
    "view": "build, check and save a group's view",
    "block": "library blocks: list, show, promote, fork, check and save",
    "source": "add, list or remove a remote",
    "run": "make hidden runs count like any run",
}


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
    """Read ``--step``: ``last``, ``all``, a step, ``first:last``, or ``last:step``.

    :param text: The value as typed.
    :return: The value in the object form."""
    if ":" in text:
        a, b = text.split(":", 1)
        return [a if a == "last" else int(a), int(b)]
    return scalar(text)


def agent_pairs(text: str) -> list[str]:
    """Read one ``--agent-set`` value: a pair, or pairs joined by commas.

    :param text: The flag value.
    :return: The ``KEY=VALUE`` pairs."""
    from beamtime.setup.plan import split_agent_set

    return split_agent_set(text) or [text]


def pair(text: str) -> tuple[str, str]:
    """Read a ``name=value`` flag value.

    :param text: The value as typed.
    :return: The name and the value."""
    name, sep, value = text.partition("=")
    if not sep or not name:
        raise argparse.ArgumentTypeError(f"{text!r}: write name=value")
    return name.strip(), value.strip()


def evidence_item(text: str) -> Any:
    """Read an ``--evidence`` value: an id or path, or an object like ``{run: ..}``.

    :param text: The value as typed.
    :return: The text, or the parsed object."""
    return json_or_yaml(text) if text.lstrip().startswith("{") else text


def add_field(
    parser: argparse.ArgumentParser, field: Any, positional: bool, from_stdin: bool = False
) -> None:
    """Add one parameter of an operation as a flag or positional argument.

    :param parser: The command's parser.
    :param field: The msgspec field info.
    :param positional: Whether it is positional.
    :param from_stdin: Whether stdin may supply it, so the flag is not required.
    :return: None."""
    import msgspec

    name = field.encode_name
    required = field.required and not from_stdin
    dest = field.name
    if positional:
        if get_origin(unwrap(field.type)[0]) is list:
            parser.add_argument(dest, metavar=name, nargs="*", default=[])
            return
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
        if default is msgspec.NODEFAULT and field.default_factory is not msgspec.NODEFAULT:
            default = field.default_factory()
        elif default is msgspec.NODEFAULT:
            default = None
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
            kw |= {"metavar": "last|all|STEP|FIRST:LAST|last:STEP", "type": step_value}
        case "depth":
            kw |= {"type": scalar, "metavar": "all|N"}
        case "verdict":
            kw |= {"action": "append", "type": pair, "default": [], "metavar": "PREDICTION=VERDICT"}
        case "evidence":
            kw |= {"action": "append", "type": evidence_item, "default": [], "metavar": "ITEM"}
        case "remote" | "skip_remote" | "install_remote" | "ssh_share":
            kw |= {"action": "append", "default": [], "metavar": "NAME"}
        case "agent_set":
            kw |= {"action": "extend", "default": [], "type": agent_pairs, "metavar": "KEY=VALUE"}
        case "import" | "import_notes" | "import_memory":
            kw |= {"action": "append", "default": [], "metavar": "PATH"}
        case _ if members == (bool,):
            # a flag that defaults to on is turned off with --no-<name>.
            kw["action"] = argparse.BooleanOptionalAction if kw.get("default") else "store_true"
            kw.pop("required")
        case _ if get_origin(members[0]) is list:
            kw |= {"type": lambda t: t.split(","), "metavar": "A,B"}
        case _ if get_origin(members[0]) is Literal:
            kw["choices"] = get_args(members[0])
        case _ if members[0] is int and len(members) > 1:
            # a number or a word, e.g. --points 500 or --points all.
            kw["type"] = scalar
        case _ if members[0] in (int, float):
            kw["type"] = members[0]
        case _:
            pass
    if (meta := describe(field.type)) is not None:
        hidden = (meta.extra or {}).get("hidden")
        kw.setdefault(
            "help", argparse.SUPPRESS if hidden else (meta.description or "").replace("%", "%%")
        )
    parser.add_argument(*flags, **kw)


def describe(tp: Any) -> Any:
    """Find the ``msgspec.Meta`` of an annotated parameter type.

    :param tp: The field's type.
    :return: Its ``Meta``, or ``None``."""
    import msgspec

    if get_origin(tp) is not Annotated:
        return None
    return next((m for m in get_args(tp)[1:] if isinstance(m, msgspec.Meta)), None)


class Version(argparse.Action):
    """Print the version, and a note when the serve extra is missing; looked up only when asked."""

    def __call__(self, parser: Any, namespace: Any, values: Any, option: Any = None):
        """Print the version and exit.

        :param parser: The parser.
        :param namespace: Ignored.
        :param values: Ignored.
        :param option: Ignored."""
        from importlib.util import find_spec

        from beamtime import __version__

        # setup reads the second word to tell whether this install can serve `beamtime mcp`.
        extra = "" if find_spec("mcp") else " (no serve extra)"
        print(f"beamtime {__version__}{extra}")
        parser.exit()


class Parser(argparse.ArgumentParser):
    """An argument parser whose usage error prints its whole help first."""

    def parse_known_args(
        self, args: list[str] | None = None, namespace: argparse.Namespace | None = None
    ) -> tuple[argparse.Namespace, list[str]]:
        """Parse like argparse, but report leftovers here, not in the top parser.

        :param args: The arguments.
        :param namespace: The namespace to fill.
        :return: The namespace and the leftover arguments (always empty)."""
        parsed, rest = super().parse_known_args(args, namespace)
        if rest:
            self.error(f"unrecognized arguments: {' '.join(rest)}")
        return parsed, rest

    def error(self, message: str) -> NoReturn:
        """Print the help and the error to stderr and exit with 2.

        :param message: The error.
        :raises SystemExit: Always, with code 2."""
        print(self.format_help(), file=sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    """Build the parser from the operation registry.

    :return: The parser."""
    import msgspec

    from beamtime.ops.registry import OPS

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS, help="another project's root")
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="the canonical answer",
    )
    common.add_argument("--quiet", action="store_true", default=argparse.SUPPRESS)
    parser = Parser(
        prog="beamtime",
        description="Experiment tracking for people and their coding agents.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action=Version, nargs=0, help="show the version")
    parser.add_argument("--root", default=None, help="another project's root")
    parser.add_argument("--json", action="store_true", help="the canonical answer as JSON")
    parser.add_argument("--quiet", action="store_true", help="print nothing on success")
    commands = parser.add_subparsers(dest="command", metavar="COMMAND", parser_class=Parser)
    groups: dict[str, Any] = {}
    for op in OPS:
        if op.name == "query":
            sub = commands.add_parser(op.name, parents=[common], help=op.summary)
            sub.add_argument("query", metavar="FILE_OR_JSON", help="a YAML/JSON file or {…}")
            sub.add_argument("--cursor", default=None)
            sub.set_defaults(op=op.name)
            continue
        where, name = commands, op.name
        if " " in op.name:
            group, name = op.name.split(" ", 1)
            if group not in groups:
                help_ = GROUPS[group]
                group_parser = commands.add_parser(group, parents=[common], help=help_)
                groups[group] = group_parser.add_subparsers(
                    dest=f"{group}_command", parser_class=Parser
                )
            where = groups[group]
        label = op.summary + (" (user only)" if op.user_only else "")
        sub = where.add_parser(name, parents=[common], help=label, description=op.summary)
        for field in msgspec.structs.fields(op.params):
            add_field(sub, field, field.name in op.positional, field.name == op.stdin)
        sub.set_defaults(op=op.name)
    return parser


def params_of(op_name: str, args: argparse.Namespace) -> dict[str, Any]:
    """Collect an operation's parameters from parsed arguments.

    :param op_name: The operation.
    :param args: The parsed arguments.
    :return: Parameters by encoded name."""
    import msgspec

    from beamtime.ops.registry import BY_NAME
    from beamtime.query.conditions import parse_where

    op = BY_NAME[op_name]
    if op_name == "query":
        return {"query": read_query(args.query), "cursor": args.cursor}
    out = {}
    for field in msgspec.structs.fields(op.params):
        value = getattr(args, field.name)
        if field.name == "where":
            value = parse_where(value)
        elif field.name == "verdict":
            value = dict(value)
        out[field.encode_name] = value
    if op.stdin and out.get(op.stdin) is None and out.get("file") is None:
        if not sys.stdin.isatty():
            out[op.stdin] = sys.stdin.read()
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
        text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) if not text.lstrip().startswith("{") else json_or_yaml(text)


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


def tool_names(argv: list[str]) -> list[str]:
    """Accept a command by its MCP tool name, as agents write it (``memory_show``).

    :param argv: The arguments.
    :return: The arguments with a tool name split into its command path."""
    from beamtime.ops.registry import BY_TOOL

    skip = False
    for i, arg in enumerate(argv):
        if skip:
            skip = False
        elif arg == "--root":
            skip = True
        elif not arg.startswith("-"):
            if "_" in arg and (op := BY_TOOL.get(arg)) is not None:
                return argv[:i] + op.name.split() + argv[i + 1 :]
            return argv
    return argv


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
    args = parser.parse_args(tool_names(join_sort(sys.argv[1:] if argv is None else argv)))
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    if args.command == "mcp" and args.mcp_command is None:
        from beamtime.mcp import serve

        sys.exit(serve(root=args.root))
    if args.command in GROUPS and getattr(args, f"{args.command}_command") is None:
        parser.parse_args([args.command, "--help"])
    from beamtime.ops.context import Context, OpError
    from beamtime.remote import answer

    try:
        params = params_of(args.op, args)
    except ValueError as e:
        parser.exit(2, f"beamtime: {e}\n")
    try:
        context = Context.make(root=args.root, caller="cli")
        answer = answer(args.op, params, context)
    except OpError as e:
        print(f"beamtime: {e}", file=sys.stderr)
        sys.exit(e.code)
    if args.json:
        print(json.dumps(answer, indent=1, default=str))
    elif not args.quiet:
        from beamtime.cli.format import render

        if text := render(answer):
            print(text)
    if answer.get("meta", {}).get("failed"):
        sys.exit(1)
    if code := answer.get("meta", {}).get("exit"):
        sys.exit(code)
