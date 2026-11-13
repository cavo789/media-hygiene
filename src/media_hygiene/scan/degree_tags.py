"""Orientation tags written in degrees (`90`, `180`) by some software (0724).

The EXIF orientation is a code from 1 to 8; some software writes the degrees instead
(12 of 38,438 pictures measured on the maintainer's collection, step 48). They are
read as the codes 6 and 3 wherever a picture is shown upright. Read when a preview is
made: only those photos' previews get a new name (`report.preview_cache`), the others
keep theirs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from PIL import Image

if TYPE_CHECKING:
    from pathlib import Path

ORIENTATION_TAG: Final = 0x0112
# PIL turns counter-clockwise: 90 degrees clockwise is its ROTATE_270.
DEGREE_TURNS: Final = {
    90: Image.Transpose.ROTATE_270,
    180: Image.Transpose.ROTATE_180,
}
# Only these formats carry an EXIF orientation Pillow reads from the header.
_TAGGED_SUFFIXES: Final = frozenset({".jpg", ".jpeg", ".jpe", ".tif", ".tiff", ".webp"})


def degree_upright(image: Image.Image, upright: Image.Image) -> Image.Image:
    """Turn a picture whose tag is in degrees; any other picture is returned as is.

    Args:
        image: The picture as opened (its EXIF is read).
        upright: The same picture, its EXIF code orientation applied.

    Returns:
        The picture upright.
    """
    turn = DEGREE_TURNS.get(image.getexif().get(ORIENTATION_TAG, 0))
    return upright if turn is None else upright.transpose(turn)


def degree_tagged(path: Path) -> bool:
    """Tell whether a picture's orientation tag is written in degrees.

    Reads the header only (measured: see the feedback of 0724).

    Args:
        path: The picture.

    Returns:
        True for a tag `90` or `180`; False for any other picture, or one unreadable.
    """
    if path.suffix.casefold() not in _TAGGED_SUFFIXES:
        return False
    try:
        with Image.open(path) as image:
            return image.getexif().get(ORIENTATION_TAG) in DEGREE_TURNS
    except OSError, ValueError, SyntaxError, EOFError:
        return False
