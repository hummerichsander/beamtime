"""Beamtime: agents-first experiment logging."""

from typing import Any

_EXPORTS = {
    "init": "beamtime.sdk.run",
    "current": "beamtime.sdk.run",
    "Run": "beamtime.sdk.run",
    "NullRun": "beamtime.sdk.run",
    "Table": "beamtime.sdk.data",
    "Image": "beamtime.sdk.data",
    "Text": "beamtime.sdk.data",
    "Histogram": "beamtime.sdk.data",
    "Figure": "beamtime.sdk.data",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Import SDK names on first use, so ``import beamtime`` stays cheap.

    :param name: The attribute name.
    :return: The SDK object, or the installed version for ``__version__``."""
    if name == "__version__":
        from importlib.metadata import version

        return version("beamtime")
    if (module := _EXPORTS.get(name)) is not None:
        from importlib import import_module

        return getattr(import_module(module), name)
    raise AttributeError(f"module 'beamtime' has no attribute {name!r}")
