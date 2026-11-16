"""Whether another connection writes the index now (0817)."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from media_hygiene.index.write_probe import index_busy

if TYPE_CHECKING:
    from pathlib import Path


def _index(tmp_path: Path) -> Path:
    """An index file with one table.

    Args:
        tmp_path: Where it goes.

    Returns:
        Its path.
    """
    index = tmp_path / "index.sqlite"
    with sqlite3.connect(index) as connection:
        connection.execute("CREATE TABLE files (path TEXT)")
    connection.close()
    return index


def test_an_idle_index_is_free(tmp_path: Path) -> None:
    """Nobody writes: a writer would go on, and nothing is left beside the file."""
    index = _index(tmp_path)
    assert not index_busy(index)
    assert sorted(each.name for each in tmp_path.iterdir()) == ["index.sqlite"]


def test_an_open_write_transaction_makes_it_busy(tmp_path: Path) -> None:
    """An audit between two commits holds the write lock: busy, at once."""
    index = _index(tmp_path)
    writer = sqlite3.connect(index)
    try:
        writer.execute("INSERT INTO files VALUES ('/data/c/a.jpg')")
        assert index_busy(index)
        writer.commit()
        assert not index_busy(index)
    finally:
        writer.close()


def test_a_missing_or_broken_index_is_busy(tmp_path: Path) -> None:
    """No index, or not an index: nothing to warm, the visit tells."""
    assert index_busy(tmp_path / "index.sqlite")
    broken = tmp_path / "broken.sqlite"
    broken.write_bytes(b"not a database at all, only some text" * 100)
    assert index_busy(broken)
