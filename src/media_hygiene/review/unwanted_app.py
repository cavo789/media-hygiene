"""The routes of `review --junk`: the page, its state, previews, and each decision.

`GET /` serves the page, `GET /api/state` every photo, its group and the decisions so
far, `GET /preview/<key>.jpg` a large preview, `GET /original/<key>.<ext>` the file
itself, untouched, `GET /api/file` the decisions file as read from the disk, and
`POST /api/junk` decides one photo or a whole group, saved in one write, then answers
with those photos as read back from the disk. `/api/strictness`: its thresholds. A
decision needs a JSON body: a page of another site cannot send one without the browser
asking first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Final, override

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.review.decide_route import DecidingApp
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.strictness import STRICTNESS_PATH, strictness_route
from media_hygiene.review.unwanted_session import UnwantedSession

if TYPE_CHECKING:
    from media_hygiene.review.http import Request, Response

JUNK_DECIDE_PATH: Final = "/api/junk"
JUNK_FILE_PATH: Final = FILE_PATH


class _Choice(BaseModel):
    """The decision on one photo: set aside, kept, or None: back to undecided."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    photo: int
    aside: bool | None


class _Choices(BaseModel):
    """`POST /api/junk`: one photo, or every photo of a group at once."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    choices: tuple[_Choice, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class UnwantedApp(DecidingApp[UnwantedSession]):
    """Answers the browser; the session holds the decisions and saves them."""

    decide_path: ClassVar[str] = JUNK_DECIDE_PATH

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request: the thresholds here, the rest as every review.

        Args:
            request: The request.

        Returns:
            The response.
        """
        tuning = self.session.strictness
        if request.path == STRICTNESS_PATH and tuning is not None:
            return strictness_route(request, tuning)
        return await DecidingApp.answer(self, request)

    @override
    def decide(self, body: bytes) -> dict[str, object]:
        """Decide one or more photos and save the decisions file.

        Args:
            body: The JSON body of `POST /api/junk`.

        Returns:
            The counts, and those photos as read back from the disk.
        """
        choices = _Choices.model_validate_json(body).choices
        proof = self.session.decide({choice.photo: choice.aside for choice in choices})
        return self.session.counts() | {"file": proof.model_dump(mode="json")}
