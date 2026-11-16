"""The library's positions: the file's own, else its Takeout `.json`'s, never 0, 0."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from media_hygiene.geo.distance import Point
from media_hygiene.services.indexed_points import indexed_points

_PARIS = (48.85, 2.35)
_LYON = (45.76, 4.84)
_FILES = (
    ("own.jpg", *_PARIS),  # its GPS, though a .json says Lyon
    ("zero.jpg", 0.0, 0.0),  # a receiver without a fix: the .json is not read
    ("takeout.jpg", None, None),  # no GPS: the .json's position
    ("takeout_zero.jpg", None, None),  # the .json at 0, 0: nowhere
    ("takeout_none.jpg", None, None),  # the .json without a position
    ("nothing.jpg", None, None),  # no GPS, no .json
)
_TAKEOUTS = (
    ("own.jpg", *_LYON),
    ("zero.jpg", *_LYON),
    ("takeout.jpg", *_LYON),
    ("takeout_zero.jpg", 0.0, 0.0),
    ("takeout_none.jpg", None, None),
    ("gone.jpg", *_LYON),  # a .json whose file left the index
)


def test_own_position_first_then_the_takeout_one() -> None:
    """Each case of `with_takeout` then `located_point`, in two queries."""
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute(
            "CREATE TABLE files (path TEXT, latitude REAL, longitude REAL)"
        )
        connection.execute(
            "CREATE TABLE takeout (path TEXT, latitude REAL, longitude REAL)"
        )
        connection.executemany("INSERT INTO files VALUES (?, ?, ?)", _FILES)
        connection.executemany("INSERT INTO takeout VALUES (?, ?, ?)", _TAKEOUTS)
        points = indexed_points(connection)
    assert points == {
        Path("own.jpg"): Point(*_PARIS),
        Path("takeout.jpg"): Point(*_LYON),
    }
