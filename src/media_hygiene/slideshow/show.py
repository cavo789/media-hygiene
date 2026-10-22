"""The show the server holds: the photos, the one on the TV, the timer.

Every change raises `version`: the pages wait for a version they have not seen yet
(`desk`). Next and previous go round the selection, passing over the photos set out
of the show ("do not show"); a photo chosen on the phone is shown even when it was set
out (the choice is explicit). The timer is read, never run: `tick` moves on once the
interval is over, called by whoever waits (the TV, the phone).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.slideshow.slides import Slide, Timing


class Show:
    """The selection, the photo shown, whether it plays; one version per change.

    `position` is the place of the photo on the TV in `slides`, None when nothing is
    shown (an empty selection, every photo set out).
    """

    __slots__ = (
        "_deadline",
        "playing",
        "position",
        "skipped",
        "slides",
        "timing",
        "version",
    )

    def __init__(self, slides: tuple[Slide, ...], timing: Timing) -> None:
        """Start paused on the first photo.

        Args:
            slides: The selection, in the order shown.
            timing: The interval and the clock.
        """
        self.slides = slides
        self.timing = timing
        self.playing = False
        self.skipped: set[int] = set()
        self.version = 1
        self.position: int | None = 0 if slides else None
        self._deadline = 0.0

    @property
    def current(self) -> Slide | None:
        """The photo on the TV.

        Returns:
            It; None when nothing is shown.
        """
        return None if self.position is None else self.slides[self.position]

    @property
    def upcoming(self) -> Slide | None:
        """The photo `move(1)` would show: the TV loads it in advance.

        Returns:
            It; None when no other photo is left to show.
        """
        position = self._step(1)
        return None if position in {None, self.position} else self.slides[position]

    def move(self, direction: int) -> None:
        """Show the next photo still in the show (1), or the previous one (-1).

        Args:
            direction: 1 forward (the first after the last), -1 back.
        """
        self._go(self._step(direction))

    def jump(self, key: int) -> bool:
        """Show a photo chosen on the phone, set back in the show if it was out.

        Args:
            key: Its key.

        Returns:
            False for a key not in the selection.
        """
        place = self._place(key)
        if place is None:
            return False
        self.skipped.discard(key)
        self._go(place)
        return True

    def set_out(self, key: int, *, out: bool) -> bool:
        """Set a photo out of the show ("do not show"), or back in.

        The TV moves on when it shows the photo set out; a photo set back in is
        shown at once when nothing was.

        Args:
            key: Its key.
            out: True to set it out, False to set it back in.

        Returns:
            False for a key not in the selection.
        """
        place = self._place(key)
        if place is None:
            return False
        if out:
            self.skipped.add(key)
        else:
            self.skipped.discard(key)
        current = self.current
        if out and current is not None and current.key == key:
            self._go(self._step(1))
        elif not out and current is None:
            self._go(place)
        else:
            self.version += 1
        return True

    def play(self, *, playing: bool) -> None:
        """Play or pause; playing starts the interval again.

        Args:
            playing: True to play.
        """
        self.playing = playing
        self._deadline = self.timing.clock() + self.timing.interval
        self.version += 1

    def wait_seconds(self) -> float | None:
        """How long until the timer moves on.

        Returns:
            Seconds (0 when due); None while paused or with nothing to show.
        """
        if not self.playing or self.position is None:
            return None
        return max(0.0, self._deadline - self.timing.clock())

    def tick(self) -> bool:
        """Move on when the interval is over.

        Returns:
            True when the show moved.
        """
        if self.wait_seconds() != 0.0:
            return False
        self.move(1)
        return True

    def _go(self, position: int | None) -> None:
        """Show a place of the selection, the timer started again.

        Args:
            position: The place; None for nothing.
        """
        self.position = position
        self._deadline = self.timing.clock() + self.timing.interval
        self.version += 1

    def _step(self, direction: int) -> int | None:
        """Find the nearest photo still in the show, one way, going round.

        Args:
            direction: 1 forward, -1 back.

        Returns:
            Its place; None when every photo is set out.
        """
        count = len(self.slides)
        start = self.position
        if start is None:
            start = -1 if direction > 0 else 0
        for offset in range(1, count + 1):
            position = (start + direction * offset) % count
            if self.slides[position].key not in self.skipped:
                return position
        return None

    def _place(self, key: int) -> int | None:
        """Find a photo of the selection by its key.

        Args:
            key: Its key.

        Returns:
            Its place, or None.
        """
        return next(
            (at for at, slide in enumerate(self.slides) if slide.key == key), None
        )
