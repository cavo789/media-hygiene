"""0694: the page freeing a phone, served by the home server under `/phone/`.

`mh` (in its window, the home server kept up) asks with `.mh-phone-page.json`; the
page is the home server's own: its ticks saved and read back, a reload keeping them,
▶ Slideshow ▾ to the TV, the way home and *Apply now*; its end written for `mh` and
read back: the lines ticked on Delete, none on Leave. The step's state names the page
while `mh` waits.
"""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.apply_api import ApplyStep
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.review.step_files import PHONE_PAGE, WATCH, read_state
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.pages_here import pages_here
from media_hygiene.services.phone_here import PhoneHere
from media_hygiene.services.phone_plan import PhoneCase
from media_hygiene.services.slideshow_selection import TvSlot
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import pytest

    from media_hygiene.services.runtime import Runtime

_LOCAL: Final = {"host": "127.0.0.1:8088", "content-type": "application/json"}
_DATE: Final = "2025-05-12T17:53:43Z"


def _line(case: PhoneCase, path: str, *reason: str) -> str:
    return "\t".join((case.value, path, "100", _DATE, *reason))


_PLAN: Final = (
    _line(PhoneCase.LIBRARY, "Camera/IMG_0.jpg", "C:\\Photos\\IMG_0.jpg"),
    _line(PhoneCase.LIBRARY, "Camera/IMG_1.jpg", "C:\\Photos\\IMG_1.jpg"),
)


class _Phone:
    """The home server's phone page on a runtime, and what reached the TV."""

    def __init__(self, tmp_path: Path, executor: ThreadPoolExecutor) -> None:
        self.runtime: Runtime = make_runtime(make_locations(tmp_path))
        folder = self.runtime.locations.data_dir / "c" / "Photos"
        indexed_photos(self.runtime.locations.index_file, folder, 2)
        self.photos = sorted(folder.iterdir())
        self.shown: list[tuple[Path, ...]] = []
        tv = TvSlot(start=self._show)
        step = ApplyStep(9, "mh clean --decisions decisions.json")
        server = HomeServer(lambda: step, Ending(), executor, tv=tv)
        self.here = PhoneHere(FreshRuntime(self.runtime, every=0), server)
        self.reports = self.runtime.locations.reports_dir

    def _show(self, files: tuple[Path, ...]) -> Response:
        self.shown.append(files)
        return Response(HTTPStatus.OK)

    def ask_mh(self, plan: tuple[str, ...] = _PLAN) -> None:
        """Write the request as `mh` does (a byte order mark, as PowerShell may)."""
        body = {"phone": "Galaxy", "destination": "", "lines": list(plan)}
        (self.reports / WATCH.phone_asked).write_text(
            "\ufeff" + json.dumps(body), encoding="utf-8"
        )

    def call(self, method: str, path: str, body: object = None) -> Response:
        """Ask the page under `/phone`, from the PC."""
        data = b"" if body is None else json.dumps(body).encode()
        request = Request(method, f"/phone{path}", _LOCAL, data)
        return asyncio.run(self.here.handle(request))

    def ended(self) -> object:
        """What the page wrote for `mh`, read from the disk."""
        return json.loads((self.reports / WATCH.phone_ended).read_text("utf-8"))


def _phone(tmp_path: Path) -> Iterator[_Phone]:
    with ThreadPoolExecutor(1) as executor:
        yield _Phone(tmp_path, executor)


def test_without_a_request_the_page_says_how_to_start(tmp_path: Path) -> None:
    """Nothing asked by `mh`: a sentence, never an empty page; no route answers."""
    for phone in _phone(tmp_path):
        page = phone.call("GET", "/")
        assert page.status is HTTPStatus.CONFLICT
        assert b"mh import --phone --free" in page.body
        assert phone.call("GET", "/api/state").status is HTTPStatus.NOT_FOUND
        assert phone.call("GET", "").status is HTTPStatus.SEE_OTHER


