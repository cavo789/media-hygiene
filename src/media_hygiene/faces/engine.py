"""Find the faces of a picture with two models, whatever runs them.

`FaceEngine` holds the arithmetic around the models (letterbox, decoding, alignment,
sharpness); a `Runner` holds a model. The ONNX runtime is one runner (`onnx_runner`),
a fake one in the tests is another: the engine never imports a model library.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

import numpy as np

from media_hygiene.faces.align import aligned_face, embedder_input
from media_hygiene.faces.detect import (
    BOX,
    LANDMARKS,
    MIN_SCORE,
    SCORE,
    decode,
    letterbox,
)
from media_hygiene.faces.models import Face, FaceBox, embedding_bytes
from media_hygiene.scan.visual import sharpness_of

if TYPE_CHECKING:
    from numpy.typing import NDArray
    from PIL import Image


class Runner(Protocol):
    """One model: input tensor → its outputs by name."""

    def __call__(self, pixels: NDArray[np.float32]) -> dict[str, NDArray[np.float32]]:
        """Run the model.

        Args:
            pixels: The input tensor.
        """


class FaceFinder(Protocol):
    """Anything that finds the faces of a picture."""

    def find(self, picture: Image.Image) -> tuple[Face, ...]:
        """Find the faces.

        Args:
            picture: The upright picture, RGB.
        """


@dataclass(frozen=True, slots=True)
class FaceEngine:
    """YuNet finds the faces, SFace describes each one."""

    detector: Runner  # YuNet
    embedder: Runner  # SFace
    least: float = MIN_SCORE  # the lowest score of a face kept

    def find(self, picture: Image.Image) -> tuple[Face, ...]:
        """Find the faces of a picture, best score first.

        Args:
            picture: The upright picture, RGB.

        Returns:
            The faces, each with its vector.
        """
        box = letterbox(picture)
        rows = decode(self.detector(box.pixels), box.scale, self.least)
        return tuple(self._describe(picture, row) for row in rows)

    def _describe(self, picture: Image.Image, row: NDArray[np.float64]) -> Face:
        """Align one face, measure its sharpness, compute its vector.

        Args:
            picture: The picture.
            row: The decoded detection.

        Returns:
            The face.
        """
        landmarks = tuple(float(value) for value in row[LANDMARKS])
        crop = aligned_face(picture, landmarks)
        outputs = self.embedder(embedder_input(crop))
        vector = next(iter(outputs.values()))
        gray = np.asarray(crop.convert("L"), dtype=np.float64)
        return Face(
            box=FaceBox(*(float(value) for value in row[BOX])),
            landmarks=landmarks,
            score=float(row[SCORE]),
            sharpness=sharpness_of(gray),
            embedding=embedding_bytes(vector),
        )
