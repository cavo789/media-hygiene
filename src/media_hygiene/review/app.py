"""The routes of the review: the page, its state, the previews, and each decision.

`GET /` serves the page, `GET /api/state` every series and the shots set aside,
`GET /preview/<key>.jpg` a large preview (rendered in the worker pool), and
`POST /api/decide` sets shots of one series aside, saved at once. A decision needs a
JSON body: a page of another site cannot send one without the browser asking first.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.errors import DecisionsError
from media_hygiene.report.thumbnails import review_preview
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import (
    PAGE_PATH,
    STATE_PATH,
    LocalApp,
    choice_failed,
    jpeg_response,
    page_or_state,
)
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.views import PREVIEW_PREFIX

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.review.http import Request
    from media_hygiene.review.session import ReviewSession

__all__ = ["DECIDE_PATH", "PAGE_PATH", "STATE_PATH", "ReviewApp"]

DECIDE_PATH: Final = "/api/decide"
_PREVIEW_SUFFIX: Final = ".jpg"
_GET, _POST = "GET", "POST"


class _Decision(BaseModel):
    """`POST /api/decide`: the ranks of the shots set aside in one series."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    series: int
    discarded: tuple[int, ...]


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
        """Serve the page, the state, or a preview.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for anything else, or a preview that cannot be made.
        """
        if path in {PAGE_PATH, STATE_PATH}:
            return page_or_state(path, self.page, self.session.state)
        key = path.removeprefix(PREVIEW_PREFIX).removesuffix(_PREVIEW_SUFFIX)
        source = self.session.preview_source(key)
        if source is None or path != f"{PREVIEW_PREFIX}{key}{_PREVIEW_SUFFIX}":
            return Response(HTTPStatus.NOT_FOUND)
        return await jpeg_response(self.executor, review_preview, source)

    def _decide(self, request: Request) -> Response:
        """Set shots of a series aside and save the decisions file.

        Args:
            request: `POST /api/decide`, with a JSON body.

        Returns:
            The new totals, or an error with a translated message.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            decision = _Decision.model_validate_json(request.body)
            self.session.decide(decision.series, frozenset(decision.discarded))
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        except (DecisionsError, OSError) as exc:
            return choice_failed(exc)
        series, shots = self.session.progress
        return json_response(HTTPStatus.OK, {"series": series, "shots": shots})
