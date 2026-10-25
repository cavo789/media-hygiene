"""Layouts: where a file goes, written with placeholders, checked for Windows.

`{year}/{year_month}/{category}` becomes `2016/2016-07/Vacances`. An empty layout means
"stay where it is". The month of an event is the month it starts; a month unknown (a
folder that gives only the year) is `00`, a digit in every language (0400).
Folder names are NFC-normalised; characters Windows refuses become `_`.
"""

from __future__ import annotations

import dataclasses
import re
import string
import unicodedata
from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _

PLACEHOLDERS: Final = frozenset(
    {"year", "year_month", "quarter", "month", "month_name", "day", "category", "event"}
    | {"event_start", "place", "country", "region", "city"}
)
_FORBIDDEN: Final = re.compile(r'[<>:"|?*\\\x00-\x1f]')
_RESERVED: Final = frozenset(
    {"con", "prn", "aux", "nul"}
    | {f"com{number}" for number in range(1, 10)}
    | {f"lpt{number}" for number in range(1, 10)}
)
_MONTHS_PER_QUARTER: Final = 3


@dataclass(frozen=True, slots=True)
class GeoValues:
    """What a layout can say of where a file was taken: its place, or its trip's."""

    place: str = ""  # a personal place
    country: str = ""  # those of a trip
    region: str = ""
    city: str = ""


@dataclass(frozen=True, slots=True)
class Values:
    """What a layout can say about one file: its date, category, event and place."""

    year: int
    month: int
    day: int
    category: str = ""
    event: str = ""
    event_start: str = ""
    geo: GeoValues = dataclasses.field(default_factory=GeoValues)


def check_layout(layout: str) -> None:
    """Refuse an unknown placeholder, or a fixed folder name Windows refuses.

    Args:
        layout: A layout, e.g. `{year}/{category}`.

    Raises:
        ValueError: The layout cannot work; the message lists the allowed placeholders.
    """
    for _text, field, _spec, _conversion in string.Formatter().parse(layout):
        if field is not None and field not in PLACEHOLDERS:
            allowed = ", ".join(f"{{{name}}}" for name in sorted(PLACEHOLDERS))
            message = _(
                "unknown placeholder {placeholder} in '{layout}'; allowed: {allowed}"
            ).format(placeholder=f"{{{field}}}", layout=layout, allowed=allowed)
            raise ValueError(message)
    for segment in layout.split("/"):
        fixed = re.sub(r"\{[^}]*\}", "", segment)
        if _FORBIDDEN.search(fixed) or segment.strip(". ") != segment.strip():
            message = _("'{name}' is not a folder name Windows accepts").format(
                name=segment
            )
            raise ValueError(message)


def render(layout: str, values: Values) -> str | None:
    """Turn a layout into a relative folder.

    Args:
        layout: A checked layout.
        values: What is known of the file.

    Returns:
        The folder, `/`-separated; None for an empty layout (stay where it is).
    """
    if not layout.strip():
        return None
    month = f"{values.month:02d}"  # `00`: only the year is known
    filled = layout.format(
        year=f"{values.year:04d}",
        year_month=f"{values.year:04d}-{month}",
        quarter=(values.month + _MONTHS_PER_QUARTER - 1) // _MONTHS_PER_QUARTER,
        month=month,
        month_name=month_name(values.month) if values.month else month,
        day=f"{values.day:02d}",
        category=values.category,
        event=values.event,
        event_start=values.event_start,
        place=values.geo.place,
        country=values.geo.country,
        region=values.geo.region,
        city=values.geo.city,
    )
    segments = [safe_name(part) for part in filled.split("/")]
    return "/".join(segment for segment in segments if segment)


def safe_name(name: str) -> str:
    """Make a folder name Windows accepts, keeping it readable.

    Args:
        name: A name from a layout, a folder label or a user's edit.

    Returns:
        The NFC name: forbidden characters as `_`, no trailing dot or space, a
        reserved device name suffixed with `_`.
    """
    clean = _FORBIDDEN.sub("_", unicodedata.normalize("NFC", name)).strip().rstrip(". ")
    return f"{clean}_" if clean.casefold() in _RESERVED else clean


def month_name(month: int) -> str:
    """The translated name of a month.

    Args:
        month: 1 to 12.

    Returns:
        E.g. `July`, `juillet` in French.
    """
    names = (
        _("January"),
        _("February"),
        _("March"),
        _("April"),
        _("May"),
        _("June"),
        _("July"),
        _("August"),
        _("September"),
        _("October"),
        _("November"),
        _("December"),
    )
    return names[month - 1]
