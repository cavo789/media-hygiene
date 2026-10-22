"""JPEG previews, generated in worker processes: small for reports, large for review."""

from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import Image, ImageFile, ImageOps

from media_hygiene.constants import THUMBNAILS_DIR_NAME, MediaKind
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.image_check import prepare_image_worker
from media_hygiene.scan.raw_check import raw_errors, raw_preview

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.models import MediaFile

PREVIEWABLE: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW})
# Large enough to judge sharpness on a screen, small enough to load at once.
REVIEW_EDGE: Final = 1600
_REVIEW_QUALITY: Final = 88
_THUMBNAIL_NAME_LENGTH = 20


def picture_errors() -> tuple[type[Exception], ...]:
    """What decoding a damaged or truncated picture raises, RAW files included.

    A function, not a constant: LibRaw's errors load LibRaw, only once a picture is
    decoded.

    Returns:
        The exception types.
    """
    return (
        ValueError,
        SyntaxError,
        EOFError,
        Image.DecompressionBombError,
        *raw_errors(),
    )


def unreadable_errors() -> tuple[type[Exception], ...]:
    """What reading a picture raises, from its file on disk to its pixels.

    Returns:
        The exception types: those of `picture_errors`, and `OSError`.
    """
    return (*picture_errors(), OSError)


def thumbnail_name(file: MediaFile) -> str:
    """Return a stable, collision-free preview file name for `file`.

    Args:
        file: The media file.

    Returns:
        A relative path such as `thumbs/0f3a....jpg`.
    """
    return preview_name(file.path)


def preview_name(path: Path) -> str:
    """Return a stable, collision-free preview file name for a picture.

    Args:
        path: The picture, container path.

    Returns:
        A relative path such as `thumbs/0f3a....jpg`.
    """
    digest = hashlib.sha256(str(path).encode()).hexdigest()[:_THUMBNAIL_NAME_LENGTH]
    return f"{THUMBNAILS_DIR_NAME}/{digest}.jpg"


def jpeg_preview(source: Path, edge: int) -> bytes | None:
    """Render a picture as an upright JPEG, its longer side at most `edge` pixels.

    Runs in a worker process: the review page, and the photos a local model sees.

    Args:
        source: Image or RAW file.
        edge: The longer side, in pixels.

    Returns:
        The JPEG bytes, or None when the picture cannot be decoded.
    """
    return fitted_jpeg(source, JpegFit((edge, edge), _REVIEW_QUALITY))


@dataclass(frozen=True, slots=True)
class JpegFit:
    """The largest width and height of a JPEG, and its quality."""

    box: tuple[int, int]
    quality: int


def fitted_jpeg(source: Path, fit: JpegFit) -> bytes | None:
    """Render a picture as an upright baseline JPEG fitted into a box.

    Runs in a worker process.

    Args:
        source: Image or RAW file.
        fit: The box and the quality.

    Returns:
        The JPEG bytes, or None when the picture cannot be decoded.
    """
    prepare_image_worker()
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        preview = upright_picture(source, max(fit.box))
        preview.thumbnail(fit.box)
        buffer = io.BytesIO()
        preview.save(buffer, "JPEG", quality=fit.quality)
    except unreadable_errors():
        return None
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = False
    return buffer.getvalue()


def upright_picture(source: Path, edge: int | None = None) -> Image.Image:
    """Open a picture as seen: an image, or the preview embedded in a RAW file.

    Shown at most `edge` pixels wide, a JPEG is decoded at a reduced scale (1/2, 1/4
    or 1/8, by libjpeg) still at least that large: 2.5 to 3.8 times faster than the
    whole picture (measured, TODO 0154). Without `edge` (faces), the whole picture.

    Args:
        source: Image or RAW file.
        edge: The longer side it will be shown at, None for the full picture.

    Returns:
        The picture, upright, in RGB.
    """
    if media_kind(source) is MediaKind.RAW:
        return raw_preview(source).convert("RGB")
    with Image.open(source) as image:
        if edge is not None:
            width, height = image.size
            scale = edge / max(width, height, 1)
            if scale < 1:
                image.draft(None, (math.ceil(width * scale), math.ceil(height * scale)))
        return ImageOps.exif_transpose(image).convert("RGB")
