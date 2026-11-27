"""The SQL of `face_rows`: the faces of each photo, and of each video (0839)."""

from __future__ import annotations

from typing import Final

from media_hygiene.index.aside_not import FORGET_ASIDE
from media_hygiene.index.face_frames import FORGET_FRAMES
from media_hygiene.index.face_groups import FORGET_GROUPS
from media_hygiene.index.face_tops import FORGET_TOPS

SCANNED: Final = (
    "SELECT 1 FROM face_scans"
    " WHERE path = ? AND size = ? AND mtime_ns = ? AND model = ?"
)
PUT_SCAN: Final = (
    "INSERT OR REPLACE INTO face_scans (path, size, mtime_ns, model, faces, seconds)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)
# The faces drawn by hand on this version of the photo stay (0715, `drawn_faces`).
DROP_FACES: Final = (
    "DELETE FROM faces WHERE path = ? AND model = ?"
    " AND NOT (number >= ? AND size = ? AND mtime_ns = ?)"
)
PUT_FACE: Final = (
    "INSERT INTO faces (path, size, mtime_ns, model, number, x, y, width, height,"
    " landmarks, score, sharpness, embedding)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
CURRENT: Final = (
    "SELECT faces.path, faces.number, faces.x, faces.y, faces.width, faces.height,"
    " faces.score, faces.sharpness, faces.embedding, face_frames.moment FROM faces"
    " JOIN files ON files.path = faces.path AND files.size = faces.size"
    " AND files.mtime_ns = faces.mtime_ns"
    " LEFT JOIN face_frames ON face_frames.path = faces.path"
    " AND face_frames.model = faces.model AND face_frames.number = faces.number"
    " AND face_frames.size = faces.size AND face_frames.mtime_ns = faces.mtime_ns"
    " WHERE faces.model = ? ORDER BY faces.path, faces.number"
)
SUMMARY: Final = (
    "SELECT COUNT(*), COALESCE(SUM(faces), 0), COALESCE(AVG(seconds), 0)"
    " FROM face_scans WHERE model = ?"
)
# Deleted pages are overwritten with zeros: forgotten faces leave no trace in the file.
FORGET: Final = (
    "PRAGMA secure_delete = ON",
    "DELETE FROM faces",
    "DELETE FROM face_scans",
    FORGET_TOPS,  # how far down each was looked for (0841)
    FORGET_FRAMES,  # the moment of each face of a video (0839)
    *FORGET_ASIDE,  # the faces of the people set aside (0328), and not them (0713)
    FORGET_GROUPS,  # which group each face fell in (0588)
)
COUNT_FACES: Final = "SELECT COUNT(*) FROM faces"
