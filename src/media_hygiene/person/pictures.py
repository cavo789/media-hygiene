"""The pictures of `/person`: a face cut out, its photo small or large (worker pool).

A face of the index is cut from its photo on request; a face found by a second look
keeps the picture cut then (its box is in a turned picture). Never written anywhere:
the photos go through the preview cache like on the other pages.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.person.routes import FACE_PREFIX, JPEG, PREVIEW_PREFIX, THUMB_PREFIX
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.search.thumbs import GRID_EDGE

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.person.shelf import FaceShelf, ShelfFace


@dataclass(frozen=True, slots=True)
class PersonPictures:
    """The faces of the shelf, cut out or whole."""

    shelf: FaceShelf
    executor: Executor
    previews: Path | None = None  # the cache folder of previews, if any

    async def answer(self, path: str) -> Response:
        """A face cut out, or its photo small or large, from the worker pool.

        Args:
            path: `<prefix><n>.jpg`.

        Returns:
            The JPEG; 404 for an unknown number or a photo that cannot be shown.
        """
        for prefix, edge in ((THUMB_PREFIX, GRID_EDGE), (PREVIEW_PREFIX, REVIEW_EDGE)):
            if path.startswith(prefix):
                face = self.shelf.face(path.removeprefix(prefix).removesuffix(JPEG))
                if face is None:
                    break
                render = PreviewPool(self.executor, self.previews).renderer(edge)
                return await jpeg_response(self.executor, render, face.path)
        if path.startswith(FACE_PREFIX):
            face = self.shelf.face(path.removeprefix(FACE_PREFIX).removesuffix(JPEG))
            image = None if face is None else await self._crop(face)
            if image is not None:
                return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)
        return Response(HTTPStatus.NOT_FOUND)

    async def _crop(self, face: ShelfFace) -> bytes | None:
        """The picture of a face: kept by the second look, or cut from its photo.

        Args:
            face: The face.

        Returns:
            The JPEG; None when the photo cannot be decoded.
        """
        if face.crop is not None or face.box is None:
            return face.crop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor, face_crop, CropJob(face.path, face.box)
        )
