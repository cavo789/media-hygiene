"""What the burst review and `review --near` serve alike, beyond the page and its state.

`GET /api/file` the decisions file as read back from the disk,
`GET /original/<key>.<ext>` a file untouched, and `GET /preview/<key>.jpg` a large
preview, rendered in the worker pool.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Protocol

from media_hygiene.errors import DecisionsError
from media_hygiene.report.thumbnails import review_preview
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import choice_failed, jpeg_response
from media_hygiene.review.originals import original_response
from media_hygiene.review.views import ORIGINAL_PREFIX, PREVIEW_PREFIX

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from pydantic import BaseModel

FILE_PATH: Final = "/api/file"
_PREVIEW_SUFFIX: Final = ".jpg"


class ReviewFiles(Protocol):
    """A review session, as far as its files are served."""

    def on_disk(self) -> BaseModel:
        """Read the decisions file back from the disk.

        Returns:
            What it holds.
        """

    def preview_source(self, key: str) -> Path | None:
        """Find the file a preview or an original key names.

        Args:
            key: The key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """


async def file_response(
    path: str, files: ReviewFiles, executor: Executor
) -> Response | None:
    """Serve the decisions file, an original or a preview.

    Args:
        path: The path asked for.
        files: The session, which knows the files.
        executor: The worker pool, for the previews.

    Returns:
        The response (404 for an unknown key, or a preview that cannot be made);
        None for any other path.
    """
    if path == FILE_PATH:
        try:
            found = files.on_disk().model_dump_json().encode()
        except DecisionsError as exc:
            return choice_failed(exc)
        return Response(HTTPStatus.OK, found, ContentType.JSON)
    if path.startswith(ORIGINAL_PREFIX):
        return await original_response(path, files.preview_source)
    if not path.startswith(PREVIEW_PREFIX):
        return None
    key = path.removeprefix(PREVIEW_PREFIX).removesuffix(_PREVIEW_SUFFIX)
    source = files.preview_source(key)
    if source is None or path != f"{PREVIEW_PREFIX}{key}{_PREVIEW_SUFFIX}":
        return Response(HTTPStatus.NOT_FOUND)
    return await jpeg_response(executor, review_preview, source)
