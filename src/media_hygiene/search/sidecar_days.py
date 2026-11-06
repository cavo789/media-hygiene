"""Read the days of the files without a date from their `.xmp` sidecars (0531).

Only the folders of files the index has no date for are listed, and only an `.xmp`
beside one of them is read: most collections read no file at all here. The sidecar is
found by its name, so a file moved with its sidecar (`sort`, Explorer) keeps its day.
"""

from __future__ import annotations

import contextlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.hand_days import ready
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.days import media_day
from media_hygiene.search.known_day import CLEAR_DAYS, OWN_UNDATED, PUT_DAY
from media_hygiene.services.xmp_sidecars import sidecar_of
from media_hygiene.tags.xmp_date import sidecar_day
from media_hygiene.tags.xmp_doc import XmpError

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

_XMP: Final = ".xmp"
_NOON: Final = 12


def days_of(paths: Iterable[Path]) -> dict[Path, str]:
    """The days the sidecars of these files hold.

    Args:
        paths: The files.

    Returns:
        The day of each file whose sidecar says one; a folder or a sidecar that
        cannot be read gives none.
    """
    folders: defaultdict[Path, list[Path]] = defaultdict(list)
    for path in paths:
        folders[path.parent].append(path)
    days: dict[Path, str] = {}
    for folder, files in folders.items():
        names = _names_with_sidecars(folder)
        for file in files if names else ():
            if (day := _day_beside(file, {folder: names})) is not None:
                days[file] = day
    return days


def moments_of(paths: Iterable[Path]) -> dict[Path, datetime]:
    """The same days as dates, at noon, as a file name without a time gives them.

    Args:
        paths: The files.

    Returns:
        The date of each file whose sidecar says a real day.
    """
    moments: dict[Path, datetime] = {}
    for path, day in days_of(paths).items():
        with contextlib.suppress(ValueError):  # `2019-13-45` names no day
            moments[path] = datetime.fromisoformat(day).replace(hour=_NOON)
    return moments


def _names_with_sidecars(folder: Path) -> list[str]:
    """The names of a folder holding a sidecar.

    Args:
        folder: The folder.

    Returns:
        Its names, sorted; none when it cannot be read or holds no sidecar.
    """
    try:
        names = sorted(entry.name for entry in folder.iterdir())
    except OSError:
        return []
    return names if any(n.casefold().endswith(_XMP) for n in names) else []


def _day_beside(file: Path, listed: dict[Path, list[str]]) -> str | None:
    """The day of a file's sidecar.

    Args:
        file: The file.
        listed: The names of its folder.

    Returns:
        The day; None without a sidecar saying one, or one that cannot be read.
    """
    sidecar = sidecar_of(file, listed)
    try:
        return sidecar_day(sidecar.read_bytes()) if sidecar.is_file() else None
    except OSError, XmpError:
        return None


def undated_days(connection: sqlite3.Connection) -> dict[Path, str]:
    """The days of the sidecars of every file without a date of its own.

    Args:
        connection: The open index.

    Returns:
        The day of each file whose sidecar says one.
    """
    return days_of(Path(row[0]) for row in connection.execute(OWN_UNDATED))


def read_days_again(connection: sqlite3.Connection) -> None:
    """Read every sidecar's day again into the search's temporary table (0618).

    The event finders (`late_files`, `found_folders`) read it at each ask: a day set,
    undone, or a file or sidecar moved since counts at once.

    Args:
        connection: The open index.
    """
    connection.create_function(DAY, 1, media_day, deterministic=True)  # a bare index
    days = undated_days(connection)
    ready(connection).execute(CLEAR_DAYS)
    connection.executemany(PUT_DAY, [(str(path), day) for path, day in days.items()])
    connection.commit()  # no transaction left open: a move writes the index
