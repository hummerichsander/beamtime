"""The beamtime command line interface (layer 8)."""

import argparse
import sys


def main() -> None:
    """Run the beamtime command line interface."""
    if sys.version_info < (3, 11):
        found = ".".join(map(str, sys.version_info[:3]))
        sys.exit(
            f"beamtime: the command line needs Python 3.11 or newer, found {found}. "
            "The SDK (import beamtime) works on 3.10."
        )
    from beamtime import __version__

    parser = argparse.ArgumentParser(prog="beamtime")
    parser.add_argument(
        "--version", action="version", version=f"beamtime {__version__}"
    )
    parser.parse_args()
