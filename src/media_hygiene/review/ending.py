"""How a local page's server ends: Ctrl+C, `POST /api/stop`, or a step chosen at home.

Every page answers `POST /api/stop` (its "Back to the home page" link) and serves the
theme's `/assets/`: the server ends with code 0, and `mh` opens the home page again.
The home page ends with `STEP_EXIT_BASE + n` when the user chooses step `n`, which `mh`
then runs with the mounts it needs. A page whose tab was closed (`presence`,
`POST /api/alive`) ends with `ExitCode.PAGE_CLOSED`, raised as `PageClosed` for its
command to say so (0262). The server listens on every interface of the container: Docker
publishes the port on the host's loopback only, under the same number.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Protocol

from media_hygiene.constants import ExitCode
from media_hygiene.errors import PageClosed
from media_hygiene.i18n import _
from media_hygiene.review.http import Response, is_local
from media_hygiene.review.presence import PRESENCE_PATH, Presence, presence_response
from media_hygiene.review.serving import json_response, refused_post, serve_connection
from media_hygiene.review.shared_routes import asset_or_page

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.http import Request

# Every interface of the container: Docker forwards the published port to it.
LISTEN_HOST: Final = "0.0.0.0"  # noqa: S104
STOP_PATH: Final = "/api/stop"
STOPPED: Final = (
    0  # the exit code of a page closed from its "Back to the home page" link
)
_POST: Final = "POST"


class Handling(Protocol):
    """A local page: answers one request."""

    async def handle(self, request: Request) -> Response:
        """Answer a request.

        Args:
            request: The request.

        Returns:
            The response.
        """


class Ending:
    """The exit code a page asked for: the first one asked wins."""

    __slots__ = ("_code", "_event")

    def __init__(self) -> None:
        """Start without any code asked for."""
        self._event = asyncio.Event()
        self._code = STOPPED

    def end(self, code: int) -> None:
        """Ask the server to end with a code.

        Args:
            code: The exit code of the command.
        """
        if self._event.is_set():
            return
        self._code = code
        self._event.set()

    @property
    def asked(self) -> int | None:
        """The code asked for so far.

        Returns:
            It, or None while no page asked the server to end.
        """
        return self._code if self._event.is_set() else None

    async def wait(self) -> int:
        """Wait until a page asks the server to end.

        Returns:
            The code asked for.
        """
        await self._event.wait()
        return self._code


@dataclass(frozen=True, slots=True)
class EndingDoor:
    """Serves a page's connections: `POST /api/stop` and `/assets/` for every page.

    With a presence, `POST /api/alive` too: the page ends once no tab shows it.
    """

    app: Handling
    ending: Ending
    presence: Presence | None = None

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
        """Stop on `POST /api/stop`; else the theme's fonts and images, or the page.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.path == PRESENCE_PATH and self.presence is not None:
            return await self._alive(request)
        if request.path != STOP_PATH:
            return await asset_or_page(request, self.app.handle)
        if not is_local(request):
            message = _("Open the review at 127.0.0.1 or localhost.")
            return Response(HTTPStatus.FORBIDDEN, message.encode())
        if request.method != _POST:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        refused = refused_post(request)
        if refused is not None:
            return refused
        self.ending.end(STOPPED)
        return json_response(HTTPStatus.OK, {"stopped": True})

    async def _alive(self, request: Request) -> Response:
        """Answer `POST /api/alive` from the loopback: a tab still shows the page.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if self.presence is None or not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        return await presence_response(self.presence, request)


async def run_server(app: Handling, port: int, ready: Callable[[int], None]) -> int:
    """Listen, tell the port, and serve until cancelled or a page asks to end.

    Args:
        app: Answers each request.
        port: The port to listen on (0: any free one).
        ready: Called with the port actually listened on.

    Returns:
        The exit code the page asked for: 0 after `POST /api/stop`.

    Raises:
        PageClosed: The page's tab was closed and none came back (0262).
    """
    ending = Ending()
    presence = Presence(ending, ExitCode.PAGE_CLOSED)
    return await serve_until_ended(EndingDoor(app, ending, presence), port, ready)


async def serve_until_ended(
    door: EndingDoor, port: int, ready: Callable[[int], None]
) -> int:
    """Serve a door until its page asks to end; the last answers are sent first.

    Args:
        door: The page and how it ends.
        port: The port to listen on (0: any free one).
        ready: Called with the port actually listened on.

    Returns:
        The exit code the page asked for.

    Raises:
        PageClosed: The page's tab was closed and none came back (0262).
    """
    server = await asyncio.start_server(door.connection, LISTEN_HOST, port)
    async with server:
        ready(server.sockets[0].getsockname()[1])
        async with asyncio.TaskGroup() as group:
            serving = group.create_task(server.serve_forever())
            code = await door.ending.wait()
            serving.cancel()
    if code == ExitCode.PAGE_CLOSED:
        raise PageClosed
    return code
