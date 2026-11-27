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
from media_hygiene.review.serving import json_response
from media_hygiene.review.versioned import disk_tag

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.people.board import PeopleBoard

FACE_PREFIX: Final = "/face/"
PHOTO_PREFIX: Final = "/photo/"
TAG_PREFIX: Final = "/api/photo-tag/"
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


def photo_tag(board: PeopleBoard, path: str) -> Response:
    """`GET /api/photo-tag/<n>`: the version of face `n`'s photo, on opening (0799).

    The large view asks it once, when it opens: a `stat` of the one photo shown, never
    one per tile at page load. The browser then asks `/photo/<n>.jpg?v=<tag>` and may
    keep the picture for good (`review/versioned`).

    Args:
        board: The board of faces.
        path: `/api/photo-tag/<n>`.

    Returns:
        `{"tag": ...}` (empty when the file cannot be read), or 404 for an unknown face.
    """
    face = board.face(path.removeprefix(TAG_PREFIX))
    if face is None:
        return Response(HTTPStatus.NOT_FOUND)
    return json_response(HTTPStatus.OK, {"tag": disk_tag(face.path)})
