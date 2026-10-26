"""Schema versions of every file kind and the check readers apply."""

from pathlib import Path
from typing import Any

SCHEMAS = {
    "run": 1,
    "config": 1,
    "card": 1,
    "preview": 1,
    "metrics": 1,
    "data": 1,
    "events": 1,
    "artifacts": 1,
    "proposal": 1,
    "note": 1,
    "view": 1,
    "memory": 1,
    "block": 1,
    "settings": 1,
    "synth": 1,
}


class SchemaError(ValueError):
    """A file has no usable schema version or one newer than this Beamtime knows."""


def schema_of(obj: Any, *, kind: str, path: Path | str) -> int:
    """Read and check the schema version of a parsed file.

    :param obj: The parsed file; must be a mapping with an integer ``schema``.
    :param kind: The file kind, a key of ``SCHEMAS``.
    :param path: The file, for the error message.
    :return: The schema version, at most the newest one known."""
    if not isinstance(obj, dict):
        raise SchemaError(f"{path}: expected a mapping, found {type(obj).__name__}.")
    version = obj.get("schema")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise SchemaError(
            f"{path}: missing or invalid 'schema' field ({version!r}); "
            "every Beamtime file states its schema version as a positive integer."
        )
    if version > (known := SCHEMAS[kind]):
        raise SchemaError(
            f"{path}: {kind} schema {version} is newer than this Beamtime knows "
            f"({known}). Upgrade with: pip install -U beamtime"
        )
    return version
