"""What the TV tells of the photo shown: its event (0448) and its place (0472)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.slideshow.chapters import Telling

if TYPE_CHECKING:
    from media_hygiene.slideshow.desk import Desk


def told_chapter(desk: Desk) -> dict[str, object] | None:
    """The event of the photo shown, when the TV tells it (0448).

    Args:
        desk: The show.

    Returns:
        Its number, name, period and place; None when told on the phone only, or
        nowhere.
    """
    current = desk.show.current
    if current is None or current.chapter is None:
        return None
    return current.chapter.view() if desk.screens.telling is Telling.TV else None


def told_place_of(desk: Desk) -> str:
    """Where the photo shown was taken, when the TV tells the events (0472).

    Args:
        desk: The show.

    Returns:
        Its place; empty without GPS, when its event says it, or when the events are
        told on the phone only, or nowhere.
    """
    current = desk.show.current
    if current is None or desk.screens.telling is not Telling.TV:
        return ""
    return current.place
