"""The moment of each face found in a video (version 24, TODO 0839).

A video's faces are rows of `faces` like a photo's; this table adds, for each one,
the moment (seconds) of the frame it was found on: its box is in that frame's
pixels (`faces.video_faces.FACE_EDGE`), and its picture is cut from that frame
again. Valid for one version of the file (size, mtime), read back joined with
`faces`; keyed by path, a table of `PATH_TABLES`: it follows a file `sort` or
`undo` moves, is parked with a file set aside, and leaves with a file gone.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.faces.video_faces import VideoFaces

CREATE_FACE_FRAMES: Final = """
CREATE TABLE IF NOT EXISTS face_frames (
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    model TEXT NOT NULL,
    number INTEGER NOT NULL,
    moment REAL NOT NULL,
    PRIMARY KEY (path, model, number)
)
"""
FORGET_FRAMES: Final = "DELETE FROM face_frames"
_DROP: Final = "DELETE FROM face_frames WHERE path = ? AND model = ?"
_PUT: Final = (
    "INSERT INTO face_frames (path, size, mtime_ns, model, number, moment)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)


def put_moments(connection: sqlite3.Connection, model: str, video: VideoFaces) -> None:
    """Replace the moments of a video's faces, numbered as `FaceStore.put` numbers them.

    Args:
        connection: The index.
        model: The pair of models.
        video: The video's faces and their moments.
    """
    found = video.found
    path = str(found.path)
    connection.execute(_DROP, (path, model))
    connection.executemany(
        _PUT,
        [
            (path, found.size, found.mtime_ns, model, number, moment)
            for number, moment in enumerate(video.moments)
        ],
    )
    connection.commit()
