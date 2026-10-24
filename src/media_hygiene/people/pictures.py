"""`GET /face/<n>.jpg` and `/photo/<n>.jpg`: a face cut out, or its whole photo.

Rendered in the worker pool on request; the faces are never written anywhere, the
photos go through the preview cache like on the other pages.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import jpeg_response

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.people.board import PeopleBoard

FACE_PREFIX: Final = "/face/"
PHOTO_PREFIX: Final = "/photo/"
JPEG: Final = ".jpg"


@dataclass(frozen=True, slots=True)
class FacePictures:
    """The faces of the board, cut out or whole, from the worker pool."""

    board: PeopleBoard
    executor: Executor
    previews: Path | None = None  # the cache folder of previews, if any

    async def answer(self, path: str) -> Response:
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
                return await jpeg_response(
                    self.executor,
                    PreviewPool(self.executor, self.previews).renderer(REVIEW_EDGE),
                    face.path,
                )
            image = await asyncio.get_running_loop().run_in_executor(
                self.executor, face_crop, CropJob(face.path, face.box)
            )
            if image is None:
                break
            return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)
        return Response(HTTPStatus.NOT_FOUND)
