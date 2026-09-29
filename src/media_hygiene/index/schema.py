"""The index tables, and how older index files are brought up to date.

Version 2 adds what images look like; version 3 what files say about themselves (a
versioned JSON document, plus typed columns for what later steps query) and when each
mounted folder was last walked completely. An older index keeps its digests and
integrity results: the new columns are filled once, without decoding images again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

SCHEMA_VERSION: Final = 3
_CREATE: Final = """
CREATE TABLE IF NOT EXISTS files (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    partial_digest TEXT,
    full_digest TEXT,
    integrity_checked INTEGER NOT NULL DEFAULT 0,
    broken_reason TEXT,
    broken_detail TEXT NOT NULL DEFAULT ''
)
"""
# Added by version 2. Hashes are stored in hexadecimal: SQLite integers are signed.
VISUAL_COLUMNS: Final = (
    ("visual_checked", "INTEGER NOT NULL DEFAULT 0"),
    ("dhash", "TEXT"),
    ("phash", "TEXT"),
    ("width", "INTEGER"),
    ("height", "INTEGER"),
    ("sharpness", "REAL"),
    ("taken_at", "TEXT"),
    ("camera", "TEXT"),
)
# Added by version 3. `metadata` is a `MediaMetadata` in JSON; the others copy what a
# reader of the index filters on: the place, and the date of images and videos alike.
METADATA_COLUMNS: Final = (
    ("metadata_version", "INTEGER NOT NULL DEFAULT 0"),
    ("metadata", "TEXT"),
    ("latitude", "REAL"),
    ("longitude", "REAL"),
    ("media_date", "TEXT"),
)
# Added by version 3: when each mounted folder was last walked without a read error.
_CREATE_ROOTS: Final = """
CREATE TABLE IF NOT EXISTS roots (
    path TEXT PRIMARY KEY,
    walked_at TEXT NOT NULL
)
"""
SELECT: Final = (
    "SELECT size, mtime_ns, partial_digest, full_digest, integrity_checked,"
    " broken_reason, broken_detail, visual_checked, dhash, phash, width, height,"
    " sharpness, taken_at, camera, metadata_version, metadata FROM files WHERE path = ?"
)
UPSERT: Final = (
    "INSERT OR REPLACE INTO files (path, size, mtime_ns, partial_digest, full_digest,"
    " integrity_checked, broken_reason, broken_detail, visual_checked, dhash, phash,"
    " width, height, sharpness, taken_at, camera, metadata_version, metadata,"
    " latitude, longitude, media_date)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
# Every path below a folder: `/` then anything sorts between `folder/` and `folder0`.
PATHS_UNDER: Final = "SELECT path FROM files WHERE path >= ? AND path < ?"
FORGET: Final = "DELETE FROM files WHERE path = ?"
MARK_WALKED: Final = "INSERT OR REPLACE INTO roots (path, walked_at) VALUES (?, ?)"
WALKED_AT: Final = "SELECT walked_at FROM roots WHERE path = ?"


def prepare(connection: sqlite3.Connection) -> None:
    """Create the tables, or add what an older index lacks.

    Args:
        connection: An open SQLite connection.
    """
    connection.execute(_CREATE)
    existing = {row[1] for row in connection.execute("PRAGMA table_info(files)")}
    for name, definition in (*VISUAL_COLUMNS, *METADATA_COLUMNS):
        if name not in existing:
            connection.execute(f"ALTER TABLE files ADD COLUMN {name} {definition}")
    connection.execute(_CREATE_ROOTS)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
