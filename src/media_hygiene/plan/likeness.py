"""How alike two pictures are: hash distance, flat hashes, proportions.

Shared by near-duplicate images, burst series and re-encoded videos.
"""

from __future__ import annotations

from typing import Final

HASH_BITS: Final = 64
_ASPECT_TOLERANCE: Final = 0.01
_FEATURELESS_BITS: Final = 2


def distance(first: int, second: int) -> int:
    """Count the bits two hashes differ by.

    Args:
        first: A hash.
        second: Another hash.

    Returns:
        The Hamming distance.
    """
    return (first ^ second).bit_count()


def is_flat(dhash: int) -> bool:
    """Tell whether a gradient hash is nearly flat: a picture with almost no detail.

    Args:
        dhash: A 64-bit difference hash.

    Returns:
        True for black, white or blank pictures and frames.
    """
    bits = dhash.bit_count()
    return bits <= _FEATURELESS_BITS or bits >= HASH_BITS - _FEATURELESS_BITS


def same_aspect(first: tuple[int, int], second: tuple[int, int]) -> bool:
    """Tell whether two pictures have the same proportions (±1 %).

    Args:
        first: Width and height of one.
        second: Width and height of the other.

    Returns:
        True when their aspect ratios agree.
    """
    (width, height), (other_width, other_height) = first, second
    return (
        abs(width * other_height - other_width * height)
        <= _ASPECT_TOLERANCE * width * other_height
    )
