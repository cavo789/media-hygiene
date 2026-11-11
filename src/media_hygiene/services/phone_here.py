r"""The page freeing a phone, served by the home server under `/phone/` (0694).

Started from the home page, `mh import --phone --free` runs in the window of `mh`
while the home server stays up (`step_watch`): instead of a server of its own, `mh`
writes the plan's lines in `.mh-phone-page.json` of the reports folder, the home page's
tab follows the step there (`GET /api/step` says `page`), and the page writes
`.mh-phone-ended.json` when it ends: the files ticked, read back from the decisions
file, on "Delete from the phone"; none on "Leave everything". The file is read back
before the page says so; `mh` deletes only the lines it holds. The session is opened
again only when `mh` wrote another request: a reload keeps the ticks. The typed
`mh import --phone --free` keeps its own server (`phone_review`).
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.ending import STOP_PATH
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.phone_app import FREE_PATH
from media_hygiene.review.serving import json_response
from media_hygiene.review.step_files import PHONE_PAGE, WATCH
from media_hygiene.services.phone_free import read_ticked
from media_hygiene.services.phone_here_parts import (
    ENCODING,
    leave,
    not_told,
    phone_here_app,
    write_ended,
)
from media_hygiene.services.phone_opening import open_phone_session

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.apply_api import ApplyingApp
    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.phone_opening import PhoneOpened

_PREFIX: Final = PHONE_PAGE.removesuffix("/")


class PhoneHere:
    """The page under `/phone/`: opened on `mh`'s request, its end written for `mh`."""

    def __init__(self, fresh: FreshRuntime, server: HomeServer) -> None:
        """Remember how to open it.

        Args:
            fresh: The server's settings, read again when their files change.
            server: The home server's *Apply now*, end, pool and TV.
        """
        self._fresh = fresh
        self._server = server
        self._asked: tuple[int, int] | None = None  # the request opened: its stat
        self._opened: PhoneOpened | None = None
        self._app: ApplyingApp | None = None
        self._folder: Path | None = None

    def serves(self, path: str) -> bool:  # the router's protocol
        """Tell whether a path is this page's.

        Args:
            path: The request's path.

        Returns:
            True for the prefix and every path under it.
        """
        return path == _PREFIX or path.startswith(PHONE_PAGE)

    async def handle(self, request: Request) -> Response:
        """Answer a path under `/phone/`, the prefix taken off.

        Args:
            request: The request.

        Returns:
            The response; 409 with the sentence while `mh` asked nothing.
        """
        path = request.path.removeprefix(_PREFIX)
        if not path:
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {PHONE_PAGE}",))
        if path == PAGE_PATH and request.method == "GET":
            said = await self._opening()
            if said:
                return Response(HTTPStatus.CONFLICT, said.encode(), ContentType.TEXT)
        if self._app is None or self._opened is None or self._folder is None:
            return Response(HTTPStatus.NOT_FOUND)
        inner = dataclasses.replace(request, path=path)
        if path == STOP_PATH:
            return await leave(inner, self._folder)
        answer = await self._app.handle(inner)
        if path != FREE_PATH or answer.status != HTTPStatus.OK:
            return answer
        return await self._freed(answer, self._opened, self._folder)

    @staticmethod
    async def _freed(answer: Response, opened: PhoneOpened, folder: Path) -> Response:
        """After "Delete from the phone": the lines ticked written for `mh`, read back.

        Args:
            answer: The page's answer to `POST /api/free`.
            opened: The session.
            folder: The reports folder.

        Returns:
            The answer; 409 when `mh` could not be told.
        """
        session = opened.session
        lines = session.ticked_lines() if session.freeing else ()
        if lines and not await asyncio.to_thread(write_ended, folder, lines):
            return json_response(HTTPStatus.CONFLICT, {"error": not_told()})
        return answer

    async def _opening(self) -> str:
        """Open the session `mh` asked for, off the server's loop.

        Returns:
            Empty once open; else why the page cannot open.
        """
        try:
            return await asyncio.to_thread(self._open)
        except MediaHygieneError as exc:
            return str(exc)

    def _open(self) -> str:
        """Open the session `mh` asked for, unless it is the one already open.

        Returns:
            Empty once open; else why the page cannot open.
        """
        runtime = self._fresh.runtime()
        folder = runtime.locations.reports_dir
        asked = folder / WATCH.phone_asked
        try:
            stat = asked.stat()
            text = asked.read_text(ENCODING)
        except OSError:
            self._app = None
            return _(
                "No phone waits here: choose Make room on the phone on the home page, "
                "or type mh import --phone --free."
            )
        seen = (stat.st_mtime_ns, stat.st_size)
        if seen == self._asked and self._app is not None:
            return ""
        try:
            request = json.loads(text)
            phone = str(request["phone"])
        except ValueError, KeyError, TypeError:
            self._app = None
            return not_told()
        files, _skipped = read_ticked(request.get("lines", ()))
        given = str(request.get("destination") or "")
        destination = runtime.mapper.to_container(given) if given else None
        opened = open_phone_session(runtime, phone, (files, destination))
        (folder / WATCH.phone_ended).unlink(missing_ok=True)
        self._app = phone_here_app(runtime, opened, self._server)
        self._opened, self._asked, self._folder = opened, seen, folder
        return ""
