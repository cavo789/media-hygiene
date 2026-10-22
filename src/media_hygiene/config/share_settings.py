"""`[share]` — the copies `share` makes of an album, to send them (0296).

`long_side_px`: the long side of each copy, in pixels (2048 by default: sharp on a
screen, a few hundred kilobytes). `quality`: the JPEG quality of the copies (85).
`keep_gps`: keep the GPS position in the copies; false by default, a photo sent must
not say where the house is (`share --keep-gps` keeps it for one run).
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

LONG_SIDE_PX: Final = 2048
_SMALLEST_SIDE: Final = 320
_LARGEST_SIDE: Final = 8192
QUALITY: Final = 85
_LOWEST_QUALITY: Final = 30
_HIGHEST_QUALITY: Final = 95  # above, Pillow's own advice: larger files, no better


class ShareSettings(BaseModel):
    """`[share]` — the size, the quality and the GPS position of the copies to send."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    long_side_px: int = Field(default=LONG_SIDE_PX, ge=_SMALLEST_SIDE, le=_LARGEST_SIDE)
    quality: int = Field(default=QUALITY, ge=_LOWEST_QUALITY, le=_HIGHEST_QUALITY)
    keep_gps: bool = False
