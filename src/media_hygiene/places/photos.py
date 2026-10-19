"""The photos of the map page: of a cluster, of a folder; their previews.

`GET /api/cluster/<rank>` lists the first photos of a cluster, `GET /api/folders` the
folders named after a town or placed (0231), `GET /api/folder/<rank>` the photos
without GPS of one, `GET /api/tree/<rank>` those below any folder of the index (0242);
`GET /preview/<key>.jpg` renders one in the worker pool for the
drawer's grid, `GET /large/<key>.jpg` larger for its viewer (0233), both kept in the
cache folder like `review`'s. The photo folders are mounted read-only: nothing is
written next to the photos.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.places.drawer_rows import JPEG, LARGE_PREFIX
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.review.serving import json_response
from media_hygiene.review.views import PREVIEW_PREFIX
from media_hygiene.search.thumbs import GRID_EDGE

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.places.board import PlacesBoard
    from media_hygiene.places.folders import FolderDesk
    from media_hygiene.report.preview_cache import PreviewPool

CLUSTER_PREFIX: Final = "/api/cluster/"
FOLDERS_PATH: Final = "/api/folders"
FOLDER_PREFIX: Final = "/api/folder/"
TREE_PREFIX: Final = "/api/tree/"


@dataclass(frozen=True, slots=True)
class PhotoSources:
    """Who knows the photos the page shows: the clusters, the folders (if any)."""

    board: PlacesBoard
    folders: FolderDesk | None = None

    def preview_source(self, key: str) -> Path | None:
        """Find the photo a preview key names.

        Args:
            key: The key, from the page.

        Returns:
            The file, or None for a key never listed.
        """
        found = self.board.preview_source(key)
        if found is None and self.folders is not None:
            found = self.folders.preview_source(key)
        return found


async def photo_response(
    path: str, sources: PhotoSources, pool: PreviewPool | None
) -> Response | None:
    """Serve the photos of a cluster or a folder, the folders, or one preview.

    Each preview has two sizes: the grid's, and the viewer's (`LARGE_PREFIX`).

    Args:
        path: The path asked for.
        sources: The map's state and its folders, which know the photos.
        pool: The worker pool and the cache folder; None: no preview is served.

    Returns:
        The response (404 for an unknown cluster or key, or a photo that cannot be
        shown: moved since the audit, or its folder not mounted); None for any
        other path.
    """
    folders = sources.folders
    if path == FOLDERS_PATH:
        found = folders.state() if folders is not None else {"folders": []}
        return json_response(HTTPStatus.OK, found)
    for prefix, lister in (
        (CLUSTER_PREFIX, sources.board.photos),
        (FOLDER_PREFIX, folders.photos if folders is not None else None),
        (TREE_PREFIX, folders.tree_photos if folders is not None else None),
    ):
        if path.startswith(prefix):
            rank = path.removeprefix(prefix)
            photos = lister(int(rank)) if lister and rank.isdigit() else None
            if photos is None:
                return Response(HTTPStatus.NOT_FOUND)
            return json_response(HTTPStatus.OK, {"photos": photos})
    large = path.startswith(LARGE_PREFIX)
    prefix = LARGE_PREFIX if large else PREVIEW_PREFIX
    if not path.startswith(prefix):
        return None
    key = path.removeprefix(prefix).removesuffix(JPEG)
    source = sources.preview_source(key)
    if pool is None or source is None or path != f"{prefix}{key}{JPEG}":
        return Response(HTTPStatus.NOT_FOUND)
    render = pool.renderer(REVIEW_EDGE if large else GRID_EDGE)
    return await jpeg_response(pool.executor, render, source)
