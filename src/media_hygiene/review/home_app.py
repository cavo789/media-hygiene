"""The routes of the home page: the page, its state, the reports, and a step chosen.

`GET /` serves the page at once, without its state: the page shows a waiting
meerkat, then asks `GET /api/state` where you are and every step (read again from
the tool folders at each call; slow through Docker Desktop's file sharing, 0277),
`GET /reports/<path>` a file of the reports folder (its images and fonts, `/assets/`,
come from the door every page shares, `ending`),
`GET /api/audit` the progress of the audit run by the page, and `POST /api/audit`
starts it (one at a time) or stops it, `/api/tags` the same for `tags`
(`home_tags_api`, 0343), `/api/people` and `/api/meaning` for faces and meaning;
`POST /api/favourites` saves the starred actions (0484), `/api/scan-scope` what
the audit analyses (0535);
`POST /api/alive` says a tab still shows the page (0261, `presence`). `POST /api/step`
ends the server with `STEP_EXIT_BASE + n` for step `n`, which `mh` then runs in the
terminal (`home_step`): only when the launcher said it does
(`MEDIA_HYGIENE_LAUNCHER_STEPS`), else it is refused and the page copies the command
instead.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import StrEnum
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.i18n import _
from media_hygiene.i18n.live import page_of
from media_hygiene.review.home_favourites_api import favourites_response
from media_hygiene.review.home_more_api import HomeMore, more_response
from media_hygiene.review.home_step import StepDoor, step_response
from media_hygiene.review.home_tags_api import INLINE_PATH, tags_response, tags_state
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.inline_step import InlineRunner, inline_response
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH, LocalApp
from media_hygiene.review.presence import PRESENCE_PATH, presence_response
from media_hygiene.review.report_shell import shelled_report
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.step_watch import STEP_PATH, step_state

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from media_hygiene.review.ending import Ending
    from media_hygiene.review.home_parts import HomeFindings, HomeSample
    from media_hygiene.review.home_views import HomeState
    from media_hygiene.review.http import Request
    from media_hygiene.review.import_chain_api import ChainDoor
    from media_hygiene.review.presence import Presence
    from media_hygiene.services.home_audit import HomeAudit
    from media_hygiene.services.home_tags import HomeTags

AUDIT_PATH: Final = "/api/audit"
FAVOURITES_PATH: Final = "/api/favourites"
_GET, _POST = "GET", "POST"


class AuditAction(StrEnum):
    """What `POST /api/audit` asks."""

    START = "start"
    STOP = "stop"


class _AuditAsked(BaseModel):
    """`POST /api/audit`: start or stop the audit."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: AuditAction


@dataclass(frozen=True, slots=True)
class HomeApp(LocalApp):  # pylint: disable=too-many-instance-attributes
    """Answers the browser; the state is read again from the tool folders each time."""

    page: bytes | Callable[[], bytes]  # `PerLocale`: follows the language (0644)
    state: Callable[[], HomeState]
    reports_dir: Path
    ending: Ending
    audit: HomeAudit
    presence: Presence
    relays_steps: bool = False  # the launcher runs the step `STEP_EXIT_BASE + n` names
    relays_fields: bool = False  # and the words of a form (`home_fields`)
    keeps: bool = False  # and runs a console step with the server up (`step_watch`)
    # Read-only steps run in the page by path: tags (0343), faces (0424), meaning (0425)
    runs: Mapping[str, HomeTags] = field(default_factory=dict)
    config_file: Path | None = None  # where the starred actions are written (0484)
    inline: InlineRunner = field(default_factory=InlineRunner)  # 0505
    samples: Callable[[], tuple[HomeSample, ...]] | None = None  # random photos, 0485
    chain: ChainDoor | None = None  # the chain after an import, followed (0604)
    safety: Callable[[], HomeFindings] | None = None  # its own route (0692)

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        more = HomeMore(self.config_file, self.samples, self.chain, self.safety)
        if (answer := await more_response(more, request)) is not None:
            return answer
        if request.path == INLINE_PATH:  # a short step run here (0505)
            return await inline_response(self.inline, request)
        if request.method == _GET:
            return await self._read(request.path)
        if request.method == _POST:
            return await self._write(request)
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    async def _write(self, request: Request) -> Response:
        """Answer a `POST`: a step chosen, the audit, a run, the stars, the presence.

        Args:
            request: The request.

        Returns:
            The response; 405 for any other path.
        """
        path = request.path
        if path == STEP_PATH:
            door = StepDoor(
                self.state,
                self.ending,
                self.reports_dir,
                relays_steps=self.relays_steps,
                relays_fields=self.relays_fields,
                keeps=self.keeps,
            )
            return await step_response(door, request)
        if path == AUDIT_PATH:
            return await self._audit(request)
        if path in self.runs:
            return await tags_response(self.runs[path], request)
        if path == FAVOURITES_PATH and self.config_file is not None:
            return await favourites_response(self.config_file, request)
        if path == PRESENCE_PATH:
            return await presence_response(self.presence, request)
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    async def _read(self, path: str) -> Response:
        """Answer a `GET`: the page, its state, the audit's progress, a report.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for any other path.
        """
        if path == PAGE_PATH:
            return Response(HTTPStatus.OK, page_of(self.page), ContentType.HTML)
        if path.startswith(REPORTS_PREFIX):
            return await shelled_report(self.reports_dir, path)
        if path in self.runs:
            return tags_state(self.runs[path])
        if path == STEP_PATH:
            return await step_state(self.reports_dir)
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
