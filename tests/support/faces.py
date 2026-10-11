"""A fake face finder: the colour of a synthetic picture says who is in it.

No model, no real face: a picture whose strongest channel is red holds "person 0", green
"person 1", blue "person 2"; a dark picture holds nobody. The face fills the picture.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image

from media_hygiene.faces.models import (
    EMBEDDING_SIZE,
    LANDMARK_VALUES,
    Face,
    FaceBox,
    embedding_bytes,
)

if TYPE_CHECKING:
    from pathlib import Path

DARK: Final = 20  # mean brightness under which a picture holds nobody
SHARP: Final = 100.0
COLOURS: Final = ((220, 30, 30), (30, 220, 30), (30, 30, 220))


@dataclass(frozen=True, slots=True)
class FakeFinder:
    """Finds one face per bright picture, its vector set by the dominant colour."""

    def find(self, picture: Image.Image) -> tuple[Face, ...]:
        """Find the face of a synthetic picture.

        Args:
            picture: The picture, RGB.

        Returns:
            One face, or none for a dark picture.
        """
        means = np.asarray(picture.convert("RGB"), dtype=np.float64).mean(axis=(0, 1))
        if means.mean() < DARK:
            return ()
        return (face_of(int(np.argmax(means)), picture.size),)


@dataclass(frozen=True, slots=True)
class FakeRecipe:
    """Builds the fake finder in a worker."""

    def build(self) -> FakeFinder:
        """Build it.

        Returns:
            The finder.
        """
        return FakeFinder()


def face_of(person: int, size: tuple[int, int]) -> Face:
    """A face of a person, filling a picture of this size.

    Args:
        person: 0, 1 or 2.
        size: Width and height.

    Returns:
        The face.
    """
    vector = np.zeros(EMBEDDING_SIZE, dtype=np.float32)
    vector[person] = 1.0
    width, height = size
    return Face(
        box=FaceBox(0.0, 0.0, float(width), float(height)),
        landmarks=(0.0,) * LANDMARK_VALUES,
        score=0.95,
        sharpness=SHARP,
        embedding=embedding_bytes(vector),
    )


def coloured(path: Path, person: int, size: tuple[int, int] = (96, 64)) -> Path:
    """Write a plain picture of a person's colour (or black for -1).

    Args:
        path: Where.
        person: 0, 1, 2, or -1 for nobody.
        size: Width and height.

    Returns:
        The file written.
    """
    colour = COLOURS[person] if person >= 0 else (0, 0, 0)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, colour).save(path)
    return path
