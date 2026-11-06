"""Where each located photo lies, worked out once: landmark, town, regions (0545).

Keyed by path, a table of `PATH_TABLES`: a row follows its photo when `sort` or `undo`
moves it, is parked with it by `clean`, and goes with it when the audit forgets it. A
row says what one position gives: it is trusted only while the file records that very
position (a file rewritten with another one, or none, no longer matches), and `stamp`
names what else it was worked out from (`services.spot_fill`). A row of source `user`
(0489 writes it) keeps its landmark whatever is filled later, at that position.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Iterator

# Added by schema version 19.
CREATE_SPOTS: Final = """
CREATE TABLE IF NOT EXISTS spots (
    path TEXT PRIMARY KEY,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    stamp TEXT NOT NULL,
    landmark TEXT NOT NULL,
    source TEXT NOT NULL,
    town TEXT NOT NULL,
    region TEXT NOT NULL,
    district TEXT NOT NULL,
    country TEXT NOT NULL,
    words TEXT NOT NULL
)
"""
_LOCATED: Final = (
    "SELECT f.path, f.latitude, f.longitude, s.latitude, s.longitude, s.stamp,"
    " s.landmark, s.source FROM files AS f LEFT JOIN spots AS s ON s.path = f.path"
    " WHERE f.latitude IS NOT NULL AND f.longitude IS NOT NULL"
    " AND NOT (f.latitude = 0 AND f.longitude = 0)"
)
_SAVE: Final = (
    "INSERT OR REPLACE INTO spots (path, latitude, longitude, stamp, landmark, source,"
    " town, region, district, country, words) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
)
_FORGET_UNLOCATED: Final = (
    "DELETE FROM spots WHERE path NOT IN (SELECT path FROM files"
    " WHERE latitude IS NOT NULL AND longitude IS NOT NULL)"
)
# Only the rows of the position the file records today.
CURRENT: Final = (
    "JOIN spots AS s ON s.path = f.path"
    " AND s.latitude = f.latitude AND s.longitude = f.longitude"
)
_BY_KEY: Final = (
    "SELECT f.rowid, f.latitude, f.longitude, s.landmark, s.source, s.town, s.region,"  # noqa: S608
    " s.district, s.country FROM json_each(?) AS k"
    f" JOIN files AS f ON f.rowid = k.value {CURRENT}"
)
_COUNTS: Final = (
    "SELECT COUNT(*), SUM(s.landmark <> ''), SUM(s.town <> '')"  # noqa: S608
    f" FROM files AS f {CURRENT}"
)


class SpotSource(StrEnum):
    """Who named the landmark."""

    NONE = ""
    USER = "user"  # typed by hand (0489)
    OSM = "osm"  # the online name the user said Yes to (0474)
    GEONAMES = "geonames"  # the offline snapshot


@dataclass(frozen=True, slots=True)
class Known:
    """What the index holds of one located file; `stored_*` None: no row yet."""

    path: str
    latitude: float
    longitude: float
    stored_at: tuple[float | None, float | None]
    stamp: str | None
    landmark: str | None
    source: str | None


@dataclass(frozen=True, slots=True)
class StoredSpot:  # pylint: disable=too-many-instance-attributes
    """Where a photo lies, as stored; the names are GeoNames', before the user's."""

    latitude: float
    longitude: float
    landmark: str = ""
    source: str = ""
    town: str = ""
    region: str = ""  # admin1
    district: str = ""  # admin2
    country: str = ""  # ISO code


@dataclass(frozen=True, slots=True)
class SpotFigures:
    """How many located files have a row, a landmark, a town."""

    stored: int
    landmarks: int
    towns: int


def located_files(connection: sqlite3.Connection) -> Iterator[Known]:
    """Every located file of the index, with its row.

    Args:
        connection: The index.

    Yields:
        One per file.
    """
    for row in connection.execute(_LOCATED).fetchall():
        yield Known(row[0], row[1], row[2], (row[3], row[4]), row[5], row[6], row[7])


def save_spots(
    connection: sqlite3.Connection, rows: Iterable[tuple[object, ...]]
) -> None:
    """Write rows, and commit: a stop keeps what is done.

    Args:
        connection: The index.
        rows: The columns of `spots`, in order.
    """
    connection.executemany(_SAVE, rows)
    connection.commit()


def forget_unlocated(connection: sqlite3.Connection) -> None:
    """Drop the rows of files that no longer record a position.

    Args:
        connection: The index.
    """
    connection.execute(_FORGET_UNLOCATED)
    connection.commit()


def spots_by_key(
    connection: sqlite3.Connection, keys_json: str
) -> dict[int, StoredSpot]:
    """The rows of some files, those of their current position only.

    Args:
        connection: The index.
        keys_json: Their keys (`files.rowid`), as a JSON list.

    Returns:
        Each file's row by key.
    """
    found = connection.execute(_BY_KEY, (keys_json,)).fetchall()
    return {int(row[0]): StoredSpot(*row[1:]) for row in found}


def spot_figures(connection: sqlite3.Connection) -> SpotFigures:
    """Count what is stored, read back from the index.

    Args:
        connection: The index.

    Returns:
        The figures.
    """
    stored, landmarks, towns = connection.execute(_COUNTS).fetchone()
    return SpotFigures(int(stored), int(landmarks or 0), int(towns or 0))
