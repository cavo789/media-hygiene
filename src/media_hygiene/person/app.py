"""`/person` on every page's server: one photo, its faces, then that person's photos.

`POST /person/api/photo` the faces of a photo (its path typed or sent by a page),
`/api/look` a second look at it (`second_look`, in the worker pool), `/api/like` the
photos of a face, `/api/aside` sets them aside (or takes them back) and remembers the
face, like the people page (`AsideDesk`). `GET /person/face/<n>.jpg` a face,
`/thumb/` and `/preview/` its photo (`pictures`). Loopback hosts only, JSON bodies
only, from the page's own origin, like every page.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.i18n import _
from media_hygiene.person.finding import face_view
from media_hygiene.person.pictures import PersonPictures
from media_hygiene.person.routes import (
    APPLY_PATH,
    ASIDE_PATH,
    JPEG,
    LIKE_PATH,
    LOOK_PATH,
    PAGE_PATH,
    PHOTO_PATH,
)
from media_hygiene.person.second_look import LookJob, second_look
from media_hygiene.person.shelf import ShelfFace
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import json_response, refused_post

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
class PersonApp:
    """Answers `/person` from the index, the worker pool and the decisions file."""

    page: bytes
    finder: PersonFinder
    executor: Executor
    recipe: Callable[[], FinderRecipe | None]  # None: the face models are not there
    aside: AsideDesk | None = None  # None: no reports folder to set photos aside in
    previews: Path | None = None  # the cache folder of previews, if any
    apply: ApplyDesk | None = None  # *Apply now*: the page was opened from home

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
        if request.method == _POST:
            return refused_post(request) or await self._post(path, request.body)
        if path == PAGE_PATH:
            return Response(HTTPStatus.OK, self.page, ContentType.HTML)
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
            found = await self._found(path, body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        if found is not None:
            return json_response(HTTPStatus.OK, found)
        if path == APPLY_PATH and self.apply is not None:
            return await self.apply.answer()
        if path == ASIDE_PATH and self.aside is not None:
            said = self.aside.answer(self.finder.shelf, body)
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
            return self.finder.like(key, self.aside)
        if path not in {PHOTO_PATH, LOOK_PATH}:
            return None
        typed = PhotoAsked.model_validate_json(body).path
        if path == LOOK_PATH:
            return await self._look(typed)
        chosen = 0 if self.aside is None else len(self.aside.paths())
        return {**self.finder.photo(typed), "chosen": chosen}

    async def _look(self, typed: str) -> dict[str, object]:
        """Look again at a photo, turned and less strict, in the worker pool.

        Args:
            typed: Its path.

        Returns:
            The faces found, numbered; a sentence when there are none.
        """
        path = self.finder.place.resolve(typed)
        if path is None:
            return self.finder.photo(typed)  # it says why
        recipe = self.recipe()
        if recipe is None:
            said = _(
                "The face models are not in the cache yet: run 'audit --people' once."
            )
            return {"faces": [], "said": said}
        loop = asyncio.get_running_loop()
        found = await loop.run_in_executor(
            self.executor, second_look, LookJob(path, recipe)
        )
        shelf = self.finder.shelf
        keys = [
            shelf.add(ShelfFace(path, face.embedding, crop=face.crop)) for face in found
        ]
        if keys:
            return {"faces": [face_view(key) for key in keys]}
        said = _("No face found, even turned: set this photo aside on its own.")
        return {"faces": [], "said": said}
