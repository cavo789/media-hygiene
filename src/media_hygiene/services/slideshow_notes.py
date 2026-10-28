"""The storyteller's notes of each photo of a show (0449), read from the index alone.

Its time (`media_date`), its position (GPS), its description and the vision model's
words (`tags`). The people recognised are not read here: their names are made at each
search, from the face lists, never kept in the index.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.slideshow.notes import Notes
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from pathlib import Path

_FACTS: Final = "SELECT media_date, metadata FROM files WHERE rowid = ?"
_TAGS: Final = "SELECT source, value FROM tags WHERE path = ?"
_TIME: Final = slice(11, 16)  # `2026:10:28 14:32:05` → `14:32`
_DESCRIBED: Final = (TagSource.CAPTION.value, TagSource.TAKEOUT.value)
# The words read on the phone: a few, the vision model's first.
MAX_WORDS: Final = 8


def notes_of(connection: sqlite3.Connection, key: int, path: Path) -> Notes:
    """What the index says of one file, for the storyteller.

    Args:
        connection: The open index.
        key: The file's key.
        path: The file, in the container.

    Returns:
        Its notes; empty ones for a file the index does not know.
    """
    row = connection.execute(_FACTS, (key,)).fetchone()
    if row is None:
        return Notes()
    date, metadata = row
    point = None
    if isinstance(metadata, str):
        try:
            located = located_point(MediaMetadata.model_validate_json(metadata))
        except ValidationError:
            located = None
        point = None if located is None else (located.latitude, located.longitude)
    try:
        tags = connection.execute(_TAGS, (str(path),)).fetchall()
    except sqlite3.OperationalError:  # an index without tags yet
        tags = []
    captions = [value for source, value in tags if source in _DESCRIBED]
    words = [value for source, value in tags if source == TagSource.VISION.value]
    clock = date[_TIME] if isinstance(date, str) and len(date) >= _TIME.stop else ""
    return Notes(
        time=clock,
        caption=captions[0] if captions else "",
        words=tuple(dict.fromkeys(words))[:MAX_WORDS],
        point=point,
    )
