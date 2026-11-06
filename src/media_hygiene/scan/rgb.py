"""A decoded picture as plain RGB, without Pillow's warning on the console."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from PIL import Image

_PALETTE: Final = "P"
_TRANSPARENCY: Final = "transparency"


def rgb_of(picture: Image.Image) -> Image.Image:
    """Convert to RGB, dropping any transparency.

    A palette whose transparency is a list of bytes (many PNG and GIF) makes a direct
    conversion warn on stderr; going through RGBA gives the same pixels, silently.

    Args:
        picture: Any decoded picture.

    Returns:
        The picture in RGB.
    """
    if picture.mode == _PALETTE and isinstance(picture.info.get(_TRANSPARENCY), bytes):
        return picture.convert("RGBA").convert("RGB")
    return picture.convert("RGB")
