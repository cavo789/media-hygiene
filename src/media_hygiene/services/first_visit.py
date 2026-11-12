"""The first `GET /` of a page server goes to its start page (0405 `--folder`, 0714).

`mh` opens the root of the port, never the address the console prints: a page started
on a folder or on a photo (`?folder=…`, `/person?path=…`) sends that first visit there,
once; every later `/` is the page as usual.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request

_ROOT: Final = "/"
_GET: Final = "GET"


@dataclass(slots=True)
class FirstVisit:
    """A page's app whose first `GET /` is sent to `target` (mutable: once only)."""

    app: Handling
    target: str  # e.g. `/person?path=…`, relative to the root
    sent: bool = field(default=False)

    async def handle(self, request: Request) -> Response:
        """Send the first visit of the root to the start page, then serve as usual.

        Args:
            request: The request.

        Returns:
            A redirect once; the app's answer otherwise.
        """
        if not self.sent and request.method == _GET and request.path == _ROOT:
            self.sent = True
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {self.target}",))
        return await self.app.handle(request)


def first_visit(app: Handling, query: str) -> Handling:
    """The app, its first `/` sent to `query` when there is one.

    Args:
        app: The page's app.
        query: What the console adds to the root's address (`?folder=…`,
            `person?path=…`); empty: the app as it is.

    Returns:
        The app to serve.
    """
    return FirstVisit(app, _ROOT + query) if query else app
