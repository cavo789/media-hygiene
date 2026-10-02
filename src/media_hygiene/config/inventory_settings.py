"""`[inventory]` — the thresholds behind the labels of `inventory`, never stored.

The index keeps raw measures only (sharpness, brightness, clipped shares). Whether a
picture is blurry, small, dark or bright is decided when the inventory is exported, with
these values: change them and export again, nothing is scanned.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

# Gray levels range from 0 to 255; shares from 0 to 1.
_GRAY_MAX: Final = 255
_BLURRY_BELOW: Final = 100.0
_SMALL_BELOW: Final = 1000
_DARK_BELOW: Final = 50.0
_BRIGHT_ABOVE: Final = 205.0
_CLIPPED_ABOVE: Final = 0.25


class InventorySettings(BaseModel):
    """`[inventory]` — when a picture reads as blurry, small, dark or bright."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Variance of the Laplacian on the fixed-size analysis thumbnail.
    blurry_below: float = Field(default=_BLURRY_BELOW, ge=0)
    # Pixels, shorter side.
    small_below: int = Field(default=_SMALL_BELOW, ge=0)
    # Mean brightness, 0 to 255.
    dark_below: float = Field(default=_DARK_BELOW, ge=0, le=_GRAY_MAX)
    bright_above: float = Field(default=_BRIGHT_ABOVE, ge=0, le=_GRAY_MAX)
    # Share of the pixels clipped to black (dark) or to white (bright), 0 to 1.
    clipped_above: float = Field(default=_CLIPPED_ABOVE, ge=0, le=1)
