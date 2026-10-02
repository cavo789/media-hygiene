"""Serve one connection of a local page: read the request, answer, close.

Shared by `review` and `places`: each page only says how it answers a request.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Protocol

from media_hygiene.review.http import (
    BadRequestError,
    ContentType,
    Response,
    read_request,
    write_response,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from media_hygiene.review.http import Request

_DROPPED_CONNECTION: Final = (
    TimeoutError,
    asyncio.IncompleteReadError,
    ConnectionError,
)


class Connected(Protocol):
    """A local page: serves each connection the browser opens."""

    async def connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Serve one connection.

        Args:
            reader: What the browser sends.
            writer: Where to answer.
        """


async def serve_connection(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    handle: Callable[[Request], Awaitable[Response]],
) -> None:
    """Serve one connection: one request, one response.

    Args:
        reader: What the browser sends.
        writer: Where to answer.
        handle: Answers a well-formed request.
    """
    try:
        try:
            request = await read_request(reader)
        except BadRequestError as exc:
            response = Response(exc.status)
        else:
            response = await handle(request)
        await write_response(writer, response)
    except _DROPPED_CONNECTION:
        pass  # the browser went away: nothing to answer
    finally:
        writer.close()
        with contextlib.suppress(ConnectionError):
            await writer.wait_closed()


def json_response(status: HTTPStatus, value: dict[str, object]) -> Response:
    """Answer with a JSON object.

    Args:
        status: The status.
        value: The object.

    Returns:
        The response.
    """
    return Response(status, json.dumps(value).encode(), ContentType.JSON)


def refused_post(request: Request) -> Response | None:
    """Refuse a POST that is not JSON from the page itself.

    A page of another site cannot send JSON without the browser asking first, and
    its `Origin` names it.

    Args:
        request: The request.

    Returns:
        415 without a JSON body, 403 from another origin, None when acceptable.
    """
    headers = request.headers
    if not headers.get("content-type", "").startswith(ContentType.JSON):
        return Response(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
    origin = headers.get("origin")
    if origin is not None and origin != f"http://{headers.get('host')}":
        return Response(HTTPStatus.FORBIDDEN)
    return None
