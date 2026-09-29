"""Measure the exposure of an image, on the gray thumbnail already made for its hashes.

Raw measures only: the mean brightness and the shares of pixels clipped to black and to
white. Whether a picture is too dark is a judgment made later, with thresholds the user
can change: a night sky is dark on purpose.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

# Gray levels counted as clipped: detail is lost in the last few levels already.
_DARK_MAX: Final = 4
_BRIGHT_MIN: Final = 251
_DECIMALS: Final = 4


@dataclass(frozen=True, slots=True)
class Exposure:
    """Mean brightness (0 to 255) and shares of clipped pixels (0 to 1)."""

    brightness: float
    dark_share: float
    bright_share: float


def measure(pixels: NDArray[np.float64]) -> Exposure | None:
    """Measure the exposure of grayscale pixels.

    Args:
        pixels: Gray levels from 0 to 255.

    Returns:
        The measures, or None for an image without pixels.
    """
    if not pixels.size:
        return None
    return Exposure(
        brightness=round(float(pixels.mean()), 1),
        dark_share=round(float((pixels <= _DARK_MAX).mean()), _DECIMALS),
        bright_share=round(float((pixels >= _BRIGHT_MIN).mean()), _DECIMALS),
    )
