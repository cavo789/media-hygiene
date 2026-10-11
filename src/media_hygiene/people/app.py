"""The routes of the people page: the page, the groups, the faces, the photos.

`GET /` serves the page, `GET /api/groups` the groups, `GET /face/<n>.jpg` a face cut
from its photo, `GET /photo/<n>.jpg` the whole photo. Read-only: nothing is written,
not even a preview. Like `review` and `search`: loopback hosts only.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.report.thumbnails import review_preview
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.review.serving import json_response, serve_connection

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.review.http import Request

PAGE_PATH: Final = "/"
GROUPS_PATH: Final = "/api/groups"
FACE_PREFIX: Final = "/face/"
PHOTO_PREFIX: Final = "/photo/"
JPEG: Final = ".jpg"
_GET: Final = "GET"


@dataclass(frozen=True, slots=True)
class PeopleApp:
    """Answers the browser from the board; the pictures come from the worker pool."""

    board: PeopleBoard
    mapper: HostPathMapper
    page: bytes
    executor: Executor

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
        """Route a request.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if not is_local(request):
            message = _("Open the page at 127.0.0.1 or localhost.")
            return Response(HTTPStatus.FORBIDDEN, message.encode())
        if request.method != _GET:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        path = request.path
        if path == PAGE_PATH:
            return Response(HTTPStatus.OK, self.page, ContentType.HTML)
        if path == GROUPS_PATH:
            return json_response(HTTPStatus.OK, self.board.state(self.mapper.to_host))
        if path.endswith(JPEG):
            return await self._picture(path)
        return Response(HTTPStatus.NOT_FOUND)

    async def _picture(self, path: str) -> Response:
        """Render a face or a whole photo in the worker pool.

        Args:
            path: `/face/<n>.jpg` or `/photo/<n>.jpg`.

        Returns:
            The JPEG, or 404 for an unknown number or an undecodable photo.
        """
        for prefix in (FACE_PREFIX, PHOTO_PREFIX):
            if not path.startswith(prefix):
                continue
            face = self.board.face(path.removeprefix(prefix).removesuffix(JPEG))
            if face is None:
                break
            if prefix == PHOTO_PREFIX:
                return await jpeg_response(self.executor, review_preview, face.path)
            loop = asyncio.get_running_loop()
            job = CropJob(face.path, face.box)
            image = await loop.run_in_executor(self.executor, face_crop, job)
            if image is None:
                break
            return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)
        return Response(HTTPStatus.NOT_FOUND)
