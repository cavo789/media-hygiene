"""How alike two pictures are: hash distance, flat hashes, proportions.

Shared by near-duplicate images, burst series and re-encoded videos.
"""

from __future__ import annotations

from typing import Final

HASH_BITS: Final = 64
_ASPECT_TOLERANCE: Final = 0.01
_FEATURELESS_BITS: Final = 2
# Colourfulness (`scan.colour`): below the floor, both are dull or grey alike; above it,
# a version with less than half the colour of the other is an edit, not a copy.
COLOUR_FLOOR: Final = 10.0
COLOUR_SHARE: Final = 0.5


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


def same_colours(first: float | None, second: float | None) -> bool:
    """Tell whether two versions keep the same colours (unlike a black and white edit).

    Args:
        first: The colourfulness of one, None when unknown.
        second: That of the other.

    Returns:
        False only when one is clearly colourful and the other has less than half of it.
    """
    if first is None or second is None:
        return True
    low, high = sorted((first, second))
    return high < COLOUR_FLOOR or low > COLOUR_SHARE * high
