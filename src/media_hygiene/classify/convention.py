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
# A year folder followed by its own month folder, anywhere in a path (`place_of_path`).
_PAIR_IN_PATH: Final = re.compile(r"/(\d{4})/\1-(?:0\d|1[0-2])/")
_SEPARATOR: Final = "/"


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


def shape_in(parts: Sequence[str]) -> Shape:
    r"""Read the convention anywhere in a file's folders, without knowing its root.

    `C:\Photos\2009\2009-11\Tom` and `D:\Tri\2009\2009-11\Tom` read the same: the
    first pair of a year folder and its `YYYY-MM` folder decides (0405, 0407).

    Args:
        parts: The folder names, outermost first (the file's name left out).

    Returns:
        Its shape; `LEFT` without such a pair.
    """
    for index in range(len(parts) - 1):
        shape = shape_of(parts[index:])
        if shape.place is not Place.LEFT:
            return shape
    return Shape(Place.LEFT)


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


def place_of_path(path: str) -> str:
    """The state a container path says, as the search's SQL filter reads it (0407).

    One regular expression instead of `shape_in` on the folders: the same answer, run
    for every row of a search (70,000 rows; measured 180 ms with `shape_in`).

    Args:
        path: A file's container path (`/`-separated).

    Returns:
        A `Place` value.
    """
    found = _PAIR_IN_PATH.search(path)
    if found is None:
        return Place.LEFT.value
    below = path[found.end() :]
    return (Place.EVENT if _SEPARATOR in below else Place.NOTHING_SPECIAL).value
