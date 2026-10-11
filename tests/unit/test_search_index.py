"""The index searched by words: diacritics, prefixes, sources, filters, staleness."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.index.schema import prepare
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import Filters, SearchQuery, parse_terms
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_FILES = (
    ("/data/c/Photos/2008/Neige/IMG_1.jpg", "2008:01:05 10:00:00"),
    ("/data/c/Photos/2019/Durbuy/IMG_2.jpg", "2019:07:14 11:00:00"),
    ("/data/c/Photos/2019/Noël/IMG_3.jpg", "2019-12-25T18:00:00"),
    ("/data/c/Photos/Divers/IMG_4.jpg", None),
)
_TAGS = (
    (0, "vision", "neige"),
    (0, "date", "2008"),
    (1, "folder", "Durbuy"),
    (1, "vision", "ours"),
    (1, "place", "Durbuy"),
    (2, "date", "Noël"),
    (2, "vision", "gâteau"),
    (2, "vision", "bougie"),
    (2, "caption", "Un gâteau d'anniversaire avec des bougies."),
    (3, "vision", "ours"),
)


def _index(tmp_path: Path, tags: Sequence[tuple[int, str, str]] = _TAGS) -> Path:
    """Write an index of four files and their tags."""
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        for number, (path, date) in enumerate(_FILES):
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns, media_date)"
                " VALUES (?, ?, ?, ?)",
                (path, 10 + number, 7, date),
            )
        connection.executemany(
            "INSERT INTO tags (path, size, mtime_ns, source, value)"
            " VALUES (?, ?, 7, ?, ?)",
            [(_FILES[at][0], 10 + at, source, value) for at, source, value in tags],
        )
        connection.commit()
    return index


def _names(search: SearchIndex, text: str, filters: Filters | None = None) -> list[str]:
    """The names of the files found."""
    query = SearchQuery(parse_terms(text), filters or Filters())
    return [hit.photo.path.name for hit in search.find(query, 10).hits]


def test_diacritics_prefixes_plurals_and_sources(tmp_path: Path) -> None:
    """`noel` finds Noël, `anniv*` the sentence, `bougies` the singular tag."""
    with SearchIndex.open(_index(tmp_path)) as search:
        assert _names(search, "noel") == ["IMG_3.jpg"]
        assert _names(search, "gateau anniv*") == ["IMG_3.jpg"]
        assert _names(search, "bougies") == ["IMG_3.jpg"]
        assert sorted(_names(search, "ours")) == ["IMG_2.jpg", "IMG_4.jpg"]
        assert _names(search, "place:durbuy") == ["IMG_2.jpg"]
        assert _names(search, "vision:durbuy") == []
        assert _names(search, '"gâteau d anniversaire"') == ["IMG_3.jpg"]


def test_filters_and_the_newest_first_without_words(tmp_path: Path) -> None:
    """Years, a part of the path (any case, either slash), one source."""
    with SearchIndex.open(_index(tmp_path)) as search:
        assert _names(search, "", Filters(years=(2019, 2019))) == [
            "IMG_3.jpg",
            "IMG_2.jpg",
        ]
        assert _names(search, "ours", Filters(folder="photos\\DIVERS")) == ["IMG_4.jpg"]
        assert _names(search, "durbuy", Filters(source=TagSource.FOLDER)) == [
            "IMG_2.jpg"
        ]
        found = search.find(SearchQuery(()), 2)
        assert found.total == len(_FILES)
        assert [hit.date for hit in found.hits] == ["2019-12-25", "2019-07-14"]
        hit = search.find(SearchQuery(parse_terms("noel")), 1).hits[0]
        assert hit.tags[TagSource.VISION] == ("gâteau", "bougie")
        assert search.source_of(hit.key) == hit.photo
        assert search.source_of(999) is None


def test_rebuilt_when_another_program_changed_the_tags(tmp_path: Path) -> None:
    """A tag written by `tags` while the page is open is found at the next search."""
    index = _index(tmp_path)
    with SearchIndex.open(index) as search:
        assert _names(search, "plage") == []
        with closing(sqlite3.connect(index)) as writer:
            writer.execute(
                "INSERT INTO tags (path, size, mtime_ns, source, value)"
                " VALUES (?, 13, 7, 'vision', 'plage')",
                (_FILES[3][0],),
            )
            writer.commit()
        assert _names(search, "plage") == ["IMG_4.jpg"]


def test_stale_tags_and_an_index_without_tags(tmp_path: Path) -> None:
    """A tag of another version of the file is not found; no table, nothing found."""
    stale = _index(tmp_path, ((0, "vision", "neige"),))
    with closing(sqlite3.connect(stale)) as connection:
        connection.execute("UPDATE files SET size = 99 WHERE path LIKE '%IMG_1.jpg'")
        connection.commit()
    with SearchIndex.open(stale) as search:
        assert _names(search, "neige") == []
    bare = tmp_path / "old.sqlite"
    with closing(sqlite3.connect(bare)) as connection:
        connection.execute(
            "CREATE TABLE files (path TEXT PRIMARY KEY, size, mtime_ns, media_date)"
        )
        connection.commit()
    with SearchIndex.open(bare) as search:
        assert not search.has_tags
        assert search.find(SearchQuery(()), 5).total == 0
