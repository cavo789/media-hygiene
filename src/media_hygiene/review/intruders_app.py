"""The routes of `review --intruders`: the page, its state, each pick (0428).

`GET /` serves the page, `GET /api/state` the intruder files tallied per extension and
per folder with those already set aside, and `POST /api/intruders` sets aside the
files of the extensions and folders ticked (or puts them all back), answered with the
intruder files the decisions file holds, read back from the disk. A pick needs a JSON
body: a page of another site cannot send one without the browser asking first.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Protocol, override

from pydantic import BaseModel, ConfigDict

from media_hygiene.review.decide_route import decide_route
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import (
    STATE_PATH,
    LocalApp,
    page_or_state,
)

if TYPE_CHECKING:
    from media_hygiene.report.chosen_decisions import ChosenFile
    from media_hygiene.review.http import Request
    from media_hygiene.review.intruders_views import IntrudersState

INTRUDERS_PATH: Final = "/api/intruders"
_GET, _POST = "GET", "POST"


class IntrudersPick(BaseModel):
    """`POST /api/intruders`: the extensions and host folders ticked, or all back."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    extensions: tuple[str, ...] = ()
    folders: tuple[str, ...] = ()  # as the page shows them: host paths
    back: bool = False  # put every intruder file set aside back


class IntrudersDesk(Protocol):
    """What the page works on: the files now, and the decisions file."""

    def state(self) -> IntrudersState:
        """Describe the intruder files now.

        Returns:
            The state.
        """

    def pick(self, pick: IntrudersPick) -> tuple[ChosenFile, ...]:
        """Save a pick, then read the decisions file back.

        Args:
            pick: What the page posted.

        Returns:
            The intruder files set aside, as read back from the disk.
        """


@dataclass(frozen=True, slots=True)
class IntrudersApp(LocalApp):
    """Answers the browser; the desk walks the folders and saves the picks."""

    desk: IntrudersDesk
    page: bytes

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        # The desk walks the folders (its own event loop): in a thread, off this one.
        if request.method == _GET and request.path == STATE_PATH:
            state = await asyncio.to_thread(self.desk.state)
            return Response(
                HTTPStatus.OK, state.model_dump_json().encode(), ContentType.JSON
            )
        if request.method == _GET:
            return page_or_state(request.path, self.page, self.desk.state)
        if request.path == INTRUDERS_PATH and request.method == _POST:
            return await asyncio.to_thread(self._pick, request)
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    def _pick(self, request: Request) -> Response:
        """Save what was ticked; answer with the file as read back.

        Args:
            request: The request, with a JSON body.

        Returns:
            200 with the files set aside; 400 for a body that is not a pick, 422 or
            500 when it cannot be saved.
        """
        return decide_route(request, self._saved)

    def _saved(self, body: bytes) -> dict[str, object]:
        """Save a pick, then read the decisions file back.

        Args:
            body: The JSON body of `POST /api/intruders`.

        Returns:
            The intruder files set aside, as read back from the disk.
        """
        pick = IntrudersPick.model_validate_json(body)
        saved = self.desk.pick(pick)  # pylint: disable=assignment-from-no-return
        return {"set_aside": [file.model_dump(mode="json") for file in saved]}
