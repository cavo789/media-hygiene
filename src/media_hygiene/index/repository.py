"""Persist `FileFacts` in SQLite by path; a size or mtime change invalidates them."""

from __future__ import annotations

import sqlite3
import time
from typing import TYPE_CHECKING, Final, Self

from media_hygiene.index.facts import FileFacts
from media_hygiene.index.moves import record_moves
from media_hygiene.index.preload import bounds_under, known_under
from media_hygiene.index.rows import facts_of, is_current, row_of
from media_hygiene.index.schema import (
    FORGET,
    MOVE,
    PATHS_UNDER,
    SELECT,
    UPSERT,
    prepare,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.index.preload import Known
    from media_hygiene.scan.models import MediaFile

_IN_MEMORY: Final = ":memory:"
# A killed run (docker stop, a crash) keeps what it stored until its last commit.
_COMMIT_EVERY_SECONDS: Final = 5.0


class FactsRepository:
    """Cache of digests and integrity checks; a stale entry reads as empty facts."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Wrap an open connection and make sure the schema exists.

        Args:
            connection: SQLite connection, owned by the repository from now on.
        """
        self._connection = connection
        self._known: Known = {}  # filled by `preload`, kept up to date by `put`
        self._preloaded: tuple[str, ...] = ()  # the folders `_known` covers, "x/"
        self._committed = time.monotonic()
        prepare(connection)

    @classmethod
    def open(cls, index_file: Path | None) -> Self:
        """Open the index file, or an in-memory index when nothing persists.

        Args:
            index_file: SQLite file, or None for a throw-away index.

        Returns:
            The repository.

        Raises:
            sqlite3.Error: The file is not an index; the connection is closed.
        """
        target = str(index_file) if index_file is not None else _IN_MEMORY
        connection = sqlite3.connect(target)
        try:
            return cls(connection)
        except sqlite3.Error:
            connection.close()
            raise

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
        path = str(file.path)
        if (known := self._known.get(path)) is not None:
            size, mtime_ns, facts = known
            current = (size, mtime_ns) == (file.size, file.mtime_ns)
            return facts if current else FileFacts()
        if path.startswith(self._preloaded):  # read at once: not in the index
            return FileFacts()
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
        if time.monotonic() - self._committed >= _COMMIT_EVERY_SECONDS:
            self._connection.commit()
            self._committed = time.monotonic()
        self._known[str(file.path)] = (file.size, file.mtime_ns, facts)

    def preload(self, roots: Iterable[Path]) -> None:
        """Read every row below the roots at once: `get` then answers from memory.

        Args:
            roots: The mounted folders about to be analysed.
        """
        folders = tuple(roots)
        self._known = known_under(self._connection, folders)
        self._preloaded = tuple(bounds_under(folder)[0] for folder in folders)

    def paths_under(self, folder: Path) -> list[str]:
        """List the indexed paths below a folder.

        Args:
            folder: A folder (container path).

        Returns:
            Every indexed path inside it, at any depth.
        """
        bounds = bounds_under(folder)
        return [row[0] for row in self._connection.execute(PATHS_UNDER, bounds)]

    def forget(self, paths: Iterable[str]) -> int:
        """Remove the rows of files that are gone.

        Args:
            paths: Their paths (container paths).

        Returns:
            How many rows were removed.
        """
        gone = [(path,) for path in paths]
        for (path,) in gone:
            self._known.pop(path, None)
        before = self._connection.total_changes
        self._connection.executemany(FORGET[0], gone)
        removed = self._connection.total_changes - before
        for statement in FORGET[1:]:
            self._connection.executemany(statement, gone)
        return removed

    def move(self, moves: Iterable[tuple[str, str]]) -> None:
        """Follow files that moved, so their facts are not computed again.

        Args:
            moves: Old and new path of each file (container paths).
        """
        pairs = [(new, old) for old, new in moves]
        for pair in pairs:
            for path in pair:
                self._known.pop(path, None)
        for statement in MOVE:
            self._connection.executemany(statement, pairs)
        record_moves(self._connection, [(old, new) for new, old in pairs])

    @property
    def connection(self) -> sqlite3.Connection:
        """The open connection, for the caches kept in the same file.

        Returns:
            It.
        """
        return self._connection
