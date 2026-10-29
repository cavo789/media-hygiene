"""The place of each photo on the TV: the user's place, a landmark, a town (0472)."""

from __future__ import annotations

import json
import lzma
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.geo.distance import Point
from media_hygiene.geo.landmarks import LANDMARKS_FILE, Landmarks
from media_hygiene.geo.towns_once import shared_towns
from media_hygiene.services.slideshow_places import Places
from media_hygiene.slideshow.chapters import Chapter
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.screen_api import screen_view
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

_HOME: Final = {"name": "Home", "latitude": 50.85, "longitude": 4.35, "radius_m": 500}
_EVENT: Final = Chapter(1, "Promenade", "October 2026", "Paris, France")
_EIFFEL: Final = Point(48.8584, 2.2945)


def _places(tmp_path: Path) -> Places:
    runtime = make_runtime(make_locations(tmp_path), {"classify": {"places": [_HOME]}})
    return Places(runtime, shared_towns(), [Point(50.85, 4.35), _EIFFEL])


def test_the_user_s_place_then_a_landmark_then_the_town(tmp_path: Path) -> None:
    """Home wins; the Eiffel Tower is named; the open sea of Liège's hills, its town."""
    places = _places(tmp_path)
    assert places.spot(Point(50.8501, 4.3501), _EVENT) == "Home"
    assert places.spot(_EIFFEL, _EVENT) == "Tour Eiffel"
    assert places.spot(Point(50.65, 5.40), _EVENT) != ""


def test_nothing_without_gps_nor_when_the_event_says_it(tmp_path: Path) -> None:
    """No position: nothing; the event's place again: nothing."""
    places = _places(tmp_path)
    assert places.spot(None, _EVENT) == ""
    at_home = Chapter(2, "Jardin", "", "Home")
    assert places.spot(Point(50.8501, 4.3501), at_home) == ""


def test_landmarks_within_the_radius_only(tmp_path: Path) -> None:
    """A landmark 100 m away is named; 1 km away, not; no file, no landmark."""
    assert len(Landmarks.load(tmp_path)) == 0
    text = "Castle\t50.0000\t5.0000\nbad row\n"
    (tmp_path / LANDMARKS_FILE).write_bytes(lzma.compress(text.encode()))
    landmarks = Landmarks.load(tmp_path)
    assert len(landmarks) == 1
    assert landmarks.at(Point(50.0009, 5.0)) == "Castle"
    assert landmarks.at(Point(50.01, 5.0)) == ""


def test_a_damaged_file_knows_no_landmark(tmp_path: Path) -> None:
    """Not xz, or a position that is no number: an empty list, never a crash."""
    (tmp_path / LANDMARKS_FILE).write_bytes(b"not xz")
    assert len(Landmarks.load(tmp_path)) == 0
    (tmp_path / LANDMARKS_FILE).write_bytes(lzma.compress(b"Castle\tnorth\t5\n"))
    assert len(Landmarks.load(tmp_path)) == 0


def test_the_tv_shows_the_place_while_it_tells_the_events() -> None:
    """Told on the TV: the place is sent; on the phone only: not."""
    show = Show((Slide(1, chapter=_EVENT, place="Tour Eiffel"),), Timing(5))
    desk = Desk(show, Screens(), Changes())
    assert screen_view(desk)["where"] == "Tour Eiffel"
    desk.ask(json.dumps({"action": "tell", "where": "phone"}).encode())
    assert screen_view(desk)["where"] == ""


def test_no_landmark_where_no_photo_of_the_show_or_index_lies(tmp_path: Path) -> None:
    """A cell without a photo loads nothing: the Eiffel Tower falls back to its town."""
    runtime = make_runtime(make_locations(tmp_path), {"classify": {"places": [_HOME]}})
    places = Places(runtime, shared_towns(), [Point(50.85, 4.35)])
    assert places.spot(_EIFFEL, _EVENT) != "Tour Eiffel"


def test_the_index_s_photos_load_their_cells(tmp_path: Path) -> None:
    """A photo of the index near the Eiffel Tower loads its cell for any show."""
    runtime = make_runtime(make_locations(tmp_path), {"classify": {"places": [_HOME]}})
    index_file = runtime.index_file
    if index_file is None:
        pytest.skip("no kept index in this runtime")
    index_file.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(index_file)) as connection:
        connection.execute("CREATE TABLE files (metadata TEXT)")
        connection.execute(
            "INSERT INTO files VALUES (?)",
            (
                json.dumps(
                    {"latitude": _EIFFEL.latitude, "longitude": _EIFFEL.longitude}
                ),
            ),
        )
        connection.commit()
    places = Places(runtime, shared_towns(), [Point(50.85, 4.35)])
    assert places.spot(_EIFFEL, _EVENT) == "Tour Eiffel"
