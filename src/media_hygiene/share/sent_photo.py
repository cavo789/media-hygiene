"""One photo made ready to send: upright, fitted, its GPS position removed (0296).

The copy is a baseline JPEG: the EXIF orientation applied (then set to 1), the long
side fitted into `long_side_px`, the given quality. What the EXIF says is kept (the
date, the camera, the description, the copyright), except:

- the GPS position, unless asked: a photo sent must not say where the house is;
- the maker's notes, private to each brand, which may hold a serial number.

The XMP packet is never copied: it may repeat the position, and its description is
also in the EXIF when Windows wrote it. The sentence and the words of `tags`, when
given, go into a new packet and the EXIF fields of Windows (`share.sent_words`). A
RAW file gives its embedded preview and no EXIF. The original is only
read. Runs in the worker pool.
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import ExifTags, Image, ImageFile

from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.image_check import prepare_image_worker
from media_hygiene.share.sent_words import NO_WORDS, SentWords, add_words

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


def sent_jpeg(job: SendJob, source: Path, words: SentWords = NO_WORDS) -> bytes | None:
    """Make the copy of one photo to send.

    Args:
        job: The size, the quality, the GPS kept or not.
        source: The photo, in the container; only read.
        words: The sentence and the words of `tags` to carry; none by default.

    Returns:
        The JPEG, or None when the photo cannot be decoded.
    """
    prepare_image_worker()
    made = b""
    ImageFile.LOAD_TRUNCATED_IMAGES = True  # a photo cut short still sends its part
    with contextlib.suppress(*unreadable_errors()):
        picture = upright_picture(source, job.long_side_px)
        picture.thumbnail((job.long_side_px, job.long_side_px))
        exif, icc, xmp = _header(source, words, keep_gps=job.keep_gps)
        buffer = io.BytesIO()
        picture.save(
            buffer, "JPEG", quality=job.quality, exif=exif, icc_profile=icc, xmp=xmp
        )
        made = buffer.getvalue()  # whole, or nothing: never half a JPEG
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    return made or None  # empty: the photo could not be decoded


def _header(
    source: Path, words: SentWords, *, keep_gps: bool
) -> tuple[bytes, bytes | None, bytes]:
    """The EXIF to write in the copy, the colour profile, the XMP packet.

    Args:
        source: The photo.
        words: The sentence and the words to carry.
        keep_gps: Keep the GPS position.

    Returns:
        The EXIF block (empty when the photo has none and no words, or for a RAW
        file), the ICC profile, if any, and the XMP packet (empty without words).
    """
    with contextlib.suppress(*unreadable_errors()), Image.open(source) as image:
        exif = image.getexif()
        icc = image.info.get("icc_profile")
        if not keep_gps:
            exif.pop(ExifTags.IFD.GPSInfo, None)
        exif.get_ifd(ExifTags.IFD.Exif).pop(_MAKER_NOTE, None)
        if _ORIENTATION in exif:
            exif[_ORIENTATION] = _UPRIGHT
        xmp = add_words(exif, words)
        block = exif.tobytes() if exif else b""
        return block, icc if isinstance(icc, bytes) else None, xmp
    return b"", None, b""
