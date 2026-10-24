"""The routes of `shrink --try`: the page, its state, the drafts, the frames (0307).

`GET /api/state` every draft as it stands and the decisions file read from the disk;
`GET /draft/<n>.mp4` a draft, piece by piece (`Range`); `GET /frame/<n>-<a|b>-<k>.jpg`
a frame of the original (A) or of the draft (B). `POST /api/shrink/choose` adds or
removes drafts from `shrink-decisions.json`, answered with the file as read back;
`POST /api/shrink/lighten` ends the page with `LIGHTEN_CODE`: the command then asks,
in the terminal, and lightens them, reusing their drafts. Loopback only, JSON only.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH, LocalApp
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.shrink_choose import (
    ChoiceAsked,
    chosen_count,
    ready_draft,
    record_choice,
)
from media_hygiene.review.shrink_views import DRAFT_PREFIX, FRAME_PREFIX, try_state
from media_hygiene.review.videos import NEAR_POLICY, streamed
from media_hygiene.shrink.draft_bench import draft_file, frame_file

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.ending import Ending
    from media_hygiene.review.http import Request
    from media_hygiene.services.shrink_try import Trial

LIGHTEN_CODE: Final = 4  # the page asked to lighten the videos chosen
CHOOSE_PATH: Final = "/api/shrink/choose"
LIGHTEN_PATH: Final = "/api/shrink/lighten"
_DRAFT: Final = re.compile(r"/draft/(?P<number>[0-9]{1,4})\.mp4")
_FRAME: Final = re.compile(
    r"/frame/(?P<number>[0-9]{1,4})-(?P<side>[ab])-(?P<k>[0-9])\.jpg"
)
_GET, _POST = "GET", "POST"


@dataclass(frozen=True, slots=True)
class ShrinkDesk:
    """The try, how its paths are shown, and how its page ends."""

    trial: Trial
    mapper: HostPathMapper
    ending: Ending


@dataclass(frozen=True, slots=True)
class ShrinkTryApp(LocalApp):
    """Answers the page of `shrink --try`."""

    page: bytes
    desk: ShrinkDesk

    @override
    async def answer(self, request: Request) -> Response:
        """Serve the page, its state, a draft or a frame; record a choice.

        Args:
            request: The request.

        Returns:
            The response; 404 for an unknown path or a draft not ready.
        """
        if request.method == _POST:
            return refused_post(request) or await self._post(request)
        if request.method != _GET:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        path = request.path
        if path.startswith(DRAFT_PREFIX):
            return await self._draft(request)
        if path.startswith(FRAME_PREFIX):
            return await self._frame(path)
        return await self._page(path)

    async def _page(self, path: str) -> Response:
        """Serve the page, which plays the drafts, or its state.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for any other path.
        """
        if path == STATE_PATH:
            state = await asyncio.to_thread(self._state)
            return Response(HTTPStatus.OK, state, ContentType.JSON)
        if path != PAGE_PATH:
            return Response(HTTPStatus.NOT_FOUND)
        return Response(HTTPStatus.OK, self.page, ContentType.HTML, policy=NEAR_POLICY)

    def _state(self) -> bytes:
        """Describe the try, the file read from the disk.

        Returns:
            The state, as JSON.
        """
        desk = self.desk
        return try_state(desk.trial, desk.mapper).model_dump_json().encode()

    async def _draft(self, request: Request) -> Response:
        """Play a draft.

        Args:
            request: `GET /draft/<n>.mp4`, with or without `Range`.

        Returns:
            The draft, whole or in part; 404 while it is not ready.
        """
        matched = _DRAFT.fullmatch(request.path)
        draft = (
            None
            if matched is None
            else ready_draft(self.desk.trial, int(matched["number"]))
        )
        if draft is None:
            return Response(HTTPStatus.NOT_FOUND)
        source = draft_file(self.desk.trial.bench.folder, draft.number)
        return await streamed(request, source, ContentType.MP4)

    async def _frame(self, path: str) -> Response:
        """Show a frame of the original or of the draft.

        Args:
            path: `/frame/<n>-<a|b>-<k>.jpg`.

        Returns:
            The JPEG; 404 while its draft is not ready.
        """
        matched = _FRAME.fullmatch(path)
        draft = (
            None
            if matched is None
            else ready_draft(self.desk.trial, int(matched["number"]))
        )
        if matched is None or draft is None:
            return Response(HTTPStatus.NOT_FOUND)
        frame = (matched["side"], int(matched["k"]))
        source = frame_file(self.desk.trial.bench.folder, draft.number, frame)
        try:
            image = await asyncio.to_thread(source.read_bytes)
        except OSError:
            return Response(HTTPStatus.NOT_FOUND)
        return Response(HTTPStatus.OK, image, ContentType.JPEG)

    async def _post(self, request: Request) -> Response:
        """Record a choice, or end the page to lighten the videos chosen.

        Args:
            request: The request, its JSON body accepted.

        Returns:
            The state read back, or the count chosen; 400 for a body that is not a
            choice, 409 when nothing is chosen, 500 when the file cannot be written.
        """
        if request.path == LIGHTEN_PATH:
            return self._lighten(await asyncio.to_thread(chosen_count, self.desk.trial))
        if request.path != CHOOSE_PATH:
            return Response(HTTPStatus.NOT_FOUND)
        try:
            asked = ChoiceAsked.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        try:
            await asyncio.to_thread(record_choice, self.desk.trial, asked)
        except OSError as exc:
            error = _("Cannot save the decisions file: {error}.")
            message = error.format(error=exc.strerror or exc)
            return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message})
        return Response(
            HTTPStatus.OK, await asyncio.to_thread(self._state), ContentType.JSON
        )

    def _lighten(self, count: int) -> Response:
        """End the page so that the command lightens the videos the file holds.

        Args:
            count: How many the file holds.

        Returns:
            Their count; 409 when the file holds none.
        """
        if not count:
            return json_response(HTTPStatus.CONFLICT, {"error": _("Nothing chosen.")})
        self.desk.ending.end(LIGHTEN_CODE)
        return json_response(HTTPStatus.OK, {"count": count})
