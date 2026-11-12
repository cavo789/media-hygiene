"""Serve one connection of a local page: read the request, answer, close.

Shared by `review` and `places`: each page only says how it answers a request.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass, replace
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.http import (
    BadRequestError,
    ContentType,
    Response,
    read_request,
)
from media_hygiene.review.respond import RUN_TAG, write_response
from media_hygiene.review.versioned import asked_from

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from media_hygiene.review.http import Request

    type Handle = Callable[[Request], Awaitable[Response]]

_DROPPED_CONNECTION: Final = (
    TimeoutError,
    asyncio.IncompleteReadError,
    ConnectionError,
)
_LOGGER: Final = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Served:
    """How a door answers, and the time its head may take (None: the usual 30 s)."""

    handle: Handle
    head_seconds: float | None = None  # shorter on the home network's doors (0682)


async def serve_connection(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, handle: Handle
) -> None:
    """Serve one connection: one request, one response.

    Args:
        reader: What the browser sends.
        writer: Where to answer.
        handle: Answers a well-formed request.
    """
    await serve_within(reader, writer, Served(handle))


async def serve_within(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, served: Served
) -> None:
    """Serve one connection as `served` says.

    Args:
        reader: What the browser sends.
        writer: Where to answer.
        served: Answers a well-formed request, within its time.
    """
    handle = served.handle
    try:
        try:
            read = (
                read_request(reader)
                if served.head_seconds is None
                else read_request(reader, served.head_seconds)
            )
            request = replace(await read, peer=peer_of(writer))
            asked_from(request.query)
        except BadRequestError as exc:
            response = Response(exc.status)
        else:
            response = still_valid(request) or await _answered(request, handle)
        await write_response(writer, response)
    except _DROPPED_CONNECTION:
        pass  # the browser went away: nothing to answer
    finally:
        writer.close()
        with contextlib.suppress(ConnectionError):
            await writer.wait_closed()


def peer_of(writer: asyncio.StreamWriter) -> str:
    """The address of the device at the other end, from the socket itself (0681).

    Args:
        writer: The connection.

    Returns:
        E.g. `192.168.1.37`; empty when the socket does not say.
    """
    peer = writer.get_extra_info("peername")
    return str(peer[0]) if isinstance(peer, tuple) and peer else ""


async def _answered(
    request: Request, handle: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Answer a request; an unexpected error is logged with its trace, then said.

    Without it the connection closed unanswered: the page said it was not running
    any more, though its server ran and had done the work (a move, 2026-11-02).

    Args:
        request: The request.
        handle: Answers it.

    Returns:
        The answer; 500 with the sentence to show after an unexpected error.
    """
    try:
        return await handle(request)
    except Exception as exc:  # pylint: disable=broad-exception-caught  # logged, answered
        _LOGGER.exception("%s %s", request.method, request.path)
        said = _(
            "mh met an unexpected error ({reason}): what it did before stays done."
            " Its window shows the details."
        )
        return json_response(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            {"error": said.format(reason=f"{type(exc).__name__}: {exc}")},
        )


def still_valid(request: Request) -> Response | None:
    """Answer 304 when the browser holds a copy made by this run.

    Only cacheable answers carry `RUN_TAG`, so only their copies are asked about;
    a part of a video (`Range`) is always sent.

    Args:
        request: The request.

    Returns:
        304, or None to answer the request.
    """
    headers = request.headers
    if headers.get("if-none-match") != RUN_TAG or "range" in headers:
        return None
    return Response(HTTPStatus.NOT_MODIFIED, cacheable=True)


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


def refused_write(request: Request) -> Response | None:
    """`refused_post`, for a route that also answers another method.

    Args:
        request: The request.

    Returns:
        405 for a method other than `POST`, else what `refused_post` says.
    """
    if request.method != "POST":
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    return refused_post(request)
