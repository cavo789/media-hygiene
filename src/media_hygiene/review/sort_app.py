"""The routes of the sort review: the page, the events, the previews, each choice.

`GET /` serves the page, `GET /api/state` the events, `GET /api/event/<id>` the photos
of one event, `GET /thumb/<row>.jpg` and `/preview/<row>.jpg` a small and a large
preview (rendered in the worker pool). `POST /api/event` names an event, `/api/files`
sends photos elsewhere, `/api/forget` takes a choice back, `/api/sure` accepts (or
takes back) the sure proposals in one write; each is saved at once. `/api/sort-now`
moves one event's files (`sort_now`). Like
`review`: loopback hosts only, JSON bodies only, from the page's own origin.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import ValidationError

from media_hygiene.errors import DecisionsError, MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import (
    PAGE_PATH,
    STATE_PATH,
    LocalApp,
    choice_failed,
    jpeg_response,
    page_or_state,
)
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.sort_choices import CHOICES, EVENT_PATH
from media_hygiene.review.sort_now import SORT_NOW_PATH, sort_now
from media_hygiene.review.sort_rule_choices import RULES_PATH
from media_hygiene.review.sort_views import JPEG_SUFFIX, PREVIEW_PREFIX, THUMB_PREFIX

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from pydantic import BaseModel

    from media_hygiene.review.http import Request
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.review.sort_now import Sorter

__all__ = ["PAGE_PATH", "STATE_PATH", "SortReviewApp"]

_THUMB_EDGE: Final = 400
_VALUE_ERROR: Final = "Value error, "


@dataclass(frozen=True, slots=True)
class SortReviewApp(LocalApp):
    """Answers the browser; the session holds the choices and saves them."""

    session: SortBatchSession
    page: bytes
    executor: Executor
    previews: Path | None = None  # the cache folder of previews, if any
    sorter: Sorter | None = None  # *Sort this event now*; None: the page cannot move

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.method == "GET":
            return await self._get(request.path)
        if request.method == "POST" and request.path == SORT_NOW_PATH:
            return await sort_now(self.sorter, request)
        if request.method != "POST" or request.path not in CHOICES:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        return self._choose(request)

    async def _get(self, path: str) -> Response:
        """Serve the page, the state, an event, or a preview.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for anything else.
        """
        if path == RULES_PATH:  # *Your rules* (0393)
            return _json(self.session.rules_view())
        if path in {PAGE_PATH, STATE_PATH}:
            return page_or_state(path, self.page, self.session.state)
        prefix = f"{EVENT_PATH}/"
        if path.startswith(prefix):
            try:
                view = self.session.event(path.removeprefix(prefix))
            except DecisionsError:
                return Response(HTTPStatus.NOT_FOUND)
            return _json(view)
        thumb = path.startswith(THUMB_PREFIX)
        prefix = THUMB_PREFIX if thumb else PREVIEW_PREFIX
        pool = PreviewPool(self.executor, self.previews)
        render = pool.renderer(_THUMB_EDGE if thumb else REVIEW_EDGE)
        row = path.removeprefix(prefix).removesuffix(JPEG_SUFFIX)
        source = self.session.preview_source(row)
        if source is None or path != f"{prefix}{row}{JPEG_SUFFIX}":
            return Response(HTTPStatus.NOT_FOUND)
        return await jpeg_response(self.executor, render, source)

    def _choose(self, request: Request) -> Response:
        """Apply one choice and save the decisions file.

        Args:
            request: `POST` to one of the choice routes, with a JSON body.

        Returns:
            The event as chosen now (or the batch, read back), or an error with a
            translated message.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            view = CHOICES[request.path](self.session, request.body)
        except ValidationError as exc:
            reasons = "; ".join(
                str(error["msg"]).removeprefix(_VALUE_ERROR).rstrip(".")
                for error in exc.errors()
            )
            message = _("Not saved: {reason}.").format(reason=reasons)
            return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": message})
        except (MediaHygieneError, OSError) as exc:
            return choice_failed(exc)
        return _json(view)


def _json(view: BaseModel) -> Response:
    """Answer with an event and its photos, or a batch read back.

    Args:
        view: The answer.

    Returns:
        The JSON response.
    """
    return Response(HTTPStatus.OK, view.model_dump_json().encode(), ContentType.JSON)
