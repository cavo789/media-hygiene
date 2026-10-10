"""The routes of the review: the page, its state, the previews, and each decision.

`GET /` serves the page, `GET /api/state` every series and the shots set aside,
`GET /preview/<key>.jpg` a large preview (rendered in the worker pool),
`GET /original/<key>.<ext>` the file itself, untouched, `GET /api/file`
the decisions file as read from the disk, and `POST /api/decide` sets shots of one
series aside (or several series: a folder at once), saved in one write, then answers
with those series as read back from the disk.
A decision needs a JSON body: a page of another site cannot send one without the
browser asking first.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import DecisionsError
from media_hygiene.review.files import FILE_PATH, file_response
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import (
    PAGE_PATH,
    STATE_PATH,
    LocalApp,
    choice_failed,
    page_or_state,
)
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.review.http import Request
    from media_hygiene.review.session import ReviewSession

__all__ = ["DECIDE_PATH", "FILE_PATH", "PAGE_PATH", "STATE_PATH", "ReviewApp"]

DECIDE_PATH: Final = "/api/decide"
_GET, _POST = "GET", "POST"


class _Decision(BaseModel):
    """The ranks of the shots set aside in one series; None: back to still to see."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    series: int
    discarded: tuple[int, ...] | None


class _Decisions(BaseModel):
    """`POST /api/decide`: one choice, or every series of a folder at once."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    choices: tuple[_Decision, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class ReviewApp(LocalApp):
    """Answers the browser; the session holds the state and saves it."""

    session: ReviewSession
    page: bytes
    executor: Executor

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.method == _GET:
            return await self._get(request.path)
        if request.path == DECIDE_PATH and request.method == _POST:
            return self._decide(request)
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    async def _get(self, path: str) -> Response:
        """Serve the page, the state, the decisions file, a preview or an original.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for anything else, or a preview that cannot be made.
        """
        if path in {PAGE_PATH, STATE_PATH}:
            return page_or_state(path, self.page, self.session.state)
        found = await file_response(path, self.session, self.executor)
        return Response(HTTPStatus.NOT_FOUND) if found is None else found

    def _decide(self, request: Request) -> Response:
        """Set shots of one or more series aside and save the decisions file.

        Args:
            request: `POST /api/decide`, with a JSON body.

        Returns:
            The new totals and those series as read back from the disk, or an error
            with a translated message.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            decisions = _Decisions.model_validate_json(request.body)
            proof = self.session.decide(
                {
                    choice.series: None
                    if choice.discarded is None
                    else frozenset(choice.discarded)
                    for choice in decisions.choices
                }
            )
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        except (DecisionsError, OSError) as exc:
            return choice_failed(exc)
        series, shots = self.session.progress
        seen, total = self.session.seen
        totals = {"series": series, "shots": shots, "seen": seen, "total": total}
        return json_response(
            HTTPStatus.OK, totals | {"file": proof.model_dump(mode="json")}
        )
