"""The TV welcome page's line of index facts (0758)."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from media_hygiene.slideshow.tv_facts import facts_line
from media_hygiene.slideshow.tv_welcome import welcome

if TYPE_CHECKING:
    from pathlib import Path


def _index(tmp_path: Path, dates: list[str | None]) -> Path:
    """An index file holding files of these dates (one broken, never counted)."""
    index = tmp_path / "index.sqlite"
    connection = sqlite3.connect(index)
    connection.execute(
        "CREATE TABLE files (path TEXT, media_date TEXT, broken_reason TEXT)"
    )
    rows: list[tuple[str, str | None, str | None]] = [
        (f"/data/c/{n}.jpg", date, None) for n, date in enumerate(dates)
    ]
    rows.append(("/data/c/broken.jpg", "1950-01-01", "truncated"))
    connection.executemany("INSERT INTO files VALUES (?, ?, ?)", rows)
    connection.commit()
    connection.close()
    return index


def test_the_line_says_how_many_files_and_which_years(tmp_path: Path) -> None:
    """Count and first/last year; a broken file is left out."""
    index = _index(tmp_path, ["2004-07-01", "2021-03-02", None])
    assert facts_line(index) == "3 photos and videos, from 2004 to 2021"


def test_one_year_or_no_date(tmp_path: Path) -> None:
    """One year said once; no date at all: the count alone."""
    (tmp_path / "a").mkdir()
    one = _index(tmp_path / "a", ["2010-01-01"])
    assert facts_line(one) == "1 photo or video, from 2010"
    (tmp_path / "b").mkdir()
    assert facts_line(_index(tmp_path / "b", [None, None])) == "2 photos and videos"


def test_no_index_or_an_unreadable_one_shows_no_line(tmp_path: Path) -> None:
    """No index, an empty one, or a file that is not SQLite: no line."""
    assert not facts_line(tmp_path / "missing.sqlite")
    (tmp_path / "e").mkdir()
    assert not facts_line(_index(tmp_path / "e", []))
    junk = tmp_path / "junk.sqlite"
    junk.write_bytes(b"not a database at all" * 10)
    assert not facts_line(junk)


def test_the_welcome_page_shows_the_line(tmp_path: Path) -> None:
    """The page carries the line under the title; without an index, none."""
    page = welcome("/", "", _index(tmp_path, ["2015-05-05", "2019-01-01"])).body
    assert b"2 photos and videos, from 2015 to 2019" in page
    assert b'class="facts"' not in welcome("/", "").body
