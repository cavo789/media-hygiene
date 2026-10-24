"""The faces of each photo, kept in the index; forgotten all at once on request.

A photo is analysed once per version (size, mtime) and pair of models: its scan row
says so, faces or not. Only the faces of the current version of a file are read back
(joined with `files`): a photo changed since is analysed again by the next run.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.faces.models import FaceBox
from media_hygiene.index.aside_faces import FORGET_ALL

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.faces.models import PhotoFaces
    from media_hygiene.index.descriptions import PhotoVersion

_SCANNED: Final = (
    "SELECT 1 FROM face_scans"
    " WHERE path = ? AND size = ? AND mtime_ns = ? AND model = ?"
)
_PUT_SCAN: Final = (
    "INSERT OR REPLACE INTO face_scans (path, size, mtime_ns, model, faces, seconds)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)
_DROP_FACES: Final = "DELETE FROM faces WHERE path = ? AND model = ?"
_PUT_FACE: Final = (
    "INSERT INTO faces (path, size, mtime_ns, model, number, x, y, width, height,"
    " landmarks, score, sharpness, embedding)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_CURRENT: Final = (
    "SELECT faces.path, faces.number, faces.x, faces.y, faces.width, faces.height,"
    " faces.score, faces.sharpness, faces.embedding FROM faces"
    " JOIN files ON files.path = faces.path AND files.size = faces.size"
    " AND files.mtime_ns = faces.mtime_ns"
    " WHERE faces.model = ? ORDER BY faces.path, faces.number"
)
_SUMMARY: Final = (
    "SELECT COUNT(*), COALESCE(SUM(faces), 0), COALESCE(AVG(seconds), 0)"
    " FROM face_scans WHERE model = ?"
)
# Deleted pages are overwritten with zeros: forgotten faces leave no trace in the file.
_FORGET: Final = (
    "PRAGMA secure_delete = ON",
    "DELETE FROM faces",
    "DELETE FROM face_scans",
    FORGET_ALL,  # the faces of the people set aside (0328)
)
_COUNT_FACES: Final = "SELECT COUNT(*) FROM faces"
_SEPARATOR: Final = ","


@dataclass(frozen=True, slots=True)
class StoredFace:
    """A face read back: which photo, which face of it, where, how good, its vector."""

    path: Path
    number: int
    box: FaceBox
    score: float
    sharpness: float
    embedding: bytes


@dataclass(frozen=True, slots=True)
class FaceTally:
    """How many photos were analysed, how many faces found, the time per photo."""

    photos: int
    faces: int
    seconds_per_photo: float


class FaceStore:
    """Reads and writes the faces of one pair of models."""

    def __init__(self, connection: sqlite3.Connection, model: str) -> None:
        """Bind the store to an open index and a pair of models.

        Args:
            connection: The index connection, tables prepared.
            model: `faces.models.FACE_MODEL`, or a test's.
        """
        self._connection = connection
        self._model = model

    @property
    def connection(self) -> sqlite3.Connection:
        """The open index, to list its photos.

        Returns:
            The connection.
        """
        return self._connection

    def scanned(self, photo: PhotoVersion) -> bool:
        """Tell whether this version of a photo was analysed already.

        Args:
            photo: The photo, with its size and mtime.

        Returns:
            True when its faces (maybe none) are in the index.
        """
        key = (str(photo.path), photo.size, photo.mtime_ns, self._model)
        return self._connection.execute(_SCANNED, key).fetchone() is not None

    def put(self, found: PhotoFaces) -> None:
        """Replace the faces of a photo, and commit at once (Ctrl+C keeps them).

        Args:
            found: The photo and its faces.
        """
        path = str(found.path)
        self._connection.execute(_DROP_FACES, (path, self._model))
        self._connection.executemany(
            _PUT_FACE,
            [
                (
                    path,
                    found.size,
                    found.mtime_ns,
                    self._model,
                    number,
                    face.box.x,
                    face.box.y,
                    face.box.width,
                    face.box.height,
                    _SEPARATOR.join(f"{value:.1f}" for value in face.landmarks),
                    face.score,
                    face.sharpness,
                    face.embedding,
                )
                for number, face in enumerate(found.faces)
            ],
        )
        scan = (path, found.size, found.mtime_ns, self._model)
        self._connection.execute(_PUT_SCAN, (*scan, len(found.faces), found.seconds))
        self._connection.commit()

    def faces(self) -> tuple[StoredFace, ...]:
        """Every face of the current version of the indexed photos.

        Returns:
            The faces, by path then number.
        """
        return tuple(
            StoredFace(
                Path(path),
                int(number),
                FaceBox(float(x), float(y), float(width), float(height)),
                float(score),
                float(sharpness),
                bytes(embedding),
            )
            for path, number, x, y, width, height, score, sharpness, embedding in (
                self._connection.execute(_CURRENT, (self._model,))
            )
        )

    def tally(self) -> FaceTally:
        """Count what the index holds for these models.

        Returns:
            Photos analysed, faces found, mean time per photo.
        """
        photos, faces, seconds = self._connection.execute(
            _SUMMARY, (self._model,)
        ).fetchone()
        return FaceTally(int(photos), int(faces), float(seconds))

    def forget(self) -> tuple[int, int]:
        """Delete every face and every scan row, of any model, zeroing their pages.

        Returns:
            How many faces were deleted, and how many the index holds afterwards,
            read back once the deletion is committed.
        """
        before = self._connection.execute(_COUNT_FACES).fetchone()
        for statement in _FORGET:
            self._connection.execute(statement)
        self._connection.commit()
        after = self._connection.execute(_COUNT_FACES).fetchone()
        return int(before[0]), int(after[0])
