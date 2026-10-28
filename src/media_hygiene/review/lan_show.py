"""The one step a paired phone may start: an album saved on the PC, on the TV (0444).

`POST /api/step` stays the PC's (`write_routes`), but for this body only:
`{"name": "slideshow-album", "fields": {"album": <name>}}`, the name one of the albums
of `albums.json` as the home page lists them (`GET /api/album-list`): no free text.
It then goes on to the home page as the PC's would: an `mh` that keeps the home server
up answers with the page `/slideshow/album/<name>`, the show served by the home server
itself (0417; `album_show`); an older one runs `slideshow --album <name> --lan`.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.http import Request
from media_hygiene.review.lan_paths import PHONE_STEPS
from media_hygiene.review.serving import json_response
from media_hygiene.share.album_page import ALBUM_LIST_PATH

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Response


class _Asked(BaseModel):
    """The step asked: its name and its one field."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    fields: dict[str, str]


def asked_album(body: bytes) -> str | None:
    """The album a phone asks to show, when the body is exactly that step.

    Args:
        body: The `POST`'s body.

    Returns:
        The album's name; None for any other step or body.
    """
    try:
        asked = _Asked.model_validate_json(body)
    except ValidationError:
        return None
    if asked.name not in PHONE_STEPS or set(asked.fields) != {"album"}:
        return None
    return asked.fields["album"].strip() or None


async def saved_albums(home: Handling, request: Request) -> frozenset[str]:
    """The names of the albums saved on the PC, as the home page lists them.

    Args:
        home: The home page.
        request: The phone's request, naming the loopback by now.

    Returns:
        The names, case folded; none when the list cannot be read.
    """
    headers = {"host": request.headers.get("host", "")}
    answer = await home.handle(Request("GET", ALBUM_LIST_PATH, headers, b""))
    if answer.status is not HTTPStatus.OK:
        return frozenset()
    try:
        albums = json.loads(answer.body).get("albums", [])
        return frozenset(str(album["name"]).casefold() for album in albums)
    except ValueError, TypeError, KeyError, AttributeError:
        return frozenset()


async def phone_step(home: Handling, request: Request) -> Response:
    """Pass the album's show to the home page; refuse any other step.

    Args:
        home: The home page.
        request: `POST /api/step` of a paired phone, naming the loopback by now.

    Returns:
        The home page's answer; 403 for another step or an album not saved.
    """
    album = asked_album(request.body)
    if album is not None and album.casefold() in await saved_albums(home, request):
        return await home.handle(request)
    message = _(
        "From a phone, only an album saved on the PC goes on the TV; run any other "
        "step on the PC."
    )
    return json_response(HTTPStatus.FORBIDDEN, {"error": message})
