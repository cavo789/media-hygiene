"""`browse`: the heaviest files of the whole library, by size or by bit rate."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.search.days import NAME, media_day
from media_hygiene.search.heaviest import (
    HeaviestAsked,
    heaviest,
    listed_total,
    video_facts,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

_ROOTS = (Path("/data/c/Photos"), Path("/data/d/Old"))
_FILES = (
    ("/data/c/Photos/a.mp4", 5_000, {"bit_rate": 2_000_000, "duration": 754.0}),
    ("/data/d/Old/b.avi", 9_000, {"bit_rate": 12_700_000, "codec": "mjpeg"}),
    ("/data/d/Old/c.mp4", 9_000, None),  # unreadable: its bit rate is unknown
    ("/data/c/Photos/d.jpg", 20_000, None),
    ("/data/e/Elsewhere/e.mp4", 99_000, {"bit_rate": 99_000_000}),  # not mounted
)


@pytest.fixture
def index() -> Iterator[sqlite3.Connection]:
    """An index holding the files above, with the day function of the search."""
    with closing(sqlite3.connect(":memory:")) as connection:
        _fill(connection)
        yield connection


def _fill(connection: sqlite3.Connection) -> None:
    """Create the table of the files, and write them."""
    connection.create_function(NAME, 1, media_day)
    connection.execute(
        "CREATE TABLE files (path TEXT PRIMARY KEY, size INTEGER, media_date TEXT,"
        " metadata TEXT)"
    )
    connection.executemany(
        "INSERT INTO files VALUES (?, ?, NULL, ?)",
        [(p, s, json.dumps(m) if m else None) for p, s, m in _FILES],
    )


def _names(index: sqlite3.Connection, asked: HeaviestAsked) -> list[str]:
    """The names listed for a request."""
    return [Path(row[1]).name for row in heaviest(index, asked, _ROOTS).rows]


def test_by_size_across_roots_ties_by_path(index: sqlite3.Connection) -> None:
    """Largest first, from both roots; equal sizes by path; never outside them."""
    assert _names(index, HeaviestAsked(kind="all")) == [
        "d.jpg",
        "b.avi",
        "c.mp4",
        "a.mp4",
    ]
    assert _names(index, HeaviestAsked()) == [
        "b.avi",
        "c.mp4",
        "a.mp4",
    ]  # videos by default
    assert _names(index, HeaviestAsked(kind="photos")) == ["d.jpg"]


def test_the_limit_and_the_library_total(index: sqlite3.Connection) -> None:
    """At most `limit`; the total counts every file under the roots."""
    found = heaviest(index, HeaviestAsked(limit=1), _ROOTS)
    assert len(found.rows) == 1
    assert found.library == 43_000
    assert listed_total(found).startswith("1 file, ")
    assert listed_total(found).endswith("21 % of your library")


def test_by_rate_unknown_last(index: sqlite3.Connection) -> None:
    """The highest bit rate first; a video without one last, never a crash."""
    assert _names(index, HeaviestAsked(order="rate")) == ["b.avi", "a.mp4", "c.mp4"]


def test_the_facts_of_a_video(index: sqlite3.Connection) -> None:
    """Length, bit rate, codec and size, those known only."""
    found = heaviest(index, HeaviestAsked(), _ROOTS)
    facts = [video_facts(found.metadata.get(row[0], {})) for row in found.rows]
    assert facts == ["12.7 Mb/s · mjpeg", "", "13 min · 2.0 Mb/s"]
    assert video_facts({"duration": 3_900, "width": 1280, "height": 720}) == (
        "1 h 05 · 1280\N{MULTIPLICATION SIGN}720"
    )
    assert video_facts({"duration": 45.2}) == "45 s"
