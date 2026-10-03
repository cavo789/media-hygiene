"""Describe how an image looks: perceptual hashes, sharpness, when and with what.

Computed on the image the integrity check has just decoded, in the same worker: the
file is never read twice. Hashes follow the usual dHash (gradient of a 9 x 8 thumbnail)
and pHash (low frequencies of the DCT of a 32 x 32 thumbnail). Sharpness is the variance
of the Laplacian, as digiKam's blur detection, on a thumbnail of fixed size so that
shots of one series compare fairly.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image, ImageOps

from media_hygiene.scan.exif import camera, taken_at
from media_hygiene.scan.exposure import Exposure, measure
from media_hygiene.scan.models import VisualFacts

if TYPE_CHECKING:
    from numpy.typing import NDArray

ANALYSIS_EDGE: Final = 512
_HASH_SIDE: Final = 8
_DCT_SIDE: Final = 32
_ORIENTATION_TAG: Final = 0x0112
_QUARTER_TURNS: Final = frozenset({5, 6, 7, 8})


@dataclass(frozen=True, slots=True)
class Look:
    """What a decoded image looks like: its visual facts and its exposure."""

    visual: VisualFacts
    exposure: Exposure | None


def visual_facts(image: Image.Image, stored_size: tuple[int, int]) -> Look:
    """Describe a decoded image.

    Args:
        image: The image, loaded (possibly drafted: decoded at a reduced scale).
        stored_size: Its full size as stored in the file, before any rotation.

    Returns:
        Its visual facts, and its exposure measured on the same thumbnail.
    """
    exif = image.getexif()
    upright = ImageOps.exif_transpose(image)
    gray = upright.convert("L")
    width, height = stored_size
    if exif.get(_ORIENTATION_TAG) in _QUARTER_TURNS:
        width, height = height, width
    analysed = _analysis_pixels(gray)
    visual = VisualFacts(
        dhash=dhash(gray),
        phash=phash(gray),
        width=width,
        height=height,
        sharpness=_sharpness(analysed),
        taken_at=taken_at(exif),
        camera=camera(exif),
    )
    return Look(visual, measure(analysed))


def _pixels(gray: Image.Image, size: tuple[int, int]) -> NDArray[np.float64]:
    """Resize a grayscale image and return its pixels as floats.

    Args:
        gray: A grayscale image.
        size: Target width and height.

    Returns:
        A `height x width` array.
    """
    small = gray.resize(size, Image.Resampling.LANCZOS)
    return np.asarray(small, dtype=np.float64)


def _as_int(bits: NDArray[np.bool_]) -> int:
    """Pack 64 booleans into an integer, first bit most significant.

    Args:
        bits: The bits, in any shape.

    Returns:
        The integer.
    """
    return int("".join("1" if bit else "0" for bit in bits.flatten()), 2)


def dhash(gray: Image.Image) -> int:
    """Difference hash: is each pixel brighter than its right neighbour?

    Args:
        gray: A grayscale image.

    Returns:
        A 64-bit hash.
    """
    pixels = _pixels(gray, (_HASH_SIDE + 1, _HASH_SIDE))
    return _as_int(pixels[:, 1:] > pixels[:, :-1])


@cache
def _dct_matrix() -> NDArray[np.float64]:
    """Rows of the DCT-II basis for the lowest frequencies.

    Returns:
        A `8 x 32` matrix.
    """
    frequencies = np.arange(_HASH_SIDE)[:, None]
    positions = np.arange(_DCT_SIDE)[None, :]
    return np.cos(np.pi * (2 * positions + 1) * frequencies / (2 * _DCT_SIDE))


def phash(gray: Image.Image) -> int:
    """Perceptual hash: which low frequencies are above their median?

    Args:
        gray: A grayscale image.

    Returns:
        A 64-bit hash.
    """
    basis = _dct_matrix()
    low = basis @ _pixels(gray, (_DCT_SIDE, _DCT_SIDE)) @ basis.T
    return _as_int(low > np.median(low))


def _analysis_pixels(gray: Image.Image) -> NDArray[np.float64]:
    """Shrink a grayscale image to the fixed analysis size, keeping its proportions.

    Args:
        gray: A grayscale image.

    Returns:
        Its pixels, at most `ANALYSIS_EDGE` per side.
    """
    small = gray.copy()
    small.thumbnail((ANALYSIS_EDGE, ANALYSIS_EDGE))
    return np.asarray(small, dtype=np.float64)


def _sharpness(pixels: NDArray[np.float64]) -> float:
    """Variance of the Laplacian: high for crisp edges, low for a blurred shot.

    Args:
        pixels: Grayscale pixels at the analysis size.

    Returns:
        The score, rounded to one decimal.
    """
    laplacian = (
        pixels[:-2, 1:-1]
        + pixels[2:, 1:-1]
        + pixels[1:-1, :-2]
        + pixels[1:-1, 2:]
        - 4 * pixels[1:-1, 1:-1]
    )
    return round(float(laplacian.var()), 1) if laplacian.size else 0.0
