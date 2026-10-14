"""Measures taken only for near-duplicate candidates: colourfulness, same-stream digest.

They depend on the file's bytes alone, so they are kept for one version of the file
(size, mtime) and taken again when it changes. A table of their own, beside `files`:
`files` is rewritten whole by every `put`, and these are measured for a few files only.
A measure the tool could not take (an undecodable frame) is not stored: it is tried
again next time.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.scan.models import MediaFile

# Added by schema version 10.
CREATE_MEASURES: Final = """
CREATE TABLE IF NOT EXISTS measures (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    colour_version INTEGER NOT NULL DEFAULT 0,
    colour REAL,
    stream_version INTEGER NOT NULL DEFAULT 0,
    stream_digest TEXT
)
"""
# A new version of the file: its older measures no longer hold.
_FORGET_STALE: Final = (
    "DELETE FROM measures WHERE path = ? AND (size, mtime_ns) != (?, ?)"
)
_ADD: Final = "INSERT OR IGNORE INTO measures (path, size, mtime_ns) VALUES (?, ?, ?)"
# Filled with the constant column names of `Measure`, never with input.
_SELECT: Final = "SELECT size, mtime_ns, {}, {} FROM measures WHERE path = ?"
_UPDATE: Final = "UPDATE measures SET {} = ?, {} = ? WHERE path = ?"


class Measure(Enum):
    """What is measured, its columns and the version of the way it is measured.

    Raise a version when its measurement changes: the files are measured again.
    """

    COLOUR = ("colour", "colour_version", 1)
    STREAM = ("stream_digest", "stream_version", 1)

    @property
    def column(self) -> str:
        """The column holding the value.

        Returns:
            Its name.
        """
        return self.value[0]

    @property
    def version_column(self) -> str:
        """The column holding the version it was measured by.

        Returns:
            Its name.
        """
        return self.value[1]

    @property
    def version(self) -> int:
        """The current version of the measurement.

        Returns:
            It.
        """
        return self.value[2]


class MeasureStore:
    """Reads and keeps the measures of the index; the connection stays its owner's."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Bind the store to an open index.

        Args:
            connection: The index connection; its schema is prepared.
        """
        self._connection = connection

    def known[T: (float, str)](
        self, files: Iterable[MediaFile], measure: Measure, kind: type[T]
    ) -> dict[Path, T]:
        """The measures already taken on these very versions of the files.

        Args:
            files: The files, with the size and mtime the walk saw.
            measure: What is wanted.
            kind: The type of its value.

        Returns:
            The value of each file measured, by path; the others are left out.
        """
        select = _SELECT.format(measure.version_column, measure.column)
        found: dict[Path, T] = {}
        for file in files:
            row = self._connection.execute(select, (str(file.path),)).fetchone()
            if row is None or (row[0], row[1]) != (file.size, file.mtime_ns):
                continue
            if row[2] == measure.version and isinstance(row[3], kind):
                found[file.path] = row[3]
        return found

    def keep(
        self,
        files: Iterable[MediaFile],
        measure: Measure,
        values: Mapping[Path, object],
    ) -> None:
        """Remember the measures just taken.

        Args:
            files: The files measured, with the size and mtime the walk saw.
            measure: What was measured.
            values: The value of each file, by path; a file left out is not stored.
        """
        taken = [file for file in files if file.path in values]
        versions = [(str(file.path), file.size, file.mtime_ns) for file in taken]
        connection = self._connection
        connection.executemany(_FORGET_STALE, versions)
        connection.executemany(_ADD, versions)
        update = _UPDATE.format(measure.version_column, measure.column)
        connection.executemany(
            update,
            [(measure.version, values[file.path], str(file.path)) for file in taken],
        )
