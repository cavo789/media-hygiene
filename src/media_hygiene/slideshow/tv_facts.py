"""The TV welcome page's line of index facts: how many files, which years (0758).

Read from the index alone, read-only, at each visit (one `COUNT` and one `MIN`/`MAX`
over the `files` table: milliseconds). No index yet, or one that cannot be read: no
line, the page stays as it was.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.index.read_only import connect_read_only

if TYPE_CHECKING:
    from pathlib import Path

_QUERY: Final = (
    "SELECT COUNT(*), MIN(substr(media_date, 1, 4)), MAX(substr(media_date, 1, 4))"
    " FROM files WHERE broken_reason IS NULL"
)


def facts_line(index_file: Path) -> str:
    """One line saying how many photos and videos the index knows, and their years.

    Args:
        index_file: The index.

    Returns:
        The line; empty without an index or without any file in it.
    """
    if not index_file.is_file():
        return ""
    try:
        connection = connect_read_only(index_file)
        try:
            count, first, last = connection.execute(_QUERY).fetchone()
        finally:
            connection.close()
    except sqlite3.Error:
        return ""
    if not count:
        return ""
    files = ngettext(
        "{count} photo or video", "{count} photos and videos", count
    ).format(count=human_number(count))
    if not first or not last:
        return files
    if first == last:
        return _("{files}, from {year}").format(files=files, year=first)
    return _("{files}, from {first} to {last}").format(
        files=files, first=first, last=last
    )
