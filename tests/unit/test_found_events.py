"""The events sorted by hand, found in the index and ticked to remember (0557)."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from datetime import date
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.classify.event_files import read_not_events
from media_hygiene.classify.found_folders import event_folder_of, found_folders, moment
from media_hygiene.classify.own_events import folder_rules
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.errors import MediaHygieneError
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.events_choose import events_get, sort_post
from media_hygiene.search.events_desk import EventsDesk
from media_hygiene.search.found_desk import FOUND_PATH, FoundDesk

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.review.http import Request
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.search.fts import SearchIndex

_GAP = 18.0
_CONFIG = """# mine
[[classify.rules]]
name = "Existing folders"
match = "existing_folder"
"""
_ROWS = (
    ("/data/c/Photos/2019/2019-07/Turin/a.jpg", "2019:07:02 10:00:00", "Apple", "t1"),
    ("/data/c/Photos/2019/2019-07/Turin/b.jpg", "2019:07:02 20:00:00", "Canon", "t2"),
    ("/data/c/Photos/2022/2022-04/Turin/c.jpg", "2022:04:01 09:00:00", None, "t3"),
    ("/data/c/Photos/2022/2022-04/Restaurant/d.jpg", "2022-04-01T12:00:00", None, "r1"),
    ("/data/c/Photos/2022/2022-04/Party/e.jpg", "2022:04:01 21:00:00", None, "p1"),
    (
        "/data/c/Photos/2010/2010-01/Prints jan10/f.jpg",
        "2010:01:01 10:00:00",
        None,
        "b1",
    ),
    (
        "/data/c/Photos/2010/2010-01/Prints jan10/g.jpg",
        "2010:01:20 10:00:00",
        None,
        "b2",
    ),
    ("/data/c/Photos/2010/2010-01/h.jpg", "2010:01:20 10:00:00", None, "n1"),
    ("/data/c/Photos/2010/2010-01/2010-01-05/i.jpg", "2010:01:05 10:00:00", None, "n2"),
)


@pytest.fixture(name="opened")
def opened_fixture() -> Iterator[list[sqlite3.Connection]]:
    """Every index a test opens, closed after it."""
    held: list[sqlite3.Connection] = []
    yield held
    for connection in held:
        connection.close()


def _index(
    held: list[sqlite3.Connection],
    rows: tuple[tuple[str, str, str | None, str], ...] = _ROWS,
) -> sqlite3.Connection:
    """An index holding the rows."""
    connection = sqlite3.connect(":memory:")
    held.append(connection)
    connection.execute(
        "CREATE TABLE files (path TEXT, media_date TEXT, camera TEXT, full_digest TEXT)"
    )
    connection.executemany("INSERT INTO files VALUES (?, ?, ?, ?)", rows)
    return connection


def _desk(tmp_path: Path, connection: sqlite3.Connection) -> FoundDesk:
    """The desk, on an empty config.toml."""
    config = tmp_path / "config.toml"
    if not config.exists():
        config.write_text(_CONFIG, encoding="utf-8")
    rules = folder_rules(ClassifySettings(), ())
    return FoundDesk(connection, HostPathMapper(Path("/data")), config, (rules, _GAP))


def _state(desk: FoundDesk) -> dict[str, list[dict[str, object]]]:
    """The list as the page reads it."""
    state: dict[str, list[dict[str, object]]] = json.loads(desk.state().body)
    return state


def test_event_folder_and_moment() -> None:
    """The `YYYY/YYYY-MM/<name>` folder of a file, below any root; EXIF, ISO dates."""
    assert event_folder_of("/data/c/x/2019/2019-07/Turin/sub/a.jpg") == (
        "/data/c/x/2019/2019-07/Turin",
        "Turin",
    )
    assert event_folder_of("/data/c/x/2019/2019-07/a.jpg") is None
    assert moment("2019:07:02 10:00:00") == moment("2019-07-02T10:00:00Z")
    assert moment("garbage") is None


def test_folders_found_in_the_index(opened: list[sqlite3.Connection]) -> None:
    """Same name in two years: two folders; dates folders skipped; a batch told.

    Args:
        opened: The indexes opened, closed after.
    """
    found = found_folders(_index(opened), folder_rules(ClassifySettings(), ()), _GAP)
    by_folder = {f.folder.rsplit("/", 2)[-2] + "/" + f.name: f for f in found}
    assert set(by_folder) == {
        "2019-07/Turin",
        "2022-04/Turin",
        "2022-04/Restaurant",
        "2022-04/Party",
        "2010-01/Prints jan10",
    }
    turin = by_folder["2019-07/Turin"]
    assert (turin.days, turin.devices, len(turin.keys)) == (
        (date(2019, 7, 2),),
        ("Apple", "Canon"),
        2,
    )
    assert not by_folder["2010-01/Prints jan10"].one_moment


def test_ticked_become_events_unticked_never_again(
    tmp_path: Path, opened: list[sqlite3.Connection]
) -> None:
    """Ticked: written (two Turins apart); unticked: remembered, foldable back."""
    connection = _index(opened)
    desk = _desk(tmp_path, connection)
    state = _state(desk)
    names = sorted(str(item["name"]) for item in state["proposed"])
    assert names == ["Party", "Restaurant", "Turin", "Turin"]
    assert [item["name"] for item in state["batches"]] == ["Prints jan10"]
    folders = {str(item["folder"]): item for item in state["proposed"]}
    restaurant = next(f for f in folders if f.endswith("Restaurant"))
    ticked = [f for f in folders if f != restaurant and not f.endswith("Party")]
    body = json.dumps({"ticked": ticked, "unticked": [restaurant]}).encode()
    answer = json.loads(desk.confirm(body).body)
    assert [item["name"] for item in answer["proposed"]] == ["Party"]
    assert [item["name"] for item in answer["not_events"]] == ["Restaurant"]
    assert read_not_events(tmp_path) == {"r1"}
    events = {
        rule.name: rule.dates
        for rule in read_rules(tmp_path / "config.toml")
        if rule.match is RuleMatch.DATE_RANGE
    }
    assert events == {
        "Turin": "2019-07-02..2019-07-02",
        "Turin (April 2022)": "2022-04-01..2022-04-01",
    }
    # Ticked back: an event, no longer refused.
    again = json.dumps({"ticked": [restaurant]}).encode()
    answer = json.loads(desk.confirm(again).body)
    assert answer["not_events"] == []
    assert read_not_events(tmp_path) == frozenset()


def test_a_renamed_folder_is_still_known(
    tmp_path: Path, opened: list[sqlite3.Connection]
) -> None:
    """Renamed in Explorer after acceptance: its event (name + period) holds it."""
    desk = _desk(tmp_path, _index(opened, _ROWS[:2]))
    folder = str(_state(desk)["proposed"][0]["folder"])
    desk.confirm(json.dumps({"ticked": [folder]}).encode())
    renamed = tuple(
        (path.replace("/Turin/", "/Turin with Tom/"), day, place, kind)
        for path, day, place, kind in _ROWS[:2]
    )
    assert _state(_desk(tmp_path, _index(opened, renamed)))["proposed"] == []


def test_a_bad_body_is_refused(
    tmp_path: Path, opened: list[sqlite3.Connection]
) -> None:
    """Anything else than the two lists: 400."""
    desk = _desk(tmp_path, _index(opened))
    assert desk.confirm(b'{"other": 1}').status is HTTPStatus.BAD_REQUEST


def test_the_routes_answer_without_a_plan(
    tmp_path: Path, opened: list[sqlite3.Connection]
) -> None:
    """GET and POST /api/found-events need no classify plan; none without a desk."""
    found = _desk(tmp_path, _index(opened))
    desk = EventsDesk(
        cast("SearchIndex", None), found.mapper, _no_plan, frozenset, found=found
    )
    assert events_get(desk, FOUND_PATH) is not None
    request = cast("Request", SimpleNamespace(path=FOUND_PATH, body=b"{}"))
    answer = asyncio.run(sort_post(desk, request))
    assert answer.status is HTTPStatus.OK
    bare = EventsDesk(cast("SearchIndex", None), found.mapper, _no_plan, frozenset)
    missing = events_get(bare, FOUND_PATH)
    assert missing is not None
    assert missing.status is HTTPStatus.NOT_FOUND
    assert asyncio.run(sort_post(bare, request)).status is HTTPStatus.NOT_FOUND


def _no_plan() -> SortBatchSession:
    """No classify plan to read."""
    said = "no plan"
    raise MediaHygieneError(said)
