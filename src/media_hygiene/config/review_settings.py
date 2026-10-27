"""`[review]` — what the burst review proposes before you choose.

In a burst series every shot shows the same scene: comparing them with each other is
meaningful. A shot far less sharp than the sharpest one, nearly identical to a sharper
one, or clearly over- or under-exposed next to the others is proposed to be set aside;
moving on to the next series accepts the proposal, a key takes it back. A series whose
only shots left are the sharpest and those of protected folders is obvious: the page
validates every obvious series at once.

`port`: the port of every page (`review`, `home`, `places`…), published by `mh` under
the same number on the host; another number for whoever cannot free 8088 (0260).

`lan`: `mh` opens the home page to the phones of the home Wi-Fi too (0367); on by
default since HTTPS and durable pairing (0430, 0431); false keeps it on the PC.

`[review.unwanted]`: what `review --junk` lists as most likely unwanted, never set
aside without you. Each threshold at 0 disables its reason.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

_PROPOSE_ASIDE_BELOW: Final = 0.35
_IDENTICAL_BELOW: Final = 6
_HASH_BITS: Final = 64
_BRIGHTNESS_GAP: Final = 60.0
_GRAY_LEVELS: Final = 255
_CLIPPED_GAP: Final = 0.25
_TINY_MEGAPIXELS: Final = 0.16  # 400 x 400: icons, stickers, thumbnails
_DARK_MEAN: Final = 25.0
_WHITE_MEAN: Final = 230.0
_FLAT_SHARE: Final = 0.7
_BLUR_PERCENTILE: Final = 2.0
_PERCENT: Final = 100
# Uncommon, so rarely taken on the host, where `mh` publishes it under the same number.
PAGE_PORT: Final = 8088
_LAST_PORT: Final = 65535


class UnwantedSettings(BaseModel):
    """`[review.unwanted]` — the photos `review --junk` shows as likely unwanted."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Below this many megapixels (width x height / 1,000,000); 0 disables.
    tiny_megapixels: float = Field(default=_TINY_MEGAPIXELS, ge=0)
    # A screenshot or a document, as `classify` tells them (`kind = "screenshot"`).
    screenshots: bool = True
    # Nearly black: mean brightness under `dark_mean` (0 to 255) with at least
    # `dark_share` of the pixels black; 0 disables.
    dark_mean: float = Field(default=_DARK_MEAN, ge=0, le=_GRAY_LEVELS)
    dark_share: float = Field(default=_FLAT_SHARE, ge=0, le=1)
    # Nearly white: mean brightness over `white_mean` with at least `white_share` of
    # the pixels white; 0 disables.
    white_mean: float = Field(default=_WHITE_MEAN, ge=0, le=_GRAY_LEVELS)
    white_share: float = Field(default=_FLAT_SHARE, ge=0, le=1)
    # The blurriest: sharpness under this percentile of the collection's own images
    # (0 to 100); 0 disables.
    blur_percentile: float = Field(default=_BLUR_PERCENTILE, ge=0, le=_PERCENT)


class ReviewSettings(BaseModel):
    """`[review]` — the shots the burst review proposes to set aside."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Share of the sharpest shot's sharpness, 0 to 1; 0 never proposes anything.
    propose_aside_below: float = Field(default=_PROPOSE_ASIDE_BELOW, ge=0, lt=1)
    # Bits of perceptual hash (0 to 64) a shot differs by from a sharper one, below
    # which it is a repeat; 0 disables the rule.
    identical_below: int = Field(default=_IDENTICAL_BELOW, ge=0, le=_HASH_BITS)
    # Gray levels (0 to 255) between a shot's mean brightness and the others'; 0
    # disables the rule.
    brightness_gap: float = Field(default=_BRIGHTNESS_GAP, ge=0, le=_GRAY_LEVELS)
    # Share of pixels clipped to white or black (0 to 1) above the others'; 0 disables.
    clipped_gap: float = Field(default=_CLIPPED_GAP, ge=0, le=1)
    # The port of the pages, inside the container and on the host (`mh update` after a
    # change: it writes the port into `mh`).
    port: int = Field(default=PAGE_PORT, ge=1, le=_LAST_PORT)
    # The home page open to the phones of the home network too, for the run (0367);
    # false: the PC alone (`mh --lan` then opens it for one run). Written into `mh` by
    # `mh update`, like `port`. On by default (maintainer, 2026-10-27).
    lan: bool = True
    unwanted: UnwantedSettings = UnwantedSettings()
