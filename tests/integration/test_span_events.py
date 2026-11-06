"""0572: the Events tab made from the index, no classify plan: files not sorted yet."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.classify.event_left import read_left
from media_hygiene.index.schema import prepare
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.events_choose import events_get
from media_hygiene.search.events_desk import EventsDesk
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.span_events import SPAN_FILES_PATH, SPAN_PATH, SpanEvents
from media_hygiene.search.span_left import left_answer

if TYPE_CHECKING:
    from media_hygiene.review.events_batch import SortBatchSession

_GAP_HOURS = 18.0
_ROWS = (
    ("/data/c/Phone/a.jpg", "2024:03:30 10:00:00"),
    ("/data/c/Phone/b.jpg", "2024:03:30 23:00:00"),  # 13 h later: the same event
    ("/data/c/Phone/v.mp4", "2024-03-31T08:00:00Z"),  # a video's ISO date
    ("/data/c/Phone/c.jpg", "2024:04:05 12:00:00"),  # days later: another event
    ("/data/c/P/2024/2024-03/Easter/d.jpg", "2024:03:30 11:00:00"),  # sorted
    ("/data/c/Phone/e.jpg", None),  # undated: in no event
)


def _nothing_chosen() -> frozenset[str]:
    """No file set aside.

    Returns:
        None.
    """
    return frozenset()


def _no_plan() -> SortBatchSession:
    """No classify plan: the tab needs none.

    Raises:
        FileNotFoundError: Always.
    """
    raise FileNotFoundError


def _index(index_file: Path) -> None:
    """Write an index of the rows.

    Args:
        index_file: Where.
    """
    with closing(sqlite3.connect(index_file)) as connection:
        prepare(connection)
        connection.executemany(
            "INSERT INTO files (path, size, mtime_ns, media_date) VALUES (?, 1, 1, ?)",
            _ROWS,
        )
        connection.commit()


def _span(search: SearchIndex) -> SpanEvents:
    """The tab's desk over an index.

    Args:
        search: The index.

    Returns:
        It.
    """
    return SpanEvents(
        search, HostPathMapper(Path("/data")), _nothing_chosen, _GAP_HOURS
    )


def test_events_of_the_files_not_sorted_yet(tmp_path: Path) -> None:
    """Grouped by gaps; a file in `YYYY/YYYY-MM/<name>` is never listed."""
    _index(tmp_path / "index.db")
    with SearchIndex.open(tmp_path / "index.db") as search:
        desk = EventsDesk(
            search,
            HostPathMapper(Path("/data")),
            _no_plan,
            _nothing_chosen,
            span=_span(search),
        )
        answer = events_get(desk, f"{SPAN_PATH}..")
        assert answer is not None
        events = json.loads(answer.body)["events"]
        assert [card["files"] for card in events] == [3, 1]
        first = events[0]
        assert first["first"] == "2024-03-30T10:00:00"
        tiles = events_get(desk, f"{SPAN_FILES_PATH}{first['id']}")
        assert tiles is not None
        names = [hit["name"] for hit in json.loads(tiles.body)["hits"]]
        assert names == ["a.jpg", "b.jpg", "v.mp4"]
        assert json.loads(tiles.body)["suggested"]  # the name of its album (0523)
        narrowed = events_get(desk, f"{SPAN_PATH}2024-04-01..2024-04-30")
        assert narrowed is not None
        assert [card["files"] for card in json.loads(narrowed.body)["events"]] == [1]


def test_a_file_sorted_since_leaves_its_event(tmp_path: Path) -> None:
    """Moved into a dated folder by any means: no longer in the event, nor its tiles."""
    _index(tmp_path / "index.db")
    with closing(sqlite3.connect(tmp_path / "index.db")) as connection:
        connection.execute(
            "UPDATE files SET path = '/data/c/P/2024/2024-04/Trip/c.jpg'"
            " WHERE path = '/data/c/Phone/c.jpg'"
        )
        connection.commit()
    with SearchIndex.open(tmp_path / "index.db") as search:
        span = _span(search)
        events = json.loads(span.answer(f"{SPAN_PATH}..").body)["events"]
        assert len(events) == 1
        gone = span.answer(f"{SPAN_FILES_PATH}2024-04-05T12:00:00..2024-04-05T12:00:00")
        assert json.loads(gone.body)["hits"] == []


def test_a_bad_period_is_a_404(tmp_path: Path) -> None:
    """Not a period, or no tab: 404, never another list."""
    _index(tmp_path / "index.db")
    with SearchIndex.open(tmp_path / "index.db") as search:
        span = _span(search)
        assert span.answer(f"{SPAN_PATH}nope").status == HTTPStatus.NOT_FOUND
        assert span.answer(f"{SPAN_FILES_PATH}x..y").status == HTTPStatus.NOT_FOUND
        bare = EventsDesk(
            search, HostPathMapper(Path("/data")), _no_plan, _nothing_chosen
        )
        missing = events_get(bare, f"{SPAN_PATH}..")
        assert missing is not None
        assert missing.status == HTTPStatus.NOT_FOUND


def test_do_not_sort_is_saved_read_back_and_undone(tmp_path: Path) -> None:
    """0574: the event's content ids in events/left.toml, the card says `left`."""
    _index(tmp_path / "index.db")
    with closing(sqlite3.connect(tmp_path / "index.db")) as connection:
        connection.execute("UPDATE files SET full_digest = 'id-' || rowid")
        connection.commit()
    with SearchIndex.open(tmp_path / "index.db") as search:
        span = SpanEvents(
            search, HostPathMapper(Path("/data")), _nothing_chosen, _GAP_HOURS, tmp_path
        )
        first = json.loads(span.answer(f"{SPAN_PATH}..").body)["events"][0]
        assert first["left"] is False
        body = json.dumps({"event": first["id"], "left": True}).encode()
        saved = json.loads(left_answer(span, body).body)
        assert saved["left"] is True
        assert "these 3 files stay" in saved["said"]
        assert read_left(tmp_path) == {"id-1", "id-2", "id-3"}
        events = json.loads(span.answer(f"{SPAN_PATH}..").body)["events"]
        assert [card["left"] for card in events] == [True, False]
        back = json.dumps({"event": first["id"], "left": False}).encode()
        assert json.loads(left_answer(span, back).body)["left"] is False
        assert read_left(tmp_path) == frozenset()


def test_do_not_sort_without_ids_or_tab_is_refused(tmp_path: Path) -> None:
    """Files not hashed yet: 409, nothing written; no settings folder: 404."""
    _index(tmp_path / "index.db")
    with SearchIndex.open(tmp_path / "index.db") as search:
        span = SpanEvents(
            search, HostPathMapper(Path("/data")), _nothing_chosen, _GAP_HOURS, tmp_path
        )
        body = json.dumps(
            {"event": "2024-04-05T12:00:00..2024-04-05T12:00:00", "left": True}
        )
        assert left_answer(span, body.encode()).status == HTTPStatus.CONFLICT
        assert not (tmp_path / "events").exists()
        assert left_answer(_span(search), body.encode()).status == HTTPStatus.NOT_FOUND
        assert left_answer(span, b"{}").status == HTTPStatus.BAD_REQUEST
