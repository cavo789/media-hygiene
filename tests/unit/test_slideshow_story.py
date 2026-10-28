"""The events of a show, told on the TV and the phone (0448)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.index.schema import prepare
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services.slideshow_pick import Pick, picked_slides
from media_hygiene.slideshow.chapters import (
    Chapter,
    Telling,
    event_name,
    event_period,
)
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.screen_api import screen_view
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_LIBRARY: Final = PurePath("/data")
_DASH: Final = "\u2013"
_VALKENBURG: Final = (50.865, 5.832)
_HOME: Final = {"name": "Home", "latitude": 50.85, "longitude": 4.35, "radius_m": 500}


@pytest.mark.parametrize(
    ("folder", "name"),
    [
        (
            "/data/c/Photos/2026/2026-10/Promenade à Valkenburg",
            "Promenade à Valkenburg",
        ),
        ("/data/c/Photos/2026/2026-10", ""),
        ("/data/c/Photos/Crète/2023/Juillet 2023", "Crète"),
        ("/data/c/Photos/2026/2026-10-28", ""),
        ("/data/c/Photos/Noël/DCIM/100CANON", "Noël"),
        ("/data/c/Photos", ""),
    ],
)
def test_the_name_is_the_deepest_folder_that_says_something(
    folder: str, name: str
) -> None:
    """Years, months, dates and devices' folders are passed; the library is no name."""
    assert event_name(PurePath(folder), _LIBRARY) == name


def test_the_period_one_month_a_span_or_nothing() -> None:
    """One month, months of a year, months across years, no date."""
    assert event_period(["2026-10-28", "2026-10-02", None]) == "October 2026"
    assert event_period(["2023-07-30", "2023-08-02"]) == f"July {_DASH} August 2023"
    assert (
        event_period(["2022-12-30", "2023-01-02"])
        == f"December 2022 {_DASH} January 2023"
    )
    assert event_period([None]) == ""


def _index(runtime: Runtime, tmp_path: Path) -> Path:
    index = tmp_path / "index.sqlite"
    data = runtime.locations.data_dir
    rows = (
        ("c/Photos/2026/2026-10/Promenade/a.jpg", "2026:10:02 10:00:00", _VALKENBURG),
        ("c/Photos/2026/2026-10/Promenade/b.jpg", "2026:10:02 11:00:00", None),
        (
            "c/Photos/2026/2026-11/Jardin/c.jpg",
            "2026:11:01 10:00:00",
            (50.8501, 4.3501),
        ),
        ("c/Photos/2026/2026-11/Jardin/d.jpg", "2026:11:02 10:00:00", None),
    )
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        for path, date, point in rows:
            metadata = (
                None
                if point is None
                else json.dumps({"latitude": point[0], "longitude": point[1]})
            )
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns, media_date, metadata)"
                " VALUES (?, 1, 7, ?, ?)",
                (str(data / path), date, metadata),
            )
        connection.commit()
    return index


def test_each_folder_is_an_event_named_dated_and_placed(tmp_path: Path) -> None:
    """The user's place wins over the town; a photo without GPS takes its event's."""
    runtime = make_runtime(make_locations(tmp_path), {"classify": {"places": [_HOME]}})
    with SearchIndex.open(_index(runtime, tmp_path)) as search:
        slides = picked_slides(runtime, search, Pick(folder=r"C:\Photos")).slides
    chapters = [slide.chapter for slide in slides]
    assert chapters[0] == chapters[1]
    assert chapters[2] == chapters[3]
    first, second = chapters[0], chapters[2]
    assert first is not None
    assert second is not None
    assert (first.number, first.name, first.period) == (1, "Promenade", "October 2026")
    assert first.place == "Valkenburg"
    assert (second.number, second.name, second.place) == (2, "Jardin", "Home")


def _desk() -> Desk:
    chapter = Chapter(1, "Promenade", "October 2026", "Valkenburg")
    show = Show((Slide(1, chapter=chapter), Slide(2, chapter=chapter)), Timing(5))
    return Desk(show, Screens(), Changes())


def test_the_phone_s_choice_reaches_the_tv() -> None:
    """By default the TV tells the event; phone only or nowhere, it does not."""
    desk = _desk()
    assert screen_view(desk)["chapter"] == {
        "number": 1,
        "name": "Promenade",
        "period": "October 2026",
        "place": "Valkenburg",
    }
    version = desk.show.version
    answer = desk.ask(json.dumps({"action": "tell", "where": "phone"}).encode())
    state = json.loads(answer.body)
    assert state["telling"] == Telling.PHONE
    assert state["chapter"]["name"] == "Promenade"
    assert desk.show.version > version
    assert screen_view(desk)["chapter"] is None
    desk.ask(json.dumps({"action": "tell", "where": "nowhere"}).encode())
    assert desk.screens.telling is Telling.PHONE  # not a choice: refused
    desk.ask(json.dumps({"action": "tell", "where": "none"}).encode())
    assert str(desk.screens.telling) == Telling.NOWHERE.value


def test_the_same_event_on_the_next_photo_is_not_told_again() -> None:
    """The TV tells an event once: its number stays the same on its next photo."""
    desk = _desk()
    first = screen_view(desk)["chapter"]
    desk.show.move(1)
    assert screen_view(desk)["chapter"] == first
