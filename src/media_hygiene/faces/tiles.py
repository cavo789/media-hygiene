"""Small faces of a large photo: looked for on overlapping tiles of it (0840).

The detector sees a photo shrunk to `DETECT_SIDE` pixels: on a group photo taken at a
few metres, each face is then 15-25 pixels wide and scores low. Cut into `GRID` x
`GRID` tiles overlapping by `TILE_OVERLAP`, each tile is shrunk less, its faces are
larger for the detector. Measured 2026-11-15 on a real group photo (3216 x 2136, 9
people): whole photo 0 faces at 0.9, 2 x 2 tiles 4, for 0.21 s instead of 0.03. A
photo whose longer side is under `TILED_FROM` is not cut: its faces are not shrunk
much. Each face found is placed back on the whole photo (the tile's corner added);
landmarks are dropped (they belong to the tile).
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Final

from media_hygiene.faces.detect import DETECT_SIDE
from media_hygiene.faces.models import FaceBox

if TYPE_CHECKING:
    from PIL import Image

    from media_hygiene.faces.engine import FaceFinder
    from media_hygiene.faces.models import Face

GRID: Final = 2
TILE_OVERLAP: Final = 0.25  # of a tile's side, shared with its neighbour
TILED_FROM: Final = 2 * DETECT_SIDE  # pixels, the longer side of a photo worth cutting
type Corners = tuple[int, int, int, int]  # left, top, right, bottom


def tiles_of(size: tuple[int, int]) -> tuple[Corners, ...]:
    """Cut a picture of this size into overlapping tiles.

    Args:
        size: Width and height, in pixels.

    Returns:
        The tiles' corners, row by row; none when the picture is too small to cut.
    """
    width, height = size
    if max(width, height) < TILED_FROM:
        return ()
    columns = _spans(width)
    return tuple(
        (left, top, right, bottom)
        for top, bottom in _spans(height)
        for left, right in columns
    )


def _spans(length: int) -> tuple[tuple[int, int], ...]:
    """Split one side into `GRID` spans overlapping by `TILE_OVERLAP`.

    Args:
        length: The side, in pixels.

    Returns:
        Each span's start and end.
    """
    span = length / (GRID - (GRID - 1) * TILE_OVERLAP)
    step = span * (1 - TILE_OVERLAP)
    return tuple(
        (round(index * step), min(length, round(index * step + span)))
        for index in range(GRID)
    )


def find_on_tiles(finder: FaceFinder, picture: Image.Image) -> tuple[Face, ...]:
    """Find the faces of each tile, placed back on the whole picture.

    Args:
        finder: The face finder.
        picture: The upright picture.

    Returns:
        Every face found on a tile (one face on two tiles comes twice: the caller
        keeps it once, by its place), none when the picture is not cut.
    """
    found: list[Face] = []
    for left, top, right, bottom in tiles_of(picture.size):
        tile = picture.crop((left, top, right, bottom))
        found.extend(
            dataclasses.replace(face, box=_moved(face.box, left, top), landmarks=())
            for face in finder.find(tile)
        )
    return tuple(found)


def _moved(box: FaceBox, left: int, top: int) -> FaceBox:
    """Place a box of a tile on the whole picture.

    Args:
        box: The box on the tile.
        left: The tile's left side on the picture.
        top: The tile's top side on the picture.

    Returns:
        The box on the picture.
    """
    return FaceBox(box.x + left, box.y + top, box.width, box.height)
