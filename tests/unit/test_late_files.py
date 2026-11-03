"""Photos arriving later in an event's days: ranked by camera, refusable (0558)."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.classify.event_files import read_refused
from media_hygiene.classify.late_files import Likely, late_files, refused_by_event
from media_hygiene.classify.rules.devices import unrefused
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.events_choose import events_get, sort_post
from media_hygiene.search.events_desk import EventsDesk
from media_hygiene.search.late_desk import LATE_PATH, LATE_REFUSE_PATH, LateDesk

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.review.events_batch import SortBatchSession
    from media_hygiene.review.http import Request
    from media_hygiene.search.fts import SearchIndex


def _no_plan() -> SortBatchSession:
    """The Events view's opener with no classify plan (the late list needs none)."""
    raise FileNotFoundError


_CONFIG = """# mine
[[classify.rules]]
name = "Easter"
match = "date_range"
category = "Easter"
dates = "2024-03-30..2024-04-01"
devices = ["Apple iPhone 12"]

[[classify.rules]]
name = "Wedding"
match = "date_range"
category = "Wedding"
dates = "2024-03-31..2024-03-31"
devices = ["Canon EOS"]
"""
_ROWS = (
    (
        "/data/c/P/2024/2024-03/Easter/a.jpg",
        "2024:03:30 10:00:00",
        "Apple iPhone 12",
        "e1",
    ),
    ("/data/c/Phone/b.jpg", "2024:03:30 11:00:00", "Apple iPhone 12", "l1"),
    ("/data/c/Phone/c.jpg", "2024:03:31 11:00:00", "Samsung S21", "l2"),
    ("/data/c/Stick/d.jpg", "2024:03:31 12:00:00", "Canon EOS", "l3"),
    ("/data/c/Stick/e.jpg", "2024:04:01 12:00:00", None, "l4"),
    ("/data/c/Stick/f.jpg", "2024:05:01 12:00:00", "Apple iPhone 12", "x1"),
)


