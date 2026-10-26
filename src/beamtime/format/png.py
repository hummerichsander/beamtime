"""A minimal PNG encoder on the standard library, for images without Pillow."""

import struct
import zlib

COLOR_TYPES = {1: 0, 2: 4, 3: 2, 4: 6}


def _chunk(kind: bytes, data: bytes) -> bytes:
    """Frame one PNG chunk with its length and CRC.

    :param kind: The four-byte chunk type.
    :param data: The chunk data.
    :return: The framed chunk."""
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def encode_png(width: int, height: int, channels: int, pixels: bytes) -> bytes:
    """Encode 8-bit pixels as PNG.

    :param width: Width in pixels.
    :param height: Height in pixels.
    :param channels: 1 (gray), 2 (gray and alpha), 3 (RGB) or 4 (RGBA).
    :param pixels: Row-major bytes, ``width * height * channels`` long.
    :return: The PNG file."""
    if len(pixels) != width * height * channels:
        raise ValueError(
            f"expected {width * height * channels} bytes, got {len(pixels)}"
        )
    stride = width * channels
    raw = b"".join(
        b"\x00" + pixels[r * stride : (r + 1) * stride] for r in range(height)
    )
    header = struct.pack(">IIBBBBB", width, height, 8, COLOR_TYPES[channels], 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(raw, 6))
        + _chunk(b"IEND", b"")
    )
