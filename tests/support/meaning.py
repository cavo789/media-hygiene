"""A stand-in for the CLIP model: a picture's vector is its mean colour.

No download, no ONNX: the tests of search by meaning give each picture the direction
of its colour (centred on mid-grey) and each search the colour its words name, so
that "sea" finds the blue pictures first, as the bench's `StubEmbedder` did with
seeded vectors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.meaning.pixels import unit

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from PIL import Image

    from media_hygiene.meaning.files import ClipFiles

_GREY: Final = 128.0
# The colours of `tests.support.subjects.EVENTS`, and a kitchen's.
COLOURS: Final = {
    "sea": (60, 120, 230),
    "mer": (60, 120, 230),
    "snow": (250, 250, 252),
    "cake": (150, 90, 60),
    "cuisine": (150, 90, 60),
    "kitchen": (150, 90, 60),
}


def colour_vector(colour: tuple[float, float, float]) -> NDArray[np.float32]:
    """The vector of a colour.

    Args:
        colour: Red, green, blue (0 to 255).

    Returns:
        A unit vector.
    """
    return unit(np.asarray(colour, dtype=np.float32) - _GREY)


class ColourImages:
    """The image side: a picture's mean colour."""

    def __init__(self, files: ClipFiles | None = None, threads: int = 1) -> None:
        """Take the arguments of `ClipImages`, and ignore them.

        Args:
            files: The model's files (unused).
            threads: Threads (unused).
        """
        del files, threads

    def image(self, picture: Image.Image) -> NDArray[np.float32]:
        """The vector of a picture.

        Args:
            picture: The picture.

        Returns:
            Its mean colour's vector.
        """
        mean = np.asarray(picture.convert("RGB"), dtype=np.float32).mean(axis=(0, 1))
        return colour_vector((float(mean[0]), float(mean[1]), float(mean[2])))


class ColourWords:
    """The text side: the colours the words name, summed."""

    def __init__(self, files: ClipFiles | None = None, threads: int = 1) -> None:
        """Take the arguments of `ClipWords`, count the searches.

        Args:
            files: The model's files (unused).
            threads: Threads (unused).
        """
        del files, threads
        self.asked: list[str] = []

    def text(self, query: str) -> NDArray[np.float32]:
        """The vector of a search.

        Args:
            query: The words.

        Returns:
            The sum of the colours it names, as a unit vector (zero for none).
        """
        self.asked.append(query)
        total = np.zeros(3, dtype=np.float32)
        for word in query.casefold().split():
            if word in COLOURS:
                total += colour_vector(COLOURS[word])
        return unit(total)
