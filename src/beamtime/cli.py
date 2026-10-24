import argparse

from beamtime import __version__


def main() -> None:
    """Run the beamtime command line interface."""
    parser = argparse.ArgumentParser(prog="beamtime")
    parser.add_argument(
        "--version", action="version", version=f"beamtime {__version__}"
    )
    parser.parse_args()


if __name__ == "__main__":
    main()
