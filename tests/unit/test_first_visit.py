"""The first `GET /` of a page started on a folder or a photo goes there, once."""

from __future__ import annotations

import asyncio
from http import HTTPStatus

from media_hygiene.review.http import Request, Response
from media_hygiene.services.first_visit import first_visit

_HOST = {"host": "127.0.0.1:8088"}


class Page:
    """Answers every request with 200."""

    async def handle(self, _request: Request) -> Response:
        """Answer.

        Returns:
            OK.
        """
        return Response(HTTPStatus.OK)


def _get(app: object, path: str) -> Response:
    """A GET of the app."""
    assert hasattr(app, "handle")
    answer = asyncio.run(app.handle(Request("GET", path, _HOST, b"")))
    assert isinstance(answer, Response)
    return answer


def test_the_root_is_sent_to_the_start_page_once() -> None:
    """`mh person x.jpg`: `/` → `/person?path=…` the first time, the page after."""
    app = first_visit(Page(), "person?path=C%3A%5Cx.jpg")
    first = _get(app, "/")
    assert first.status is HTTPStatus.SEE_OTHER
    assert first.headers == ("Location: /person?path=C%3A%5Cx.jpg",)
    assert _get(app, "/").status is HTTPStatus.OK


def test_without_a_query_the_app_is_served_as_it_is() -> None:
    """`mh library`: no redirect at all; another path never redirects."""
    page = Page()
    assert first_visit(page, "") is page
    app = first_visit(page, "?folder=status")
    assert _get(app, "/library").status is HTTPStatus.OK
    assert _get(app, "/").headers == ("Location: /?folder=status",)
