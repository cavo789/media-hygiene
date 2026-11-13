"""0600: `people` served by the home server once every face is found."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.apply_api import ApplyStep
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services import people as people_service
from media_hygiene.services import people_here as people_here_module
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.people_here import (
    PeopleStepDoor,
    faces_found,
    people_door,
    people_here,
)
from media_hygiene.services.subject_answers import Answering
from tests.support.faces import FakeRecipe
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_PC: Final = {
    "host": "127.0.0.1:8088",
    "content-type": "application/json",
    "origin": "http://127.0.0.1:8088",
}
_STEP: Final = json.dumps({"number": 4, "command": "mh people"}).encode()


class _Home:
    """The home page: says it answered, so the test sees who did."""

    def __init__(self) -> None:
        self.asked = 0

    async def handle(self, request: Request) -> Response:
        """Count the request and answer 418.

        Args:
            request: Unused.

        Returns:
            418.
        """
        del request
        self.asked += 1
        return Response(HTTPStatus.IM_A_TEAPOT)


def test_people_opens_in_the_home_server_once_every_face_is_found(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Faces missing: the step goes to `mh` as today; all found: `/people/` here."""
    del cli  # the coloured tree, audited
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    runtime = make_runtime(locations)
    home = _Home()
    door = PeopleStepDoor(home, FreshRuntime(runtime))
    step = Request("POST", "/api/step", _PC, _STEP)
    assert asyncio.run(door.handle(step)).status is HTTPStatus.IM_A_TEAPOT
    assert home.asked == 1  # faces missing: the home page hands the step to `mh`
    with PeopleStep(runtime) as people:
        people.find(people.plan(()).missing, Answering(True, NullProgress()))  # noqa: FBT003
    answer = asyncio.run(door.handle(step))
    assert json.loads(answer.body) == {"page": "/people/", "command": "mh people"}
    assert home.asked == 1  # the home server goes on: nothing handed to `mh`
    audit = b'{"number": 2, "command": "mh audit"}'
    assert (
        asyncio.run(door.handle(Request("POST", "/api/step", _PC, audit))).status
        is HTTPStatus.IM_A_TEAPOT
    )
    with ThreadPoolExecutor(1) as executor:
        page = people_here(
            FreshRuntime(runtime),
            HomeServer(lambda: ApplyStep(7, "mh clean"), Ending(), executor),
        )
        assert page.serves("/people/api/groups")
        opened = asyncio.run(page.handle(Request("GET", "/people/", _PC)))
        assert opened.status is HTTPStatus.OK
        assert b'"api/groups"' in opened.body  # relative to `/people/`
        assert b'id="applyNow"' in opened.body  # 0621: the home page's way to apply
        assert b'id="mhUndoToast"' in opened.body
        assert b'"api/undo-run"' in opened.body
        undo = Request("GET", "/people/api/undo-run", _PC)
        assert json.loads(asyncio.run(page.handle(undo)).body) == {"run_id": None}
        groups = asyncio.run(page.handle(Request("GET", "/people/api/groups", _PC)))
        assert groups.status is HTTPStatus.OK


def test_new_photos_open_the_page_which_analyses_them_itself(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0588: past the first run the page opens at once, with what is left to analyse."""
    del cli  # the coloured tree, audited
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    runtime = make_runtime(locations)
    with PeopleStep(runtime) as people:
        missing = people.plan(()).missing
        people.find(missing[:-1], Answering(True, NullProgress()))  # noqa: FBT003
    assert faces_found(runtime)
    home = _Home()
    door = PeopleStepDoor(home, FreshRuntime(runtime))
    answer = asyncio.run(door.handle(Request("POST", "/api/step", _PC, _STEP)))
    assert json.loads(answer.body)["page"] == "/people/"
    assert home.asked == 0
    with ThreadPoolExecutor(1) as executor:
        page = people_here(
            FreshRuntime(runtime), HomeServer(lambda: None, Ending(), executor)
        )
        opened = asyncio.run(page.handle(Request("GET", "/people/", _PC)))
    assert opened.status is HTTPStatus.OK
    assert b"const NEW_PHOTOS = 1;" in opened.body
    assert b'const SCAN_PATH = "/api/people"' in opened.body
    assert b'id="newPhotosStop"' in opened.body


def test_too_many_new_photos_stay_with_the_terminal(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0588: over `MOST_NEW`, the terminal's bar and Ctrl+C, as a first run."""
    del cli  # the coloured tree, audited
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    runtime = make_runtime(locations)
    with PeopleStep(runtime) as people:
        missing = people.plan(()).missing
        people.find(missing[:-1], Answering(True, NullProgress()))  # noqa: FBT003
    monkeypatch.setattr(people_here_module, "MOST_NEW", 0)
    assert not faces_found(runtime)


def test_a_home_that_ends_on_every_step_keeps_its_way() -> None:
    """Not the home page of an `mh` that keeps it up: no door added."""
    home = _Home()
    assert people_door(home, None) is home  # type: ignore[arg-type]


def test_a_turn_only_job_never_counts_as_a_new_photo(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Photos analysed before, their turn not guessed: counted apart (0803)."""
    del cli  # the coloured tree, audited
    monkeypatch.setattr(people_service, "face_recipe", lambda _runtime: FakeRecipe())
    runtime = make_runtime(locations)
    with PeopleStep(runtime) as people:
        people.find(people.plan(()).missing, Answering(True, NullProgress()))  # noqa: FBT003
        people.store.connection.execute("DELETE FROM face_turns")
        work = people.plan(())
    assert work.photos
    assert work.turn_only == len(work.missing) == len(work.photos)
    assert work.new == 0
    assert people_here_module.faces_found(runtime)  # the page still opens
