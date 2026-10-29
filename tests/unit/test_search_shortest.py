"""0459: *Sort by: length, shortest first*, on the index's own rows."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing

from media_hygiene.search.query import Order
from media_hygiene.search.statements import BY_ORDER, FOLD


def test_the_videos_come_by_length_then_the_photos() -> None:
    """A 1 s video first, then 2 s, 40 s; the photos (no length) after, by name."""
    rows = [
        ("b.jpg", {}),
        ("long.mp4", {"duration": 40.0}),
        ("a.jpg", {"width": 10}),
        ("failed.mp4", {"duration": 1.2}),
        ("short.mov", {"duration": 2.0}),
    ]
    with closing(sqlite3.connect(":memory:")) as base:
        base.create_function(FOLD, 1, str.casefold, deterministic=True)
        base.execute("CREATE TABLE files (path TEXT, metadata TEXT)")
        base.executemany(
            "INSERT INTO files VALUES (?, ?)",
            [(path, json.dumps(meta)) for path, meta in rows],
        )
        order = BY_ORDER[Order.SHORT]
        query = "SELECT path FROM files" + order  # noqa: S608  # constant
        shown = [row[0] for row in base.execute(query)]
    assert shown == ["failed.mp4", "short.mov", "long.mp4", "a.jpg", "b.jpg"]
