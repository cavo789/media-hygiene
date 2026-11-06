"""Pages served by the home server itself, no restart (0594): quarantine, intruders."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import runs_beside, served_here
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.pages_here import pages_here
from tests.support.cleaning import clean
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_HOST = {"host": "127.0.0.1"}


def _get(page: object, path: str) -> object:
    """One `GET` from the loopback."""
    request = Request("GET", path, _HOST, b"")
    return asyncio.run(page.handle(request))  # type: ignore[attr-defined]


def test_the_quarantine_answers_under_its_prefix(locations: Locations) -> None:
    """The page, then its tiles; the prefix redirects; another host is refused."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    clean(runtime)
    with ThreadPoolExecutor(1) as executor:
        page = pages_here(FreshRuntime(runtime), HomeServer(None, Ending(), executor))[
            0
        ]
        assert page.serves("/quarantine/api/state")
        assert not page.serves("/quarantined")
        assert _get(page, "/quarantine").status is HTTPStatus.SEE_OTHER  # type: ignore[attr-defined]
        assert _get(page, "/quarantine/api/state").status is HTTPStatus.NOT_FOUND  # type: ignore[attr-defined]
        assert _get(page, "/quarantine/").status is HTTPStatus.OK  # type: ignore[attr-defined]
        state = _get(page, "/quarantine/api/state")
        assert state.status is HTTPStatus.OK  # type: ignore[attr-defined]
        assert b'"tiles"' in state.body  # type: ignore[attr-defined]


def test_the_import_page_says_why_it_cannot_open(locations: Locations) -> None:
    """No backup folder: 409 with the sentence, never a traceback."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    with ThreadPoolExecutor(1) as executor:
        page = pages_here(FreshRuntime(runtime), HomeServer(None, Ending(), executor))[
            1
        ]
        answer = _get(page, "/import/")
    assert answer.status is HTTPStatus.CONFLICT  # type: ignore[attr-defined]
    assert b"import" in answer.body  # type: ignore[attr-defined]


def test_the_steps_are_plain_links_and_a_typed_folder_ends_the_server() -> None:
    """The folder's page needs its own mount: never beside the home server."""
    assert served_here(("undo", "--pick")) == "/quarantine/"
    assert served_here(("review", "--intruders")) == "/review/intruders/"
    assert served_here(("import", "--pick")) == "/import/"
    assert not runs_beside(("import", "--pick", r"E:\DCIM"))
    assert runs_beside(("import",))
