"""`/person` on every page's server: one photo, its faces, then that person's photos.

`POST /person/api/photo` the faces of a photo (its path typed or sent by a page),
`/api/look` a second look at it, `/api/scan` its faces found now (`scan_route`),
`/api/draw` and `/api/forget` a face drawn by hand, `/api/like` the photos of a face,
`/api/aside` sets them aside (or takes them back) and remembers the face, like the
people page (`AsideDesk`). `GET /person/face/<n>.jpg` a face, `/thumb/` and
`/preview/` its photo (`pictures`). Loopback hosts only, JSON bodies only, from the
page's own origin.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.i18n.live import Page, page_of
from media_hygiene.person.draw_route import drawn
from media_hygiene.person.forget_route import forgotten
from media_hygiene.person.name_tags import tagged
from media_hygiene.person.pictures import PersonPictures
from media_hygiene.person.routes import (
    APPLY_PATH,
    ASIDE_PATH,
    DRAW_PATH,
    FORGET_PATH,
    JPEG,
    LIKE_PATH,
    LOOK_PATH,
    NAMES_PATH,
    PAGE_PATH,
    PHOTO_PATH,
    SCAN_PATH,
    UNDO_PATH,
)
from media_hygiene.person.scan_route import looked_again, scanned_now
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.slow_log import timed
from media_hygiene.search.undo_api import undo_route

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.faces.worker import FinderRecipe
    from media_hygiene.people.aside import AsideDesk
    from media_hygiene.person.finding import PersonFinder
    from media_hygiene.review.apply_api import ApplyDesk
    from media_hygiene.review.http import Request

_PATH_LENGTH: Final = 4096
_POST: Final = "POST"


class PhotoAsked(BaseModel):
    """A photo, by its path."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = Field(min_length=1, max_length=_PATH_LENGTH)


class LikeAsked(BaseModel):
    """A face, by its number."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: int = Field(ge=0)


@dataclass(frozen=True, slots=True)
class PersonApp:  # pylint: disable=too-many-instance-attributes
    """Answers `/person` from the index, the worker pool and the decisions file."""

    page: Page
    finder: PersonFinder
    executor: Executor
    recipe: Callable[[], FinderRecipe | None]  # None: the face models are not there
    aside: AsideDesk | None = None  # None: no reports folder to set photos aside in
    previews: Path | None = None  # the cache folder of previews, if any
    apply: ApplyDesk | None = None  # *Apply now*: the page was opened from home
    # One question or choice at a time, in the order sent, off the event loop: the
    # thumbnails and the other pages keep being served meanwhile (2026-11-15).
    turn: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def handle(self, request: Request) -> Response:
        """Route a request below `/person`.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        path = request.path.split("?", 1)[0]
        undo = self.apply.offer.undo if self.apply else None
        if path == UNDO_PATH and undo is not None:
            return await undo_route(undo, request)
        if request.method == _POST:
            return refused_post(request) or await self._post(path, request.body)
        if path == PAGE_PATH:
            return Response(HTTPStatus.OK, page_of(self.page), ContentType.HTML)
        if path.endswith(JPEG):
            pictures = PersonPictures(self.finder.shelf, self.executor, self.previews)
            return await pictures.answer(path)
        return Response(HTTPStatus.NOT_FOUND)

    async def _post(self, path: str, body: bytes) -> Response:
        """Answer the page's questions and choices.

        Args:
            path: The route.
            body: The JSON sent.

        Returns:
            The JSON answer; 400 for a body that is not a question.
        """
        try:
            async with self.turn:
                found = await self._found(path, body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        if found is not None:
            return json_response(HTTPStatus.OK, found)
        if path == APPLY_PATH and self.apply is not None:
            return await self.apply.answer()
        if path == ASIDE_PATH and (aside := self.aside) is not None:
            async with self.turn:
                said = await asyncio.to_thread(aside.answer, self.finder.shelf, body)
            return (
                said
                if isinstance(said, Response)
                else json_response(HTTPStatus.OK, {"aside": said})
            )
        return Response(HTTPStatus.NOT_FOUND)

    async def _found(self, path: str, body: bytes) -> dict[str, object] | None:
        """Answer a question: a photo's faces, a second look, a face's photos.

        Args:
            path: The route.
            body: The JSON sent.

        Returns:
            The answer; None for a route that is not a question.

        Raises:
            ValidationError: The body is not the question.
        """
        if path == LIKE_PATH:
            key = str(LikeAsked.model_validate_json(body).key)
            liked = await asyncio.to_thread(self.finder.like, key, self.aside)
            return await timed(
                "names of a like", asyncio.to_thread(tagged, self.finder.names, liked)
            )
        if path == NAMES_PATH and (names := self.finder.names) is not None:
            return await asyncio.to_thread(names.answer, body)
        if path in {DRAW_PATH, FORGET_PATH}:  # a face drawn by hand, or forgotten
            return (
                await drawn(self, body)
                if path == DRAW_PATH
                else await asyncio.to_thread(forgotten, self.finder, body)
            )
        if path not in {PHOTO_PATH, LOOK_PATH, SCAN_PATH}:
            return None
        typed = PhotoAsked.model_validate_json(body).path
        if path != PHOTO_PATH:  # looked at again, or its faces found now and kept
            answer = looked_again if path == LOOK_PATH else scanned_now
            return await answer(self, typed)
        chosen = 0 if self.aside is None else len(self.aside.paths())
        found = await asyncio.to_thread(self.finder.photo, typed)
        return await asyncio.to_thread(
            tagged, self.finder.names, {**found, "chosen": chosen}
        )
