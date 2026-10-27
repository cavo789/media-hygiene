"""The sockets a page's server listens on: the PC's door, and the home network's (0384).

The PC's door listens on the page's port, the home network's on `LAN_DOOR_PORT` only
when `mh --lan` asked for it: every request of the second one is marked `Door.LAN`,
so that no header can make it pass for the PC.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.review.doors import Door, lan_door_port
from media_hygiene.review.serving import serve_connection

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable

    from media_hygiene.review.http import Request, Response

    type Handle = Callable[[Request], Awaitable[Response]]

# Every interface of the container: Docker forwards the published ports to it.
LISTEN_HOST: Final = "0.0.0.0"  # noqa: S104


def lan_handle(handle: Handle) -> Handle:
    """Mark every request as come in by the home network's door, then answer it.

    Args:
        handle: Answers a request.

    Returns:
        The same, for the home network's socket.
    """

    async def marked(request: Request) -> Response:
        """Answer the request as come in by the home network's door.

        Args:
            request: The request.

        Returns:
            The response.
        """
        return await handle(replace(request, door=Door.LAN))

    return marked


@contextlib.asynccontextmanager
async def listening(handle: Handle, port: int) -> AsyncIterator[asyncio.Server]:
    """Listen on the PC's door, and on the home network's under `mh --lan`.

    Args:
        handle: Answers a request.
        port: The page's port (0: any free one).

    Yields:
        The PC's server (its port is the page's).
    """
    lan_port = lan_door_port()
    async with contextlib.AsyncExitStack() as stack:
        server = await asyncio.start_server(
            lambda reader, writer: serve_connection(reader, writer, handle),
            LISTEN_HOST,
            port,
        )
        await stack.enter_async_context(server)
        if lan_port is not None:
            marked = lan_handle(handle)
            lan = await asyncio.start_server(
                lambda reader, writer: serve_connection(reader, writer, marked),
                LISTEN_HOST,
                lan_port,
            )
            await stack.enter_async_context(lan)
        yield server
