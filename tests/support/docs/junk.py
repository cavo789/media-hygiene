"""Four photos most likely unwanted, for `review --junk`."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from PIL import Image

from tests.support.docs.pictures import Kind, Picture, render
from tests.support.docs.shots import Shot, stamp, write_shot

if TYPE_CHECKING:
    from tests.support.docs.names import Library

_WHEN: Final = datetime(2024, 3, 1, 9, tzinfo=UTC)
_TINY: Final = (120, 120)  # under 0.16 megapixels
_SCREEN: Final = (900, 600)
_DARK: Final = (800, 533)


def junk(library: Library) -> None:
    """Write two icons, a screenshot and a nearly black photo in `Downloads`."""
    folder = library.photos / "Downloads"
    folder.mkdir(parents=True, exist_ok=True)
    for index, kind in enumerate((Kind.BEACH, Kind.MOUNTAINS), start=1):
        shot = Shot(Picture(kind, 90 + index), _WHEN, size=_TINY)
        write_shot(folder / f"icon_{index}.jpg", shot)
    screen = render(Picture(Kind.MEADOW, 95)).resize(_SCREEN)
    screen.save(folder / "Screenshot_20240301-090000.png")
    stamp(folder / "Screenshot_20240301-090000.png", _WHEN)
    Image.new("RGB", _DARK, (3, 3, 4)).save(folder / "IMG_0001.jpg", "JPEG")
    stamp(folder / "IMG_0001.jpg", _WHEN)
