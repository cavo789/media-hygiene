"""0455: a folder or a month chosen on a paired phone, shown on the TV."""

from __future__ import annotations

import asyncio
import contextlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services import slideshow_choices, slideshow_here
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.slideshow_here import SlideshowHere
from media_hygiene.share.album_api import MAX_ADDED
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_HOST: Final = {"host": "127.0.0.1:8088", "content-type": "application/json"}
_DATES: Final = ("2025:11:03 10:00:00", "2025:11:30 10:00:00", "2025:12:01 10:00:00")


@pytest.fixture
def here(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[SlideshowHere]:
    """The home slideshow over Trip (3 dated), Home (2), and a folder outside."""
    runtime = make_runtime(make_locations(tmp_path))
    data = runtime.locations.data_dir
    index = tmp_path / "index.sqlite"
    indexed_photos(index, data / "c" / "Trip", len(_DATES))
    with closing(sqlite3.connect(index)) as connection:
        for number, when in enumerate(_DATES, start=1):
            connection.execute(
                "UPDATE files SET media_date = ? WHERE rowid = ?", (when, number)
            )
        for name in ("a.jpg", "b.jpg"):
            path = data / "c" / "Home" / name
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns) VALUES (?, 1, 1)",
                (str(path),),
            )
        connection.execute(
            "INSERT INTO files (path, size, mtime_ns) VALUES (?, 1, 1)",
            (str(tmp_path / "elsewhere" / "x.jpg"),),
        )
        connection.commit()

    @contextlib.contextmanager
    def opened(_runtime: Runtime, *, words: bool) -> Iterator[SearchIndex]:
        assert not words
        with SearchIndex.open(index) as search:
            yield search

    monkeypatch.setattr(slideshow_here, "open_search", opened)
    with ThreadPoolExecutor(1) as executor:
        built = SlideshowHere(
            FreshRuntime(runtime), HomeServer(None, Ending(), executor)
        )
        yield built
        built.close()


def _ask(here: SlideshowHere, request: Request) -> Response:
    return asyncio.run(here.handle(request))


def _choose(here: SlideshowHere, body: dict[str, str]) -> Response:
    payload = json.dumps(body).encode()
    return _ask(here, Request("POST", "/slideshow/choose", _HOST, payload))


def _shown(here: SlideshowHere) -> list[int]:
    answer = _ask(here, Request("GET", "/slideshow/api/slides", _HOST))
    return [slide["key"] for slide in json.loads(answer.body)["slides"]]


def test_the_choices_list_the_folders_analysed_and_the_months(
    here: SlideshowHere,
) -> None:
    """Two folders under the data mount (not the one outside), months newest first."""
    lists = json.loads(_ask(here, Request("GET", "/slideshow/choices", _HOST)).body)
    assert [name.rsplit("\\", 1)[-1] for name in lists["folders"]] == ["Home", "Trip"]
    assert lists["months"] == ["2025-12", "2025-11"]


def test_a_folder_shows_exactly_its_files(here: SlideshowHere) -> None:
    """Trip: its three photos, oldest first; the remote's page."""
    lists = json.loads(_ask(here, Request("GET", "/slideshow/choices", _HOST)).body)
    trip = next(name for name in lists["folders"] if name.endswith("Trip"))
    answer = _choose(here, {"folder": trip})
    assert answer.status is HTTPStatus.OK
    assert json.loads(answer.body)["page"] == "/slideshow/"
    assert _shown(here) == [1, 2, 3]


def test_a_month_shows_exactly_its_files(here: SlideshowHere) -> None:
    """November 2025: the two photos dated in it."""
    answer = _choose(here, {"first": "2025-11-01", "last": "2025-11-30"})
    assert answer.status is HTTPStatus.OK
    assert _shown(here) == [1, 2]


@pytest.mark.parametrize("folder", ["/etc", "C:\\Windows", "../../etc"])
def test_a_folder_not_listed_is_refused(here: SlideshowHere, folder: str) -> None:
    """A path the index does not list under the folders analysed: a line, no show."""
    answer = _choose(here, {"folder": folder})
    assert answer.status is HTTPStatus.CONFLICT
    assert json.loads(answer.body)["error"]
    assert here.app is None


def test_a_period_without_photos_is_refused(here: SlideshowHere) -> None:
    """January 2020: nothing taken, a line, no show."""
    answer = _choose(here, {"first": "2020-01-01", "last": "2020-01-31"})
    assert answer.status is HTTPStatus.CONFLICT
    assert json.loads(answer.body)["error"]
    assert here.app is None


@pytest.mark.parametrize(
    "body", ['{"folder": 3}', "not json", '{"path": "/etc"}', "{}"]
)
def test_a_bad_request_is_refused(here: SlideshowHere, body: str) -> None:
    """Anything but a folder or days: 400."""
    request = Request("POST", "/slideshow/choose", _HOST, body.encode())
    assert _ask(here, request).status is HTTPStatus.BAD_REQUEST


def test_a_form_post_is_refused(here: SlideshowHere) -> None:
    """JSON only."""
    headers = {"host": "127.0.0.1:8088", "content-type": "text/plain"}
    request = Request("POST", "/slideshow/choose", headers, b"{}")
    assert _ask(here, request).status is HTTPStatus.UNSUPPORTED_MEDIA_TYPE


def test_more_files_than_the_cap_are_refused(
    here: SlideshowHere, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Over the cap: the album's message, no show."""
    monkeypatch.setattr(
        slideshow_choices,
        "too_many",
        lambda files: (
            Response(HTTPStatus.CONFLICT, str(MAX_ADDED + 1).encode())
            if files
            else None
        ),
    )
    answer = _choose(here, {"first": "2025-11-01", "last": "2025-12-31"})
    assert answer.status is HTTPStatus.CONFLICT
    assert here.app is None
