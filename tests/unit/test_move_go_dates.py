"""*Move to an event…*: the index's date of a video (ISO) gives its month too."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.search import move_go

if TYPE_CHECKING:
    from media_hygiene.search.rule_desk import RuleDesk


def test_a_video_date_is_read_like_a_photo_date() -> None:
    """`2022-04-26T10:00:00Z` (ffprobe) is a date, as `2022:04:26 10:00:00` (EXIF)."""
    with closing(sqlite3.connect(":memory:")) as connection:
        days = _days_read(connection)
    assert days == {"a.jpg": "2022-04-26T10:00:00", "b.mov": "2022-04-26T10:00:00"}


def _days_read(connection: sqlite3.Connection) -> dict[str, str]:
    """The days `_picked` reads for a photo, a video and a file without a date.

    Args:
        connection: An empty database.

    Returns:
        Each dated file's name and day.
    """
    connection.execute("CREATE TABLE files (media_date TEXT)")
    written = ("2022:04:26 10:00:00", "2022-04-26T10:00:00+0200", None)
    connection.executemany("INSERT INTO files VALUES (?)", [(w,) for w in written])
    paths = {1: Path("/data/c/a.jpg"), 2: Path("/data/c/b.mov"), 3: Path("/data/c/c")}
    index = SimpleNamespace(
        connection=connection,
        source_of=lambda key: SimpleNamespace(path=paths[key]),
    )
    desk = cast("RuleDesk", SimpleNamespace(index=index, mover=None))
    picked = move_go._picked(desk, (1, 2, 3))  # noqa: SLF001  # pylint: disable=protected-access
    return {path.name: when.isoformat() for path, when in picked.days.items()}
