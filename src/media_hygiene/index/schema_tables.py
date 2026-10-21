"""The tables of the index holding rows by file path, in the order they are handled."""

from __future__ import annotations

from typing import Final

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
)
FORGET: Final = tuple(
    f"DELETE FROM {table} WHERE path = ?"  # noqa: S608 - constant table names
    for table in PATH_TABLES
)
