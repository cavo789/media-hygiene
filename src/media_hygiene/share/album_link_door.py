"""The routes of an album's link (0462): `/a/<token>` on the LAN door, before pairing.

- `GET /a/<token>`: the albums' page, read-only, on that album alone;
- `GET /a/<token>/api/album/…`: that album's view, its pictures' addresses under the
  link; `GET /a/<token>/thumb|tv|film/<key>`: the files **of that album** only;
- anything else, any `POST`: 404, as an unknown, expired or stopped token.

On the PC (loopback only, never listed in `lan_paths`): `POST /api/album-link` makes an
album's link (its address, its QR code, its hours) or stops it.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

import segno
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.serving import json_response
from media_hygiene.review.videos import NEAR_POLICY
from media_hygiene.search.views import THUMB_PREFIX
from media_hygiene.share.album_links import LINK_HOURS, AlbumLinks
from media_hygiene.slideshow.films import FILM_PREFIX
from media_hygiene.slideshow.pictures import TV_PREFIX

if TYPE_CHECKING:
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.share.album_shelf import AlbumShelf

LINK_PREFIX: Final = "/a/"
ALBUM_LINK_PATH: Final = "/api/album-link"
_VIEW: Final = "api/album/"
_PICTURES: Final = (TV_PREFIX, THUMB_PREFIX, FILM_PREFIX)
_QR_SCALE: Final = 4
_MAX_NAME: Final = 200


class LinkAsked(BaseModel):
    """`POST /api/album-link`: make an album's link, or stop it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["make", "stop"]
    album: str = Field(min_length=1, max_length=_MAX_NAME)


@dataclass(frozen=True, slots=True)
class AlbumLinkDoor:
    """Answers an album's link from the home network, and the PC making one."""

    shelf: AlbumShelf
    page: bytes  # the albums' page in its read-only link mode
    links: AlbumLinks = field(default_factory=AlbumLinks)

    async def answer(self, request: Request) -> Response:
        """Answer `/a/<token>…`: the page, the view, a picture of that album.

        Args:
            request: A request of the home network's door under `/a/`.

        Returns:
            The response; 404 for anything else, whatever the token.
        """
        token, _slash, rest = request.path.removeprefix(LINK_PREFIX).partition("/")
        name = self.links.opened(token)
        if request.method != "GET" or name is None:
            return Response(HTTPStatus.NOT_FOUND)
        if not rest:
            return Response(
                HTTPStatus.OK, self.page, ContentType.HTML, policy=NEAR_POLICY
            )
        keyed = await asyncio.to_thread(self.shelf.album, name)
        if keyed is None:
            return Response(HTTPStatus.NOT_FOUND)
        view, keys = keyed
        if rest.startswith(_VIEW):
            moved = {
                key: linked(item, f"{LINK_PREFIX}{token}") for key, item in view.items()
            }
            return json_response(HTTPStatus.OK, moved)
        inner = f"/{rest}"
        if not inner.startswith(_PICTURES):
            return Response(HTTPStatus.NOT_FOUND)
        asked = Request("GET", inner, request.headers, door=request.door)
        try:
            with self.shelf.pictures(keys) as pictures:
                shown = await pictures.answer(asked)
        except MediaHygieneError:
            shown = None
        return Response(HTTPStatus.NOT_FOUND) if shown is None else shown

    async def make(self, request: Request, lan: LanAccess) -> Response:
        """`POST /api/album-link` of the PC: the link, its QR code, or stopped.

        Args:
            request: The request (loopback, checked by the caller).
            lan: The PC's address on the home network.

        Returns:
            `url`, `qr`, `hours` (made) or `stopped`; 400, 404 for an unknown album.
        """
        try:
            asked = LinkAsked.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        if asked.action == "stop":
            return json_response(
                HTTPStatus.OK, {"stopped": self.links.stop(asked.album)}
            )
        keyed = await asyncio.to_thread(self.shelf.album, asked.album)
        if keyed is None:
            return Response(HTTPStatus.NOT_FOUND)
        name = str(keyed[0]["name"])
        link = self.links.shared(name) or self.links.make(name)
        url = f"{lan.origin}{LINK_PREFIX}{link.token}"
        qr = segno.make(url, error="m").svg_inline(
            scale=_QR_SCALE, dark="#000", light="#fff"
        )
        return json_response(HTTPStatus.OK, {"url": url, "qr": qr, "hours": LINK_HOURS})


def linked(value: object, prefix: str) -> object:
    """A view's pictures under the link: `/thumb/1.jpg` → `/a/<t>/thumb/1.jpg`.

    Args:
        value: The view, or a part of it.
        prefix: `/a/<token>`.

    Returns:
        The same view, its pictures' addresses moved.
    """
    if isinstance(value, dict):
        return {key: linked(item, prefix) for key, item in value.items()}
    if isinstance(value, list):
        return [linked(item, prefix) for item in value]
    if isinstance(value, str) and value.startswith(_PICTURES):
        return prefix + value
    return value
