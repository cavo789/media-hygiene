"""Search by meaning: names and places narrow, the meaning ranks, the words merge in."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import FaceModelError
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.meaning_rows import MeaningStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.meaning.clip import MODEL
from media_hygiene.search.meaning import RRF_K, Meaning, MeaningSource, fused
from media_hygiene.search.meaning_index import MeaningIndex
from media_hygiene.search.query import Filters, SearchQuery, parse_terms
from media_hygiene.tags.models import TagSource
from tests.support.meaning import COLOURS, ColourWords, colour_vector

if TYPE_CHECKING:
    from media_hygiene.meaning.embedder import TextReader

_ROOT = "/data/c/Photos"
# Each photo: its colour, its place (empty: none) and its year.
_PHOTOS = {
    "kitchen_ann.jpg": (COLOURS["kitchen"], "", 2019),
    "beach_ann.jpg": (COLOURS["sea"], "Durbuy", 2020),
    "kitchen_bob.jpg": (COLOURS["kitchen"], "", 2019),
    "snow_bob.jpg": (COLOURS["snow"], "Durbuy", 2021),
    "beach_none.jpg": (COLOURS["sea"], "", 2021),
}
_PEOPLE = {
    "kitchen_ann.jpg": ("Frédérique",),
    "beach_ann.jpg": ("Frédérique",),
    "kitchen_bob.jpg": ("Bob",),
    "snow_bob.jpg": ("Bob",),
}


def _index(tmp_path: Path) -> Path:
    """An index of five photos: places, a vision word, their vectors."""
    target = tmp_path / "index.sqlite"
    with FactsRepository.open(target) as repository:
        connection = repository.connection
        store = MeaningStore(connection, MODEL)
        for number, (name, (colour, place, year)) in enumerate(_PHOTOS.items()):
            photo = PhotoVersion(Path(f"{_ROOT}/{name}"), 10 + number, 7)
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns, media_date)"
                " VALUES (?, ?, ?, ?)",
                (str(photo.path), photo.size, 7, f"{year}:01:01 10:00:00"),
            )
            words = [("folder", "Photos")] + ([("place", place)] if place else [])
            if name == "kitchen_bob.jpg":
                words.append(("vision", "cuisine"))
            connection.executemany(
                "INSERT INTO tags (path, size, mtime_ns, source, value)"
                " VALUES (?, ?, 7, ?, ?)",
                [
                    (str(photo.path), photo.size, source, value)
                    for source, value in words
                ],
            )
            store.put(photo, colour_vector(colour), 0.05)
    return target


def _open(
    tmp_path: Path, words: TextReader | None = None, results: int = 10
) -> MeaningIndex:
    """The index, its people named, ranking by meaning with the colour model."""
    search = MeaningIndex.open(_index(tmp_path))
    search.name_people(
        {Path(f"{_ROOT}/{name}"): names for name, names in _PEOPLE.items()}
    )
    reader = words or ColourWords()
    search.understand(MeaningSource(lambda: reader, results))
    return search


def _names(
    search: MeaningIndex, text: str, filters: Filters | None = None
) -> list[str]:
    """The names of the files found, best first."""
    query = SearchQuery(parse_terms(text), filters or Filters())
    return [hit.photo.path.name for hit in search.find(query, 10).hits]


def test_reciprocal_rank_fusion() -> None:
    """In both lists beats first of one; ties go to the smaller row."""
    assert fused(([1, 2, 3], [3, 4])) == (3, 1, 2, 4)
    assert fused(([5], [6])) == (5, 6)
    assert not fused(())
    assert RRF_K == 60


def test_a_name_narrows_and_the_meaning_ranks(tmp_path: Path) -> None:
    """Frédérique dans la cuisine: her photos only, the kitchen first."""
    with _open(tmp_path) as search:
        assert _names(search, "Frédérique dans la cuisine") == [
            "kitchen_ann.jpg",
            "beach_ann.jpg",
        ]
        assert _names(search, "person:Bob mer") == ["snow_bob.jpg", "kitchen_bob.jpg"]
        assert _names(search, "Durbuy mer") == ["beach_ann.jpg", "snow_bob.jpg"]
        assert _names(search, "place:durbuy mer") == ["beach_ann.jpg", "snow_bob.jpg"]


def test_the_meaning_alone_ranks_every_photo_and_merges_the_words(
    tmp_path: Path,
) -> None:
    """Mer: the blue photos first; cuisine: the word and the meaning agree."""
    with _open(tmp_path) as search:
        sea = _names(search, "mer")
        assert set(sea[:2]) == {"beach_ann.jpg", "beach_none.jpg"}
        assert len(sea) == len(_PHOTOS)
        assert _names(search, "cuisine")[0] == "kitchen_bob.jpg"
        found = search.find(SearchQuery(parse_terms("mer")), 1)
        assert found.total == len(_PHOTOS)
        assert len(found.hits) == 1


def test_filters_narrow_and_results_limit(tmp_path: Path) -> None:
    """Years and a folder narrow the photos; `results` caps the meaning's list."""
    with _open(tmp_path, results=2) as search:
        assert _names(search, "mer", Filters(years=(2021, 2021))) == [
            "beach_none.jpg",
            "snow_bob.jpg",
        ]
        assert set(_names(search, "mer")) == {"beach_ann.jpg", "beach_none.jpg"}
        versions = search.versions(SearchQuery(parse_terms("mer")))
        assert {photo.path.name for photo in versions} == {
            "beach_ann.jpg",
            "beach_none.jpg",
        }


