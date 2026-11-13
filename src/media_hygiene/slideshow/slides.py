"""One photo or video of a show, and the pace of the show (`show`).

A video (0292) is played as it is, never transcoded: the TV's browser plays the
codecs of `PLAYED_CODECS` (H.264 for 1,187 of the maintainer's 1,191 videos, measured
2026-10-21); another one (HEVC: 4 of them) is skipped, its thumbnail labelled on the
phone. A video stays until the TV says it ended; should the TV never say so (gone,
asleep), the timer moves on after its length and a margin (`Timing.stay`).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from media_hygiene.slideshow.chapters import TITLE_SECONDS

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.slideshow.chapters import Chapter
    from media_hygiene.slideshow.notes import Notes

# What a Chromecast's browser plays without help; an unknown codec is tried, the TV
# says when it fails.
PLAYED_CODECS: Final = frozenset({"h264", "vp8", "vp9"})
# The containers served as they are, with the type the TV's browser plays them by.
FILM_SUFFIXES: Final = frozenset({".mp4", ".m4v", ".mov", ".webm"})
# A video whose length the index does not know: the most it waits for its end.
UNKNOWN_LENGTH_SECONDS: Final = 300.0
# The margin over a video's length before the timer moves on without the TV.
_MARGIN_SECONDS: Final = 15.0


@dataclass(frozen=True, slots=True)
class Film:
    """What the index knows of a video: its container, its codec, its length."""

    suffix: str  # lower case, e.g. `.mov`
    codec: str | None = None  # as `ffprobe` names it: `h264`, `hevc`…
    seconds: float | None = None

    @property
    def playable(self) -> bool:
        """Tell whether the TV's browser can play it as it is.

        Returns:
            True for a container served as it is holding a codec it plays (or one
            the index does not know).
        """
        if self.suffix not in FILM_SUFFIXES:
            return False
        return self.codec is None or self.codec in PLAYED_CODECS

    @property
    def label(self) -> str:
        """Its format, as the phone names it: the container, else the codec.

        Returns:
            E.g. `avi` or `hevc`; empty when the index does not know the codec.
        """
        if self.suffix not in FILM_SUFFIXES:
            return self.suffix.removeprefix(".")
        return self.codec or ""


@dataclass(frozen=True, slots=True)
class Slide:
    """One photo or video: its key in the index (names its pictures), its day."""

    key: int
    day: str | None = None
    film: Film | None = None  # None: a photo
    chapter: Chapter | None = None  # its event (0448)
    place: str = ""  # where it was taken, when its event does not say it (0472)
    notes: Notes | None = None  # what the storyteller reads (0449)
    tag: str = ""  # its file's version, from the index: `?v=` of its pictures (0723)


@dataclass(frozen=True, slots=True)
class Timing:
    """How long a photo stays while playing, and the clock it is measured with."""

    interval: float
    clock: Callable[[], float] = field(default=time.monotonic)
    card: float = (
        TITLE_SECONDS  # the title card's seconds, 0 when the TV does not tell (0654)
    )

    def card_end(self, before: Slide | None, slide: Slide | None) -> float:
        """When the title card of a slide that comes hides (0654).

        Args:
            before: The slide shown until now.
            slide: The slide that comes.

        Returns:
            A time of the clock: now when there is no card.
        """
        return self.clock() + self.card_for(before, slide)

    def deadline(self, card_end: float, slide: Slide | None) -> float:
        """When the timer moves on: the slide's stay, counted from the card's end.

        Args:
            card_end: When the card hides.
            slide: The slide shown.

        Returns:
            A time of the clock.
        """
        return max(self.clock(), card_end) + self.stay(slide)

    def card_for(self, before: Slide | None, slide: Slide | None) -> float:
        """How long the TV's title card hides the photo, the timer waiting (0654).

        Args:
            before: The slide shown until now; None for none.
            slide: The slide that comes.

        Returns:
            Seconds: the card's, when `slide` starts an event with something to say;
            else 0.
        """
        chapter = None if slide is None else slide.chapter
        if chapter is None or not chapter.has_card:
            return 0.0
        if (
            before is not None
            and before.chapter is not None
            and before.chapter.number == chapter.number
        ):
            return 0.0
        return self.card

    def stay(self, slide: Slide | None) -> float:
        """How long a photo or a video stays while the show plays.

        Args:
            slide: The one shown; None for nothing.

        Returns:
            Seconds: the interval for a photo; for a video, the most it waits for
            the TV to say it ended.
        """
        film = None if slide is None else slide.film
        if film is None:
            return self.interval
        if film.seconds is None:
            return UNKNOWN_LENGTH_SECONDS
        return film.seconds + max(_MARGIN_SECONDS, film.seconds / 2)
