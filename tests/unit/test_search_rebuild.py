"""The search's full-text table follows a `tags` run, not rebuilt at each answer."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.index.repository import FactsRepository
from media_hygiene.search import fts
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import SearchQuery, parse_terms

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _add(index: Path, name: str) -> None:
    """Another program (`tags`) commits a file and its word."""
    with closing(sqlite3.connect(index)) as connection:
        path = f"/data/c/{name}.jpg"
        connection.execute(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, 1, 1)", (path,)
        )
        connection.execute(
            "INSERT INTO tags (path, size, mtime_ns, source, value, model, kind)"
            " VALUES (?, 1, 1, 'vision', 'snow', 'vision', '')",
            (path,),
        )
        connection.commit()


def test_a_rebuild_waits_its_time_unless_the_page_wrote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A change within `REBUILD_EVERY` shows later; `built = None` shows it at once."""
    index = tmp_path / "index.sqlite"
    with FactsRepository.open(index):
        pass
    _add(index, "a")
    snow = SearchQuery(parse_terms("snow"))
    with SearchIndex.open(index) as search:
        assert search.find(snow, 10).total == 1
        _add(index, "b")
        assert search.find(snow, 10).total == 1  # a run in progress: not rebuilt yet
        search.built = None  # the page moved files itself
        assert search.find(snow, 10).total == 2
        monkeypatch.setattr(fts, "REBUILD_EVERY", 0.0)
        _add(index, "c")
        assert search.find(snow, 10).total == 3  # its time has come