def test_names_places_and_sources_alone_keep_the_words(tmp_path: Path) -> None:
    """Nothing left to understand, or one source asked: the full-text search."""
    words = ColourWords()
    with _open(tmp_path, words) as search:
        assert sorted(_names(search, "Frédérique")) == [
            "beach_ann.jpg",
            "kitchen_ann.jpg",
        ]
        assert _names(search, "mer", Filters(source=TagSource.VISION)) == []
        assert _names(search, "") != []
        versions = search.versions(SearchQuery(parse_terms("Durbuy")))
        assert {photo.path.name for photo in versions} == {
            "beach_ann.jpg",
            "snow_bob.jpg",
        }
    assert all("Frédérique" not in asked for asked in words.asked)


def test_a_model_that_cannot_load_leaves_the_words(tmp_path: Path) -> None:
    """A build without the model: the words answer, the page never fails."""
    calls: list[int] = []

    def broken() -> TextReader:
        calls.append(1)
        message = "no tokenizers"
        raise FaceModelError(message)

    search = MeaningIndex.open(_index(tmp_path))
    with search:
        search.understand(MeaningSource(broken, 10))
        assert _names(search, "cuisine") == ["kitchen_bob.jpg"]
        assert _names(search, "mer") == []
    assert calls == [1]  # tried once


def test_a_search_typed_again_reuses_its_vector(tmp_path: Path) -> None:
    """The text model answers once per search."""
    words = ColourWords()
    with _open(tmp_path, words) as search:
        _names(search, "mer")
        _names(search, "mer")
    assert words.asked == ["mer"]


def test_without_vectors_the_meaning_finds_nothing_more(tmp_path: Path) -> None:
    """An index whose photos have no vector: the words alone."""
    meaning = Meaning(MeaningSource(ColourWords, 10))
    target = tmp_path / "empty.sqlite"
    with FactsRepository.open(target) as repository:
        meaning.read(repository.connection)
    assert meaning.closest("mer", None) == ()


@pytest.mark.parametrize("text", ["", "   "])
def test_no_words_no_meaning(tmp_path: Path, text: str) -> None:
    """A search without words lists the newest first, as before."""
    with _open(tmp_path) as search:
        assert len(_names(search, text)) == len(_PHOTOS)
