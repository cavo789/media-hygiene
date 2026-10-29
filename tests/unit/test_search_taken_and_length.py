"""0433, 0434: a tile says which date it shows, its EXIF, and a video's length."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, cast

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.exif_facts import exif_lines, modified_day, taken_text
from media_hygiene.search.hits import with_facts
from media_hygiene.search.models import Found, Hit
from media_hygiene.search.views import found_view

if TYPE_CHECKING:
    from media_hygiene.search.fts import SearchIndex

_NANO = 1_000_000_000
_MARCH_2025 = 1_740_900_000  # 2025-03-02, UTC
_PHOTO = {
    "make": "Canon",
    "model": "EOS 5D",
    "lens": "EF 50mm",
    "exposure_time": 0.004,
    "f_number": 2.8,
    "iso": 400,
    "focal_length": 50.0,
    "width": 4000,
    "height": 3000,
    "latitude": 50.85,
    "longitude": 4.35,
}


@dataclass(frozen=True)
class _Index:
    """The part of the search index `with_facts` reads."""

    connection: sqlite3.Connection


def _index(
    connection: sqlite3.Connection,
    rows: list[tuple[int, dict[str, object] | None, str | None]],
) -> SearchIndex:
    """An index holding the metadata and date of a few files.

    Args:
        connection: An empty database, closed by the test.
        rows: Key, metadata and date as written of each file.

    Returns:
        The index.
    """
    connection.execute("CREATE TABLE files (metadata TEXT, media_date TEXT)")
    for key, metadata, written in rows:
        connection.execute(
            "INSERT INTO files (rowid, metadata, media_date) VALUES (?, ?, ?)",
            (key, json.dumps(metadata) if metadata else None, written),
        )
    return cast("SearchIndex", _Index(connection))


def _found(*names: str) -> Found:
    """Files found, each modified on 2025-03-02.

    Args:
        *names: Their names.

    Returns:
        What a search found.
    """
    hits = tuple(
        Hit(key, PhotoVersion(Path("/data/c") / name, 1, _MARCH_2025 * _NANO), None, {})
        for key, name in enumerate(names, start=1)
    )
    return Found(len(hits), hits)


def test_a_photo_carries_its_time_taken_its_exif_and_its_modified_day() -> None:
    """The time taken and the EXIF lines reach the page; the modified day too."""
    with closing(sqlite3.connect(":memory:")) as connection:
        index = _index(connection, [(1, _PHOTO, "2023:07:14 10:32:05")])
        found = with_facts(index, _found("IMG_1.jpg"))
    view = found_view(found, HostPathMapper(Path("/data")))["hits"]
    hit = cast("list[dict[str, object]]", view)[0]
    assert hit["taken"] == "2023-07-14 10:32"
    assert hit["modified"] == "2025-03-02"
    assert hit["seconds"] is None
    assert hit["exif"] == [
        "Taken: 2023-07-14 10:32",
        "Camera: Canon EOS 5D",
        "Lens: EF 50mm",
        "1/250 s · f/2.8 · ISO 400 · 50 mm",
        "4000 by 3000 pixels",
        "GPS: 50.85000, 4.35000 (Brussels, Belgium)",
    ]


def test_a_video_carries_its_length_and_a_file_without_a_row_nothing() -> None:
    """A video's seconds feed its badge; a file the index lacks stays as found."""
    with closing(sqlite3.connect(":memory:")) as connection:
        index = _index(connection, [(1, {"duration": 2.4, "codec": "h264"}, None)])
        movie, unknown = with_facts(index, _found("clip.mp4", "IMG_2.jpg")).hits
    assert movie.seconds == 2.4
    assert "h264" in movie.facts
    assert movie.exif == ("No date taken",)
    assert unknown.exif == ()


def test_the_dates_read_and_written() -> None:
    """Every form of date is written as `YYYY-MM-DD HH:MM`; a slow exposure in s."""
    assert taken_text(None) == ""
    assert taken_text("2004-12-04T10:00:00Z").startswith("2004-12-04 10:00")
    assert modified_day(0) == "1970-01-01"
    assert "2 s" in exif_lines({"exposure_time": 2.0}, "")[1]
