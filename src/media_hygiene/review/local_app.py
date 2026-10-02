"""What the burst and the sort reviews share: loopback only, page, previews, errors.

Each review only says how it answers a request from the loopback (`answer`).
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import json_response, serve_connection

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor
    from pathlib import Path

    from pydantic import BaseModel

    from media_hygiene.review.http import Request

PAGE_PATH: Final = "/"
STATE_PATH: Final = "/api/state"


class LocalApp(ABC):
    """A local page: refuses other hosts, then answers one request per connection."""

    __slots__ = ()

    async def connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Serve one connection: one request, one response.

        Args:
            reader: What the browser sends.
            writer: Where to answer.
        """
        await serve_connection(reader, writer, self.handle)

    async def handle(self, request: Request) -> Response:
        """Refuse a request naming another host, else answer it.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if not is_local(request):
            message = _("Open the review at 127.0.0.1 or localhost.")
            return Response(HTTPStatus.FORBIDDEN, message.encode())
        return await self.answer(request)

    @abstractmethod
    async def answer(self, request: Request) -> Response:
        """Answer a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """


def page_or_state(path: str, page: bytes, state: Callable[[], BaseModel]) -> Response:
    """Serve the page itself, or its state.

    Args:
        path: The path asked for.
        page: The page.
        state: Builds the state, only when asked for.

    Returns:
        The response; 404 for any other path.
    """
    if path == PAGE_PATH:
        return Response(HTTPStatus.OK, page, ContentType.HTML)
    if path == STATE_PATH:
        return Response(
            HTTPStatus.OK, state().model_dump_json().encode(), ContentType.JSON
        )
    return Response(HTTPStatus.NOT_FOUND)


async def jpeg_response(
    executor: Executor, render: Callable[[Path], bytes | None], source: Path
) -> Response:
    """Render a preview in the worker pool.

    Args:
        executor: The worker pool.
        render: Makes the JPEG, or None when the file cannot be shown.
        source: The file, in the container.

    Returns:
        The JPEG, cached by the browser; 404 when it cannot be made.
    """
    loop = asyncio.get_running_loop()
    image = await loop.run_in_executor(executor, render, source)
    if image is None:
        return Response(HTTPStatus.NOT_FOUND)
    return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)


def choice_failed(exc: DecisionsError | OSError) -> Response:
    """Answer a choice that was refused, or could not be saved.

    Args:
        exc: Why.

    Returns:
        422 with the reason, or 500 when the decisions file could not be written.
    """
    if isinstance(exc, DecisionsError):
        return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": exc.message})
    message = _("Cannot save the decisions file: {error}.")
    error = message.format(error=exc.strerror or exc)
    return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": error})
