"""What the Takeout `.json` of each file says, kept by the path of that file.

Keyed by the photo's path, a row of `PATH_TABLES`: it follows the photo when `sort`
moves it (its `.json` travels with it), is parked with it by `clean` and comes back
with `undo`. Each `.json` is read once per version (its size and mtime); a row whose
`.json` the walk no longer finds next to its photo is forgotten.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import Sizes
from media_hygiene.scan.takeout import is_takeout_json
from media_hygiene.scan.takeout_facts import TakeoutFacts, read_takeout

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.sidecars import Sidecar

# Added by schema version 13.
CREATE_TAKEOUT: Final = """
CREATE TABLE IF NOT EXISTS takeout (
    path TEXT PRIMARY KEY,
    json_size INTEGER NOT NULL,
    json_mtime_ns INTEGER NOT NULL,
    taken_at INTEGER,
    latitude REAL,
    longitude REAL,
    description TEXT
)
"""
_VERSIONS: Final = "SELECT path, json_size, json_mtime_ns FROM takeout"
_EVERY: Final = "SELECT path, taken_at, latitude, longitude, description FROM takeout"
_SAVE: Final = (
    "INSERT OR REPLACE INTO takeout (path, json_size, json_mtime_ns, taken_at,"
    " latitude, longitude, description) VALUES (?, ?, ?, ?, ?, ?, ?)"
)
_FORGET: Final = "DELETE FROM takeout WHERE path = ?"
_ONE: Final = (
    "SELECT taken_at, latitude, longitude, description FROM takeout WHERE path = ?"
)


def remember_takeout(
    connection: sqlite3.Connection, sidecars: Iterable[Sidecar], listed: Iterable[Path]
) -> int:
    """Read the Takeout `.json` files new or changed since the last walk.

    Args:
        connection: The index.
        sidecars: The sidecars the walk listed (the Takeout ones with their files).
        listed: Every media file the walk listed: a row of one without its `.json`
            any more is forgotten.

    Returns:
        How many `.json` files were read.
    """
    wanted: dict[str, MediaFile] = {
        str(sidecar.file.path.parent / name): sidecar.file
        for sidecar in sidecars
        if is_takeout_json(sidecar.file.path.name)
        for name in sidecar.companions
    }
    known = {row[0]: (row[1], row[2]) for row in connection.execute(_VERSIONS)}
    for path in map(str, listed):
        if path in known and path not in wanted:
            connection.execute(_FORGET, (path,))
    stale = {
        path: json
        for path, json in wanted.items()
        if known.get(path) != (json.size, json.mtime_ns)
    }
    to_read = sorted({json.path for json in stale.values()})
    with ThreadPoolExecutor(max_workers=Sizes.IO_CONCURRENCY) as pool:
        read = dict(zip(to_read, pool.map(read_takeout, to_read), strict=True))
    for path, json in stale.items():
        facts = read[json.path]
        if facts is None:
            connection.execute(_FORGET, (path,))
            continue
        connection.execute(
            _SAVE,
            (
                path,
                json.size,
                json.mtime_ns,
                facts.taken_at,
                facts.latitude,
                facts.longitude,
                facts.description,
            ),
        )
    return len(to_read)


def takeout_facts(connection: sqlite3.Connection) -> dict[Path, TakeoutFacts]:
    """What the Takeout `.json` files said, by the path of the file each describes.

    Args:
        connection: The index.

    Returns:
        The facts, by path.
    """
    return {
        Path(path): TakeoutFacts(taken_at, latitude, longitude, description)
        for path, taken_at, latitude, longitude, description in connection.execute(
            _EVERY
        )
    }


def takeout_of(connection: sqlite3.Connection, path: Path) -> TakeoutFacts | None:
    """What the Takeout `.json` of one file said.

    Args:
        connection: The index.
        path: The file it describes.

    Returns:
        The facts, or None without a Takeout `.json`.
    """
    row = connection.execute(_ONE, (str(path),)).fetchone()
    return None if row is None else TakeoutFacts(*row)
