"""Library blocks: custom blocks with a name, a description and params, used in views like widgets.

A block lives in ``blocks/<name>/`` of the log dir root or of a group; one further down overrides
one of the same name further up. Each version is ``<version>.yaml`` next to its code in ``code/``.
Drafts are ``.beamtime/drafts/blocks/<name>/`` with ``block.yaml`` and ``code/<name>.js``."""

import posixpath
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any, Literal

import msgspec

from beamtime.format import constants as c
from beamtime.format.authored import versions
from beamtime.format.schema import SchemaError
from beamtime.ops.context import Context
from beamtime.query.models import closest
from beamtime.views import code
from beamtime.views import model as m

BLOCK_FILE = "block.yaml"
Kind = Literal["field", "fields", "metric", "metrics", "number", "string", "bool"]


class Param(msgspec.Struct, kw_only=True, forbid_unknown_fields=True, omit_defaults=True):
    """One param of a library block."""

    kind: Kind
    default: Any = None
    description: str | None = None


class BlockDef(msgspec.Struct, kw_only=True, forbid_unknown_fields=True, omit_defaults=True):
    """A library block's definition, one version."""

    schema: int = 1
    name: str
    description: str = ""
    params: dict[str, Param] = msgspec.field(default_factory=dict)
    examples: list[dict[str, Any]] = msgspec.field(default_factory=list)
    queries: dict[str, dict[str, Any]] = msgspec.field(default_factory=dict)
    code: str
    kit: int = 1
    libs: list[str] = msgspec.field(default_factory=list)
    derived_from: str | None = None
    author: str | None = None
    user: str | None = None
    message: str | None = None


@dataclass(kw_only=True)
class Resolved:
    """A block found for a page: its definition and where it lives."""

    block: BlockDef
    version: str
    group: str
    folder: Path
    draft: str | None = None

    @property
    def code_ref(self) -> dict[str, Any]:
        """Name the block's code for the page's ``code`` call.

        :return: ``{block, group, path}``, or ``{block_draft, path}`` for a draft."""
        if self.draft is not None:
            return {"block_draft": self.draft, "path": self.block.code}
        return {"block": self.block.name, "group": self.group, "path": self.block.code}


def read_def(file: Path, *, source: str) -> BlockDef:
    """Read a block definition.

    :param file: A version's YAML, or a draft's ``block.yaml``.
    :param source: How to name it in messages.
    :return: The definition."""
    import yaml

    try:
        data = yaml.safe_load(file.read_text())
        if (schema := (data or {}).get("schema", 1)) != 1:
            raise SchemaError(f"{source}: no reader for block schema {schema}")
        return msgspec.convert(data, BlockDef)
    except yaml.YAMLError as e:
        raise SchemaError(f"{source}: not valid YAML: {e}") from None
    except msgspec.ValidationError as e:
        raise SchemaError(f"{source}: {e}") from None


class Library:
    """The library blocks a page can use."""

    def __init__(self, *, ctx: Context, path: str, drafts: dict[str, str] | None = None) -> None:
        """Prepare finding blocks for a page.

        :param ctx: The operation context.
        :param path: The page: a group below the log dir, or a run's path.
        :param drafts: Block drafts that stand in for blocks of the same name, by name."""
        self.ctx = ctx
        self.path = path
        self.drafts = drafts or {}

    @cached_property
    def folders(self) -> dict[str, tuple[str, Path]]:
        """Find the block folders from the log dir root down to the page; nearer ones win.

        :return: ``{name: (group, folder)}``."""
        parts = [] if self.path in (".", "") else self.path.split("/")
        out = {}
        for i in range(len(parts) + 1):
            group = "/".join(parts[:i]) or "."
            root = self.ctx.logdir / group / c.BLOCKS
            if not root.is_dir():
                continue
            for folder in sorted(root.iterdir()):
                if folder.name in m.BLOCKS or not any(versions(folder)):
                    continue
                out[folder.name] = (group, folder)
        return out

    @property
    def names(self) -> list[str]:
        """List the blocks the page can use.

        :return: Their names, drafts included."""
        return sorted(set(self.folders) | set(self.drafts))

    def get(self, name: str, version: str | None = None) -> Resolved:
        """Find a block, pinned or newest.

        :param name: Its name.
        :param version: The pinned version; default the newest.
        :return: The block.
        :raises SchemaError: If there is no such block or version."""
        if (draft := self.drafts.get(name)) is not None:
            folder = drafts_dir(self.ctx) / draft
            block = read_def(folder / BLOCK_FILE, source=f"block draft {draft}")
            return Resolved(
                block=block, version="draft", group=self.path, folder=folder, draft=draft
            )
        if name not in self.folders:
            known = ", ".join([*sorted(m.BLOCKS), *self.names])
            hint = closest(name, [*m.BLOCKS, *self.names])
            raise SchemaError(f"no block {name!r}{hint}; the blocks here are {known}")
        group, folder = self.folders[name]
        files = [f for f in versions(folder) if f.suffix == ".yaml"]
        file = files[-1] if version is None else folder / f"{version}.yaml"
        if file not in files:
            raise SchemaError(f"block {name!r} has no version {version!r} in {group}")
        block = read_def(file, source=f"{posixpath.join(group, c.BLOCKS, name)}/{file.name}")
        return Resolved(block=block, version=file.stem, group=group, folder=folder)

    def newest(self, name: str) -> str | None:
        """Name a block's newest version.

        :param name: The block.
        :return: The version, or ``None`` if the page has no such block."""
        if name not in self.folders:
            return None
        files = [f for f in versions(self.folders[name][1]) if f.suffix == ".yaml"]
        return files[-1].stem if files else None


def drafts_dir(ctx: Context) -> Path:
    """Locate the block drafts.

    :param ctx: The operation context.
    :return: ``.beamtime/drafts/blocks``."""
    from beamtime.views.store import drafts

    return drafts(ctx) / c.BLOCKS


def problems(block: BlockDef, given: dict[str, Any]) -> list[str]:
    """Check a use's params against a block's.

    :param block: The block.
    :param given: The params a view gives.
    :return: What is wrong, one message each."""
    out = []
    for name in given:
        if name not in block.params:
            out.append(f"{block.name} has no param {name!r}{closest(name, list(block.params))}")
    for name, p in block.params.items():
        value = given.get(name, p.default)
        if value is None:
            out.append(f"{block.name} needs {name} ({p.kind})")
        elif not fits(p.kind, value):
            out.append(f"{block.name}.{name} is a {p.kind}, not {value!r}")
    return out


def fits(kind: Kind, value: Any) -> bool:
    """Tell whether a value fits a param's kind.

    :param kind: The kind.
    :param value: The value.
    :return: Whether it fits."""
    match kind:
        case "field" | "metric" | "string":
            return isinstance(value, str)
        case "fields" | "metrics":
            return isinstance(value, list) and all(isinstance(v, str) for v in value)
        case "number":
            return isinstance(value, (int, float)) and not isinstance(value, bool)
        case "bool":
            return isinstance(value, bool)
        case _:
            raise ValueError(f"no param kind {kind!r}")


def queries_for(block: BlockDef, given: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Fill a block's queries with a use's params; runtime placeholders stay.

    :param block: The block.
    :param given: The params a view gives.
    :return: The queries."""
    values = {name: given.get(name, p.default) for name, p in block.params.items()}
    return {name: code.fill(q, values) for name, q in block.queries.items()}