@pytest.fixture(name="connection")
def connection_fixture() -> Iterator[sqlite3.Connection]:
    """An index holding the rows, closed after the test."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE files (path TEXT, media_date TEXT, camera TEXT, full_digest TEXT)"
    )
    connection.executemany("INSERT INTO files VALUES (?, ?, ?, ?)", _ROWS)
    yield connection
    connection.close()


def _desk(tmp_path: Path, connection: sqlite3.Connection) -> LateDesk:
    """The desk, on the config.toml of two events."""
    config = tmp_path / "config.toml"
    if not config.exists():
        config.write_text(_CONFIG, encoding="utf-8")
    index = cast("SearchIndex", SimpleNamespace(connection=connection))
    return LateDesk(index, HostPathMapper(Path("/data")), config, frozenset)


def test_late_files_ranked_by_camera(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """Own camera probably, another event's camera there, none asked; folders skipped.

    Args:
        tmp_path: Where config.toml goes.
        connection: The index.
    """
    desk = _desk(tmp_path, connection)
    rules = read_rules(desk.config_file)
    found = {event.rule.name: event for event in late_files(connection, rules, {})}
    easter = {file.digest: file for file in found["Easter"].files}
    assert set(easter) == {"l1", "l2", "l3", "l4"}  # neither its folder nor May
    assert easter["l1"].likely is Likely.PROBABLY
    assert easter["l2"].likely is Likely.ELSEWHERE
    assert easter["l3"].likely is Likely.OTHER
    assert easter["l3"].other == "Wedding"
    assert easter["l4"].likely is Likely.ASK
    wedding = {file.digest: file.likely for file in found["Wedding"].files}
    assert wedding == {"l2": Likely.ELSEWHERE, "l3": Likely.PROBABLY}
    assert not late_files(
        connection,
        rules,
        {
            "Easter": frozenset({"l1", "l2", "l3", "l4"}),
            "Wedding": frozenset({"l2", "l3"}),
        },
    )


def test_refused_files_written_read_back_and_never_proposed(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """A refusal goes to events/<start>-<name>.toml, linked; the list forgets it.

    Args:
        tmp_path: Where config.toml goes.
        connection: The index.
    """
    desk = _desk(tmp_path, connection)
    keys = [
        row[0]
        for row in connection.execute(
            "SELECT rowid FROM files WHERE full_digest IN ('l2', 'l4')"
        )
    ]
    answer = desk.refuse(json.dumps({"event": "Easter", "keys": keys}).encode())
    view = json.loads(answer.body)
    assert "2 photos refused" in view["said"]
    easter = next(item for item in view["events"] if item["id"] == "Easter")
    assert easter["total"] == 2
    assert easter["page"] == "/events?late=Easter"
    rule = next(r for r in read_rules(desk.config_file) if r.name == "Easter")
    assert rule.file == "events/2024-03-30-Easter.toml"
    assert read_refused(tmp_path, rule) == {"l2", "l4"}
    assert refused_by_event(tmp_path, read_rules(desk.config_file)) == {
        "Easter": frozenset({"l2", "l4"})
    }
    assert desk.refuse(b"{}").status is HTTPStatus.BAD_REQUEST
    unknown = json.dumps({"event": "Nope", "keys": [1]}).encode()
    assert desk.refuse(unknown).status is HTTPStatus.BAD_REQUEST


def test_routes_of_the_events_view(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """GET the list, POST a refusal, through the Events view; 404 without a desk.

    Args:
        tmp_path: Where config.toml goes.
        connection: The index.
    """
    late = _desk(tmp_path, connection)
    desk = EventsDesk(late.index, late.mapper, _no_plan, frozenset, late=late)
    listed = events_get(desk, LATE_PATH)
    assert listed is not None
    assert len(json.loads(listed.body)["events"]) == 2
    request = cast(
        "Request",
        SimpleNamespace(
            path=LATE_REFUSE_PATH, body=b'{"event": "Easter", "keys": [2]}'
        ),
    )
    answer = asyncio.run(sort_post(desk, request))
    assert "1 photo refused" in json.loads(answer.body)["said"]
    bare = EventsDesk(late.index, late.mapper, _no_plan, frozenset)
    missing = events_get(bare, f"{LATE_PATH}/Easter")
    assert missing is not None
    assert missing.status is HTTPStatus.NOT_FOUND
    assert asyncio.run(sort_post(bare, request)).status is HTTPStatus.NOT_FOUND


def test_classify_skips_refused_files() -> None:
    """A refused file is never the event's again; others still are."""
    taken = unrefused(frozenset({"r"}), lambda _file: True)
    refused = cast("MediaInput", SimpleNamespace(digest="r"))
    kept = cast("MediaInput", SimpleNamespace(digest="k"))
    assert not taken(refused)
    assert taken(kept)
    always = unrefused(frozenset(), lambda _file: True)
    assert always(refused)


def test_an_unreadable_event_file_refuses_nothing(tmp_path: Path) -> None:
    """A linked file gone: classify still runs, nothing refused.

    Args:
        tmp_path: Where config.toml goes.
    """
    rule = ClassifyRule(
        name="Gone",
        match=RuleMatch.DATE_RANGE,
        category="Gone",
        dates="2024-01-01..2024-01-02",
        file="events/gone.toml",
    )
    assert not refused_by_event(tmp_path, [rule])


def test_an_event_whose_late_files_are_all_set_aside_is_not_proposed(
    tmp_path: Path, connection: sqlite3.Connection
) -> None:
    """A file set aside is a soft delete: never a late file, its event dropped (0518).

    Args:
        tmp_path: Where config.toml goes.
        connection: The index.
    """
    shown = _desk(tmp_path, connection)
    before = {item["id"]: item for item in json.loads(shown.state().body)["events"]}
    assert before["Wedding"]["total"] == 2
    aside = frozenset({r"C:\Stick\d.jpg", r"C:\Phone\c.jpg"})
    desk = LateDesk(shown.index, shown.mapper, shown.config_file, lambda: aside)
    after = {item["id"]: item for item in json.loads(desk.state().body)["events"]}
    assert "Wedding" not in after
    assert after["Easter"]["total"] == before["Easter"]["total"] - 2
