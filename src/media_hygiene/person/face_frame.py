"""Where each face is on its photo, as fractions of the upright picture (0838).

The index keeps a face's box in pixels of the upright picture (`FaceBox`); a page draws
it over the `<img>` whatever size it is shown at, so it receives fractions (0 to 1) of
the upright width and height. That size comes from the index's visual facts (`files`:
width and height, already swapped for a quarter-turned photo), else from the file's
header (its EXIF orientation applied). A face drawn by hand (0715) is the same.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

from PIL import Image, UnidentifiedImageError

from media_hygiene.index.read_only import connect_read_only

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.models import FaceBox

_SIZE: Final = "SELECT width, height FROM files WHERE path = ?"
_ORIENTATION_TAG: Final = 0x0112
_QUARTER_TURNS: Final = frozenset({5, 6, 7, 8})
_DIGITS: Final = 4


def _indexed_size(index_file: Path | None, path: Path) -> tuple[int, int] | None:
    """The upright size the index knows for a photo.

    Args:
        index_file: The index; None without a persistent cache.
        path: The photo, in the container.

    Returns:
        Its width and height; None when unknown.
    """
    if index_file is None or not index_file.is_file():
        return None
    try:
        connection = connect_read_only(index_file)
        try:
            row = connection.execute(_SIZE, (str(path),)).fetchone()
        finally:
            connection.close()
    except sqlite3.Error:
        return None
    if row is None or not row[0] or not row[1]:
        return None
    return int(row[0]), int(row[1])


def _header_size(path: Path) -> tuple[int, int] | None:
    """The upright size a photo's header gives.

    Args:
        path: The photo.

    Returns:
        Its width and height; None for a file Pillow cannot read.
    """
    try:
        with Image.open(path) as image:
            width, height = image.size
            turned = image.getexif().get(_ORIENTATION_TAG) in _QUARTER_TURNS
    except OSError, UnidentifiedImageError, ValueError:
        return None
    return (height, width) if turned else (width, height)


def upright_size(index_file: Path | None, path: Path) -> tuple[int, int] | None:
    """The size of a photo, upright.

    Args:
        index_file: The index; None without a persistent cache.
        path: The photo, in the container.

    Returns:
        Its width and height in pixels; None when neither the index nor the file says.
    """
    return _indexed_size(index_file, path) or _header_size(path)


def box_fractions(box: FaceBox, size: tuple[int, int]) -> dict[str, float]:
    """A face's box as fractions of the upright picture, kept inside it.

    Args:
        box: The box, in pixels of the upright picture.
        size: The upright picture's width and height.

    Returns:
        `x`, `y`, `w`, `h`, each between 0 and 1.
    """
    width, height = size
    return {
        "x": _part(box.x, width),
        "y": _part(box.y, height),
        "w": _part(box.width, width),
        "h": _part(box.height, height),
    }


def _part(value: float, whole: int) -> float:
    """A length as a fraction of a whole, between 0 and 1.

    Args:
        value: The length, in pixels.
        whole: The whole, in pixels.

    Returns:
        The fraction, rounded.
    """
    return round(min(max(value / whole, 0.0), 1.0), _DIGITS)
