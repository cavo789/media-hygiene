"""The thumbnails find their file on a connection of their own."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.search.picture_sources import PictureSources

if TYPE_CHECKING:
    from media_hygiene.search.fts import SearchIndex


def _index(file: Path) -> None:
    with closing(sqlite3.connect(file)) as connection:
        connection.execute(
            "CREATE TABLE files (path TEXT, size INTEGER, mtime_ns INTEGER)"
        )
        connection.execute("INSERT INTO files VALUES ('/data/c/a.jpg', 12, 34)")
        connection.commit()


def test_found_on_its_own_connection_while_the_pages_is_busy(tmp_path: Path) -> None:
    """A statement left open on the page's connection: the lookup still answers."""
    file = tmp_path / "index.sqlite"
    _index(file)
    page = sqlite3.connect(file, check_same_thread=False)
    busy = page.execute("SELECT path FROM files")  # a search reading, not finished
    index = cast("SearchIndex", SimpleNamespace(connection=page))
    sources = PictureSources(index)
    assert sources.source_of(1) == PhotoVersion(Path("/data/c/a.jpg"), 12, 34)
    assert sources.source_of(2) is None
    busy.close()
    page.close()


def test_an_index_in_memory_asks_the_page(tmp_path: Path) -> None:
    """No file to open again: the page's index answers."""
    del tmp_path
    page = sqlite3.connect(":memory:")
    asked: list[int] = []

    def source_of(key: int) -> None:
        asked.append(key)

    index = cast("SearchIndex", SimpleNamespace(connection=page, source_of=source_of))
    assert PictureSources(index).source_of(7) is None
    assert asked == [7]
    page.close()
