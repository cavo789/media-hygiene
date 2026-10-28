"""What the storyteller reads on the phone (0449): the photo, its notes, the next one.

The phone shows the photo on the TV larger, its time, its words and description from
the index (`tags`), the next photo, and the event's positions for a small map drawn
offline. Read-only: the story controls only move the show (`event_start`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.slideshow.show import Show
    from media_hygiene.slideshow.slides import Slide


@dataclass(frozen=True, slots=True)
class Notes:
    """What the index says of one photo, for the storyteller."""

    time: str = ""  # `14:32`, empty when unknown
    caption: str = ""  # its description (`caption`, else the Takeout one)
    words: tuple[str, ...] = ()  # the vision model's words
    point: tuple[float, float] | None = None  # latitude, longitude


def story_view(show: Show) -> dict[str, object]:
    """The storyteller's view of the photo shown.

    Args:
        show: The show.

    Returns:
        The photo's time, description and words, the next photo's key, and the
        positions of the event's photos.
    """
    current = show.current
    upcoming = show.upcoming
    notes = Notes() if current is None or current.notes is None else current.notes
    return {
        "day": None if current is None else current.day,
        "time": notes.time,
        "caption": notes.caption,
        "words": list(notes.words),
        "here": notes.point,
        "next": None if upcoming is None else upcoming.key,
        "points": [
            slide.notes.point
            for slide in _event_of(show)
            if slide.notes is not None and slide.notes.point is not None
        ],
    }


def event_start(show: Show, step: int) -> int | None:
    """The photo a story control goes to: this event's first, or the next event's.

    Args:
        show: The show.
        step: 0 for the start of this event, 1 for the next event.

    Returns:
        The key of the first photo shown of that event; None when there is none.
    """
    current = show.current
    if current is None or current.chapter is None:
        return None
    wanted = current.chapter.number + step
    later = [
        slide
        for slide in show.slides
        if slide.chapter is not None
        and slide.chapter.number >= wanted
        and slide.key not in show.skipped
        and show.plays(slide)
    ]
    if not later:
        return None
    first = min(slide.chapter.number for slide in later if slide.chapter)
    return next(
        slide.key for slide in later if slide.chapter and slide.chapter.number == first
    )


def _event_of(show: Show) -> list[Slide]:
    """The slides of the event shown.

    Args:
        show: The show.

    Returns:
        Its slides; none when nothing is shown.
    """
    current = show.current
    if current is None or current.chapter is None:
        return []
    number = current.chapter.number
    return [s for s in show.slides if s.chapter and s.chapter.number == number]
