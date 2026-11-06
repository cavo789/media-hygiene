"""The tables of the index holding rows by file path, in the order they are handled."""

from __future__ import annotations

from typing import Final

from media_hygiene.index.face_schema import FACE_TABLES
from media_hygiene.index.gone_rows import CREATE_GONE
from media_hygiene.index.journal_words import JOURNAL_TABLES
from media_hygiene.index.meaning_rows import CREATE_MEANINGS
from media_hygiene.index.spot_rows import CREATE_SPOTS

# The tables created last, whatever the version of the index (`schema.prepare`).
LATER_TABLES: Final = (
    *JOURNAL_TABLES,
    CREATE_GONE,
    CREATE_MEANINGS,
    *FACE_TABLES,
    CREATE_SPOTS,
)
# `files` first: `FactsRepository.forget` counts the files it removes on it.
PATH_TABLES: Final = (
    "files",
    "descriptions",
    "tags",
    "face_scans",
    "faces",
    "measures",
    "takeout",
    "former_names",
    "meanings",
    "spots",
)
FORGET: Final = tuple(
    f"DELETE FROM {table} WHERE path = ?"  # noqa: S608 - constant table names
    for table in PATH_TABLES
)
