"""The order of the show: the nearest slide still shown, a slide found by its key."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.slideshow.slides import Slide


@dataclass(frozen=True, slots=True)
class Order:
    """The selection, and what tells whether a slide may be shown now."""

    slides: tuple[Slide, ...]
    shown: Callable[[Slide], bool]

    def step(self, start: int | None, direction: int) -> int | None:
        """Find the nearest slide still shown from a place, one way, going round.

        Args:
            start: The place now; None for nothing shown.
            direction: 1 forward, -1 back.

        Returns:
            The place found; None when no slide may be shown.
        """
        count = len(self.slides)
        if start is None:
            start = -1 if direction > 0 else 0
        for offset in range(1, count + 1):
            position = (start + direction * offset) % count
            if self.shown(self.slides[position]):
                return position
        return None

    def place_of(self, key: int) -> int | None:
        """Find a slide of the selection by its key.

        Args:
            key: Its key.

        Returns:
            Its place, or None.
        """
        return next(
            (at for at, slide in enumerate(self.slides) if slide.key == key), None
        )
