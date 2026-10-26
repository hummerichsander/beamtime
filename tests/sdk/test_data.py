import json
import struct
import zlib
from pathlib import Path

import pytest

from beamtime.format.png import encode_png
from beamtime.sdk.data import Histogram, Image, Table, Text


def png_size(data: bytes) -> tuple[int, int, int]:
    """Read width, height and color type from a PNG header.

    :param data: The PNG file.
    :return: Width, height and PNG color type."""
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    width, height, _, color = struct.unpack(">IIBB", data[16:26])
    return width, height, color


def test_encode_png_round_trip() -> None:
    """The stdlib encoder writes valid image data."""
    data = encode_png(3, 2, 1, bytes(range(6)))
    assert png_size(data) == (3, 2, 0)
    idat = data[data.index(b"IDAT") + 4 :]
    raw = zlib.decompressobj().decompress(idat)
    assert raw == b"\x00\x00\x01\x02\x00\x03\x04\x05"
    with pytest.raises(ValueError):
        encode_png(3, 2, 1, b"short")


def test_small_table_is_inline() -> None:
    """Small tables are stored inline as columns, from rows or columns."""
    enc = Table([{"a": 1, "b": "x"}, {"a": 2}]).encode()
    assert enc.content is None
    assert enc.fields == {"kind": "table", "columns": {"a": [1, 2], "b": ["x", None]}}
    assert Table({"c": (1, 2)}).encode().fields["columns"] == {"c": [1, 2]}
    with pytest.raises(TypeError):
        Table(3)


def test_large_table_is_a_file() -> None:
    """Tables above 1000 cells go to a file: Parquet with PyArrow, else JSON."""
    enc = Table({"x": list(range(2000))}).encode()
    assert enc.ext in ("parquet", "json") and enc.content
    if enc.ext == "json":
        assert json.loads(enc.content)["columns"]["x"][-1] == 1999


def test_text_inline_or_file() -> None:
    """Text up to 4 KB is inline, longer text a file."""
    assert Text("hi").encode().fields == {"kind": "text", "text": "hi"}
    long = Text("x" * 5000).encode()
    assert long.ext == "txt" and long.content == b"x" * 5000


def test_histogram() -> None:
    """Histograms are tables of bins, from values or from counts."""
    cols = Histogram([0.0, 0.5, 1.0, float("nan")], bins=2).encode().fields["columns"]
    assert cols == {"bin_start": [0.0, 0.5], "bin_end": [0.5, 1.0], "count": [1, 2]}
    given = Histogram(bins=[0, 1, 2], counts=[3, 4]).encode().fields["columns"]
    assert given["count"] == [3, 4]
    with pytest.raises(ValueError):
        Histogram(bins=[0, 1], counts=[1, 2])


def test_image_from_path(tmp_path: Path) -> None:
    """An image file is stored as is, with its extension and a caption."""
    p = tmp_path / "a.PNG"
    p.write_bytes(encode_png(1, 1, 1, b"\x00"))
    enc = Image(p, caption="c").encode()
    assert enc.ext == "png" and enc.fields == {"kind": "image", "caption": "c"}


def test_image_from_arrays() -> None:
    """Arrays in HW, HWC and CHW layout, float or uint8, become PNGs."""
    np = pytest.importorskip("numpy")
    assert png_size(Image(np.zeros((4, 5))).encode().content) == (5, 4, 0)
    rgb = np.random.default_rng(0).random((3, 4, 5))
    assert png_size(Image(rgb).encode().content) == (5, 4, 2)
    rgba = np.zeros((4, 5, 4), dtype=np.uint8)
    assert png_size(Image(rgba).encode().content) == (5, 4, 6)
    with pytest.raises(ValueError):
        Image(np.zeros((2, 2, 2, 2))).encode()


def test_histogram_of_array() -> None:
    """Histograms accept arrays of any shape."""
    np = pytest.importorskip("numpy")
    cols = Histogram(np.arange(10.0).reshape(2, 5), bins=5).encode().fields["columns"]
    assert sum(cols["count"]) == 10
