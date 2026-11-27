"""How far down each photo's faces were looked for, and the faces added since (0841).

Until 0841 the audit kept a face from a detector score of 0.9 only; a group photo
taken at a few metres scores its faces 0.70-0.90 and kept none (measured: "Communion
Manon", 215 photos, 234 faces at 0.9, 497 at 0.6, 488 of them close to a named
person). `face_tops` holds, per version of a photo, the least score its faces were
looked for down to (`faces.detect.MIN_SCORE`). A photo scanned before, with no row
here, is *topped up*: looked at again, and the faces it did not have are added after
its own (`add_found`), never renumbered: a name given to face 2 stays on face 2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.faces.detect import MIN_SCORE
from media_hygiene.faces.models import LANDMARK_VALUES, FaceBox
from media_hygiene.index.drawn_faces import DRAWN_FROM

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.faces.models import PhotoFaces

CREATE_FACE_TOPS: Final = """
CREATE TABLE IF NOT EXISTS face_tops (
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    model TEXT NOT NULL,
    least REAL NOT NULL,
    PRIMARY KEY (path, model)
)
"""
FORGET_TOPS: Final = "DELETE FROM face_tops"
_TOPPED: Final = (
    "SELECT path, size, mtime_ns FROM face_tops WHERE model = ? AND least <= ?"
)
_IS_TOPPED: Final = (
    "SELECT 1 FROM face_tops"
    " WHERE path = ? AND size = ? AND mtime_ns = ? AND model = ? AND least <= ?"
)
_MARK: Final = "INSERT OR REPLACE INTO face_tops VALUES (?, ?, ?, ?, ?)"
_BOXES: Final = (
    "SELECT x, y, width, height FROM faces"
    " WHERE path = ? AND model = ? AND size = ? AND mtime_ns = ?"
)
_LAST_FOUND: Final = (
    "SELECT MAX(number) FROM faces WHERE path = ? AND model = ? AND number < ?"
)
_ADD: Final = (
    "INSERT INTO faces (path, size, mtime_ns, model, number, x, y, width, height,"
    " landmarks, score, sharpness, embedding)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_COUNT: Final = "UPDATE face_scans SET faces = faces + ? WHERE path = ? AND model = ?"
_SEPARATOR: Final = ","

type Version = tuple[str, int, int]


def topped_versions(
    connection: sqlite3.Connection, model: str, least: float
) -> frozenset[Version]:
    """The photo versions whose faces were looked for down to `least` or lower.

    Args:
        connection: The index.
        model: The face model.
        least: The score the audit keeps faces from now.

    Returns:
        Their keys (path, size, mtime).
    """
    return frozenset(connection.execute(_TOPPED, (model, least)))


def mark_topped(connection: sqlite3.Connection, model: str, found: PhotoFaces) -> None:
    """Remember that this version's faces were looked for down to `MIN_SCORE`.

    Committed at once, like the faces `FaceStore.put` just wrote.

    Args:
        connection: The index, writable.
        model: The face model.
        found: The photo analysed.
    """
    key = (str(found.path), found.size, found.mtime_ns, model, MIN_SCORE)
    connection.execute(_MARK, key)
    connection.commit()


def is_topped(connection: sqlite3.Connection, model: str, version: Version) -> bool:
    """Tell whether a version of a photo was looked at down to `MIN_SCORE`.

    Args:
        connection: The index.
        model: The face model.
        version: The photo's path, size and mtime.

    Returns:
        True when nothing is left to add.
    """
    found = connection.execute(_IS_TOPPED, (*version, model, MIN_SCORE)).fetchone()
    return found is not None


def boxes_of(
    connection: sqlite3.Connection, model: str, version: Version
) -> tuple[FaceBox, ...]:
    """The boxes of the faces a version of a photo has, drawn ones included.

    Args:
        connection: The index.
        model: The face model.
        version: The photo's path, size and mtime.

    Returns:
        Its boxes, upright pixels.
    """
    path, size, mtime = version
    rows = connection.execute(_BOXES, (path, model, size, mtime))
    return tuple(FaceBox(*map(float, row)) for row in rows)


def add_found(connection: sqlite3.Connection, model: str, found: PhotoFaces) -> None:
    """Add the faces a top-up found after the photo's own, mark it, and commit.

    Args:
        connection: The index, writable.
        model: The face model.
        found: The new faces only (those apart from every box it had).
    """
    path = str(found.path)
    last = connection.execute(_LAST_FOUND, (path, model, DRAWN_FROM)).fetchone()[0]
    first = 0 if last is None else int(last) + 1
    connection.executemany(
        _ADD,
        [
            (
                path,
                found.size,
                found.mtime_ns,
                model,
                first + offset,
                face.box.x,
                face.box.y,
                face.box.width,
                face.box.height,
                _SEPARATOR.join(
                    f"{value:.1f}"
                    for value in face.landmarks or (0.0,) * LANDMARK_VALUES
                ),
                face.score,
                face.sharpness,
                face.embedding,
            )
            for offset, face in enumerate(found.faces)
            if first + offset < DRAWN_FROM
        ],
    )
    connection.execute(_COUNT, (len(found.faces), path, model))
    mark_topped(connection, model, found)  # commits the faces with it
