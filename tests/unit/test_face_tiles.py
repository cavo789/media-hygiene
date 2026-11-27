"""0840: small faces of a large photo are looked for on overlapping tiles."""

from __future__ import annotations

from PIL import Image, ImageDraw

from media_hygiene.faces.models import Face, FaceBox
from media_hygiene.faces.tiles import TILED_FROM, find_on_tiles, tiles_of

_SQUARE = (1700, 900, 1740, 940)  # a small white "face" on a large black photo


class _WhiteFinder:
    """A finder that sees the bounding box of the white pixels as one face."""

    def find(self, picture: Image.Image) -> tuple[Face, ...]:
        """Return the white area as a face.

        Args:
            picture: The tile.

        Returns:
            One face, or none.
        """
        corners = picture.convert("L").getbbox()
        if corners is None:
            return ()
        left, top, right, bottom = corners
        box = FaceBox(left, top, right - left, bottom - top)
        return (Face(box, (1.0,) * 10, 0.8, 1.0, b""),)


def test_a_small_photo_is_not_cut() -> None:
    """Under the size worth cutting, no tile."""
    assert not tiles_of((TILED_FROM - 1, 600))


def test_the_tiles_cover_the_photo_and_overlap() -> None:
    """Four tiles, from corner to corner, sharing a band."""
    tiles = tiles_of((3200, 2000))
    assert len(tiles) == 4
    assert tiles[0][:2] == (0, 0)
    assert tiles[-1][2:] == (3200, 2000)
    assert tiles[1][0] < tiles[0][2]


def test_a_face_on_a_tile_is_placed_back_on_the_photo() -> None:
    """The square's box on the whole photo, landmarks dropped."""
    picture = Image.new("RGB", (3200, 2000))
    ImageDraw.Draw(picture).rectangle(_SQUARE, fill="white")
    faces = find_on_tiles(_WhiteFinder(), picture)
    assert faces
    for face in faces:
        assert (round(face.box.x), round(face.box.y)) == _SQUARE[:2]
        assert face.landmarks == ()
