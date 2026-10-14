"""Decode a RAW file with LibRaw to prove it is readable, and read its preview.

Runs in worker processes, like the image checks. RAW files get no visual facts: they
stay out of near duplicates and bursts, whose tests are tuned on JPEG pictures.

`rawpy` loads LibRaw, a native library: it is imported by the functions that decode
only, so that a command which never opens a picture (`undo`, `history`…) never loads it.
"""

# ruff: noqa: PLC0415
# pylint: disable=import-outside-toplevel

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import ExifTags, Image, ImageOps

from media_hygiene.scan.hashing import digests_of
from media_hygiene.scan.image_check import ImageInspection
from media_hygiene.scan.whole_read import WHOLE_READ_LIMIT, read_whole

if TYPE_CHECKING:
    from pathlib import Path
# LibRaw's `flip`: how the picture must be turned to be seen upright.
_FLIPS: Final = {
    3: Image.Transpose.ROTATE_180,
    5: Image.Transpose.ROTATE_90,
    6: Image.Transpose.ROTATE_270,
}
_UPRIGHT: Final = 1


def inspect_raw(path: Path, limit: int = WHOLE_READ_LIMIT) -> ImageInspection:
    """Unpack every pixel of a RAW file: a truncated or damaged one fails.

    The file is read once (`whole_read`): LibRaw unpacks the bytes the digests come
    from.

    Args:
        path: RAW file.
        limit: The largest file read at once, in bytes (`[scan] read_whole_mb`).

    Returns:
        The decoder error, or nothing to report; its digests.
    """
    import rawpy

    digests = None
    try:
        data = read_whole(path, limit)
        digests = None if data is None else digests_of(data)
        source = str(path) if data is None else io.BytesIO(data)
        with rawpy.imread(source) as raw:
            raw.unpack()
    except raw_errors() as exc:
        return ImageInspection(problem=_describe(exc), digests=digests)
    return ImageInspection(digests=digests)


def raw_errors() -> tuple[type[Exception], ...]:
    """The errors of a damaged RAW file: LibRaw fails in many ways, all "unreadable".

    Returns:
        The exception types.
    """
    # rawpy only re-exports these names to type checkers: take them at the source.
    from rawpy._rawpy import LibRawError, NotSupportedError

    return (LibRawError, NotSupportedError, OSError, MemoryError)


def raw_preview(path: Path) -> Image.Image:
    """Return the preview embedded in a RAW file, upright.

    Cameras embed a JPEG preview; without one, the file is developed at half size.

    Args:
        path: RAW file.

    Returns:
        The preview.
    """
    import rawpy
    from rawpy._rawpy import (
        LibRawNoThumbnailError,
        LibRawUnsupportedThumbnailError,
        ThumbFormat,
    )

    with rawpy.imread(str(path)) as raw:
        try:
            thumb = raw.extract_thumb()
        except LibRawNoThumbnailError, LibRawUnsupportedThumbnailError:
            return Image.fromarray(raw.postprocess(half_size=True))  # already upright
        flip = raw.sizes.flip
    image: Image.Image
    if thumb.format is ThumbFormat.JPEG:
        image = Image.open(io.BytesIO(thumb.data))
        if image.getexif().get(ExifTags.Base.Orientation, _UPRIGHT) != _UPRIGHT:
            return ImageOps.exif_transpose(image)
    else:
        image = Image.fromarray(np.asarray(thumb.data))
    return image.transpose(_FLIPS[flip]) if flip in _FLIPS else image


def _describe(exc: Exception) -> str:
    """Turn a LibRaw error (its message is bytes) into readable text.

    Args:
        exc: The error.

    Returns:
        `<error type>: <message>`.
    """
    message = exc.args[0] if exc.args else ""
    if isinstance(message, bytes):
        message = message.decode(errors="replace")
    return f"{type(exc).__name__}: {message}"
