"""The most frequent droppable tags, and a synonym merged into another tag (0622).

The same sources as dropping (`index.tag_drop.DROPPABLE`): a row of the synonym becomes
a row of the tag it means; a photo carrying both keeps one. The next `tags` names it so
too, from `[tags] synonyms`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.index.tag_drop import DROPPABLE, spellings

if TYPE_CHECKING:
    import sqlite3

_SOURCES: Final = ", ".join(f"'{source.value}'" for source in DROPPABLE)
_FREQUENT: Final = (
    "SELECT value, COUNT(DISTINCT path) AS photos FROM tags"  # noqa: S608
    f" WHERE source IN ({_SOURCES}) GROUP BY value ORDER BY photos DESC, value"
    " LIMIT ?"
)
_RENAME: Final = (
    "UPDATE OR IGNORE tags SET value = ?"  # noqa: S608
    f" WHERE source IN ({_SOURCES}) AND value IN ({{marks}})"
)
_LEFT: Final = (
    "DELETE FROM tags"  # noqa: S608
    f" WHERE source IN ({_SOURCES}) AND value IN ({{marks}})"
)


def frequent(connection: sqlite3.Connection, limit: int) -> list[tuple[str, int]]:
    """The droppable tags carried by the most photos.

    Args:
        connection: The open index.
        limit: How many.

    Returns:
        Each tag and its number of photos, the most frequent first.
    """
    found = connection.execute(_FREQUENT, (limit,))
    return [(str(value), int(photos)) for value, photos in found]


def merge_word(connection: sqlite3.Connection, word: str, target: str) -> int:
    """Make every row of a word a row of another tag, committed.

    Args:
        connection: The index, writable.
        word: The synonym, any case.
        target: The tag it means.

    Returns:
        The rows of the synonym there were.
    """
    values = [value for value in spellings(connection, (word,)) if value != target]
    if not values:
        return 0
    marks = ", ".join("?" * len(values))
    renamed = connection.execute(_RENAME.format(marks=marks), [target, *values])
    left = connection.execute(_LEFT.format(marks=marks), values)
    connection.commit()
    return renamed.rowcount + left.rowcount
