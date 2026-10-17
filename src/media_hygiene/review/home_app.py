"""The routes of the home page: the page, its state, the reports, and a step chosen.

`GET /` serves the page, `GET /api/state` where you are and every step (read again
from the tool folders at each call), `GET /reports/<path>` a file of the reports
folder, `GET /api/audit` the progress of the audit run by the page, and
`POST /api/audit` starts it (one at a time) or stops it. `POST /api/step` ends the
server with `100 + n` for step `n`, which `mh` then runs in the terminal. A step
needs a JSON body naming its number and command: a page of another site cannot
send one without the browser asking first, and a menu changed since the page was
drawn is refused.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import StrEnum
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.home_views import REPORTS_PREFIX, STEP_EXIT_BASE
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH, LocalApp
from media_hygiene.review.report_files import report_response
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.ending import Ending
    from media_hygiene.review.home_views import HomeState
    from media_hygiene.review.http import Request
    from media_hygiene.services.home_audit import HomeAudit

STEP_PATH: Final = "/api/step"
AUDIT_PATH: Final = "/api/audit"
_GET, _POST = "GET", "POST"


class AuditAction(StrEnum):
    """What `POST /api/audit` asks."""

    START = "start"
    STOP = "stop"


class _AuditAsked(BaseModel):
    """`POST /api/audit`: start or stop the audit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: AuditAction


class _Chosen(BaseModel):
    """`POST /api/step`: the step chosen, as the page showed it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    number: int
    command: str


@dataclass(frozen=True, slots=True)
class HomeApp(LocalApp):
    """Answers the browser; the state is read again from the tool folders each time."""

    page: bytes
    state: Callable[[], HomeState]
    reports_dir: Path
    ending: Ending
    audit: HomeAudit

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        path = request.path
        if request.method == _GET:
            return await self._read(path)
        if path == STEP_PATH and request.method == _POST:
            return await self._step(request)
        if path == AUDIT_PATH and request.method == _POST:
            return await self._audit(request)
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    async def _read(self, path: str) -> Response:
        """Answer a `GET`: the page, its state, the audit's progress, a report.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for any other path.
        """
        if path == PAGE_PATH:
            return Response(HTTPStatus.OK, self.page, ContentType.HTML)
        if path.startswith(REPORTS_PREFIX):
            return await report_response(self.reports_dir, path)
        if path == STATE_PATH:
            state: BaseModel = await asyncio.to_thread(self.state)
        elif path == AUDIT_PATH:
            state = self.audit.state()
        else:
            return Response(HTTPStatus.NOT_FOUND)
        return Response(
            HTTPStatus.OK, state.model_dump_json().encode(), ContentType.JSON
        )

    async def _audit(self, request: Request) -> Response:
        """Start the audit, or stop it.

        Args:
            request: `POST /api/audit`.

        Returns:
            The audit's state; 409 when one already runs.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            asked = _AuditAsked.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        if asked.action is AuditAction.STOP:
            await asyncio.to_thread(self.audit.stop)
        elif not self.audit.start():
            message = _("An audit already runs: wait for its end, or stop it.")
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        body = self.audit.state().model_dump_json().encode()
        return Response(HTTPStatus.OK, body, ContentType.JSON)

    async def _step(self, request: Request) -> Response:
        """End the server with the code of the step chosen, when the menu agrees.

        Args:
            request: `POST /api/step`.

        Returns:
            The step, about to run in the terminal; 409 when the steps changed.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            chosen = _Chosen.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        state = await asyncio.to_thread(self.state)
        command = state.command_of(chosen.number)
        if command is None or command != chosen.command:
            message = _("The steps changed since the page was shown: here they are.")
            return json_response(HTTPStatus.CONFLICT, {"error": message})
        self.ending.end(STEP_EXIT_BASE + chosen.number)
        return json_response(
            HTTPStatus.OK, {"number": chosen.number, "command": command}
        )
