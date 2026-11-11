"""What a device paired as a guest gets (0684): the albums chosen for guests alone.

An allow-list of its own, not a filter over the family's (`lan_paths`):

- `GET /`: 303 to `/albums`, the guest's home page;
- `GET /albums`: the albums' page in its guest mode (read-only, no way to the rest);
- `GET /api/album-list`: the albums ticked *Show to guests* only;
- `GET /api/album/<name>`: such an album; another name answers 404, as unknown;
- `GET /thumb|tv|film/<key>`: a file of such an album only;
- `GET /assets/…`: the theme's images and fonts (nothing private);
- anything else, any `POST`: 404. Never the reports, the search, the docs, the steps.

The list is read on each request (`AlbumShelf.listing`, read again once `albums.json`
changed): an album taken off the guests' list is gone at the next request.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from urllib.parse import unquote

from media_hygiene.i18n.live import Page, page_of
from media_hygiene.review.home_assets import ASSETS_PREFIX, asset_response
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response
from media_hygiene.review.videos import NEAR_POLICY
from media_hygiene.search.views import THUMB_PREFIX
from media_hygiene.share.album_page import ALBUM_LIST_PATH, ALBUM_PREFIX, ALBUMS_PAGE
from media_hygiene.share.album_shelf import shelf_picture
from media_hygiene.share.albums import same_name
from media_hygiene.slideshow.films import FILM_PREFIX
from media_hygiene.slideshow.pictures import TV_PREFIX

if TYPE_CHECKING:
    from media_hygiene.share.album_shelf import AlbumShelf

_PICTURES: Final = (TV_PREFIX, THUMB_PREFIX, FILM_PREFIX)
_GET: Final = "GET"


def guest_albums(listing: dict[str, object]) -> list[dict[str, object]]:
    """The albums of a listing ticked for guests.

    Args:
        listing: `{"albums": [...]}`, as the shelf lists them.

    Returns:
        Those whose `guests` is true.
    """
    albums = listing.get("albums")
    if not isinstance(albums, list):
        return []
    return [a for a in albums if isinstance(a, dict) and a.get("guests") is True]


@dataclass(frozen=True, slots=True)
class AlbumGuestDoor:
    """Answers a guest's device: the guests' albums, their files; 404 otherwise."""

    shelf: AlbumShelf
    page: Page  # the albums' page in its guest mode

    async def answer(self, request: Request) -> Response:
        """Answer a request of a device paired as a guest.

        Args:
            request: A request of the home network's door, from a guest.

        Returns:
            The response; 404 for anything not listed above.
        """
        path = request.path
        if request.method != _GET:
            return Response(HTTPStatus.NOT_FOUND)
        fixed = await self._fixed(path)
        if fixed is not None:
            return fixed
        listing, _keys = await asyncio.to_thread(self.shelf.listing)
        shown = guest_albums(listing)
        if path == ALBUM_LIST_PATH:
            return json_response(HTTPStatus.OK, {"albums": shown})
        names = tuple(str(album.get("name", "")) for album in shown)
        if path.startswith(ALBUM_PREFIX):
            return await self._album(unquote(path.removeprefix(ALBUM_PREFIX)), names)
        if path.startswith(_PICTURES):
            return await self._picture(request, names)
        return Response(HTTPStatus.NOT_FOUND)

    async def _fixed(self, path: str) -> Response | None:
        """The guest's home (`/` leads to the albums' page), the theme's files.

        Args:
            path: The path asked for.

        Returns:
            The redirection, the page or the file; None for another path.
        """
        if path == PAGE_PATH:
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {ALBUMS_PAGE}",))
        if path.startswith(ASSETS_PREFIX):
            return await asset_response(path)
        if path != ALBUMS_PAGE:
            return None
        body = page_of(self.page)
        return Response(HTTPStatus.OK, body, ContentType.HTML, policy=NEAR_POLICY)

    async def _album(self, name: str, names: tuple[str, ...]) -> Response:
        """One album of the guests'; any other answers as unknown.

        Args:
            name: As the address names it.
            names: The guests' albums.

        Returns:
            Its view; 404 for an album not shown to guests.
        """
        if same_name(name) not in {same_name(each) for each in names}:
            return Response(HTTPStatus.NOT_FOUND)
        keyed = await asyncio.to_thread(self.shelf.album, name)
        if keyed is None:
            return Response(HTTPStatus.NOT_FOUND)
        return json_response(HTTPStatus.OK, keyed[0])

    async def _picture(self, request: Request, names: tuple[str, ...]) -> Response:
        """A file of an album of the guests'.

        Args:
            request: `GET /thumb|tv|film/<key>`.
            names: The guests' albums.

        Returns:
            The picture; 404 for a file of no such album.
        """
        keys: frozenset[int] = frozenset()
        for name in names:
            keyed = await asyncio.to_thread(self.shelf.album, name)
            keys |= frozenset() if keyed is None else keyed[1]
        asked = Request(_GET, request.path, request.headers, door=request.door)
        return await shelf_picture(self.shelf, keys, asked)
