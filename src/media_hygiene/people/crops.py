"""The face pictures of the page: cut from the photo on request, never kept on disk.

A face is shown with some of its surroundings (hair, chin), as a small square JPEG
rendered in the worker pool. The browser keeps it; the cache folder never does.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.image_check import prepare_image_worker

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.models import FaceBox

CROP_EDGE: Final = 160
_MARGIN: Final = 0.3  # of the box's longer side, on each side
_QUALITY: Final = 85


@dataclass(frozen=True, slots=True)
class CropJob:
    """One face to show: its photo and its box."""

    path: Path
    box: FaceBox


def face_crop(job: CropJob) -> bytes | None:
    """Cut a face out of its photo, as a small square JPEG.

    Runs in a worker process.

    Args:
        job: The photo and the box.

    Returns:
        The JPEG bytes, or None when the photo cannot be decoded any more.
    """
    prepare_image_worker()
    try:
        picture = upright_picture(job.path)
    except unreadable_errors():
        return None
    box = job.box
    side = max(box.width, box.height) * (1 + 2 * _MARGIN)
    left = box.x + box.width / 2 - side / 2
    top = box.y + box.height / 2 - side / 2
    area = (round(left), round(top), round(left + side), round(top + side))
    face = picture.crop(area)
    face.thumbnail((CROP_EDGE, CROP_EDGE))
    buffer = io.BytesIO()
    face.save(buffer, "JPEG", quality=_QUALITY)
    return buffer.getvalue()
