"""The sockets a page's server listens on: the PC's door, and the home network's (0384).

The PC's door listens on the page's port, the home network's on `LAN_DOOR_PORT` only
when `mh --lan` asked for it: every request of the second one is marked `Door.LAN`,
so that no header can make it pass for the PC. With the certificates of `/lan` (0430)
that door is HTTPS, and a plain HTTP one beside it hands out the authority to install,
and serves the TV's pages under the slideshow (a TV cannot install it).
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.review.doors import LAN_CA_DOOR_PORT, Door, lan_door_port
from media_hygiene.review.lan_address import lan_address
from media_hygiene.review.lan_ca_page import CaDoor
from media_hygiene.review.lan_tls import lan_folder, secure_door
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
async def listening(
    handle: Handle, port: int, plain: Handle | None = None
) -> AsyncIterator[asyncio.Server]:
    """Listen on the PC's door, and on the home network's under `mh --lan`.

    Args:
        handle: Answers a request.
        port: The page's port (0: any free one).
        plain: Answers the plain HTTP door beside the HTTPS one, but the authority.

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
            address = lan_address()
            secure = None if address is None else secure_door(address)
            marked = lan_handle(handle)
            lan = await asyncio.start_server(
                lambda reader, writer: serve_connection(reader, writer, marked),
                LISTEN_HOST,
                lan_port,
                ssl=secure,
            )
            await stack.enter_async_context(lan)
            folder = lan_folder()
            if secure is not None and folder is not None:
                origin = f"https://{address}:{port}"
                screen = None if plain is None else lan_handle(plain)
                door = CaDoor(folder, origin, screen)
                await stack.enter_async_context(await _ca_door(door))
        yield server


async def _ca_door(door: CaDoor) -> asyncio.Server:
    """Listen on the plain HTTP door that hands out the authority (0430).

    Args:
        door: Its pages.

    Returns:
        The server, on `LAN_CA_DOOR_PORT`.
    """
    return await asyncio.start_server(
        lambda reader, writer: serve_connection(reader, writer, door.handle),
        LISTEN_HOST,
        LAN_CA_DOOR_PORT,
    )