def test_served_with_the_slideshow_the_way_home_and_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bar of the other tile pages: ▶ Slideshow ▾, *Apply now*; paths relative."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)  # the home server kept up
    for phone in _phone(tmp_path):
        phone.ask_mh()
        page = phone.call("GET", "/")
        assert page.status is HTTPStatus.OK
        assert b'id="showBar"' in page.body
        assert b'id="applyNow"' in page.body
        assert (
            b'const UNDO_PATH = "api/undo-run"' in page.body
        )  # the toast's Undo (0757)
        assert b'id="mhUndoToast"' in page.body
        assert phone.call("GET", "/api/undo-run").status is HTTPStatus.OK
        assert b'id="homeLink" href="/" data-shared="1"' in page.body
        assert b"const SERVED = true" in page.body
        assert b'"/api/state"' not in page.body  # relative: answered under /phone/
        state = json.loads(phone.call("GET", "/api/state").body)
        assert [tile["name"] for tile in state["tiles"]] == ["IMG_0.jpg", "IMG_1.jpg"]


def test_on_the_tv_shows_the_tiles_chosen(tmp_path: Path) -> None:
    """▶ Slideshow ▾ > On the TV: the home server's slot gets the PC's files."""
    for phone in _phone(tmp_path):
        phone.ask_mh()
        phone.call("GET", "/")
        answer = phone.call("POST", "/api/albums", {"action": "tv", "keys": ["1"]})
        assert answer.status is HTTPStatus.OK
        assert phone.shown == [(phone.photos[1],)]


def test_delete_hands_mh_the_lines_read_back(tmp_path: Path) -> None:
    """A tick saved, a reload keeps it, Delete writes only the ticked lines for `mh`."""
    for phone in _phone(tmp_path):
        phone.ask_mh()
        phone.call("GET", "/")
        untick = {"choices": [{"file": 0, "ticked": False}]}
        assert phone.call("POST", "/api/phone", untick).status is HTTPStatus.OK
        phone.call("GET", "/")  # a reload: the same session
        state = json.loads(phone.call("GET", "/api/state").body)
        assert [tile["ticked"] for tile in state["tiles"]] == [False, True]
        assert read_state(phone.reports) == {"state": "idle", "id": None, "code": None}
        (phone.reports / WATCH.running).write_text('{"id": "a1"}')
        assert read_state(phone.reports)["page"] == PHONE_PAGE
        assert phone.call("POST", "/api/free", {}).status is HTTPStatus.OK
        assert phone.ended() == {"lines": [_PLAN[1]]}
        assert "page" not in read_state(phone.reports)


def test_leave_tells_mh_nothing_leaves(tmp_path: Path) -> None:
    """Leave everything: an empty list, never the home server stopped."""
    for phone in _phone(tmp_path):
        phone.ask_mh()
        phone.call("GET", "/")
        assert phone.call("POST", "/api/stop", {}).status is HTTPStatus.OK
        assert phone.ended() == {"lines": []}
        far = Request("POST", "/phone/api/stop", {"host": "evil.example"}, b"{}")
        assert asyncio.run(phone.here.handle(far)).status is HTTPStatus.FORBIDDEN


def test_a_new_request_opens_a_new_session(tmp_path: Path) -> None:
    """`mh` asked again (another phone run): the former end is forgotten."""
    for phone in _phone(tmp_path):
        phone.ask_mh()
        phone.call("GET", "/")
        phone.call("POST", "/api/stop", {})
        phone.ask_mh(_PLAN[:1])
        phone.call("GET", "/")
        assert not (phone.reports / WATCH.phone_ended).exists()
        state = json.loads(phone.call("GET", "/api/state").body)
        assert len(state["tiles"]) == 1


def test_the_home_server_routes_phone_paths_there(tmp_path: Path) -> None:
    """`/phone/` is one of the pages the home server serves itself."""
    for phone in _phone(tmp_path):
        fresh = FreshRuntime(phone.runtime, every=0)
        server = HomeServer(None, Ending(), ThreadPoolExecutor(1))
        pages = pages_here(fresh, server)
        assert any(page.serves(PHONE_PAGE) for page in pages)
        assert not any(page.serves("/phonebook") for page in pages)
