"""The index tables, and how older index files are brought up to date.

Version 2 adds what images look like; version 3 what files say about themselves (a
versioned JSON document, plus typed columns for what later steps query) and when each
mounted folder was last walked completely; version 4 what a local model saw in a
photo and the categories it chose (`subject` rules); version 5 the fingerprint of
videos (the hashes of a few frames, `scan.keyframes`). An older index keeps its digests
and integrity results: the new columns are filled once, without decoding images again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

SCHEMA_VERSION: Final = 5
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
# Added by version 5: the hashes of a few frames of a video (`index.video_rows`).
VIDEO_PRINT_COLUMNS: Final = (
    ("video_print_version", "INTEGER NOT NULL DEFAULT 0"),
    ("video_print", "TEXT"),
)
# Added by version 3: when each mounted folder was last walked without a read error.
_CREATE_ROOTS: Final = """
CREATE TABLE IF NOT EXISTS roots (
    path TEXT PRIMARY KEY,
    walked_at TEXT NOT NULL
)
"""
# Added by version 4. A description is valid for one version of the file (size,
# mtime), one model and one prompt; a mapping for one description, one model, one
# prompt and one list of categories (`key`, a digest of them all).
_CREATE_DESCRIPTIONS: Final = """
CREATE TABLE IF NOT EXISTS descriptions (
    path TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    model TEXT NOT NULL,
    prompt TEXT NOT NULL,
    description TEXT NOT NULL,
    tags TEXT NOT NULL,
    seconds REAL NOT NULL,
    PRIMARY KEY (path, model, prompt)
)
"""
_CREATE_MAPPINGS: Final = """
CREATE TABLE IF NOT EXISTS subject_mappings (
    key TEXT PRIMARY KEY,
    category TEXT NOT NULL
)
"""
# What `rows.facts_of` reads, in its order.
_FACTS: Final = (
    "size, mtime_ns, partial_digest, full_digest, integrity_checked,"
    " broken_reason, broken_detail, visual_checked, dhash, phash, width, height,"
    " sharpness, taken_at, camera, metadata_version, metadata, video_print_version,"
    " video_print"
)
# Both built from the constant column list above, never from input.
SELECT: Final = f"SELECT {_FACTS} FROM files WHERE path = ?"  # noqa: S608
# Every file, its path first, then the same columns.
EVERY_FILE: Final = f"SELECT path, {_FACTS} FROM files ORDER BY path"  # noqa: S608
UPSERT: Final = (
    "INSERT OR REPLACE INTO files (path, size, mtime_ns, partial_digest, full_digest,"
    " integrity_checked, broken_reason, broken_detail, visual_checked, dhash, phash,"
    " width, height, sharpness, taken_at, camera, metadata_version, metadata,"
    " latitude, longitude, media_date, video_print_version, video_print)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
# Every path below a folder: `/` then anything sorts between `folder/` and `folder0`.
PATHS_UNDER: Final = "SELECT path FROM files WHERE path >= ? AND path < ?"
FORGET: Final = (
    "DELETE FROM files WHERE path = ?",
    "DELETE FROM descriptions WHERE path = ?",
)
# A file moved by `sort` (or back by `undo`) keeps its facts: size and mtime are kept.
MOVE: Final = (
    "UPDATE OR REPLACE files SET path = ? WHERE path = ?",
    "UPDATE OR REPLACE descriptions SET path = ? WHERE path = ?",
)
MARK_WALKED: Final = "INSERT OR REPLACE INTO roots (path, walked_at) VALUES (?, ?)"
WALKED_AT: Final = "SELECT walked_at FROM roots WHERE path = ?"


def prepare(connection: sqlite3.Connection) -> None:
    """Create the tables, or add what an older index lacks.

    Args:
        connection: An open SQLite connection.
    """
    connection.execute(_CREATE)
    existing = {row[1] for row in connection.execute("PRAGMA table_info(files)")}
    for name, definition in (
        *VISUAL_COLUMNS,
        *METADATA_COLUMNS,
        *VIDEO_PRINT_COLUMNS,
    ):
        if name not in existing:
            connection.execute(f"ALTER TABLE files ADD COLUMN {name} {definition}")
    connection.execute(_CREATE_ROOTS)
    connection.execute(_CREATE_DESCRIPTIONS)
    connection.execute(_CREATE_MAPPINGS)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
