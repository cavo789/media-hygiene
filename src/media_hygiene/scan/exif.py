"""Read what the EXIF of an image says: when, with what device, how, and where.

Only tags the decoder has already loaded are read: this costs nothing next to decoding
the pixels. A malformed tag is ignored, never fatal.
"""

from __future__ import annotations

import contextlib
import struct
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.exif_values import integer, number, text
from media_hygiene.scan.gps import exif_position, position_fields
from media_hygiene.scan.jpeg_quality import jpeg_quality
from media_hygiene.scan.metadata import MediaMetadata

if TYPE_CHECKING:
    from PIL import Image

EXIF_IFD: Final = 0x8769
# First IFD.
_MAKE, _MODEL, _SOFTWARE, _DESCRIPTION, _ARTIST = 0x010F, 0x0110, 0x0131, 0x010E, 0x013B
_RATING: Final = 0x4746
# EXIF IFD.
_DATE, _SUBSEC, _OFFSET = 0x9003, 0x9291, 0x9011
_EXPOSURE_TIME, _F_NUMBER, _ISO, _FLASH = 0x829A, 0x829D, 0x8827, 0x9209
_FOCAL_LENGTH, _LENS, _USER_COMMENT = 0x920A, 0xA434, 0x9286
_MAX_RATING: Final = 5
# UserComment starts with 8 bytes naming its character set.
_CHARSET_SIZE: Final = 8
_UNICODE: Final = b"UNICODE"
_BAD_EXIF: Final = (OSError, ValueError, TypeError, KeyError, IndexError, struct.error)


def taken_at(exif: Image.Exif) -> str | None:
    """When the shot was taken, with sub-seconds when recorded (bursts share seconds).

    Args:
        exif: The image's EXIF.

    Returns:
        `YYYY:MM:DD HH:MM:SS[.fraction]` as written (some cameras write other
        formats), or None.
    """
    details = exif.get_ifd(EXIF_IFD)
    taken = text(details.get(_DATE))
    subsec = text(details.get(_SUBSEC))
    if taken is None:
        return None
    return f"{taken}.{subsec}" if subsec else taken


def camera(exif: Image.Exif) -> str | None:
    """Which device took the shot.

    Args:
        exif: The image's EXIF.

    Returns:
        Make and model, or None.
    """
    parts = (text(exif.get(_MAKE)), text(exif.get(_MODEL)))
    return " ".join(part for part in parts if part) or None


def image_metadata(image: Image.Image) -> MediaMetadata:
    """Describe an opened image from its header: format, quality and EXIF.

    Args:
        image: An image opened by Pillow (its pixels need not be loaded).

    Returns:
        Its metadata; exposure is measured later, on the decoded pixels.
    """
    fields: dict[str, object] = {
        "file_format": image.format,
        "jpeg_quality": jpeg_quality(image),
    }
    with contextlib.suppress(*_BAD_EXIF):
        fields |= _exif_fields(image.getexif())
    return MediaMetadata.model_validate(fields)


def _exif_fields(exif: Image.Exif) -> dict[str, object]:
    """Read the tags of the first IFD, the EXIF IFD and the GPS IFD.

    Args:
        exif: The image's EXIF.

    Returns:
        The metadata fields found.
    """
    details = exif.get_ifd(EXIF_IFD)
    fields: dict[str, object] = {
        "offset": text(details.get(_OFFSET)),
        "lens": text(details.get(_LENS)),
        "focal_length": number(details.get(_FOCAL_LENGTH)),
        "exposure_time": number(details.get(_EXPOSURE_TIME)),
        "f_number": number(details.get(_F_NUMBER)),
        "iso": integer(details.get(_ISO)),
        "flash": integer(details.get(_FLASH)),
        "software": text(exif.get(_SOFTWARE)),
        "description": text(exif.get(_DESCRIPTION))
        or _comment(details.get(_USER_COMMENT)),
        "artist": text(exif.get(_ARTIST)),
        "rating": _rating(exif.get(_RATING)),
    }
    return fields | position_fields(exif_position(exif))


def _comment(value: object) -> str | None:
    """Decode a UserComment: 8 bytes naming the character set, then the text.

    Args:
        value: The raw tag.

    Returns:
        The comment, or None when empty (cameras often fill it with spaces).
    """
    if not isinstance(value, bytes) or len(value) <= _CHARSET_SIZE:
        return text(value)
    charset, body = value[:_CHARSET_SIZE], value[_CHARSET_SIZE:]
    if charset.startswith(_UNICODE):
        encoding = "utf-16-be" if body[:1] == b"\x00" else "utf-16-le"
        return text(body.decode(encoding, errors="replace"))
    return text(body)


def _rating(value: object) -> int | None:
    """Read the stars given in Windows.

    Args:
        value: The raw tag.

    Returns:
        0 to 5, or None when absent or out of range.
    """
    stars = integer(value)
    return stars if stars is not None and 0 <= stars <= _MAX_RATING else None
