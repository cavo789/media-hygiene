"""What an album's page shows on a phone (0297): cover, dates, place, days."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.services.slideshow_pick import Picked
from media_hygiene.share.album_view import AlbumSeen, album_view, facts_of
from media_hygiene.slideshow.slides import Film, Slide

if TYPE_CHECKING:
    from media_hygiene.geo.distance import Point

_HERAKLION: Final = (35.34, 25.13)
_CHANIA: Final = (35.51, 24.02)
_TOWNS: Final = {_HERAKLION: "Heraklion", _CHANIA: "Chania"}


def _index(
    rows: dict[int, tuple[float | None, tuple[float, float] | None]],
) -> sqlite3.Connection:
    """An index of a few files: their sharpness and position."""
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE files (sharpness REAL, metadata TEXT)")
    for key, (sharpness, where) in rows.items():
        metadata = (
            {} if where is None else {"latitude": where[0], "longitude": where[1]}
        )
        connection.execute(
            "INSERT INTO files (rowid, sharpness, metadata) VALUES (?, ?, ?)",
            (key, sharpness, json.dumps(metadata)),
        )
    return connection


def _town(point: Point) -> str | None:
    return _TOWNS.get((point.latitude, point.longitude))


def test_the_cover_is_the_sharpest_photo_of_the_first_day_and_days_are_named() -> None:
    """Cover, first and last day, the album's town, each day's town, the videos."""
    slides = (
        Slide(1, "2023-07-10"),
        Slide(2, "2023-07-10"),
        Slide(3, "2023-07-10", Film(".mp4", "h264", 12.0)),
        Slide(4, "2023-07-11"),
        Slide(5, "2023-07-11", Film(".avi")),
        Slide(6, None),
    )
    rows = {
        1: (10.0, _HERAKLION),
        2: (50.0, _HERAKLION),
        3: (None, None),
        4: (90.0, _CHANIA),
        5: (None, None),
        6: (None, _HERAKLION),
    }
    with closing(_index(rows)) as connection:
        view = album_view(
            AlbumSeen("Crete 2023", Picked(slides, 6, missing=1)), connection, _town
        )
    assert view["cover"] == {"key": 2, "thumb": "/thumb/2.jpg", "photo": "/tv/2.jpg"}
    assert (view["first"], view["last"], view["place"]) == (
        "2023-07-10",
        "2023-07-11",
        "Heraklion",
    )
    assert (view["count"], view["missing"]) == (6, 1)
    days = view["days"]
    assert isinstance(days, list)
    assert [(day["day"], day["place"]) for day in days] == [
        ("2023-07-10", "Heraklion"),
        ("2023-07-11", "Chania"),
        ("", "Heraklion"),
    ]
    film, unplayable = days[0]["items"][2], days[1]["items"][1]
    assert (film["film"], film["photo"], film["thumb"]) == ("/film/3.mp4", "", "")
    assert (unplayable["film"], unplayable["format"]) == ("", "avi")


def test_an_album_of_videos_has_no_cover_and_unknown_facts_are_empty() -> None:
    """No photo, no cover; a key the index lost, nor sharpness nor position."""
    slides = (Slide(7, None, Film(".mov", "hevc")),)
    with closing(_index({})) as connection:
        view = album_view(AlbumSeen("Films", Picked(slides, 1)), connection, _town)
        assert facts_of(connection, 99).point is None
    assert view["cover"] is None
    assert (view["first"], view["place"]) == ("", "")
