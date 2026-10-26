"""Beamtime: agents-first experiment logging."""


def __getattr__(name: str) -> str:
    """Resolve ``__version__`` lazily, so importing beamtime stays cheap.

    :param name: The attribute name.
    :return: The installed package version."""
    if name == "__version__":
        from importlib.metadata import version

        return version("beamtime")
    raise AttributeError(f"module 'beamtime' has no attribute {name!r}")
