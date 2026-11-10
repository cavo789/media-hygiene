"""The pictures of the search page: small and large previews, and the originals."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.originals import original_response
from media_hygiene.review.respond import IMMUTABLE_S
from media_hygiene.search.stable_pictures import (
    parsed_name,
    picture_tag,
    still_this_version,
)
from media_hygiene.search.thumbs import GRID_EDGE
from media_hygiene.search.views import (
    JPEG,
    ORIGINAL_PREFIX,
    PREVIEW_PREFIX,
    THUMB_PREFIX,
)

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.search.fts import SearchIndex


@dataclass(frozen=True, slots=True)
class Pictures:
    """Renders the previews in the worker pool, kept in the cache folder."""

    index: SearchIndex
    previews: Path | None  # the cache folder of previews, if any
    executor: Executor

    async def answer(self, path: str) -> Response | None:
        """Serve a preview or an original.

        Args:
            path: The path asked for.

        Returns:
            The response (404 for an unknown key or a file that cannot be shown),
            or None when the path names no picture.
        """
        if path.startswith(ORIGINAL_PREFIX):
            return await original_response(path, self.source)
        for prefix in (THUMB_PREFIX, PREVIEW_PREFIX):
            if path.startswith(prefix) and path.endswith(JPEG):
                return await self._picture(prefix, path)
        return None

    async def _picture(self, prefix: str, path: str) -> Response:
        """Render a small or a large preview in the worker pool.

        A name with the file's version (`12.<tag>`) is kept by the browser for good
        while the file is still that version; an older version's: 404.

        Args:
            prefix: `/thumb/` or `/preview/`.
            path: The path asked for.

        Returns:
            The JPEG, or 404.
        """
        named = parsed_name(path.removeprefix(prefix).removesuffix(JPEG))
        photo = None if named is None else self.index.source_of(named[0])
        if named is None or photo is None:
            return Response(HTTPStatus.NOT_FOUND)
        edge = REVIEW_EDGE if prefix == PREVIEW_PREFIX else GRID_EDGE
        tag = named[1]
        if tag and tag != picture_tag(photo, edge):
            return Response(
                HTTPStatus.NOT_FOUND
            )  # another version: the page lists again
        render = PreviewPool(self.executor, self.previews).renderer(edge)
        loop = asyncio.get_running_loop()
        image = await loop.run_in_executor(self.executor, render, photo.path)
        if image is None:
            return Response(HTTPStatus.NOT_FOUND)
        if tag and (await asyncio.to_thread(still_this_version, photo)) is True:
            return Response(HTTPStatus.OK, image, ContentType.JPEG, max_age=IMMUTABLE_S)
        return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)

    def source(self, key: str) -> Path | None:
        """The file a key names: an original, a video.

        Args:
            key: The key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        photo = self.index.source_of(int(key)) if key.isdigit() else None
        return None if photo is None else photo.path
