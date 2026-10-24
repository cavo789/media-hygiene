"""What the index knows of the faces, read without the right to change it.

Every face of the index is read once, at the first question: a page's server holds a
few tens of thousands of them (22,000 on the maintainer's index, measured
2026-10-24). Without an index (no persistent cache) or with one that cannot be read,
nothing is known: the page says to run `audit --people`.
"""

from __future__ import annotations

import sqlite3
from functools import cached_property
from typing import TYPE_CHECKING, Final

from media_hygiene.faces.models import FACE_MODEL
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.read_only import connect_read_only

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.face_rows import StoredFace

_SCANNED: Final = "SELECT 1 FROM face_scans WHERE path = ? AND model = ?"


class FaceIndex:
    """The faces of the index, and the photos it analysed."""

    def __init__(self, index_file: Path | None, model: str = FACE_MODEL) -> None:
        """Bind the index file.

        Args:
            index_file: The cache's index; None without a persistent cache.
            model: The pair of models whose faces are read.
        """
        self._file = index_file
        self._model = model

    @cached_property
    def every(self) -> tuple[StoredFace, ...]:
        """Every face of the current version of the indexed photos.

        Returns:
            Them; none when the index cannot be read.
        """
        if self._file is None or not self._file.is_file():
            return ()
        try:
            connection = connect_read_only(self._file)
            try:
                return FaceStore(connection, self._model).faces()
            finally:
                connection.close()
        except sqlite3.Error:
            return ()

    def of(self, path: Path) -> tuple[StoredFace, ...]:
        """The faces of one photo.

        Args:
            path: The photo, in the container.

        Returns:
            Its faces, in their order; none for a photo without any.
        """
        return tuple(face for face in self.every if face.path == path)

    def scanned(self, path: Path) -> bool:
        """Tell whether the faces of a photo were looked for.

        Args:
            path: The photo, in the container.

        Returns:
            True when the index says so, faces found or not.
        """
        if self._file is None or not self._file.is_file():
            return False
        try:
            connection = connect_read_only(self._file)
            try:
                found = connection.execute(_SCANNED, (str(path), self._model))
                return found.fetchone() is not None
            finally:
                connection.close()
        except sqlite3.Error:
            return False
