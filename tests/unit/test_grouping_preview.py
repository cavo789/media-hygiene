"""The events as other grouping values would make them, nothing written (0643)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.grouping_preview import Grouping, compared, event_spans
from media_hygiene.search.days import NAME, media_day
from media_hygiene.search.grouping_desk import GroupingPreview

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_START = datetime(2024, 5, 1, 10, tzinfo=UTC)


def _times(*hours: float) -> list[datetime]:
    """Times that many hours after the start."""
    return [_START + timedelta(hours=hour) for hour in hours]


def test_spans_follow_the_gap_and_the_minimum() -> None:
    """A longer gap merges; a group too small is no event."""
    times = _times(0, 1, 2, 30, 31, 32, 100)
    assert event_spans(times, Grouping(4, 12, 3)) == [(0, 2), (3, 5)]
    assert event_spans(times, Grouping(4, 48, 3)) == [(0, 5)]


def test_compared_lists_merges_splits_new_and_gone() -> None:
    """Each kind of change is counted and listed."""
    times = _times(0, 1, 2, 30, 31, 32, 100, 101)
    merged = compared(times, Grouping(4, 12, 3), Grouping(4, 48, 3))
    assert merged["before"] == {"events": 2, "files": 6}
    assert merged["after"] == {"events": 1, "files": 6}
    assert merged["merged"] == {
        "count": 1,
        "listed": [
            {
                "first": _START.isoformat(),
                "last": times[5].isoformat(),
                "files": 6,
                "parts": 2,
            }
        ],
    }
    split = compared(times, Grouping(4, 48, 3), Grouping(4, 12, 3))
    assert split["split"] == {
        "count": 1,
        "listed": [
            {
                "first": _START.isoformat(),
                "last": times[5].isoformat(),
                "files": 6,
                "parts": 2,
            }
        ],
    }
    smaller = compared(times, Grouping(4, 12, 3), Grouping(4, 12, 2))
    assert smaller["new"] == {
        "count": 1,
        "listed": [
            {
                "first": times[6].isoformat(),
                "last": times[7].isoformat(),
                "files": 2,
                "parts": 0,
            }
        ],
    }
    larger = compared(times, Grouping(4, 12, 3), Grouping(4, 12, 4))
    assert larger["gone"] == {
        "count": 2,
        "listed": [
            {
                "first": _START.isoformat(),
                "last": times[2].isoformat(),
                "files": 3,
                "parts": 0,
            },
            {
                "first": times[3].isoformat(),
                "last": times[5].isoformat(),
                "files": 3,
                "parts": 0,
            },
        ],
    }


@pytest.fixture
def desk(tmp_path: Path) -> Iterator[GroupingPreview]:
    """A tiny index of three dated photos, `[classify]` written."""
    connection = sqlite3.connect(":memory:")
    connection.create_function(NAME, 1, media_day)
    connection.execute("CREATE TABLE files (media_date TEXT)")
    dates = ["2024:05:01 10:00:00", "2024:05:01 11:00:00", "2024:05:02 20:00:00", None]
    connection.executemany("INSERT INTO files VALUES (?)", [(one,) for one in dates])
    config = tmp_path / "config.toml"
    config.write_text(
        "[classify]\nmerge_gap_hours = 4.0\nmin_event_size = 2\n", encoding="utf-8"
    )
    with closing(connection):
        yield GroupingPreview(connection, config, 4.0)


def test_the_route_compares_without_writing(desk: GroupingPreview) -> None:
    """The kept values against the typed ones; the file untouched."""
    before = desk.config_file.read_bytes()
    body = {"merge_gap_hours": 48.0, "min_event_size": 2, "trip_min_km": 100.0}
    answer = desk.answer(json.dumps(body).encode())
    assert answer.status == HTTPStatus.OK
    shown = json.loads(answer.body)
    assert shown["before"]["events"] == 1
    assert shown["after"] == {"events": 1, "files": 3}
    assert desk.config_file.read_bytes() == before


def test_the_route_refuses_what_the_save_would(desk: GroupingPreview) -> None:
    """A body the save would refuse is refused here too."""
    for body in (
        b"[]",
        b"{}",
        json.dumps(
            {"merge_gap_hours": -1, "min_event_size": 2, "trip_min_km": 100}
        ).encode(),
    ):
        assert desk.answer(body).status == HTTPStatus.BAD_REQUEST
