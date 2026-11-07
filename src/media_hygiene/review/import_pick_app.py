"""The routes of `import --pick` (0590): the tiles, leaving out, then the copy.

`GET /` the page, `GET /api/state` the tiles and where the copy is, `GET /preview/…` and
`GET /original/…` a file where it lies, only read; `POST /api/leave` (the keys, `out`)
leaves files out or brings them back; `POST /api/copy` (the count the button states)
starts the copy in a thread, followed on `/api/state`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from threading import Thread
from typing import TYPE_CHECKING, Final, override

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.i18n import _
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.review.files import file_response
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import LocalApp, choice_failed, page_or_state
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.i18n.live import Page
    from media_hygiene.review.http import Request
    from media_hygiene.services.import_pick import ImportDesk
    from media_hygiene.services.runtime import Runtime

LEAVE_PATH: Final = "/api/leave"
COPY_PATH: Final = "/api/copy"


class _Leave(BaseModel):
    """`POST /api/leave`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    keys: tuple[str, ...] = Field(min_length=1)
    out: bool


class _Copy(BaseModel):
    """`POST /api/copy`: what the button states."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    count: int = Field(ge=1)


@dataclass(slots=True)
class ImportPickApp(LocalApp):
    """Answers the browser for one opening of the page."""

    runtime: Runtime
    desk: ImportDesk
    page: Page
    executor: Executor

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.method == "GET":
            pool = PreviewPool(self.executor, self.runtime.previews_dir)
            found = await file_response(request.path, self.desk, pool)
            if found is not None:
                return found
            return page_or_state(request.path, self.page, self.desk.state)
        if request.method != "POST" or request.path not in {LEAVE_PATH, COPY_PATH}:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        return refused_post(request) or await self._write(request)

    async def _write(self, request: Request) -> Response:
        """Answer a `POST` that may be read.

        Args:
            request: The request.

        Returns:
            The response; 400 on a bad body.
        """
        try:
            if request.path == LEAVE_PATH:
                return await self._leave(request)
            return self._copy(request)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)

    async def _leave(self, request: Request) -> Response:
        """Save what is left out, then answer what the file holds.

        Args:
            request: The request.

        Returns:
            The state, read back from the disk.
        """
        asked = _Leave.model_validate_json(request.body)
        try:
            state = await asyncio.to_thread(self.desk.choose, asked.keys, out=asked.out)
        except OSError as exc:
            return choice_failed(exc)
        return json_response(HTTPStatus.OK, state.model_dump(mode="json"))

    def _copy(self, request: Request) -> Response:
        """Start the copy of the count the button stated.

        Args:
            request: The request.

        Returns:
            The state; 409 when another copy runs or the page was out of date.
        """
        asked = _Copy.model_validate_json(request.body)
        jobs = self.desk.claim(asked.count)
        if jobs is None:
            message = _("The files changed since the page was shown: nothing copied.")
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        # Not the server's loop: a copy started goes on, whatever comes.
        Thread(target=self.desk.copy, args=(jobs,), name="import-copy").start()
        return json_response(HTTPStatus.OK, self.desk.state().model_dump(mode="json"))
