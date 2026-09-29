"""Estimate the quality a JPEG was saved with, from its quantization tables.

Encoders following the IJG reference (libjpeg, most cameras and editors) scale one
standard luminance table by the quality: `5000 / q` percent below 50, `200 - 2q` above.
Comparing the file's table with the standard one gives the quality back. The sums are
compared, not each entry, so the order the tables are stored in does not matter. Other
encoders give an estimate, which is what this is.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from PIL import Image

# The IJG standard luminance table (quality 50).
_STANDARD_LUMINANCE: Final = (
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
)  # fmt: skip
_PERCENT: Final = 100
_HALF_SCALE: Final = 200
_LOW_SCALE: Final = 5000


def jpeg_quality(image: Image.Image) -> int | None:
    """Estimate the quality of a JPEG (MPO included) from its luminance table.

    Args:
        image: An image opened by Pillow.

    Returns:
        A quality from 1 to 100, or None when the image holds no quantization table.
    """
    tables = getattr(image, "quantization", None)
    if not isinstance(tables, dict) or not tables:
        return None
    luminance = [int(value) for value in tables[min(tables)]]
    if len(luminance) != len(_STANDARD_LUMINANCE):
        return None
    scale = _PERCENT * sum(luminance) / sum(_STANDARD_LUMINANCE)
    quality = (_HALF_SCALE - scale) / 2 if scale <= _PERCENT else _LOW_SCALE / scale
    return max(1, min(_PERCENT, round(quality)))
