"""Ask a page's app in a test: one request, its JSON answer."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Final, Protocol, runtime_checkable

from media_hygiene.review.http import Request

if TYPE_CHECKING:
    from media_hygiene.review.http import Response

JSON: Final = {"host": "127.0.0.1:8766", "content-type": "application/json"}


@runtime_checkable
class Answering(Protocol):
    """A page's app: answers one request."""

    async def handle(self, request: Request) -> Response:
        """Answer a request.

        Args:
            request: The request.
        """


def call(app: object, route: str, body: object = None) -> Response:
    """Send one request, from the loopback.

    Args:
        app: The page's app (anything answering a request).
        route: `METHOD /path`.
        body: The JSON body, if any.

    Returns:
        The response.
    """
    assert isinstance(app, Answering)
    method, path = route.split()
    data = b"" if body is None else json.dumps(body).encode()
    return asyncio.run(app.handle(Request(method, path, JSON, data)))


def answer(app: object, route: str, body: object = None) -> dict[str, object]:
    """The JSON answer of one request.

    Args:
        app: The page's app (anything answering a request).
        route: `METHOD /path`.
        body: The JSON body, if any.

    Returns:
        The answer, a JSON object.
    """
    result = json.loads(call(app, route, body).body)
    assert isinstance(result, dict)
    return result
