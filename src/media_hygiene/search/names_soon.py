"""The names of the people on each photo, read in a thread while the page opens (0354).

Reading the faces and naming them took 1.8 s at each start of `search` (11,457 photos
named, measured on Windows): the server waited for it before answering. A thread now
reads them on a connection of its own while the server starts and the browser loads
the page; the first search waits for what is left (`MeaningIndex`). On a server living
the whole session (0358), they are read again when the faces or the moves of the index
change (`people` or `sort` in a container of their own); the searches meanwhile keep
the names they had.
"""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.search.people_words import people_words

if TYPE_CHECKING:
    from concurrent.futures import Future
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings

type Names = dict[Path, tuple[str, ...]]
_THREAD: Final = "people-names"
# What the names are made of in the index: a face's path changes in place on a move.
_MARKS: Final = (
    "SELECT rowid, path, number FROM faces",
    "SELECT rowid, old, new FROM moves",
)


def names_soon(index_file: Path, settings: PeopleSettings) -> Future[Names]:
    """Start reading the names of the people on each photo.

    Args:
        index_file: The index, opened read-only by the thread itself.
        settings: `[people]`, with the names.

    Returns:
        The names, once read; its `sqlite3.Error` raised by `result()`.
    """
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix=_THREAD)
    later = pool.submit(_read, index_file, settings)
    pool.shutdown(wait=False)  # the thread ends with its one task
    return later


def _read(index_file: Path, settings: PeopleSettings) -> Names:
    """Read the names on a connection of the thread's own.

    Args:
        index_file: The index.
        settings: `[people]`, with the names.

    Returns:
        Each photo with someone named on it, and their names.
    """
    with closing(connect_read_only(index_file)) as connection:
        return people_words(connection, settings)


def faces_mark(connection: sqlite3.Connection) -> bytes:
    """A digest of the faces and moves of the index: what the names are read from.

    Args:
        connection: The index.

    Returns:
        The digest; another one once a face is found, removed or moved.
    """
    digest = hashlib.sha256()
    for statement in _MARKS:
        try:
            rows = connection.execute(statement).fetchall()
        except sqlite3.OperationalError:  # no such table yet: `people` never ran
            rows = []
        digest.update(repr(rows).encode())
    return digest.digest()


class NamesKept:
    """The names of a long-lived search: read again when the faces change (0358)."""

    def __init__(self, index_file: Path, settings: PeopleSettings) -> None:
        """Start reading them at once, in a thread.

        Args:
            index_file: The index.
            settings: `[people]`, with the names.
        """
        self._source = (index_file, settings)
        self._later: Future[Names] | None = names_soon(index_file, settings)
        self._mark: bytes | None = None
        self._named = False

    @property
    def pending(self) -> bool:
        """Tell whether names are being read.

        Returns:
            True while a thread reads them.
        """
        return self._later is not None

    def fresh(self, connection: sqlite3.Connection) -> Names | None:
        """New names to give the photos, if any: waited for the first time only.

        Args:
            connection: The index, to see whether its faces changed.

        Returns:
            The names read; None when they are the ones given already, or are
            still being read again.
        """
        mark = faces_mark(connection)
        if self._mark is not None and mark != self._mark:
            self._later = names_soon(*self._source)
        self._mark = mark
        later = self._later
        if later is None or (self._named and not later.done()):
            return None
        self._later = None
        self._named = True
        return later.result()
