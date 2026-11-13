"""Change a JPEG's EXIF orientation in its bytes, lossless: two bytes only (0725).

The pixels are not decoded nor encoded again: only the value of the orientation entry
of the first IFD changes, so writing the old value back gives the file byte for byte.
A JPEG without an orientation entry is not changed (adding one would rewrite the EXIF
block): the guess is only proposed for camera photos, which carry one.
"""

from __future__ import annotations

import struct
from typing import Final

_SOI: Final = b"\xff\xd8"
_APP1: Final = 0xE1
_START_OF_SCAN: Final = 0xDA
_EXIF: Final = b"Exif\x00\x00"
_ORIENTATION: Final = 0x0112
_SHORT: Final = 3
_ENTRY: Final = 12
_ORDERS: Final = {b"II": "<", b"MM": ">"}
_CODES: Final = range(9)  # 0 (some cameras) to 8: what was there can be put back


class NoOrientationError(ValueError):
    """The file is not a JPEG holding an EXIF orientation entry."""


def orientation_offset(data: bytes) -> tuple[int, str]:
    """Find the two bytes holding a JPEG's EXIF orientation.

    Args:
        data: The JPEG file's bytes.

    Returns:
        Their offset in the file, and the byte order (`<` or `>`).

    Raises:
        NoOrientationError: Not a JPEG, no EXIF, or no orientation entry.
    """
    if not data.startswith(_SOI):
        raise NoOrientationError
    at = len(_SOI)
    while at + 4 <= len(data) and data[at] == 0xFF:  # noqa: PLR2004 - marker, length
        marker = data[at + 1]
        (length,) = struct.unpack(">H", data[at + 2 : at + 4])
        body = at + 4
        if marker == _APP1 and data[body : body + len(_EXIF)] == _EXIF:
            return _in_tiff(data, body + len(_EXIF))
        if marker == _START_OF_SCAN:
            break
        at += 2 + length
    raise NoOrientationError


def _in_tiff(data: bytes, tiff: int) -> tuple[int, str]:
    """Find the orientation entry in the TIFF block of an EXIF segment.

    Args:
        data: The file's bytes.
        tiff: Where the TIFF header starts.

    Returns:
        The offset of its value, and the byte order.

    Raises:
        NoOrientationError: No orientation entry, or a damaged block.
    """
    order = _ORDERS.get(data[tiff : tiff + 2])
    if order is None:
        raise NoOrientationError
    try:
        (first,) = struct.unpack(f"{order}I", data[tiff + 4 : tiff + 8])
        ifd = tiff + first
        (count,) = struct.unpack(f"{order}H", data[ifd : ifd + 2])
        for number in range(count):
            entry = ifd + 2 + number * _ENTRY
            tag, kind = struct.unpack(f"{order}HH", data[entry : entry + 4])
            if tag == _ORIENTATION and kind == _SHORT:
                return entry + 8, order
    except struct.error as error:
        raise NoOrientationError from error
    raise NoOrientationError


def with_orientation(data: bytes, code: int) -> tuple[bytes, int]:
    """The same JPEG with another EXIF orientation code.

    Args:
        data: The JPEG file's bytes.
        code: The new orientation, 1 to 8.

    Returns:
        The new bytes (same length), and the code they held before.

    Raises:
        ValueError: The code is not an EXIF orientation.
    """
    if code not in _CODES:
        message = f"not an EXIF orientation: {code}"
        raise ValueError(message)
    offset, order = orientation_offset(data)
    (before,) = struct.unpack(f"{order}H", data[offset : offset + 2])
    value = struct.pack(f"{order}H", code)
    return data[:offset] + value + data[offset + 2 :], int(before)
