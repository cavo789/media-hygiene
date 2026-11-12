"""The faces drawn by hand on a photo (TODO 0715), kept with the faces the audit found.

A drawn face is a row of `faces` like any other: the people page, the search and the
names read it the same way. Its number, from `DRAWN_FROM` on, says it was drawn: a new
analysis of the same version of the photo replaces the faces the detector found and
keeps those (`face_rows.FaceStore.put`); a changed photo, or `people --forget`, drops
them with the rest. Moves and renames follow them like every row of the path. One
drawn by mistake, or twice, is forgotten on its own (`forget_drawn`); a face the
audit found never is: the next audit would find it again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.faces.models import LANDMARK_VALUES

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

    from media_hygiene.faces.models import Face

DRAWN_FROM: Final = 1000  # the numbers of the faces drawn; a photo has fewer found
_VERSION: Final = "SELECT size, mtime_ns FROM files WHERE path = ?"
_LAST: Final = "SELECT MAX(number) FROM faces WHERE path = ? AND model = ?"
_PUT: Final = (
    "INSERT INTO faces (path, size, mtime_ns, model, number, x, y, width, height,"
    " landmarks, score, sharpness, embedding)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_FORGET: Final = (
    "DELETE FROM faces WHERE path = ? AND model = ? AND number = ? AND number >= ?"
)
_SEPARATOR: Final = ","


def is_drawn(number: int) -> bool:
    """Tell whether a face of the index was drawn by hand.

    Args:
        number: Its number in its photo.

    Returns:
        True from `DRAWN_FROM` on.
    """
    return number >= DRAWN_FROM


def add_drawn(
    connection: sqlite3.Connection, model: str, drawn: tuple[Path, Face]
) -> int | None:
    """Keep a face drawn on a photo of the index, and commit.

    Args:
        connection: The index, writable.
        model: The pair of models its vector comes from.
        drawn: The photo, in the container, and the face.

    Returns:
        Its number; None when the index does not know the photo.
    """
    path, face = drawn
    version = connection.execute(_VERSION, (str(path),)).fetchone()
    if version is None:
        return None
    last = connection.execute(_LAST, (str(path), model)).fetchone()[0]
    number = max(DRAWN_FROM, int(last) + 1 if last is not None else DRAWN_FROM)
    landmarks = face.landmarks or (0.0,) * LANDMARK_VALUES
    box = face.box
    connection.execute(
        _PUT,
        (
            str(path),
            *version,
            model,
            number,
            box.x,
            box.y,
            box.width,
            box.height,
            _SEPARATOR.join(f"{value:.1f}" for value in landmarks),
            face.score,
            face.sharpness,
            face.embedding,
        ),
    )
    connection.commit()
    return number


def forget_drawn(
    connection: sqlite3.Connection, model: str, face: tuple[Path, int]
) -> bool:
    """Forget a face drawn on a photo, and commit; a face the audit found stays.

    Args:
        connection: The index, writable.
        model: The pair of models its vector comes from.
        face: Its photo, in the container, and its number in it.

    Returns:
        True when a face drawn was deleted.
    """
    path, number = face
    deleted = connection.execute(_FORGET, (str(path), model, number, DRAWN_FROM))
    connection.commit()
    return deleted.rowcount > 0
