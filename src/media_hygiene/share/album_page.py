"""The albums on a phone at home (0297): the list, an album, its pictures, its changes.

Served by the home page's server, in front of it, to the PC and to a phone paired by
`mh --lan` (`review.lan_app` lets these paths through, `Origin` checked):

- `GET /albums`: the page; `GET /api/album-list`: every album, its cover, dates and
  place; `GET /api/album/<name>`: one album, its photos and videos by day;
- `GET /thumb/<key>.jpg`, `/tv/<key>.jpg` (the picture sized for a phone) and
  `/film/<key>.<ext>`: the files **of an album** only, never another file of the
  library, nor an original;
- `POST /api/albums`: a file of an album added to an album or taken out (0295 item 4:
  a phone's only write besides the audit; no photo touched).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from urllib.parse import unquote

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.videos import NEAR_POLICY
from media_hygiene.search.views import THUMB_PREFIX
from media_hygiene.share.album_api import ALBUMS_PATH
from media_hygiene.slideshow.films import FILM_PREFIX
from media_hygiene.slideshow.pictures import TV_PREFIX

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request
    from media_hygiene.share.album_api import AlbumDesk
    from media_hygiene.share.album_shelf import AlbumShelf, Keyed, Shown

ALBUMS_PAGE: Final = "/albums"
ALBUM_LIST_PATH: Final = "/api/album-list"
ALBUM_PREFIX: Final = "/api/album/"
# What a paired phone may ask of the albums (`review.lan_app`): reads, and one write.
PHONE_READS: Final = frozenset({ALBUMS_PAGE, ALBUM_LIST_PATH})
PHONE_READ_PREFIXES: Final = (ALBUM_PREFIX, TV_PREFIX, THUMB_PREFIX, FILM_PREFIX)
PHONE_WRITES: Final = frozenset({ALBUMS_PATH})
_PICTURE_PREFIXES: Final = (TV_PREFIX, THUMB_PREFIX, FILM_PREFIX)
_GET, _POST = "GET", "POST"


@dataclass(frozen=True, slots=True)
class AlbumParts:
    """The page, the albums, and the desk saving their changes."""

    page: bytes
    shelf: AlbumShelf
    desk: AlbumDesk
    shown: Shown  # shared with the desk: a change names an album's files only


@dataclass(frozen=True, slots=True)
class AlbumPages:
    """In front of the home page: answers the albums' paths, passes on the rest."""

    home: Handling
    parts: AlbumParts

    async def handle(self, request: Request) -> Response:
        """Answer an album's path from the loopback; pass anything else on.

        Args:
            request: The request (a phone's names the loopback by now).

        Returns:
            The response.
        """
        if not is_local(request):
            return await self.home.handle(request)
        if request.method == _POST and request.path in PHONE_WRITES:
            refused = refused_post(request)
            if refused is not None:
                return refused
            return await self.parts.desk.answer(request.body)
        answer = await self._get(request) if request.method == _GET else None
        return await self.home.handle(request) if answer is None else answer

    async def _get(self, request: Request) -> Response | None:
        """Answer a `GET` of the albums: the page, the list, an album, a picture.

        Args:
            request: The request.

        Returns:
            The response; None for a path of the home page.
        """
        path = request.path
        if path == ALBUMS_PAGE:
            page = self.parts.page
            return Response(HTTPStatus.OK, page, ContentType.HTML, policy=NEAR_POLICY)
        if path == ALBUM_LIST_PATH:
            return await self._read(None)
        if path.startswith(ALBUM_PREFIX):
            return await self._read(unquote(path.removeprefix(ALBUM_PREFIX)))
        if path.startswith(_PICTURE_PREFIXES):
            return await self._picture(request)
        return None

    async def _read(self, name: str | None) -> Response:
        """The list of the albums, or one album; their files may be shown from now.

        Args:
            name: The album; None for the list.

        Returns:
            The JSON; 404 for an unknown album, 409 when the albums cannot be read.
        """
        shelf = self.parts.shelf
        try:
            if name is None:
                keyed: Keyed | None = await asyncio.to_thread(shelf.listing)
            else:
                keyed = await asyncio.to_thread(shelf.album, name)
        except MediaHygieneError as exc:
            said = " ".join(part for part in (exc.message, exc.tip) if part)
            return json_response(HTTPStatus.CONFLICT, {"error": said})
        if keyed is None:
            return Response(HTTPStatus.NOT_FOUND)
        view, keys = keyed
        shown = self.parts.shown
        shown.keys = keys if name is None else shown.keys | keys
        return json_response(HTTPStatus.OK, view)

    async def _picture(self, request: Request) -> Response:
        """A thumbnail, a picture or a video of an album's file; 404 for any other.

        Args:
            request: The request.

        Returns:
            The JPEG or the video; 404 for a file in no album.
        """
        key = request.path.rsplit("/", 1)[-1].split(".", 1)[0]
        shown = self.parts.shown
        if key.isdigit() and int(key) not in shown.keys:
            await self._read(None)  # an album changed since: its files, read again
        try:
            with self.parts.shelf.pictures(shown.keys) as pictures:
                answer = await pictures.answer(request)
        except MediaHygieneError:
            answer = None
        return Response(HTTPStatus.NOT_FOUND) if answer is None else answer
