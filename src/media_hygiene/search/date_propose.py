"""What *📅 Date…* proposes (0531): the folder's name, the neighbours' dates."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.search import statements as sql

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

_IN_NAME: Final = re.compile(
    r"(?<!\d)((?:19|20)\d{2})[-_. ]?(0[1-9]|1[0-2])"
    r"(?:[-_. ]?(0[1-9]|[12]\d|3[01]))?(?!\d)"
)
_MOST: Final = 4  # proposals: a choice, not a list


def folder_day(folder: Path) -> str | None:
    """The day a folder's name says, or the first of the month it says.

    Args:
        folder: The folder.

    Returns:
        `YYYY-MM-DD`, from the folder or its nearest parent naming one; None.
    """
    for part in reversed(folder.parts):
        if found := _IN_NAME.search(part):
            year, month, day = found.groups()
            return f"{year}-{month}-{day or '01'}"
    return None


def neighbour_days(connection: sqlite3.Connection, photo: Path) -> list[str]:
    """The days of the nearest dated files of its folder, before and after by name.

    Args:
        connection: The open index.
        photo: The photo.

    Returns:
        Up to two days.
    """
    folder = str(photo.parent)
    rows = connection.execute(sql.FOLDER_FILES, (folder + "/", folder + "0"))
    dated = sorted(
        (row[1], row[3])
        for row in rows
        if row[3] and "/" not in row[1][len(folder) + 1 :]
    )
    before = [day for path, day in dated if path < str(photo)]
    after = [day for path, day in dated if path > str(photo)]
    return [*before[-1:], *after[:1]]


def proposals(connection: sqlite3.Connection, photos: tuple[Path, ...]) -> list[str]:
    """The days to propose for the photos picked, the likeliest first.

    Args:
        connection: The open index.
        photos: The photos picked.

    Returns:
        The distinct days, a few at most.
    """
    days: dict[str, None] = {}
    for photo in photos[:_MOST]:
        if (named := folder_day(photo.parent)) is not None:
            days[named] = None
        days.update(dict.fromkeys(neighbour_days(connection, photo)))
    return list(days)[:_MOST]
