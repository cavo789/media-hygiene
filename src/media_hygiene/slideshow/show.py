"""The show the server holds: the photos and videos, the one on the TV, the timer.

Every change raises `version`: the pages wait for a version they have not seen yet
(`desk`). Next and previous go round the selection, passing over the photos set out
of the show ("do not show") and the videos the TV cannot play (0292); a photo chosen
on the phone is shown even when it was set out (the choice is explicit). The timer is
read, never run: `tick` moves on once the interval is over (a video: once the TV says
it ended, `ended`), called by whoever waits (the TV, the phone).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.slideshow.order import Order

if TYPE_CHECKING:
    from media_hygiene.slideshow.slides import Slide, Timing


class Show:  # pylint: disable=too-many-instance-attributes
    """The selection, the photo shown, whether it plays; one version per change.

    `position` is the place of the photo on the TV in `slides`, None when nothing is
    shown (an empty selection, every photo set out). `films` is False once every TV
    paired shows photos only (a 2012 TV's own browser): its videos are passed over.
    """

    __slots__ = (
        "_deadline",
        "films",
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
        self.films = True
        self.version = 1
        self.position: int | None = self._order.step(None, 1)  # the first shown
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
        position = self._order.step(self.position, 1)
        return None if position in {None, self.position} else self.slides[position]

    def move(self, direction: int) -> None:
        """Show the next photo still in the show (1), or the previous one (-1).

        Args:
            direction: 1 forward (the first after the last), -1 back.
        """
        self._go(self._order.step(self.position, direction))

    def jump(self, key: int) -> bool:
        """Show a photo chosen on the phone, set back in the show if it was out.

        Args:
            key: Its key.

        Returns:
            False for a key not in the selection.
        """
        place = self._order.place_of(key)
        if place is None or not self.plays(self.slides[place]):
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
        place = self._order.place_of(key)
        if place is None:
            return False
        if out:
            self.skipped.add(key)
        else:
            self.skipped.discard(key)
        current = self.current
        shown_out = out and current is not None and current.key == key
        if shown_out or (not out and current is None):
            self.move(1)
        else:
            self.version += 1
        return True

    def play(self, *, playing: bool) -> None:
        """Play or pause; playing starts the interval again.

        Args:
            playing: True to play.
        """
        self.playing = playing
        self._deadline = self.timing.clock() + self.timing.stay(self.current)
        self.version += 1

    def plays(self, slide: Slide) -> bool:
        """Tell whether the TV can show a slide: a photo, or a video it plays.

        Args:
            slide: The slide.

        Returns:
            False for a video in a format the TV cannot play, or while every TV
            shows photos only.
        """
        film = slide.film
        return film is None or (film.playable and self.films)

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
        self._deadline = self.timing.clock() + self.timing.stay(self.current)
        self.version += 1

    @property
    def _order(self) -> Order:
        """The selection, stopping at the slides still shown.

        Returns:
            It.
        """
        return Order(self.slides, self._shown)

    def _shown(self, slide: Slide) -> bool:
        """Tell whether next and previous stop at a slide.

        Args:
            slide: The slide.

        Returns:
            False for one set out of the show, or a video the TV cannot play.
        """
        return slide.key not in self.skipped and self.plays(slide)
