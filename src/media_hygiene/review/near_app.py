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
from typing import TYPE_CHECKING, ClassVar, Final, override

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.plan.near_review import NearAction
from media_hygiene.review.decide_route import DecidingApp
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.near_session import NearSession
from media_hygiene.review.videos import NEAR_POLICY, VIDEO_PREFIX, video_response

if TYPE_CHECKING:
    from media_hygiene.review.http import Request

NEAR_DECIDE_PATH: Final = "/api/near"
NEAR_FILE_PATH: Final = FILE_PATH
_GET = "GET"


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
class NearApp(DecidingApp[NearSession]):
    """Answers the browser; the session holds the decisions and saves them."""

    decide_path: ClassVar[str] = NEAR_DECIDE_PATH

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback: the videos and the page first.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.method == _GET and request.path.startswith(VIDEO_PREFIX):
            return await video_response(request, self.session.preview_source)
        if request.method == _GET and request.path == PAGE_PATH:
            # It plays the videos: `media-src` too.
            return Response(
                HTTPStatus.OK, self.page, ContentType.HTML, policy=NEAR_POLICY
            )
        return await DecidingApp.answer(self, request)

    @override
    def decide(self, body: bytes) -> dict[str, object]:
        """Decide one or more groups and save the decisions file.

        Args:
            body: The JSON body of `POST /api/near`.

        Returns:
            The groups decided, and those groups as read back from the disk.
        """
        choices = _Choices.model_validate_json(body).choices
        proof = self.session.decide({choice.group: choice.action for choice in choices})
        return self.session.counts() | {"file": proof.model_dump(mode="json")}
