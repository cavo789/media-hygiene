"""The albums' folder on the albums page (0625): the PC's alone, in the home server.

`/api/album-root` (and its `/move`) and `/api/album-make` write on the disk: a phone,
whose request `review.lan_app` marks, is refused here too, not only at its door.
One write at a time, away from the event loop.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.http import Response
from media_hygiene.review.serving import refused_post

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.review.http import Request


@dataclass(frozen=True, slots=True)
class AlbumFolderDoor:
    """Answers the paths of the albums' folder."""

    gets: Mapping[str, Callable[[], Response]]
    posts: Mapping[str, Callable[[bytes], Response]]
    phone_header: str
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def answer(self, request: Request) -> Response | None:
        """Answer one of its paths from the PC.

        Args:
            request: The request.

        Returns:
            The response; 403 to a phone; None for any other path.
        """
        table = self.posts if request.method == "POST" else self.gets
        if request.method not in {"GET", "POST"} or request.path not in table:
            return None
        if self.phone_header in request.headers:
            return Response(HTTPStatus.FORBIDDEN)
        if request.method == "GET":
            return await asyncio.to_thread(self.gets[request.path])
        refused = refused_post(request)
        if refused is not None:
            return refused
        async with self.lock:
            return await asyncio.to_thread(self.posts[request.path], request.body)
