"""Layouts: where a file goes, written with placeholders, checked for Windows.

`{year}/{category}` becomes `2016/Vacances`. An empty layout means "stay where it is".
Folder names are NFC-normalised; characters Windows refuses become `_`.
"""

from __future__ import annotations

import re
import string
import unicodedata
from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _

PLACEHOLDERS: Final = frozenset(
    {"year", "quarter", "month", "month_name", "day", "category", "event"}
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
class Values:
    """What a layout can say about one file: its date, its category, its event."""

    year: int
    month: int
    day: int
    category: str = ""
    event: str = ""
    event_start: str = ""


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
            message = (
                f"unknown placeholder {{{field}}} in {layout!r}; allowed: {allowed}"
            )
            raise ValueError(message)
    for segment in layout.split("/"):
        fixed = re.sub(r"\{[^}]*\}", "", segment)
        if _FORBIDDEN.search(fixed) or segment.strip(". ") != segment.strip():
            message = f"{segment!r} is not a folder name Windows accepts"
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
    filled = layout.format(
        year=f"{values.year:04d}",
        quarter=(values.month - 1) // _MONTHS_PER_QUARTER + 1,
        month=f"{values.month:02d}",
        month_name=month_name(values.month),
        day=f"{values.day:02d}",
        category=values.category,
        event=values.event,
        event_start=values.event_start,
        place="",
        country="",
        region="",
        city="",
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
