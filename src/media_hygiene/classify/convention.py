"""The sort convention read from a path alone: `YYYY/YYYY-MM/<event>` (0401, 0405).

The tree says by itself, without plan, journal nor media-hygiene, what was done:

| Where the file is | State |
|---|---|
| `YYYY/YYYY-MM/<name>` (and a stage below) | sorted into an event |
| directly in `YYYY/YYYY-MM` | looked at, nothing special that month |
| anywhere else | left to do |

The month folder carries its year (`2009-11`, `1985-00` when only the year is known)
and must agree with the year folder above it: `2009/2010-01` is left to do.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.dating_models import Dating

_YEAR: Final = re.compile(r"\d{4}")
_YEAR_MONTH: Final = re.compile(r"(?P<year>\d{4})-(?P<month>0\d|1[0-2])")


class Place(StrEnum):
    """Where a file lies, as the convention reads it."""

    EVENT = "event"  # in a named folder below its month
    NOTHING_SPECIAL = "nothing-special"  # directly in its month folder
    LEFT = "left"  # anywhere else: still to sort


@dataclass(frozen=True, slots=True)
class Shape:
    """The state of a folder, and the year and month its folders give."""

    place: Place
    year: int = 0
    month: int = 0  # 0: `YYYY-00`, only the year is known


def shape_of(parts: Sequence[str]) -> Shape:
    """Read the convention from the folders of a file, below its sort root.

    Args:
        parts: The folder names, outermost first (the file's name left out).

    Returns:
        Its shape.
    """
    if len(parts) < 2 or not _YEAR.fullmatch(parts[0]):  # noqa: PLR2004 - year, month
        return Shape(Place.LEFT)
    found = _YEAR_MONTH.fullmatch(parts[1])
    if found is None or found["year"] != parts[0]:
        return Shape(Place.LEFT)
    place = Place.NOTHING_SPECIAL if len(parts) == 2 else Place.EVENT  # noqa: PLR2004
    return Shape(place, int(found["year"]), int(found["month"]))


def looked_at(path: Path, root: Path, dating: Dating) -> bool:
    """Tell a file put directly in the month folder its date gives: nothing special.

    The user looked at it and left it there; no event takes it again (0402).

    Args:
        path: The file.
        root: The sort root it lies below.
        dating: Its date.

    Returns:
        True when it lies in `YYYY/YYYY-MM` of its own year and month.
    """
    if not path.is_relative_to(root):
        return False
    shape = shape_of(path.parent.relative_to(root).parts)
    moment = (dating.when.year, dating.month)
    return shape.place is Place.NOTHING_SPECIAL and (shape.year, shape.month) == moment
