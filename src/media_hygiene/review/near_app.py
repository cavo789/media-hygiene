"""The routes of `review --near`: the page, its state, previews, and each decision.

`GET /` serves the page, `GET /api/state` every group and the decisions so far,
`GET /preview/<key>.jpg` a large preview of a picture, `GET /video/<key>.<ext>` a video
played in the page (by parts), `GET /original/<key>.<ext>` the file itself, untouched,
`GET /api/file` the decisions file as read from the disk, and
`POST /api/near` decides one group or several (a folder pair at once), saved in one
write, then answers with those groups as read back from the disk.
A decision needs a JSON body: a page of another site cannot send one without the
browser asking first.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import DecisionsError
from media_hygiene.plan.near_review import NearAction
from media_hygiene.review.files import FILE_PATH, file_response
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import (
    PAGE_PATH,
    LocalApp,
    choice_failed,
    page_or_state,
)
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.videos import NEAR_POLICY, VIDEO_PREFIX, video_response

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.review.http import Request
    from media_hygiene.review.near_session import NearSession

NEAR_DECIDE_PATH: Final = "/api/near"
NEAR_FILE_PATH: Final = FILE_PATH
_GET, _POST = "GET", "POST"


class _Choice(BaseModel):
    """The decision on one group; None: back to undecided."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    group: int
    action: NearAction | None


class _Choices(BaseModel):
    """`POST /api/near`: one choice, or every group of a folder pair at once."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    choices: tuple[_Choice, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class NearApp(LocalApp):
    """Answers the browser; the session holds the decisions and saves them."""

    session: NearSession
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
            if request.path.startswith(VIDEO_PREFIX):
                return await video_response(request, self.session.preview_source)
            return await self._get(request.path)
        if request.path == NEAR_DECIDE_PATH and request.method == _POST:
            return self._decide(request)
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)

    async def _get(self, path: str) -> Response:
        """Serve the page, the state, the decisions file, a preview or an original.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for anything else.
        """
        if path == PAGE_PATH:  # it plays the videos: `media-src` too
            return Response(
                HTTPStatus.OK, self.page, ContentType.HTML, policy=NEAR_POLICY
            )
        found = await file_response(path, self.session, self.executor)
        if found is not None:
            return found
        return page_or_state(path, self.page, self.session.state)

    def _decide(self, request: Request) -> Response:
        """Decide one or more groups and save the decisions file.

        Args:
            request: `POST /api/near`, with a JSON body.

        Returns:
            The groups decided, and those groups as read back from the disk, or an
            error with a translated message.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            choices = _Choices.model_validate_json(request.body)
            proof = self.session.decide(
                {choice.group: choice.action for choice in choices.choices}
            )
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        except (DecisionsError, OSError) as exc:
            return choice_failed(exc)
        decided, total = self.session.decided
        totals = {"decided": decided, "total": total}
        return json_response(
            HTTPStatus.OK, totals | {"file": proof.model_dump(mode="json")}
        )
