"""Sample matplotlib's colormaps into src/beamtime/views/colormaps.json.

Run with ``uv run --with matplotlib python scripts/colormaps.py``; matplotlib stays out of the
serve path, which only reads the committed file."""

import json
from pathlib import Path

from matplotlib import colormaps
from matplotlib.colors import to_hex

STOPS = 11
SEQUENTIAL = (
    "viridis", "plasma", "inferno", "magma", "cividis", "turbo",
    "Blues", "Greens", "Greys", "Oranges", "Purples", "Reds",
)  # fmt: skip
DIVERGING = ("coolwarm", "RdBu", "bwr", "seismic", "PuOr", "BrBG", "PiYG", "RdYlBu", "Spectral")


def stops(name: str) -> list[str]:
    """Sample one colormap at evenly spaced points.

    :param name: The colormap's name in matplotlib.
    :return: The colors as ``#rrggbb``."""
    return [to_hex(colormaps[name](i / (STOPS - 1))) for i in range(STOPS)]


def main() -> None:
    """Write the file."""
    out = Path(__file__).parents[1] / "src/beamtime/views/colormaps.json"
    data = {
        "source": "sampled from matplotlib by scripts/colormaps.py",
        "sequential": {n: stops(n) for n in SEQUENTIAL},
        "diverging": {n: stops(n) for n in DIVERGING},
    }
    out.write_text(json.dumps(data, indent=1) + "\n")


if __name__ == "__main__":
    main()
