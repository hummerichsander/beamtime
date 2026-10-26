"""Data wrappers for tables, images, text, histograms and figures.

Heavy libraries (NumPy, PyArrow, Matplotlib, Pillow) are only used through the objects
the caller passes in, or imported inside the wrapper that needs them."""

import io
import json
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beamtime.format import constants as c
from beamtime.format.png import encode_png


@dataclass(kw_only=True, frozen=True)
class Encoded:
    """A data entry ready to store: its record fields and, if large, a file."""

    fields: dict[str, Any]
    content: bytes | None = None
    ext: str | None = None


def plain(value: Any) -> Any:
    """Turn NumPy and tensor values into JSON-ready Python values.

    :param value: A cell or a sequence of cells.
    :return: The plain value; unknown objects become strings."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if hasattr(value, "tolist"):
        return plain(value.tolist())
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return str(value)


class Data(ABC):
    """Base class of the data wrappers that ``run.log`` accepts."""

    @abstractmethod
    def encode(self) -> Encoded:
        """Encode the data for ``_data.jsonl`` and ``_data/``.

        :return: The encoded entry."""
        raise NotImplementedError


class Table(Data):
    """A table: a DataFrame, a dict of columns or a list of row dicts."""

    def __init__(self, data: Any) -> None:
        """Wrap tabular data.

        :param data: A DataFrame, a dict of columns, or a list of row dicts."""
        self.columns = self.to_columns(data)

    @staticmethod
    def to_columns(data: Any) -> dict[str, list[Any]]:
        """Convert supported inputs to a dict of plain columns.

        :param data: The table.
        :return: Column name to values."""
        if isinstance(data, dict):
            return {str(k): plain(list(v)) for k, v in data.items()}
        if isinstance(data, list):
            names = list(dict.fromkeys(k for row in data for k in row))
            return {str(n): [plain(row.get(n)) for row in data] for n in names}
        if hasattr(data, "columns") and hasattr(data, "__getitem__"):
            return {str(n): plain(list(data[n])) for n in data.columns}
        raise TypeError(
            f"Table expects a DataFrame, dict or list of dicts, not {type(data)}"
        )

    def encode(self) -> Encoded:
        """Store small tables inline, large ones as Parquet (or JSON without PyArrow).

        :return: The encoded entry."""
        cells = sum(len(v) for v in self.columns.values())
        if cells <= c.INLINE_CELLS:
            return Encoded(fields={"kind": "table", "columns": self.columns})
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            content = json.dumps({"columns": self.columns}).encode()
            return Encoded(fields={"kind": "table"}, content=content, ext="json")
        buf = io.BytesIO()
        pq.write_table(pa.table(self.columns), buf)
        return Encoded(fields={"kind": "table"}, content=buf.getvalue(), ext="parquet")


def array_png(array: Any) -> bytes:
    """Encode an image array (H×W, H×W×C or C×H×W; floats in [0, 1] or uint8) as PNG.

    :param array: A NumPy array or a tensor.
    :return: The PNG file."""
    import numpy as np

    if hasattr(array, "detach"):
        array = array.detach().cpu().numpy()
    a = np.asarray(array)
    if a.ndim == 3 and a.shape[0] in (1, 3, 4) and a.shape[-1] not in (1, 3, 4):
        a = np.moveaxis(a, 0, -1)
    if a.ndim == 3 and a.shape[-1] == 1:
        a = a[..., 0]
    if a.ndim not in (2, 3) or (a.ndim == 3 and a.shape[-1] not in (2, 3, 4)):
        raise ValueError(f"cannot read an image from an array of shape {a.shape}")
    if a.dtype != np.uint8:
        a = np.clip(np.nan_to_num(a.astype(np.float64)) * 255.0, 0, 255).round()
    a = np.ascontiguousarray(a.astype(np.uint8))
    channels = 1 if a.ndim == 2 else a.shape[-1]
    return encode_png(a.shape[1], a.shape[0], channels, a.tobytes())


class Image(Data):
    """An image: a NumPy array or tensor, a PIL image, or a path to an image file."""

    def __init__(self, data: Any, caption: str | None = None) -> None:
        """Wrap an image.

        :param data: The image.
        :param caption: An optional caption."""
        self.data = data
        self.caption = caption

    def encode(self) -> Encoded:
        """Encode the image as a file below ``_data/``.

        :return: The encoded entry."""
        fields: dict[str, Any] = {"kind": "image"}
        if self.caption is not None:
            fields["caption"] = self.caption
        if isinstance(self.data, (str, Path)):
            path = Path(self.data)
            ext = path.suffix.lstrip(".").lower() or "png"
            return Encoded(fields=fields, content=path.read_bytes(), ext=ext)
        if hasattr(self.data, "save") and hasattr(self.data, "mode"):
            buf = io.BytesIO()
            self.data.save(buf, format="PNG")
            return Encoded(fields=fields, content=buf.getvalue(), ext="png")
        return Encoded(fields=fields, content=array_png(self.data), ext="png")


class Text(Data):
    """A piece of text, such as a generated sample or a prompt."""

    def __init__(self, text: str) -> None:
        """Wrap text.

        :param text: The text."""
        self.text = str(text)

    def encode(self) -> Encoded:
        """Store short text inline and long text as a file.

        :return: The encoded entry."""
        data = self.text.encode()
        if len(data) <= c.INLINE_TEXT:
            return Encoded(fields={"kind": "text", "text": self.text})
        return Encoded(fields={"kind": "text"}, content=data, ext="txt")


class Histogram(Data):
    """A histogram, stored as a table with ``bin_start``, ``bin_end`` and ``count``."""

    def __init__(
        self,
        values: Any = None,
        bins: int | list[float] = 64,
        counts: list[float] | None = None,
    ) -> None:
        """Wrap a histogram of values, or precomputed bins and counts.

        :param values: The values to bin.
        :param bins: The number of bins, or the bin edges when ``counts`` is given.
        :param counts: Precomputed counts, one fewer than the edges in ``bins``."""
        if counts is not None:
            edges, counts = plain(list(bins)), plain(list(counts))
            if len(edges) != len(counts) + 1:
                raise ValueError("Histogram needs one more bin edge than counts")
        elif values is not None:
            edges, counts = self.bin(values, int(bins))
        else:
            raise ValueError("Histogram needs values, or bins and counts")
        self.columns = {"bin_start": edges[:-1], "bin_end": edges[1:], "count": counts}

    @staticmethod
    def bin(values: Any, n: int) -> tuple[list[float], list[int]]:
        """Bin finite values into ``n`` equal-width bins.

        :param values: An array-like of numbers.
        :param n: The number of bins.
        :return: The edges and the counts."""
        flat = plain(values.ravel() if hasattr(values, "ravel") else list(values))
        xs = [v for v in flat if isinstance(v, (int, float)) and math.isfinite(v)]
        if not xs:
            return [0.0, 1.0], [0]
        lo, hi = min(xs), max(xs)
        if lo == hi:
            lo, hi = lo - 0.5, hi + 0.5
        width = (hi - lo) / n
        counts = [0] * n
        for v in xs:
            counts[min(int((v - lo) / width), n - 1)] += 1
        return [lo + i * width for i in range(n)] + [hi], counts

    def encode(self) -> Encoded:
        """Encode the histogram as a table.

        :return: The encoded entry."""
        return Table(self.columns).encode()


class Figure(Data):
    """A Matplotlib figure, stored as a PNG image."""

    def __init__(self, fig: Any, caption: str | None = None) -> None:
        """Wrap a figure.

        :param fig: A Matplotlib figure.
        :param caption: An optional caption."""
        self.fig = fig
        self.caption = caption

    def encode(self) -> Encoded:
        """Render the figure to PNG.

        :return: The encoded entry."""
        buf = io.BytesIO()
        self.fig.savefig(buf, format="png", bbox_inches="tight", dpi=150)
        fields: dict[str, Any] = {"kind": "image"}
        if self.caption is not None:
            fields["caption"] = self.caption
        return Encoded(fields=fields, content=buf.getvalue(), ext="png")
