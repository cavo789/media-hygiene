"""`[review]` — what the burst review proposes before you choose.

In a burst series every shot shows the same scene: comparing their sharpness with each
other is meaningful. A shot far less sharp than the sharpest one is proposed to be set
aside; moving on to the next series accepts the proposal, a key takes it back.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

_PROPOSE_ASIDE_BELOW: Final = 0.35


class ReviewSettings(BaseModel):
    """`[review]` — the shots the burst review proposes to set aside."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Share of the sharpest shot's sharpness, 0 to 1; 0 never proposes anything.
    propose_aside_below: float = Field(default=_PROPOSE_ASIDE_BELOW, ge=0, lt=1)
