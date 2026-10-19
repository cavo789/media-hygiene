"""The Google Photos description as tags (0240): own source, safe for old indexes."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.schema import prepare
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import Filters, SearchQuery, parse_terms
from media_hygiene.tags.models import (
    CHEAP_SOURCES,
    MODEL_SOURCES,
    FileTags,
    Tag,
    TagSource,
)

PATH = Path("/data/c/Photos/IMG_1.jpg")
PHOTO = PhotoVersion(PATH, 10, 7)
SENTENCE = Tag(TagSource.TAKEOUT, "Fête de Léa à la plage")
WORD = Tag(TagSource.TAKEOUT, "plage")
CAPTION = Tag(TagSource.CAPTION, "Un chien.", "vision")
DOG = Tag(TagSource.VISION, "chien", "vision")


def names(index: Path, text: str) -> list[str]:
    """The names of the files a search finds."""
    query = SearchQuery(parse_terms(text), Filters())
    with SearchIndex.open(index) as search:
        return [hit.photo.path.name for hit in search.find(query, 10).hits]


def make_index(tmp_path: Path) -> Path:
    """An index of one photo."""
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        connection.execute(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, 10, 7)", (str(PATH),)
        )
        connection.commit()
    return index


def test_a_word_of_the_description_finds_the_photo(tmp_path: Path) -> None:
    """By a word, the phrase, the source filter; `describe` keeps the words."""
    index = make_index(tmp_path)
    with closing(sqlite3.connect(index)) as connection:
        store = TagStore(connection)
        store.replace(CHEAP_SOURCES, [FileTags(PHOTO, (SENTENCE, WORD))])
        store.replace(MODEL_SOURCES, [FileTags(PHOTO, (CAPTION, DOG))])
        assert store.of(PHOTO) == (SENTENCE, WORD, CAPTION, DOG)
    assert names(index, "plage") == ["IMG_1.jpg"]
    assert names(index, "takeout:lea") == ["IMG_1.jpg"]
    assert names(index, '"fete de lea"') == ["IMG_1.jpg"]
    assert names(index, "folder:plage") == []
    assert names(index, "chien") == ["IMG_1.jpg"]


def test_a_new_takeout_changes_the_words_at_the_next_tags_run(tmp_path: Path) -> None:
    """The cheap sources are replaced whole: an emptied description leaves none."""
    index = make_index(tmp_path)
    with closing(sqlite3.connect(index)) as connection:
        store = TagStore(connection)
        store.replace(CHEAP_SOURCES, [FileTags(PHOTO, (SENTENCE, WORD))])
        store.replace(
            CHEAP_SOURCES, [FileTags(PHOTO, (Tag(TagSource.TAKEOUT, "neige"),))]
        )
    assert names(index, "plage") == []
    assert names(index, "neige") == ["IMG_1.jpg"]
    with closing(sqlite3.connect(index)) as connection:
        TagStore(connection).replace(CHEAP_SOURCES, [FileTags(PHOTO, ())])
        assert TagStore(connection).counts() == {}


def test_an_index_of_before_reads_and_a_later_one_is_ignored_by_an_older_tool() -> None:
    """No schema change: rows of the new source are plain text; unknown ones skipped."""
    with FactsRepository.open(None) as repository:
        connection = repository.connection
        connection.execute(
            "INSERT INTO tags (path, size, mtime_ns, source, value)"
            " VALUES (?, 10, 7, 'folder', 'Durbuy'), (?, 10, 7, 'later', 'x')",
            (str(PATH), str(PATH)),
        )
        store = TagStore(connection)
        assert store.of(PHOTO) == (Tag(TagSource.FOLDER, "Durbuy"),)
        store.replace(CHEAP_SOURCES, [FileTags(PHOTO, (WORD,))])
        assert store.counts() == {TagSource.TAKEOUT: 1}


def test_the_description_is_not_written_to_xmp_by_default() -> None:
    """It came from Google: the user adds `takeout` to `xmp_sources` if wanted."""
    assert TagSource.TAKEOUT not in TagSettings().xmp_sources
