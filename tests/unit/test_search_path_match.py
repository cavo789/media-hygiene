"""0426: *Path contains* takes wildcards, `/regex/`, and keeps a plain part literal."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

import pytest

from media_hygiene.index.schema import prepare
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.path_match import condition, refusal, regex_matches
from media_hygiene.search.query import Filters, SearchQuery

if TYPE_CHECKING:
    from pathlib import Path

_PATHS = (
    "/data/c/Videos/Trip/CLIP_1.MOV",
    "/data/c/Videos/Trip/clip_2.mov",
    "/data/c/Videos/movies/film.mp4",
    "/data/c/Photos/Vacances (2019)/IMG_1.jpg",
    "/data/c/Photos/a+b/IMG_2.jpg",
    "/data/c/Photos/100%/IMG_3.jpg",
    "/data/c/Photos/a_b/IMG_4.jpg",
    "/data/c/Photos/axb/IMG_5.jpg",
)


def _search(tmp_path: Path) -> SearchIndex:
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        connection.executemany(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, 1, 1)",
            [(path,) for path in _PATHS],
        )
        connection.executemany(  # the full-text table holds the files that have a tag
            "INSERT INTO tags (path, size, mtime_ns, source, value)"
            " VALUES (?, 1, 1, 'folder', 'x')",
            [(path,) for path in _PATHS],
        )
        connection.commit()
    return SearchIndex.open(index)


def _names(search: SearchIndex, typed: str) -> list[str]:
    found = search.find(SearchQuery((), Filters(folder=typed)), 20)
    return sorted(hit.photo.path.name for hit in found.hits)


@pytest.mark.parametrize(
    ("typed", "names"),
    [
        ("*mov", ["CLIP_1.MOV", "clip_2.mov", "film.mp4"]),  # contains: movies/ too
        ("*.mov", ["CLIP_1.MOV", "clip_2.mov"]),
        (".MOV", ["CLIP_1.MOV", "clip_2.mov"]),
        ("trip/clip_?.mov", ["CLIP_1.MOV", "clip_2.mov"]),
        ("trip\\clip_?.mov", ["CLIP_1.MOV", "clip_2.mov"]),
        ("movies", ["film.mp4"]),
        ("100%", ["IMG_3.jpg"]),
        ("a_b", ["IMG_4.jpg"]),
        ("a_b*", ["IMG_4.jpg"]),
        ("100%*", ["IMG_3.jpg"]),
        ("/\\.(mov|mp4)$/", ["CLIP_1.MOV", "clip_2.mov", "film.mp4"]),
        ("/\\.mov$/", ["CLIP_1.MOV", "clip_2.mov"]),
        ("Vacances (2019)", ["IMG_1.jpg"]),
        ("a+b", ["IMG_2.jpg"]),
        ("/(/", []),  # invalid: matches nothing, never an error
        ("", sorted(path.rsplit("/", 1)[1] for path in _PATHS)),
    ],
)
def test_path_contains(tmp_path: Path, typed: str, names: list[str]) -> None:
    """Wildcards, case, slashes, `%` and `_` literal, regex between slashes."""
    with _search(tmp_path) as search:
        assert _names(search, typed) == names


def test_an_invalid_regex_is_told_in_one_line() -> None:
    """Only a `/…/` that does not compile is refused."""
    message = refusal("/(/")
    assert message is not None
    assert "\n" not in message
    assert refusal("/\\.mov$/") is None
    assert refusal("Vacances (2019)") is None
    assert refusal("a+b") is None
    assert refusal("//") is None  # two slashes: a plain part of the path


def test_the_condition_and_the_function() -> None:
    """A plain part binds as is, a wildcard as LIKE, a regex as itself."""
    assert condition("   ") is None
    assert condition("Trip\\X") == ("instr(fold(files.path), ?) > 0", "trip/x")
    assert condition("a_b*")[1] == "%a\\_b%%"  # type: ignore[index]
    assert condition("/a.b/") == ("mh_regex(?, files.path)", "a.b")
    assert regex_matches("(", "x") == 0
    assert regex_matches("A.B", "xaxb") == 1
