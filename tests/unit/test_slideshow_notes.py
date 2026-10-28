"""The storyteller's view on the phone (0449): notes, story controls, the map."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from media_hygiene.search.fts import SearchIndex
from media_hygiene.services.slideshow_notes import notes_of
from media_hygiene.services.slideshow_pick import Pick, picked_slides
from media_hygiene.slideshow.chapters import Chapter
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.notes import Notes
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_slideshow_story import _index

if TYPE_CHECKING:
    from pathlib import Path


def test_each_photo_carries_its_time_and_position(tmp_path: Path) -> None:
    """The time of `media_date` and the GPS of the index reach the slide."""
    runtime = make_runtime(make_locations(tmp_path))
    with SearchIndex.open(_index(runtime, tmp_path)) as search:
        slides = picked_slides(runtime, search, Pick(folder=r"C:\Photos")).slides
    first = slides[0].notes
    assert first is not None
    assert first.time == "10:00"
    assert first.point == (50.865, 5.832)
    assert slides[1].notes == Notes(time="11:00")


def test_the_description_and_words_come_from_the_tags(tmp_path: Path) -> None:
    """The caption is the description; the vision words follow, without repeats."""
    path = tmp_path / "a.jpg"
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE files (media_date TEXT, metadata TEXT)")
        connection.execute("CREATE TABLE tags (path TEXT, source TEXT, value TEXT)")
        connection.execute("INSERT INTO files VALUES ('bad', 'not json')")
        rows = [
            ("caption", "A walk"),
            ("vision", "dog"),
            ("vision", "dog"),
            ("vision", "tree"),
        ]
        connection.executemany(
            "INSERT INTO tags VALUES (?, ?, ?)", [(str(path), *row) for row in rows]
        )
        notes = notes_of(connection, 1, path)
        assert notes == Notes(caption="A walk", words=("dog", "tree"))
        assert notes_of(connection, 99, path) == Notes()
        connection.execute("DROP TABLE tags")
        assert notes_of(connection, 1, path) == Notes()


def _desk() -> Desk:
    walk = Chapter(1, "Walk")
    garden = Chapter(2, "Garden")
    slides = (
        Slide(
            1, "2026-10-02", chapter=walk, notes=Notes(time="10:00", point=(50.0, 5.0))
        ),
        Slide(2, chapter=walk, notes=Notes(point=(50.1, 5.1))),
        Slide(3, chapter=walk),
        Slide(4, chapter=garden),
    )
    return Desk(Show(slides, Timing(5)), Screens(), Changes())


def _ask(desk: Desk, action: str) -> dict[str, object]:
    answer = desk.ask(json.dumps({"action": action}).encode())
    state = json.loads(answer.body)
    assert isinstance(state, dict)
    return state


def test_the_storyteller_reads_the_photo_the_next_one_and_the_map() -> None:
    """The view says the time, the next photo and the event's positions."""
    desk = _desk()
    desk.show.jump(1)
    story = desk.state()["story"]
    assert story == {
        "day": "2026-10-02",
        "time": "10:00",
        "caption": "",
        "words": [],
        "here": (50.0, 5.0),
        "map": None,
        "next": 2,
        "points": [(50.0, 5.0), (50.1, 5.1)],
    }


def test_the_story_controls_move_by_event() -> None:
    """Back to the event's start, the next event; past the last one, it stays."""
    desk = _desk()
    desk.show.jump(3)
    assert _ask(desk, "event")["current"] == 1
    assert _ask(desk, "next_event")["current"] == 4
    assert _ask(desk, "next_event")["current"] == 4
    desk.show.set_out(1, out=True)
    desk.show.jump(3)
    assert _ask(desk, "event")["current"] == 2  # its first photo still shown
