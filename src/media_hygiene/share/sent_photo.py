"""One photo made ready to send: upright, fitted, its GPS position removed (0296).

The copy is a baseline JPEG: the EXIF orientation applied (then set to 1), the long
side fitted into `long_side_px`, the given quality. What the EXIF says is kept (the
date, the camera, the description, the copyright), except:

- the GPS position, unless asked: a photo sent must not say where the house is;
- the maker's notes, private to each brand, which may hold a serial number.

The XMP packet is never copied: it may repeat the position, and its description is
also in the EXIF when Windows wrote it. A RAW file gives its embedded preview and no
EXIF. The original is only read. Runs in the worker pool.
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import ExifTags, Image, ImageFile

from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.image_check import prepare_image_worker

if TYPE_CHECKING:
    from pathlib import Path

_ORIENTATION: Final = 0x0112
_UPRIGHT: Final = 1
_MAKER_NOTE: Final = 0x927C


@dataclass(frozen=True, slots=True)
class SendJob:
    """How each photo is made: its long side, its quality, its position kept or not."""

    long_side_px: int
    quality: int
    keep_gps: bool = False


def sent_jpeg(job: SendJob, source: Path) -> bytes | None:
    """Make the copy of one photo to send.

    Args:
        job: The size, the quality, the GPS kept or not.
        source: The photo, in the container; only read.

    Returns:
        The JPEG, or None when the photo cannot be decoded.
    """
    prepare_image_worker()
    ImageFile.LOAD_TRUNCATED_IMAGES = True
    try:
        picture = upright_picture(source, job.long_side_px)
        picture.thumbnail((job.long_side_px, job.long_side_px))
        exif, icc = _header(source, keep_gps=job.keep_gps)
        buffer = io.BytesIO()
        picture.save(buffer, "JPEG", quality=job.quality, exif=exif, icc_profile=icc)
    except unreadable_errors():
        return None
    finally:
        ImageFile.LOAD_TRUNCATED_IMAGES = False
    return buffer.getvalue()


def _header(source: Path, *, keep_gps: bool) -> tuple[bytes, bytes | None]:
    """The EXIF to write in the copy, and the colour profile of the photo.

    Args:
        source: The photo.
        keep_gps: Keep the GPS position.

    Returns:
        The EXIF block (empty when the photo has none, or for a RAW file), and the
        ICC profile, if any.
    """
    with contextlib.suppress(*unreadable_errors()), Image.open(source) as image:
        exif = image.getexif()
        icc = image.info.get("icc_profile")
        if not keep_gps:
            exif.pop(ExifTags.IFD.GPSInfo, None)
        exif.get_ifd(ExifTags.IFD.Exif).pop(_MAKER_NOTE, None)
        if _ORIENTATION in exif:
            exif[_ORIENTATION] = _UPRIGHT
        block = exif.tobytes() if exif else b""
        return block, icc if isinstance(icc, bytes) else None
    return b"", None
