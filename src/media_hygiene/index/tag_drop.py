"""The rows of words dropped from every photo (0546): who carries it, and removing it.

Only the sources `[tags] stop_words` governs: a word left in another source would come
back or was never ours to judge (the model's sentence, Google Photos' description, a
date, a place, the words typed by hand). A word is one whatever its case.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    import sqlite3

DROPPABLE: Final = (
    TagSource.VISION,
    TagSource.FOLDER,
    TagSource.NAME,
    TagSource.FORMER,
)
_SOURCES: Final = ", ".join(f"'{source.value}'" for source in DROPPABLE)
_VALUES: Final = f"SELECT DISTINCT value FROM tags WHERE source IN ({_SOURCES})"  # noqa: S608
_KEYS: Final = (
    "SELECT DISTINCT f.rowid FROM tags t JOIN files f ON f.path = t.path"  # noqa: S608
    " AND f.size = t.size AND f.mtime_ns = t.mtime_ns"
    f" WHERE t.source IN ({_SOURCES}) AND t.value IN ({{marks}}) ORDER BY f.rowid"
)
_PATHS: Final = (
    "SELECT DISTINCT path FROM tags"  # noqa: S608
    f" WHERE source IN ({_SOURCES}) AND value IN ({{marks}})"
)
_DELETE: Final = (
    f"DELETE FROM tags WHERE source IN ({_SOURCES}) AND value IN ({{marks}})"  # noqa: S608
)


def spellings(connection: sqlite3.Connection, words: tuple[str, ...]) -> list[str]:
    """Every spelling of some words in the droppable rows.

    Args:
        connection: The open index.
        words: The words, any case.

    Returns:
        The values stored.
    """
    folded = {word.casefold() for word in words}
    return [
        str(value)
        for (value,) in connection.execute(_VALUES)
        if str(value).casefold() in folded
    ]


def _marks(values: list[str]) -> str:
    """The placeholders of a list of values.

    Args:
        values: The values.

    Returns:
        `?, ?`.
    """
    return ", ".join("?" * len(values))


def keys_of(connection: sqlite3.Connection, words: tuple[str, ...]) -> list[int]:
    """The files carrying any of some words, in their current version.

    Args:
        connection: The open index.
        words: The words.

    Returns:
        Their keys (the search's).
    """
    values = spellings(connection, words)
    found = connection.execute(_KEYS.format(marks=_marks(values)), values)
    return [int(key) for (key,) in found]


def paths_of(connection: sqlite3.Connection, words: tuple[str, ...]) -> list[str]:
    """The paths with a row of some words, any version: their sidecars may hold them.

    Args:
        connection: The open index.
        words: The words.

    Returns:
        The container paths.
    """
    values = spellings(connection, words)
    found = connection.execute(_PATHS.format(marks=_marks(values)), values)
    return [str(path) for (path,) in found]


def delete_word(connection: sqlite3.Connection, words: tuple[str, ...]) -> int:
    """Remove some words from every file, committed.

    Args:
        connection: The index, writable.
        words: The words.

    Returns:
        The rows removed.
    """
    values = spellings(connection, words)
    removed = connection.execute(_DELETE.format(marks=_marks(values)), values).rowcount
    connection.commit()
    return removed
