"""The photos of a cluster on the map page: their list, and their previews.

`GET /api/cluster/<rank>` lists the first photos of a cluster; `GET /preview/<key>.jpg`
renders one in the worker pool, kept in the cache folder like `review`'s. The photo
folders are mounted read-only: nothing is written next to the photos.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.places.board import JPEG
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.review.serving import json_response
from media_hygiene.review.views import PREVIEW_PREFIX
from media_hygiene.search.thumbs import GRID_EDGE

if TYPE_CHECKING:
    from media_hygiene.places.board import PlacesBoard
    from media_hygiene.report.preview_cache import PreviewPool

CLUSTER_PREFIX: Final = "/api/cluster/"


async def photo_response(
    path: str, board: PlacesBoard, pool: PreviewPool | None
) -> Response | None:
    """Serve the photos of a cluster, or one preview.

    Args:
        path: The path asked for.
        board: The map's state, which knows the photos.
        pool: The worker pool and the cache folder; None: no preview is served.

    Returns:
        The response (404 for an unknown cluster or key, or a photo that cannot be
        shown: moved since the audit, or its folder not mounted); None for any
        other path.
    """
    if path.startswith(CLUSTER_PREFIX):
        rank = path.removeprefix(CLUSTER_PREFIX)
        photos = board.photos(int(rank)) if rank.isdigit() else None
        if photos is None:
            return Response(HTTPStatus.NOT_FOUND)
        return json_response(HTTPStatus.OK, {"photos": photos})
    if not path.startswith(PREVIEW_PREFIX):
        return None
    key = path.removeprefix(PREVIEW_PREFIX).removesuffix(JPEG)
    source = board.preview_source(key)
    if pool is None or source is None or path != f"{PREVIEW_PREFIX}{key}{JPEG}":
        return Response(HTTPStatus.NOT_FOUND)
    return await jpeg_response(pool.executor, pool.renderer(GRID_EDGE), source)
