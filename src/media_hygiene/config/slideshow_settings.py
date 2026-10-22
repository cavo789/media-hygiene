"""`[slideshow]` — the photos on the TV, driven from the phone (0291).

`screen_px`: the width of the TV's picture, in pixels; each photo is sent fitted into
`screen_px` x `screen_px * 9 / 16` (1920: a Full HD TV, 3840: a 4K one). A smaller
picture loads and decodes faster on an old TV. `interval_seconds`: how long each photo
stays when the slideshow plays, until the phone changes it. The port is the one of
every page, `[review] port`: a TV's bookmark keeps working while it does not change.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

SCREEN_PX: Final = 1920
_SMALLEST_SCREEN: Final = 640
_LARGEST_SCREEN: Final = 7680  # 8K
INTERVAL_SECONDS: Final = 8
SHORTEST_INTERVAL: Final = 2
LONGEST_INTERVAL: Final = 600


class SlideshowSettings(BaseModel):
    """`[slideshow]` — the size of the TV's pictures and the pace of the show."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    screen_px: int = Field(default=SCREEN_PX, ge=_SMALLEST_SCREEN, le=_LARGEST_SCREEN)
    interval_seconds: int = Field(
        default=INTERVAL_SECONDS, ge=SHORTEST_INTERVAL, le=LONGEST_INTERVAL
    )
