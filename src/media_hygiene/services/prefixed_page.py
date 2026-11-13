"""A page the home server answers under its own prefix (0594), its app built on demand.

Same as `review_here` for the pages that need no audit of their own: the page's paths
are relative to it, so its app answers under the prefix unchanged; the app is built
again each time the page itself is asked for, on the server's current settings — or,
for a `KeptPage` (0804: the people page), only once the index, `/config` or the
settings changed (`KeptState`): its session and *Apply now* go on.
"""

from __future__ import annotations

import asyncio
import dataclasses
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Protocol, override

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.services.kept_state import KeptState, page_key

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.ending import Handling
    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.runtime import Runtime


class ServedPage(Protocol):
    """What the home server's router asks of a page under a prefix."""

    def serves(self, path: str) -> bool:
        """Tell whether a path is this page's.

        Args:
            path: The request's path.

        Returns:
            True when it is.
        """

    async def handle(self, request: Request) -> Response:
        """Answer a request.

        Args:
            request: The request.

        Returns:
            The response.
        """


class PrefixedPage:
    """One page under a prefix: built each time it is opened."""

    def __init__(
        self, page: str, fresh: FreshRuntime, build: Callable[[Runtime], Handling]
    ) -> None:
        """Remember how to build it.

        Args:
            page: Its path, e.g. `/quarantine/`.
            fresh: The server's settings, read again when their files change.
            build: Builds its app; may raise `MediaHygieneError`.
        """
        self._page = page
        self._prefix = page.removesuffix("/")
        self._fresh = fresh
        self._build = build
        self._app: Handling | None = None

    def serves(self, path: str) -> bool:
        """Tell whether a path is this page's.

        Args:
            path: The request's path.

        Returns:
            True for the prefix and every path under it.
        """
        return path == self._prefix or path.startswith(self._page)

    async def handle(self, request: Request) -> Response:
        """Answer a path under the prefix, the prefix taken off.

        Args:
            request: The request.

        Returns:
            The response; the app built again for the page itself; 409 with the
            sentence when it cannot be.
        """
        path = request.path.removeprefix(self._prefix)
        if not path:
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {self._page}",))
        if path == PAGE_PATH and request.method == "GET":
            runtime = self._fresh.runtime()
            try:
                self._app = await asyncio.to_thread(self._built, runtime)
            except MediaHygieneError as exc:
                return Response(HTTPStatus.CONFLICT, str(exc).encode())
        if self._app is None:
            return Response(HTTPStatus.NOT_FOUND)
        return await self._app.handle(dataclasses.replace(request, path=path))

    def _built(self, runtime: Runtime) -> Handling:
        """The app, built again.

        Args:
            runtime: The server's settings now.

        Returns:
            The app.
        """
        return self._build(runtime)


class KeptPage(PrefixedPage):
    """A page whose app is kept while the index, `/config`, settings are the same."""

    _kept: KeptState[Handling] | None = None

    @override
    def _built(self, runtime: Runtime) -> Handling:
        """The app kept, or built again after a change.

        Args:
            runtime: The server's settings now.

        Returns:
            The app.
        """
        if self._kept is None:
            self._kept = KeptState()
        return self._kept.value(
            partial(page_key, runtime), partial(self._build, runtime)
        )
