"""How long the model takes on a photo: its time grows with the size of the file.

Decoding is what varies, the model's own time does not. Measured on the maintainer's
38,077 photos (2026-11-06, their index): 0.03 s below 500 KB, 0.08 s from 5 to 10 MB,
correlation 0.84. A single figure per photo said 18 min for 34 min when the photos
timed so far were the small ones (626 KB on average, against 3.3 MB for the rest);
this line, fitted on those same small ones, says 40 min.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence

# Below this, a line through a few photos says little: their median is safer.
_FITTED_FROM: Final = 100


@dataclass(frozen=True, slots=True)
class PhotoPace:
    """Seconds for a photo: a fixed part, and a part per byte of its file."""

    base: float
    per_byte: float = 0.0

    def seconds(self, size: int) -> float:
        """How long a photo of this size should take.

        Args:
            size: The file's size, in bytes.

        Returns:
            Seconds.
        """
        return self.base + self.per_byte * size


def fitted_pace(timed: Sequence[tuple[int, float]]) -> PhotoPace | None:
    """Fit the pace of this machine on the photos already timed.

    Args:
        timed: Size in bytes and seconds of each photo really looked at.

    Returns:
        The pace; a flat median with few photos, or when size explains nothing; None
        without any photo.
    """
    if not timed:
        return None
    flat = PhotoPace(statistics.median(seconds for _, seconds in timed))
    sizes = np.array([size for size, _ in timed], dtype=np.float64)
    if len(timed) < _FITTED_FROM or sizes.std() == 0:
        return flat
    times = np.array([seconds for _, seconds in timed], dtype=np.float64)
    per_byte, base = np.polyfit(sizes, times, 1)
    return PhotoPace(float(base), float(per_byte)) if min(base, per_byte) > 0 else flat
