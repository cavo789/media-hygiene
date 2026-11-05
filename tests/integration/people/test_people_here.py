"""0600: `people` served by the home server once every face is found."""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Request, Response
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services import people as people_service
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.people_here import PeopleStepDoor, people_door, people_here
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
    other = Request("POST", "/api/step", _PC, b'{"number": 2, "command": "mh audit"}')
    assert asyncio.run(door.handle(other)).status is HTTPStatus.IM_A_TEAPOT
    with ThreadPoolExecutor(1) as executor:
        page = people_here(FreshRuntime(runtime), executor)
        assert page.serves("/people/api/groups")
        opened = asyncio.run(page.handle(Request("GET", "/people/", _PC)))
        assert opened.status is HTTPStatus.OK
        assert b'"api/groups"' in opened.body  # relative to `/people/`
        groups = asyncio.run(page.handle(Request("GET", "/people/api/groups", _PC)))
        assert groups.status is HTTPStatus.OK


def test_a_home_that_ends_on_every_step_keeps_its_way() -> None:
    """Not the home page of an `mh` that keeps it up: no door added."""
    home = _Home()
    assert people_door(home, None) is home  # type: ignore[arg-type]
