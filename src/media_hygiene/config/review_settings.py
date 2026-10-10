"""`[review]` — what the burst review proposes before you choose.

In a burst series every shot shows the same scene: comparing them with each other is
meaningful. A shot far less sharp than the sharpest one, nearly identical to a sharper
one, or clearly over- or under-exposed next to the others is proposed to be set aside;
moving on to the next series accepts the proposal, a key takes it back. A series whose
only shots left are the sharpest and those of protected folders is obvious: the page
validates every obvious series at once.
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
