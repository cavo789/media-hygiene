"""`GET`/`POST` of a page's albums API, for the pages adding it to their server (0657).

The phone page and `/person` answer it as the reviews do (`review.app`): `GET` the
albums read from the disk, `POST` a change (or `action: "tv"`, a show), JSON from the
page's own origin only. Each page's desk resolves its keys to files itself, from the
index, never a path sent by the page.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.http import Response, is_local
from media_hygiene.review.serving import refused_post

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request
    from media_hygiene.share.album_api import AlbumDesk


async def album_route(desk: AlbumDesk, request: Request) -> Response:
    """Answer the albums API.

    Args:
        desk: The page's albums.
        request: A request of its path.

    Returns:
        The albums, or the change saved and read back.
    """
    if request.method == "GET":
        return desk.state()
    return refused_post(request) or await desk.answer(request.body)


@dataclass(frozen=True, slots=True)
class WithAlbums:
    """A page's app, answering its albums API first."""

    app: Handling
    desk: AlbumDesk
    path: str  # where the page asks: `/person/api/albums`

    async def handle(self, request: Request) -> Response:
        """Answer the albums from the loopback, anything else with the page's app.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.path.split("?", 1)[0] != self.path:
            return await self.app.handle(request)
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        return await album_route(self.desk, request)
