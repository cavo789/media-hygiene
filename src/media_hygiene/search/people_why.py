"""*Why this name?* on the search page: the face, how it got the name, its reference.

`POST /api/people/why` (`{key, name}`) answers, for each face of the photo that gives it
the name, how (confirmed by the user, or close to a face they confirmed), the
reference that decided it (cut out, its folder and file), the likeness against the
threshold (`[people] similarity`), and the next person when close too (TODO 0318).
Computed on demand for one photo, never for every hit. `GET /api/people/face/<n>.jpg`
cuts a face out in the worker pool, never written anywhere.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.i18n import _
from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.people.naming import How
from media_hygiene.people.why import why_named
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.views import PREVIEW_PREFIX

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.people.why import Why
    from media_hygiene.search.people_desk import PeopleDesk
    from media_hygiene.search.people_seen import Seen

PEOPLE_WHY_PATH: Final = "/api/people/why"
FACE_CROP_PREFIX: Final = "/api/people/face/"
_JPEG: Final = ".jpg"
_KEY_OF: Final = "SELECT rowid FROM files WHERE path = ?"
_NAME_LENGTH: Final = 100


class WhyAsked(BaseModel):
    """Which photo, and which name on it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    key: int = Field(ge=0)
    name: str = Field(min_length=1, max_length=_NAME_LENGTH)


def why_answer(desk: PeopleDesk, body: bytes) -> Response:
    """Explain the name of a photo, face by face.

    Args:
        desk: The names of the search.
        body: `{key, name}`.

    Returns:
        The faces and why; 400 for another body, 404 for an unknown photo, 422
        when the name is not on it.
    """
    try:
        asked = WhyAsked.model_validate_json(body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    photo = desk.search.source_of(asked.key)
    if photo is None:
        return Response(HTTPStatus.NOT_FOUND)
    seen = desk.faces()
    try:
        ids = seen.ids(photo.path, asked.name, None)
    except ValueError as exc:
        return save_refused(exc)
    faces = [_face_view(desk, seen, seen.numbers[key]) for key in ids]
    return json_response(HTTPStatus.OK, {"name": asked.name, "faces": faces})


async def crop_answer(desk: PeopleDesk, path: str, executor: Executor) -> Response:
    """A face cut out of its photo.

    Args:
        desk: The names of the search.
        path: `/api/people/face/<n>.jpg`.
        executor: The worker pool.

    Returns:
        The JPEG; 404 for an unknown face or a photo that cannot be read.
    """
    number = path.removeprefix(FACE_CROP_PREFIX).removesuffix(_JPEG)
    face = desk.faces().face(int(number)) if number.isdigit() else None
    if face is None:
        return Response(HTTPStatus.NOT_FOUND)
    image = await asyncio.get_running_loop().run_in_executor(
        executor, face_crop, CropJob(face.path, face.box)
    )
    if image is None:
        return Response(HTTPStatus.NOT_FOUND)
    return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)


def _face_view(desk: PeopleDesk, seen: Seen, number: int) -> dict[str, object]:
    """One face: its picture, how it got the name, its reference, the next person.

    Args:
        desk: The names of the search.
        seen: The faces of the search.
        number: The face's rank.

    Returns:
        The JSON object of the panel.
    """
    why = why_named(seen.faces[number], seen.known)
    view: dict[str, object] = {
        "face": number,
        "crop": f"{FACE_CROP_PREFIX}{number}{_JPEG}",
        "how": why.how.value if why.how else "",
        "said": _said(why),
    }
    reference = seen.numbers.get(why.reference)
    if why.how is How.ASSIGNED and reference is not None:
        source = seen.faces[reference].path
        row = desk.search.connection.execute(_KEY_OF, (str(source),)).fetchone()
        view["reference"] = {
            "crop": f"{FACE_CROP_PREFIX}{reference}{_JPEG}",
            "where": desk.place.mapper.to_host(source),
            "file": source.name,
            "preview": f"{PREVIEW_PREFIX}{row[0]}{_JPEG}" if row else "",
        }
    if why.runner is not None:
        view["runner"] = _("{name} comes close too: resemblance {score}.").format(
            name=why.runner.name, score=f"{why.runner.score:.2f}"
        )
    return view


def _said(why: Why) -> str:
    """How a face got its name, in one sentence with the figures.

    Args:
        why: The reason.

    Returns:
        The sentence.
    """
    if why.how is How.CONFIRMED:
        return _("Confirmed by you on the people page: it is a face of reference.")
    if why.how is How.ASSIGNED:
        return _(
            "Close to a face you confirmed: resemblance {score}, a name is given "
            "from {threshold} ([people] similarity)."
        ).format(score=f"{why.score:.2f}", threshold=f"{why.threshold:.2f}")
    return _("No name any more: resemblance {score}, below {threshold}.").format(
        score=f"{why.score:.2f}", threshold=f"{why.threshold:.2f}"
    )
