r"""What the TV tells of each event of the show: its name, its period, its place (0448).

An event is a run of photos of the same folder, in the show's order. Its name is the
deepest folder that says something: not a year, a month, a date nor a device's folder
(`2026/2026-10/Promenade à Valkenburg` is *Promenade à Valkenburg*); the top folder
of a drive (`C:\Photos`) is the library, never a name. Its period is the month of
its photos, or the months it spans; its place is given by `services.slideshow_story`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import month_name
from media_hygiene.plan.name_rules import DEFAULT_NAME_RULES

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import PurePath

    from media_hygiene.slideshow.event_map import EventMap

# How long the TV shows an event's title card, then the banner on its first photo.
TITLE_SECONDS: Final = 3
BANNER_SECONDS: Final = 5
_SPAN: Final = "{first} \u2013 {last} {year}"  # an en dash, in every language
_DAY_LENGTH: Final = 10  # `2026-10-28`


class Telling(StrEnum):
    """Where the events are told, chosen on the phone."""

    TV = "tv"  # the title card on the TV, the details on the phone
    PHONE = "phone"  # the phone only
    NOWHERE = "none"


@dataclass(frozen=True, slots=True)
class Chapter:
    """One event of the show: a number (tells events apart), what is said of it."""

    number: int
    name: str = ""
    period: str = ""
    place: str = ""
    map: EventMap | None = None  # the phone's small map (0449), not sent to the TV

    def view(self) -> dict[str, object]:
        """The event, for the pages.

        Returns:
            Its number, name, period and place (empty when unknown).
        """
        return {
            "number": self.number,
            "name": self.name,
            "period": self.period,
            "place": self.place,
        }


def event_name(folder: PurePath, library: PurePath) -> str:
    """The name of an event: the deepest folder that says something.

    Args:
        folder: The photos' folder, in the container.
        library: The folder of the drives (`/data`): the drive and its top folder
            are never a name.

    Returns:
        The name, accents kept; empty when every folder is a date or generic.
    """
    parts = folder.parts
    if folder.is_relative_to(library):
        parts = folder.relative_to(library).parts[2:]  # past `c/Photos`
    for name in reversed(parts):
        generic = DEFAULT_NAME_RULES.generic_folders
        if not any(pattern.fullmatch(name) for pattern in generic):
            return name
    return ""


def event_period(days: Iterable[str | None]) -> str:
    """The month of an event's photos, or the months it spans.

    Args:
        days: The photos' days (`2026-10-28`), None when undated.

    Returns:
        E.g. `October 2026`, `July - August 2023` (an en dash); empty without a date.
    """
    known = sorted(day for day in days if day and len(day) >= _DAY_LENGTH)
    if not known:
        return ""
    first, last = (_month_of(day) for day in (known[0], known[-1]))
    if first == last:
        return f"{month_name(first[1])} {first[0]}"
    if first[0] == last[0]:
        return _SPAN.format(
            first=month_name(first[1]), last=month_name(last[1]), year=first[0]
        )
    return _SPAN.format(
        first=f"{month_name(first[1])} {first[0]}",
        last=month_name(last[1]),
        year=last[0],
    )


def _month_of(day: str) -> tuple[int, int]:
    """The year and month of a day.

    Args:
        day: E.g. `2026-10-28`.

    Returns:
        E.g. (2026, 10).
    """
    return int(day[:4]), int(day[5:7])
