"""Readers for authored files: proposals, notes, views, memory and blocks."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from beamtime.format.ids import is_version_id
from beamtime.format.schema import SchemaError, schema_of

_FRONTMATTER = re.compile(r"---\r?\n(?P<front>.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(?P<body>.*)", re.S)


@dataclass(kw_only=True, frozen=True)
class AuthoredDoc:
    """One version of an authored file: its fields and, for Markdown, its body."""

    path: Path
    id: str
    schema: int
    meta: dict[str, Any] = field(default_factory=dict)
    body: str = ""


def _doc(path: Path, meta: Any, body: str, kind: str) -> AuthoredDoc:
    """Check the schema of a parsed authored file and wrap it.

    :param path: The file.
    :param meta: The parsed YAML or frontmatter.
    :param body: The Markdown body, empty for YAML files.
    :param kind: The file kind, a key of ``SCHEMAS``.
    :return: The document."""
    match schema_of(meta, kind=kind, path=path):
        case 1:
            return AuthoredDoc(path=path, id=path.stem, schema=1, meta=meta, body=body)
        case v:
            raise SchemaError(f"{path}: no reader for {kind} schema {v}.")


def read_yaml_doc(path: Path, *, kind: str) -> AuthoredDoc:
    """Read a YAML file: a proposal, view or block version.

    :param path: The file.
    :param kind: ``proposal``, ``view`` or ``block``.
    :return: The document."""
    import yaml

    return _doc(path, yaml.safe_load(path.read_text()), "", kind)


def read_markdown_doc(path: Path, *, kind: str) -> AuthoredDoc:
    """Read a Markdown file with YAML frontmatter: a note or memory version.

    :param path: The file.
    :param kind: ``note`` or ``memory``.
    :return: The document with its frontmatter as ``meta`` and the rest as ``body``."""
    import yaml

    if (m := _FRONTMATTER.match(path.read_text())) is None:
        raise SchemaError(f"{path}: expected YAML frontmatter between '---' lines.")
    return _doc(path, yaml.safe_load(m["front"]), m["body"], kind)


def versions(folder: Path) -> list[Path]:
    """List the versions in an authored folder, oldest first.

    :param folder: E.g. ``<group>/proposal``; may be missing.
    :return: The files named by a version id."""
    if not folder.is_dir():
        return []
    return sorted(
        (p for p in folder.iterdir() if p.is_file() and is_version_id(p.stem)),
        key=lambda p: p.stem,
    )


def newest(folder: Path) -> Path | None:
    """Find the current version in an authored folder.

    :param folder: E.g. ``<group>/view``.
    :return: The newest version, or ``None`` if there is none."""
    return all_[-1] if (all_ := versions(folder)) else None
