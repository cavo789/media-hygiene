"""The name proposed for new photos: place, day, activity (0477)."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import TYPE_CHECKING

from media_hygiene.classify.event_title import TitleFacts, activity_of, proposed_title
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.search.event_suggest import title_of

if TYPE_CHECKING:
    from pathlib import Path

DAY = date(2026, 10, 29)


def test_gps_and_a_shared_tag_name_an_activity_at_a_place() -> None:
    """« Promenade à Liège » in French, « Walk in Liège » in English."""
    facts = TitleFacts("Liège", DAY, activity_of([["walk", "tree"], ["Promenade"]]))
    assert proposed_title(facts) == "Walk in Liège"
    with using(Locale.FR):
        french = TitleFacts("Liège", DAY, activity_of([["promenade"], ["walk"]]))
        assert proposed_title(french) == "Promenade à Liège"
        assert proposed_title(TitleFacts("Liège", DAY)) == "Liège — 29 octobre"


def test_no_shared_tag_gives_the_place_and_the_day() -> None:
    """A tag of one photo in three is not shared."""
    activity = activity_of([["beach"], ["tree"], ["car"]])
    assert activity == ""
    assert proposed_title(TitleFacts("Liège", DAY, activity)) == "Liège — 29 October"


def test_no_gps_gives_the_day_only() -> None:
    """Without a place, the day; without anything, nothing."""
    assert proposed_title(TitleFacts("", DAY, "Walk")) == "29 October"
    assert proposed_title(TitleFacts("", None)) == ""


def test_the_index_tags_name_the_files(tmp_path: Path) -> None:
    """The user's place before the town; the vision words of the described photos."""
    connection = sqlite3.connect(tmp_path / "index.sqlite")
    connection.execute(
        "CREATE TABLE tags (path TEXT, size INTEGER, mtime_ns INTEGER, source TEXT,"
        " value TEXT, model TEXT DEFAULT '', kind TEXT DEFAULT '')"
    )
    rows = [
        ("/data/a.jpg", "place", "Liège", "town"),
        ("/data/b.jpg", "place", "Liège", "town"),
        ("/data/a.jpg", "vision", "walk", ""),
        ("/data/b.jpg", "vision", "walk", ""),
        ("/data/c.jpg", "vision", "car", ""),
    ]
    connection.executemany(
        "INSERT INTO tags (path, size, mtime_ns, source, value, kind)"
        " VALUES (?, 1, 1, ?, ?, ?)",
        rows,
    )
    paths = ["/data/a.jpg", "/data/b.jpg", "/data/c.jpg"]
    assert title_of(connection, paths, DAY) == "Walk in Liège"
    connection.execute(
        "INSERT INTO tags (path, size, mtime_ns, source, value, kind)"
        " VALUES ('/data/c.jpg', 1, 1, 'place', 'Home', 'personal')"
    )
    assert title_of(connection, paths, DAY) == "Walk in Home"
    assert title_of(connection, [], DAY) == ""
    connection.close()
