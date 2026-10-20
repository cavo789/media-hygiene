"""The vector of each photo for search by meaning: one per version of a photo.

A row is kept for one version of the file (size, mtime) and one model, as every row of
the index: a photo edited since gets a new vector at the next `tags`, a vector of
another model is never compared. 512 float32 values (2 KB) per photo, unit length,
so that a cosine is a dot product. Keyed by path, a table of `PATH_TABLES`: it
follows the photo when `sort`, `undo` or the audit move it, and is forgotten with it.
Version 16 of the index.
"""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import embedding_bytes, vector_of

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

    from numpy.typing import NDArray

    from media_hygiene.index.descriptions import PhotoVersion

CREATE_MEANINGS: Final = """
CREATE TABLE IF NOT EXISTS meanings (
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    model TEXT NOT NULL,
    vector BLOB NOT NULL,
    seconds REAL NOT NULL,
    PRIMARY KEY (path, model)
)
"""
_VERSION: Final = "SELECT size, mtime_ns FROM meanings WHERE path = ? AND model = ?"
_UPSERT: Final = (
    "INSERT OR REPLACE INTO meanings (path, size, mtime_ns, model, vector, seconds)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)
_SECONDS: Final = "SELECT seconds FROM meanings WHERE model = ? AND seconds > 0"
HAS_MEANINGS: Final = (
    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'meanings'"
)
# The vectors of the version of each file the index knows, by the file's row.
VECTORS: Final = (
    "SELECT f.rowid, m.vector FROM meanings AS m JOIN files AS f ON f.path = m.path"
    " AND f.size = m.size AND f.mtime_ns = m.mtime_ns WHERE m.model = ?"
)

COUNT: Final = "SELECT COUNT(*) FROM (" + VECTORS + ")"  # noqa: S608 - constant


class MeaningStore:
    """The vectors of one model."""

    def __init__(self, connection: sqlite3.Connection, model: str) -> None:
        """Bind the store to a model.

        Args:
            connection: The index connection, tables prepared.
            model: The model the vectors come from.
        """
        self._connection = connection
        self._model = model

    def missing(self, photos: Iterable[PhotoVersion]) -> tuple[PhotoVersion, ...]:
        """The photos without a vector of their present version.

        Args:
            photos: The photos of a run.

        Returns:
            Those to look at, in their order.
        """
        return tuple(photo for photo in photos if not self._known(photo))

    def put(
        self, photo: PhotoVersion, vector: NDArray[np.float32], seconds: float
    ) -> None:
        """Remember a vector at once: an interrupted run keeps it.

        Args:
            photo: The photo.
            vector: Its vector.
            seconds: How long it took, decoding included.
        """
        version = (str(photo.path), photo.size, photo.mtime_ns)
        stored = (self._model, embedding_bytes(vector), seconds)
        self._connection.execute(_UPSERT, version + stored)
        self._connection.commit()

    def seconds_per_photo(self) -> float | None:
        """How long a photo takes on this machine.

        Returns:
            The median of the times recorded, or None before the first one.
        """
        rows = self._connection.execute(_SECONDS, (self._model,)).fetchall()
        return statistics.median(row[0] for row in rows) if rows else None

    def _known(self, photo: PhotoVersion) -> bool:
        """Tell whether a photo has a vector of its present version.

        Args:
            photo: The photo.

        Returns:
            True when its size and mtime are those of the vector.
        """
        row = self._connection.execute(
            _VERSION, (str(photo.path), self._model)
        ).fetchone()
        return row is not None and (row[0], row[1]) == (photo.size, photo.mtime_ns)


def vectors(
    connection: sqlite3.Connection, model: str
) -> tuple[tuple[int, ...], NDArray[np.float32]]:
    """Every vector of a model, of the files as the index knows them.

    Args:
        connection: The index (read-only is enough).
        model: The model.

    Returns:
        The files' rows, and their vectors, one per line of the matrix (none: an
        empty tuple and a `0 x 0` matrix, also for an index older than the table).
    """
    if connection.execute(HAS_MEANINGS).fetchone() is None:
        return (), np.zeros((0, 0), dtype=np.float32)
    rows = connection.execute(VECTORS, (model,)).fetchall()
    if not rows:
        return (), np.zeros((0, 0), dtype=np.float32)
    keys = tuple(int(row[0]) for row in rows)
    return keys, np.stack([vector_of(row[1]) for row in rows])


def vector_count(connection: sqlite3.Connection, model: str) -> int:
    """How many files of the index have a vector of their present version.

    Args:
        connection: The index (read-only is enough).
        model: The model.

    Returns:
        The count; 0 for an index older than the table.
    """
    if connection.execute(HAS_MEANINGS).fetchone() is None:
        return 0
    return int(connection.execute(COUNT, (model,)).fetchone()[0])
