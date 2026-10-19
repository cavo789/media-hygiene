r"""The routes of the page freeing a phone (0248): its state, previews, ticks, the end.

`GET /` the page, `GET /api/state` every file and its tick, `GET /preview/<key>.jpg`
the PC's file a tile shows, `GET /api/file` the decisions file as read from the disk;
`POST /api/phone` ticks or unticks files, saved in one write, then read back;
`POST /api/free` ("Delete from the phone") ends the page once the file read back holds
files ticked, and `POST /api/stop` ends it with nothing deleted. A choice needs a JSON
body: a page of another site cannot send one without the browser asking first.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Final, override

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.review.decide_route import DecidingApp, decide_route
from media_hygiene.review.ending import STOPPED, Ending
from media_hygiene.review.phone_session import PhoneSession

if TYPE_CHECKING:
    from media_hygiene.review.http import Request, Response

PHONE_DECIDE_PATH: Final = "/api/phone"
FREE_PATH: Final = "/api/free"
_POST: Final = "POST"


class _Choice(BaseModel):
    """One file ticked (to delete from the phone) or unticked (kept on it)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    file: int
    ticked: bool


class _Choices(BaseModel):
    """`POST /api/phone`: one file, or every file of a group at once."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    choices: tuple[_Choice, ...] = Field(min_length=1)


class _Free(BaseModel):
    """`POST /api/free`: an empty JSON object."""

    model_config = ConfigDict(frozen=True, extra="forbid")


@dataclass(frozen=True, slots=True)
class PhoneApp(DecidingApp[PhoneSession]):
    """Answers the browser; the session holds the ticks, saves them, reads them back."""

    decide_path: ClassVar[str] = PHONE_DECIDE_PATH
    ending: Ending = field(default_factory=Ending)

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback: "Delete from the phone", else the rest.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.path == FREE_PATH and request.method == _POST:
            return decide_route(request, self.free)
        return await DecidingApp.answer(self, request)

    @override
    def decide(self, body: bytes) -> dict[str, object]:
        """Tick or untick files and save the decisions file.

        Args:
            body: The JSON body of `POST /api/phone`.

        Returns:
            The counts, and the files ticked as read back from the disk.
        """
        choices = _Choices.model_validate_json(body).choices
        proof = self.session.decide({choice.file: choice.ticked for choice in choices})
        return self.session.counts() | {"file": proof.model_dump(mode="json")}

    def free(self, body: bytes) -> dict[str, object]:
        """Accept "Delete from the phone", then end the page.

        Args:
            body: The JSON body of `POST /api/free`.

        Returns:
            The counts, and the files ticked as read back from the disk.
        """
        _Free.model_validate_json(body)
        proof = self.session.free()
        self.ending.end(STOPPED)
        return self.session.counts() | {"file": proof.model_dump(mode="json")}
