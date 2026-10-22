"""One photo of a show, and the pace of the show (`show`)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class Slide:
    """One photo of the show: its key in the index (names its pictures), its day."""

    key: int
    day: str | None = None


@dataclass(frozen=True, slots=True)
class Timing:
    """How long a photo stays while playing, and the clock it is measured with."""

    interval: float
    clock: Callable[[], float] = field(default=time.monotonic)
