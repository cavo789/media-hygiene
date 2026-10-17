"""The routes of `review --gone`: the page, its state, previews kept, each answer.

`GET /` serves the page, `GET /api/state` every file gone, its group and the answers
so far, `GET /preview/<key>.jpg` the preview the cache still holds of it, `GET
/api/file` the decisions file as read from the disk, and `POST /api/gone` answers one
file or a whole group, saved in one write, then answered with those files as read back
from the disk. An answer needs a JSON body: a page of another site cannot send one
without the browser asking first.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, ClassVar, Final, override

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.review.decide_route import DecidingApp
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.gone_session import GoneSession
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.views import PREVIEW_PREFIX

if TYPE_CHECKING:
    from media_hygiene.review.http import Request

GONE_DECIDE_PATH: Final = "/api/gone"
GONE_FILE_PATH: Final = FILE_PATH
_GET: Final = "GET"
_SUFFIX: Final = ".jpg"


class _Choice(BaseModel):
    """The answer on one file: deleted on purpose, moved, or None: undecided."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    file: int
    deleted: bool | None


class _Choices(BaseModel):
    """`POST /api/gone`: one file, or every file of a group at once."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    choices: tuple[_Choice, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class GoneApp(DecidingApp[GoneSession]):
    """Answers the browser; the session holds the answers and saves them."""

    decide_path: ClassVar[str] = GONE_DECIDE_PATH

    @override
    async def answer(self, request: Request) -> Response:
        """Serve a preview kept from the cache; anything else as the other reviews.

        Args:
            request: The request.

        Returns:
            The response; 404 for a file gone without a preview kept.
        """
        path = request.path
        if request.method != _GET or not path.startswith(PREVIEW_PREFIX):
            return await DecidingApp.answer(self, request)
        key = path.removeprefix(PREVIEW_PREFIX).removesuffix(_SUFFIX)
        kept = self.session.preview_source(key)
        if kept is None or path != f"{PREVIEW_PREFIX}{key}{_SUFFIX}":
            return Response(HTTPStatus.NOT_FOUND)
        try:
            image = kept.read_bytes()
        except OSError:
            return Response(HTTPStatus.NOT_FOUND)
        return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)

    @override
    def decide(self, body: bytes) -> dict[str, object]:
        """Answer one or more files and save the decisions file.

        Args:
            body: The JSON body of `POST /api/gone`.

        Returns:
            The counts, and those files as read back from the disk.
        """
        choices = _Choices.model_validate_json(body).choices
        proof = self.session.decide({c.file: c.deleted for c in choices})
        return self.session.counts() | {"file": proof.model_dump(mode="json")}
