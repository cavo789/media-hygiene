"""The face tables of the index (version 8): which photos were looked at, their faces.

`face_scans` remembers every photo analysed, faces or not, so that a photo without
any face is not analysed again; `faces` holds one row per face. Both are valid for one
version of the file (size, mtime) and one pair of models (`faces.models.FACE_MODEL`).
"""

from __future__ import annotations

from typing import Final

CREATE_FACE_SCANS: Final = """
CREATE TABLE IF NOT EXISTS face_scans (
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    model TEXT NOT NULL,
    faces INTEGER NOT NULL,
    seconds REAL NOT NULL,
    PRIMARY KEY (path, model)
)
"""
# The box in the upright picture's pixels, the landmarks as comma separated numbers,
# the vector as float32 bytes of length 1.
CREATE_FACES: Final = """
CREATE TABLE IF NOT EXISTS faces (
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    model TEXT NOT NULL,
    number INTEGER NOT NULL,
    x REAL NOT NULL,
    y REAL NOT NULL,
    width REAL NOT NULL,
    height REAL NOT NULL,
    landmarks TEXT NOT NULL,
    score REAL NOT NULL,
    sharpness REAL NOT NULL,
    embedding BLOB NOT NULL,
    PRIMARY KEY (path, model, number)
)
"""
