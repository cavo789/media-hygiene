"""A burst series seen before `clean --decisions` stays seen in the next review."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from tests.support.review import review_session, write_burst

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_ARCHIVE: Final = "decisions.applied-20261024-101500.json"


def applied(locations: Locations) -> None:
    """Do what `clean --decisions` does to the decisions file once applied."""
    reports = locations.reports_dir
    (reports / "decisions.json").rename(reports / _ARCHIVE)


def test_a_series_kept_whole_stays_seen_after_the_clean(locations: Locations) -> None:
    """Key A, then a clean: the series is not shown again, still every shot kept."""
    write_burst(locations.data_dir)
    review_session(locations).decide({0: frozenset()})
    applied(locations)
    session = review_session(locations)
    assert session.seen == (1, 1)
    assert session.progress == (0, 0)
    saved = json.loads((locations.reports_dir / "decisions.json").read_text())
    assert [burst["status"] for burst in saved["bursts"]] == ["done"]


def test_what_is_left_once_shots_went_to_quarantine_stays_seen(
    locations: Locations,
) -> None:
    """The shot set aside is gone: the shots kept are the series, already seen."""
    shots = write_burst(locations.data_dir)
    review_session(locations).decide({0: frozenset({1})})
    applied(locations)
    shots[1].unlink()
    session = review_session(locations)
    assert session.seen == (1, 1)
    assert session.progress == (0, 0)


def test_a_series_back_from_the_quarantine_is_listed_again(
    locations: Locations,
) -> None:
    """After an undo the series is whole again: not what was seen, so to see."""
    write_burst(locations.data_dir)
    review_session(locations).decide({0: frozenset({1})})
    applied(locations)
    assert review_session(locations).seen == (0, 1)


def test_an_archive_of_other_folders_is_ignored(locations: Locations) -> None:
    """Made on other folders: nothing is carried over."""
    write_burst(locations.data_dir)
    review_session(locations).decide({0: frozenset()})
    applied(locations)
    archive = locations.reports_dir / _ARCHIVE
    held = json.loads(archive.read_text())
    archive.write_text(json.dumps({**held, "roots": ["E:\\"]}))
    assert review_session(locations).seen == (0, 1)


def test_an_unreadable_archive_is_ignored(locations: Locations) -> None:
    """Not a decisions file: the review opens, every series to see."""
    write_burst(locations.data_dir)
    (locations.reports_dir / _ARCHIVE).write_text("{}")
    assert review_session(locations).seen == (0, 1)


def test_a_series_seen_in_the_open_file_wins(locations: Locations) -> None:
    """The file of the review in progress already holds the series: kept as it is."""
    write_burst(locations.data_dir)
    review_session(locations).decide({0: frozenset()})
    reports = locations.reports_dir
    (reports / _ARCHIVE).write_text((reports / "decisions.json").read_text())
    review_session(locations).decide({0: frozenset({2})})
    assert review_session(locations).progress == (1, 1)
