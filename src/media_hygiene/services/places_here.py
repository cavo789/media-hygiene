"""The map of `places` served by the home server itself, under `/places/` (0417).

A click on *Name your places on a map* used to stop the home server, start a container
for the map and wait for it. Now the home server answers it: each time the page itself
is asked for, the clusters and folders are read again from the index and
`config.toml` (the towns once per process, `towns_once`), and the map's app answers
under the prefix, its addresses relative to the page. Places are saved into
`config.toml` as before; the server's settings follow (`FreshRuntime`).
"""

from __future__ import annotations

import asyncio
import dataclasses
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import ConfigError, MountError
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.http import Request, Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.step_watch import PLACES_PAGE
from media_hygiene.services.next_command import NextVerb
from media_hygiene.services.places import open_places
from media_hygiene.services.places_build import places_app

if TYPE_CHECKING:
    from media_hygiene.places.app import PlacesApp
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer

PLACES_PREFIX: Final = PLACES_PAGE.removesuffix("/")
_AGAIN: Final = NextVerb("places", (MountKind.CONFIG, MountKind.CACHE))


class PlacesHere:
    """The map: built again each time its page is opened."""

    def __init__(self, fresh: FreshRuntime, server: HomeServer) -> None:
        """Remember how to build it.

        Args:
            fresh: The server's settings, read again when their files change.
            server: The home server's pool.
        """
        self._fresh = fresh
        self._server = server
        self._app: PlacesApp | None = None

    async def handle(self, request: Request) -> Response:
        """Answer a path under `/places`, the prefix taken off.

        Args:
            request: The request, its path under the prefix.

        Returns:
            The response; the map itself rebuilt first.
        """
        path = request.path.removeprefix(PLACES_PREFIX)
        if not path:  # its paths are relative to `/places/`
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {PLACES_PAGE}",))
        if path == PAGE_PATH and request.method == "GET":
            try:
                self._app = await asyncio.to_thread(self._build)
            except (MountError, ConfigError) as exc:
                text = str(exc) if exc.tip is None else f"{exc}\n{exc.tip}"
                return Response(HTTPStatus.CONFLICT, text.encode())
        if self._app is None:
            return Response(HTTPStatus.NOT_FOUND)
        return await self._app.handle(dataclasses.replace(request, path=path))

    def _build(self) -> PlacesApp:
        """Read the clusters, the folders and the places saved.

        Returns:
            The map's app.
        """
        runtime = self._fresh.runtime()
        opened = open_places(runtime, _AGAIN)
        return places_app(runtime, opened, self._server.executor)
