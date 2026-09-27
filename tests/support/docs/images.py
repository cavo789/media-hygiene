"""Publish the screenshots: trim the empty band under a page, convert to WebP."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from PIL import Image, ImageChops

if TYPE_CHECKING:
    from pathlib import Path

_PAGE_BACKGROUND: Final = (247, 247, 245)  # --bg of the report and review pages
_BOTTOM_MARGIN: Final = 24
_TERMINAL: Final = "terminal-"
_QUALITY: Final = 88
_EFFORT: Final = 6


def _trimmed(picture: Image.Image) -> Image.Image:
    """Cut the page background left below the content (short page, tall viewport)."""
    background = Image.new("RGB", picture.size, _PAGE_BACKGROUND)
    content = ImageChops.difference(picture, background).getbbox()
    if content is None:
        return picture
    bottom = min(picture.height, content[3] + _BOTTOM_MARGIN)
    return picture.crop((0, 0, picture.width, bottom))


def publish(shots: Path, images: Path) -> list[Path]:
    """Convert every screenshot to a WebP image of the documentation.

    Args:
        shots: The PNG screenshots.
        images: The `images/` folder of one language.

    Returns:
        The images written.
    """
    images.mkdir(parents=True, exist_ok=True)
    written = []
    for shot in sorted(shots.glob("*.png")):
        picture = Image.open(shot).convert("RGB")
        if not shot.stem.startswith(_TERMINAL):
            picture = _trimmed(picture)
        target = images / f"{shot.stem}.webp"
        picture.save(target, "WEBP", quality=_QUALITY, method=_EFFORT)
        written.append(target)
    return written
