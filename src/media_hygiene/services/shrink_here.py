"""`/shrink/`: the page of `shrink --try` in the home server, which owns the try (0599).

The first `GET` opens the try; every path under the prefix goes to its app, the prefix
taken off. The page says it is alive on `api/alive`: once no tab shows it, the try
closes and its drafts go, the server staying up. *Lighten* hands the drafts over to a
step `mh` runs beside the server (`shrink_handed`), the page having asked.
"""

from __future__ import annotations

import asyncio
import dataclasses
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ExitCode
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Response, is_local
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.presence import PRESENCE_PATH, Presence, presence_response
from media_hygiene.review.served_more import SHRINK_PAGE
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.shrink_app import ShrinkDesk, ShrinkTryApp
from media_hygiene.review.step_watch import busy, keep_step, keeps_server
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.shrink_handed import (
    CHOSEN_WORDS,
    hand_over,
    opened_here,
)
from media_hygiene.services.shrink_page import try_page

if TYPE_CHECKING:
    import contextlib

    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.shrink_try import Trial

_PREFIX: Final = SHRINK_PAGE.removesuffix("/")


@dataclass(frozen=True, slots=True)
class _Open:
    """One try open in the server."""

    trial: Trial
    stack: contextlib.ExitStack
    app: ShrinkTryApp
    ending: Ending
    presence: Presence


class ShrinkHere:
    """The page under its prefix, and the one try it may hold."""

    def __init__(self, fresh: FreshRuntime) -> None:
        """Start without a try.

        Args:
            fresh: The server's settings, read again when their files change.
        """
        self._fresh = fresh
        self._open: _Open | None = None
        self._guard = asyncio.Lock()
        self._watchers: set[asyncio.Task[None]] = set()

    @staticmethod
    def serves(path: str) -> bool:
        """Tell whether a path is this page's.

        Args:
            path: The request's path.

        Returns:
            True for the prefix and under it.
        """
        return path == _PREFIX or path.startswith(SHRINK_PAGE)

    def close(self) -> None:
        """The server ends: remove the drafts of the try still open."""
        opened, self._open = self._open, None
        if opened is not None:
            opened.stack.close()

    async def handle(self, request: Request) -> Response:
        """Answer a request from the PC.

        Args:
            request: The request.

        Returns:
            The response; 403 off the PC's door, 409 with the sentence when the try
            cannot open, 404 under the prefix without a try.
        """
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        path = request.path.removeprefix(_PREFIX)
        if not path:
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {SHRINK_PAGE}",))
        if path == PRESENCE_PATH and request.method == "POST":
            return await self._alive(request)
        if path == PAGE_PATH and request.method == "GET":
            try:
                await self._ensure_open()
            except MediaHygieneError as exc:
                return Response(HTTPStatus.CONFLICT, str(exc).encode())
        if self._open is None:
            return Response(HTTPStatus.NOT_FOUND)
        return await self._open.app.handle(dataclasses.replace(request, path=path))

    async def _alive(self, request: Request) -> Response:
        """A tab spoke: the try's presence hears it.

        Args:
            request: `POST api/alive`.

        Returns:
            200, also once the try is over.
        """
        if self._open is not None:
            return await presence_response(self._open.presence, request)
        return refused_post(request) or json_response(HTTPStatus.OK, {})

    async def _ensure_open(self) -> None:
        """Open the try unless one is open; a tab showing it starts the count."""
        async with self._guard:
            if self._open is None:
                runtime = self._fresh.runtime()
                stack, trial = await asyncio.to_thread(opened_here, runtime)
                ending = Ending()
                desk = ShrinkDesk(trial, runtime.mapper, ending, self._hand)
                self._open = _Open(
                    trial,
                    stack,
                    ShrinkTryApp(try_page(), desk),
                    ending,
                    Presence(ending, ExitCode.PAGE_CLOSED),
                )
                watcher = asyncio.create_task(self._closing(self._open))
                self._watchers.add(watcher)
                watcher.add_done_callback(self._watchers.discard)
            self._open.presence.seen(leaving=False)

    async def _closing(self, opened: _Open) -> None:
        """Once no tab shows the page, close its try: the drafts go.

        Args:
            opened: The try; another one by then is left alone.
        """
        await opened.ending.wait()
        async with self._guard:
            if self._open is opened:
                self._open = None
                await asyncio.to_thread(opened.stack.close)

    async def _hand(self) -> Response:
        """Hand the videos chosen to `mh`: the server and this page stay.

        Returns:
            The step to follow; 409 when `mh` cannot take it, the try still open.
        """
        folder = self._fresh.runtime().locations.reports_dir
        if not keeps_server():
            message = _("This mh does not run the steps of the page: type the command.")
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        refused = busy(folder)
        if refused is not None:
            return refused
        async with self._guard:
            opened, self._open = self._open, None
            if opened is not None:
                await asyncio.to_thread(hand_over, opened.trial)
                await asyncio.to_thread(opened.stack.close)
        command = " ".join((LAUNCHER_FUNCTION, *CHOSEN_WORDS))
        return await keep_step(folder, CHOSEN_WORDS, command)
