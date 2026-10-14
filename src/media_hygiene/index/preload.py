"""Read the index rows below the scanned folders at once, instead of one per file.

An audit asks the index about every file, several times for some (integrity, then
each digest). One `SELECT` per mounted folder, parsed once, answers all of them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.index.rows import facts_of
from media_hygiene.index.schema import FILES_UNDER

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.index.facts import FileFacts

    # Size, mtime and the facts of that version, by path.
    type Known = dict[str, tuple[int, int, FileFacts]]

# Sorts right after "/": every "folder/..." path is below "folder0".
AFTER_SEPARATOR: Final = "0"
# The path, then the columns `rows.facts_of` reads, size and mtime first.
_PATH, _SIZE, _MTIME = 0, 1, 2


def bounds_under(folder: Path) -> tuple[str, str]:
    """The range of the paths below a folder, for `path >= ? AND path < ?`.

    Args:
        folder: A folder (container path).

    Returns:
        The lower bound, included, and the upper bound, excluded.
    """
    return f"{folder}/", f"{folder}{AFTER_SEPARATOR}"


def known_under(connection: sqlite3.Connection, roots: Iterable[Path]) -> Known:
    """Every row below the roots, its facts parsed.

    Args:
        connection: The index.
        roots: The mounted folders.

    Returns:
        The facts of each file, with the size and mtime they hold for.
    """
    known: Known = {}
    for root in roots:
        for row in connection.execute(FILES_UNDER, bounds_under(root)):
            known[row[_PATH]] = (row[_SIZE], row[_MTIME], facts_of(row[_SIZE:]))
    return known
