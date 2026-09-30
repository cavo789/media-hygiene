"""Persist `FileFacts` in SQLite by path; a size or mtime change invalidates them."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import TYPE_CHECKING, Final, Self

from media_hygiene.index.facts import FileFacts
from media_hygiene.index.rows import facts_of, is_current, row_of
from media_hygiene.index.schema import (
    FORGET,
    MARK_WALKED,
    MOVE,
    PATHS_UNDER,
    SELECT,
    UPSERT,
    WALKED_AT,
    prepare,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.scan.models import MediaFile

_IN_MEMORY: Final = ":memory:"
# Sorts right after "/": every "folder/..." path is below "folder0".
_AFTER_SEPARATOR: Final = "0"


class FactsRepository:
    """Cache of digests and integrity checks; a stale entry reads as empty facts."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Wrap an open connection and make sure the schema exists.

        Args:
            connection: SQLite connection, owned by the repository from now on.
        """
        self._connection = connection
        prepare(connection)

    @classmethod
    def open(cls, index_file: Path | None) -> Self:
        """Open the index file, or an in-memory index when nothing persists.

        Args:
            index_file: SQLite file, or None for a throw-away index.

        Returns:
            The repository.
        """
        target = str(index_file) if index_file is not None else _IN_MEMORY
        return cls(sqlite3.connect(target))

    def __enter__(self) -> Self:
        """Use the repository as a context manager.

        Returns:
            The repository itself.
        """
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Commit and close the connection, whether or not an exception occurred.

        Args:
            *exc_info: Exception details from the `with` statement (unused).
        """
        self._connection.commit()
        self._connection.close()

    def get(self, file: MediaFile) -> FileFacts:
        """Return the facts known for this exact version of `file`.

        Args:
            file: The file, with the size and mtime seen by the scan.

        Returns:
            The cached facts, or empty facts when unknown or stale.
        """
        row = self._connection.execute(SELECT, (str(file.path),)).fetchone()
        if row is None or not is_current(file, row):
            return FileFacts()
        return facts_of(row)

    def put(self, file: MediaFile, facts: FileFacts) -> None:
        """Store the facts of this version of `file`.

        Args:
            file: The file they describe.
            facts: The facts to remember.
        """
        self._connection.execute(UPSERT, row_of(file, facts))

    def paths_under(self, folder: Path) -> list[str]:
        """List the indexed paths below a folder.

        Args:
            folder: A folder (container path).

        Returns:
            Every indexed path inside it, at any depth.
        """
        prefix = f"{folder}/"
        bounds = (prefix, f"{folder}{_AFTER_SEPARATOR}")
        return [row[0] for row in self._connection.execute(PATHS_UNDER, bounds)]

    def forget(self, paths: Iterable[str]) -> int:
        """Remove the rows of files that are gone.

        Args:
            paths: Their paths (container paths).

        Returns:
            How many rows were removed.
        """
        before = self._connection.total_changes
        self._connection.executemany(FORGET, ((path,) for path in paths))
        return self._connection.total_changes - before

    def move(self, moves: Iterable[tuple[str, str]]) -> None:
        """Follow files that moved, so their facts are not computed again.

        Args:
            moves: Old and new path of each file (container paths).
        """
        self._connection.executemany(MOVE, ((new, old) for old, new in moves))

    def mark_walked(self, folder: Path, when: datetime) -> None:
        """Record that a folder was just walked without any read error.

        Args:
            folder: A mounted folder (container path).
            when: When the walk ended.
        """
        self._connection.execute(MARK_WALKED, (str(folder), when.isoformat()))

    def walked_at(self, folder: Path) -> datetime | None:
        """Tell when a folder was last walked without any read error.

        Args:
            folder: A mounted folder (container path).

        Returns:
            When, or None when never.
        """
        row = self._connection.execute(WALKED_AT, (str(folder),)).fetchone()
        return datetime.fromisoformat(row[0]) if row is not None else None
