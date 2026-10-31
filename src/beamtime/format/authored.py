"""Readers for authored files: proposals, notes, views, memory and blocks."""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from beamtime.format.ids import is_run_id, is_version_id
from beamtime.format.schema import SchemaError, schema_of

_FRONTMATTER = re.compile(r"---\r?\n(?P<front>.*?)\r?\n---[ \t]*(?:\r?\n|\Z)(?P<body>.*)", re.S)
_LINK = re.compile(r"\[\[([^\[\]\n]+)\]\]")
HASH_CHARS = 16
EVIDENCE_KINDS = ("run", "view", "prediction", "note")


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

    return _doc(path, load_yaml(path.read_text()), "", kind)


def read_markdown_doc(path: Path, *, kind: str) -> AuthoredDoc:
    """Read a Markdown file with YAML frontmatter: a note or memory version.

    :param path: The file.
    :param kind: ``note`` or ``memory``.
    :return: The document with its frontmatter as ``meta`` and the rest as ``body``."""
    meta, body = split_frontmatter(path.read_text(), source=str(path))
    return _doc(path, meta, body, kind)


def split_frontmatter(text: str, *, source: str) -> tuple[Any, str]:
    """Split Markdown into its YAML frontmatter and body.

    :param text: The file's text.
    :param source: Where it came from, for messages.
    :return: The parsed frontmatter and the body."""

    if (m := _FRONTMATTER.match(text)) is None:
        raise SchemaError(f"{source}: expected YAML frontmatter between '---' lines.")
    return load_yaml(m["front"]), m["body"]


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


def file_hash(path: Path) -> str:
    """Hash an authored file, so edits of a frozen version can be told apart.

    :param path: The file.
    :return: The first 16 hex characters of its SHA-256."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:HASH_CHARS]


def link_kind(target: str) -> str:
    """Tell what a link target points to.

    :param target: The text between ``[[`` and ``]]``, or a plain id or path.
    :return: ``run``, ``note``, ``prediction``, ``view`` or ``folder``."""
    if target.startswith("@"):
        return "folder"
    if "#" in target:
        return "prediction"
    if "@" in target:
        return "view"
    if is_run_id(target):
        return "run"
    if is_version_id(target):
        return "note"
    return "folder"


def parse_links(text: str) -> list[tuple[str, str]]:
    """Find the ``[[...]]`` links in a note or memory body.

    :param text: The body.
    :return: ``(kind, target)`` per link, in order, without repeats."""
    targets = dict.fromkeys(m.strip() for m in _LINK.findall(text))
    return [(link_kind(t), t) for t in targets if t]


def note_links(meta: dict[str, Any], body: str) -> list[tuple[str, str]]:
    """Collect what a note points to: its fields and the links in its body.

    :param meta: The frontmatter.
    :param body: The Markdown body.
    :return: ``(kind, target)`` pairs without repeats."""
    out: list[tuple[str, str]] = []
    for entry in meta.get("evidence") or []:
        if isinstance(entry, str):
            out.append((link_kind(entry), entry))
        elif isinstance(entry, dict):
            out += [(k, str(v)) for k, v in entry.items() if k in EVIDENCE_KINDS]
    for key in ("resolves", "supersedes"):
        ids = meta.get(key) or []
        out += [("note", str(i)) for i in (ids if isinstance(ids, list) else [ids])]
    out += parse_links(body)
    return list(dict.fromkeys(out))


def load_yaml(text: str) -> Any:
    """Parse YAML safely, with libyaml's C parser where PyYAML has it (several times faster).

    :param text: The YAML.
    :return: The value."""
    import yaml

    return yaml.load(text, Loader=getattr(yaml, "CSafeLoader", yaml.SafeLoader))
