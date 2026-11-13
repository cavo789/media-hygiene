"""`people` served by the home server once its faces are found (0600, 0588).

`people` first looks for the faces the cache lacks, with a progress bar in the window of
`mh`: hours on a first run. Past that first run nothing keeps its page apart: the step
*people* opens `/people/` in the home server, which goes on, and the page analyses the
few new photos itself, with their progress (`/api/people`). A first run, or too many new
photos, runs as before (`mh` ends the page, finds them, serves the groups).
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
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp, ApplyOffer
from media_hygiene.review.apply_relay import home_relay
from media_hygiene.review.home_app import HomeApp
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.step_watch import STEP_PATH
from media_hygiene.services.names_file import names_file
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.services.people import PeopleStep, PeopleWork
from media_hygiene.services.people_app_build import PeopleBuild, people_app
from media_hygiene.services.people_files import require_people_index
from media_hygiene.services.prefixed_page import KeptPage, PrefixedPage

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request, Response
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.runtime import Runtime

PEOPLE_PAGE: Final = "/people/"
_WORDS: Final = ("people",)  # the step as `mh menu` gives it, options none
# Followed in the page up to this many: about 3 min at the 0.16 s per photo measured on
# Windows (0583). Beyond, the terminal's progress bar, and its Ctrl+C, as a first run.
MOST_NEW: Final = 1000


def faces_found(runtime: Runtime) -> bool:
    """Tell whether the page can open now: its faces found but for a few new photos.

    Args:
        runtime: Settings, index, cache.

    Returns:
        True with photos analysed and at most `MOST_NEW` left; False otherwise,
        or when `people` could not run here (no index, a read-only cache).
    """
    try:
        require_people_index(runtime)
        if not runtime.persistent(MountKind.CACHE):
            return False
        with PeopleStep(runtime) as step:
            work = step.plan(())
    except MediaHygieneError:
        return False
    return _ready(work)


def _ready(work: PeopleWork) -> bool:
    """Tell whether a run is past its first analysis, with few new photos left.

    Args:
        work: The photos of the run.

    Returns:
        True when the page can show groups and analyse the rest itself.
    """
    return work.new < len(work.photos) and len(work.missing) <= MOST_NEW


def _built(runtime: Runtime, server: HomeServer) -> ApplyingApp:
    """The page's app on the faces of the index, with *Apply now*.

    Args:
        runtime: The server's settings now.
        server: The home server's *Apply now*, end and pool.

    Returns:
        The app.

    Raises:
        MediaHygieneError: Too many faces missing: `people` must run in the terminal.
    """
    with PeopleStep(runtime) as step:
        work = step.plan(())
        if not _ready(work):
            raise MediaHygieneError(
                _("Faces are still to be found: run 'mh people' in the terminal.")
            )
        result = step.result(work)
    offered = server.apply is not None
    build = PeopleBuild(
        server.executor,
        names_file(runtime),
        offered,
        relative=True,
        new=len(work.missing),
        turns=work.turn_only,
    )
    app, aside = people_app(runtime, result, build)
    offer = ApplyOffer(server.apply, lambda: bool(aside.paths()), PageUndo(runtime))
    relay = home_relay(runtime.locations.reports_dir)
    return ApplyingApp(app, ApplyDesk(offer, server.ending, relay))


@dataclass(frozen=True, slots=True)
class PeopleStepDoor:
    """The home page, but its step *people* opens `/people/` past the first run."""

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


def people_here(fresh: FreshRuntime, server: HomeServer) -> PrefixedPage:
    """The people page under `/people/`.

    Args:
        fresh: The server's settings, read again when their files change.
        server: The home server's *Apply now*, end and pool.

    Returns:
        The page.
    """
    return KeptPage(PEOPLE_PAGE, fresh, lambda runtime: _built(runtime, server))


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
