"""`people` served by the home server once every face is found (0600).

`people` first looks for the faces the cache lacks, with a progress bar in the window of
`mh`: hours on a first run. With none left to find, nothing keeps its page apart: the
step *people* then opens `/people/` in the home server, which goes on. With faces
missing, the step runs as before (`mh` ends the page, finds them, serves the groups).
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.home_app import HomeApp
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.step_watch import STEP_PATH
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.people import PeopleStep
from media_hygiene.services.people_app_build import PeopleBuild, people_app
from media_hygiene.services.people_files import require_people_index
from media_hygiene.services.people_page import names_file
from media_hygiene.services.prefixed_page import PrefixedPage

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.people.app import PeopleApp
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request, Response
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.runtime import Runtime

PEOPLE_PAGE: Final = "/people/"
_WORDS: Final = ("people",)  # the step as `mh menu` gives it, options none


def faces_found(runtime: Runtime) -> bool:
    """Tell whether every photo of the index had its faces looked for.

    Args:
        runtime: Settings, index, cache.

    Returns:
        True with photos and none left to analyse; False otherwise, or when
        `people` could not run here (no index, a read-only cache).
    """
    try:
        require_people_index(runtime)
        if not runtime.persistent(MountKind.CACHE):
            return False
        with PeopleStep(runtime) as step:
            work = step.plan(())
    except MediaHygieneError:
        return False
    return bool(work.photos) and not work.missing


def _built(runtime: Runtime, executor: Executor) -> PeopleApp:
    """The page's app on the faces of the index, none left to find.

    Args:
        runtime: The server's settings now.
        executor: The worker pool.

    Returns:
        The app.

    Raises:
        MediaHygieneError: Faces are missing: `people` must run in the terminal.
    """
    with PeopleStep(runtime) as step:
        work = step.plan(())
        if not work.photos or work.missing:
            raise MediaHygieneError(
                _("Faces are still to be found: run 'mh people' in the terminal.")
            )
        result = step.result(work)
    build = PeopleBuild(executor, names_file(runtime), relative=True)
    return people_app(runtime, result, build)[0]


@dataclass(frozen=True, slots=True)
class PeopleStepDoor:
    """The home page, but its step *people* opens `/people/` when no face is missing."""

    home: Handling
    fresh: FreshRuntime

    async def handle(self, request: Request) -> Response:
        """Answer the step *people* with its page here; anything else, the home page.

        Args:
            request: The request.

        Returns:
            `{"page": "/people/", "command": …}`, or the home page's answer.
        """
        if request.path != STEP_PATH or request.method != "POST":
            return await self.home.handle(request)
        if refused_post(request) is not None:
            return await self.home.handle(request)
        try:
            command = str(json.loads(request.body).get("command", ""))
        except ValueError, AttributeError:
            return await self.home.handle(request)
        words = tuple(command.split())
        if words[:1] == (LAUNCHER_FUNCTION,):
            words = words[1:]
        runtime = self.fresh.runtime()
        if words != _WORDS or not await asyncio.to_thread(faces_found, runtime):
            return await self.home.handle(request)
        return json_response(HTTPStatus.OK, {"page": PEOPLE_PAGE, "command": command})


def people_here(fresh: FreshRuntime, executor: Executor) -> PrefixedPage:
    """The people page under `/people/`.

    Args:
        fresh: The server's settings, read again when their files change.
        executor: The worker pool.

    Returns:
        The page.
    """
    return PrefixedPage(PEOPLE_PAGE, fresh, lambda runtime: _built(runtime, executor))


def people_door(home: Handling, fresh: FreshRuntime) -> Handling:
    """The home page, its step *people* answered here when `mh` keeps the server up.

    Args:
        home: The home page's app.
        fresh: The server's settings.

    Returns:
        The door; the home page itself when `mh` ends the server on every step.
    """
    keeps = isinstance(home, HomeApp) and home.keeps
    return PeopleStepDoor(home, fresh) if keeps else home
