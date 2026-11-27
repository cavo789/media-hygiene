"""The faces of one video for `people_find`: a few frames of it, in the pool (0839)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.faces.video_faces import find_video_faces
from media_hygiene.faces.worker import FaceJob
from media_hygiene.index.face_frames import put_moments
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from media_hygiene.faces.models import PhotoFaces
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.services.people_find import FindDeps


def is_video(photo: PhotoVersion) -> bool:
    """Tell whether a file of the run is a video.

    Args:
        photo: The file.

    Returns:
        True for a video.
    """
    return media_kind(photo.path) is MediaKind.VIDEO


async def video_faces(photo: PhotoVersion, deps: FindDeps) -> PhotoFaces | None:
    """Find the faces of a video in the pool, and keep the moment of each.

    The faces themselves are kept by the caller, as a photo's (`FaceStore.put`).

    Args:
        photo: The video.
        deps: The recipe, the store, the pool.

    Returns:
        Its faces; None when no frame of it could be decoded.
    """
    job = FaceJob(photo.path, photo.size, photo.mtime_ns, deps.recipe)
    loop = asyncio.get_running_loop()
    found = await loop.run_in_executor(deps.executor, find_video_faces, job)
    if found is None:
        return None
    put_moments(deps.store.connection, deps.model, found)
    return found.found
