"""What is known of one face: where it is, how sure, how crisp, its vector."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

# The detector and the embedder together: a face found by another pair is not compared.
FACE_MODEL: Final = "yunet-2023mar+sface-2021dec"
EMBEDDING_SIZE: Final = 128
LANDMARK_VALUES: Final = 10  # x, y of: eyes, nose tip, mouth corners
_VECTOR_TYPE: Final = "<f4"  # little-endian float32, as stored in the index


@dataclass(frozen=True, slots=True)
class FaceBox:
    """Where a face is in the upright picture, in pixels."""

    x: float
    y: float
    width: float
    height: float

    @property
    def side(self) -> float:
        """The shorter side of the box: what tells a face too small to recognise.

        Returns:
            Pixels.
        """
        return min(self.width, self.height)


@dataclass(frozen=True, slots=True)
class Face:
    """One face: its box, its landmarks, the detector's score, sharpness, vector."""

    box: FaceBox
    landmarks: tuple[float, ...]
    score: float
    sharpness: float  # variance of the Laplacian of the aligned face
    embedding: bytes  # unit vector of EMBEDDING_SIZE float32 values

    def vector(self) -> NDArray[np.float32]:
        """The embedding as numbers.

        Returns:
            EMBEDDING_SIZE values, of length 1.
        """
        return vector_of(self.embedding)


@dataclass(frozen=True, slots=True)
class PhotoFaces:
    """The faces of one version of a photo, and how long finding them took."""

    path: Path
    size: int
    mtime_ns: int
    faces: tuple[Face, ...]
    seconds: float


def embedding_bytes(vector: NDArray[np.float32]) -> bytes:
    """Store a vector as bytes, scaled to length 1 (cosine becomes a dot product).

    Args:
        vector: The embedder's output.

    Returns:
        The float32 bytes; zeros stay zeros.
    """
    values = np.asarray(vector, dtype=np.float64).ravel()
    length = float(np.linalg.norm(values))
    unit = values / length if length > 0 else values
    return unit.astype(_VECTOR_TYPE).tobytes()


def vector_of(embedding: bytes) -> NDArray[np.float32]:
    """Read a stored vector.

    Args:
        embedding: The bytes of `embedding_bytes`.

    Returns:
        The values.
    """
    return np.frombuffer(embedding, dtype=_VECTOR_TYPE).astype(np.float32)
