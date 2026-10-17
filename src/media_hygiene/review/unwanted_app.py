"""The routes of `review --junk`: the page, its state, previews, and each decision.

`GET /` serves the page, `GET /api/state` every photo, its group and the decisions so
far, `GET /preview/<key>.jpg` a large preview, `GET /original/<key>.<ext>` the file
itself, untouched, `GET /api/file` the decisions file as read from the disk, and
`POST /api/junk` decides one photo or a whole group, saved in one write, then answers
with those photos as read back from the disk. A decision needs a JSON body: a page of
another site cannot send one without the browser asking first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final, override

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.review.decide_route import DecidingApp
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.unwanted_session import UnwantedSession

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
