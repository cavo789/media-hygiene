"""The page's address: `/library`; `/search`, its former one, leads to it (0617).

Favourites, bookmarks and links saved before the rename keep working, query string kept.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response

if TYPE_CHECKING:
    from media_hygiene.review.http import Request

LIBRARY_PAGE: Final = "/library"
FORMER_PAGE: Final = "/search"
FORMER_PREFIX: Final = f"{FORMER_PAGE}/"


def moved_page(request: Request) -> Response | None:
    """Send a request for the former address to the page's address.

    Args:
        request: The request.

    Returns:
        A permanent redirect, its sub-path and query kept; None for any other request.
    """
    path = request.path
    if request.method != "GET" or not (
        path == FORMER_PAGE or path.startswith(FORMER_PREFIX)
    ):
        return None
    below = path.removeprefix(FORMER_PAGE).rstrip("/")
    query = f"?{request.query}" if request.query else ""
    location = f"Location: {LIBRARY_PAGE}{below}{query}"
    return Response(HTTPStatus.MOVED_PERMANENTLY, headers=(location,))
