"""Alignment and the engine around two fake models: arithmetic only, no model file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest
from PIL import Image

from media_hygiene.faces.align import (
    CROP_SIDE,
    TEMPLATE,
    aligned_face,
    embedder_input,
    similarity,
)
from media_hygiene.faces.engine import FaceEngine
from media_hygiene.faces.models import EMBEDDING_SIZE, embedding_bytes, vector_of
from tests.unit.test_faces_detect import silent_outputs, with_face

if TYPE_CHECKING:
    from numpy.typing import NDArray


def test_similarity_of_the_template_is_the_identity() -> None:
    """Landmarks already in place need no move."""
    matrix = similarity(TEMPLATE.copy())
    assert np.allclose(matrix, ((1, 0, 0), (0, 1, 0)), atol=1e-9)


def test_similarity_undoes_a_scale_and_a_shift() -> None:
    """Landmarks twice as far apart, shifted, come back onto the template."""
    points = TEMPLATE * 2 + (100, 50)
    matrix = similarity(points)
    moved = points @ matrix[:, :2].T + matrix[:, 2]
    assert np.allclose(moved, TEMPLATE, atol=1e-6)


def test_similarity_of_a_mirrored_face_stays_a_rotation() -> None:
    """Mirrored landmarks give a proper rotation (determinant > 0), never a flip."""
    points = TEMPLATE * (-1, 1)
    matrix = similarity(points)
    assert np.linalg.det(matrix[:, :2]) > 0


def test_similarity_of_one_point_repeated_does_not_divide_by_zero() -> None:
    """Five landmarks at one spot give a finite matrix."""
    assert np.isfinite(similarity(np.ones((5, 2)))).all()


def test_aligned_face_is_square_and_ready_for_the_embedder() -> None:
    """The crop has SFace's size, and its tensor is channels first, RGB untouched."""
    picture = Image.new("RGB", (400, 300), (10, 20, 30))
    crop = aligned_face(picture, tuple(float(v) for v in (TEMPLATE * 2).ravel()))
    assert crop.size == (CROP_SIDE, CROP_SIDE)
    tensor = embedder_input(crop)
    assert tensor.shape == (1, 3, CROP_SIDE, CROP_SIDE)
    assert tensor[0, :, 50, 50].tolist() == [10.0, 20.0, 30.0]


def test_embedding_bytes_are_of_length_one_and_zeros_stay_zeros() -> None:
    """A vector is stored scaled to length 1; a zero vector is kept as is."""
    vector = vector_of(embedding_bytes(np.full(EMBEDDING_SIZE, 3.0, np.float32)))
    assert float(np.linalg.norm(vector)) == pytest.approx(1.0)
    zeros = vector_of(embedding_bytes(np.zeros(EMBEDDING_SIZE, np.float32)))
    assert not zeros.any()


def detector(pixels: NDArray[np.float32]) -> dict[str, NDArray[np.float32]]:
    """A fake YuNet: one face in a cell of stride 32, whatever the picture.

    Args:
        pixels: The letterbox (its shape is checked).

    Returns:
        The outputs.
    """
    assert pixels.shape == (1, 3, 640, 640)
    outputs = silent_outputs()
    with_face(outputs, (5, 5), 0.96)
    return outputs


def embedder(pixels: NDArray[np.float32]) -> dict[str, NDArray[np.float32]]:
    """A fake SFace: the mean of each channel, then zeros.

    Args:
        pixels: The aligned face.

    Returns:
        `fc1`, the vector.
    """
    vector = np.zeros((1, EMBEDDING_SIZE), dtype=np.float32)
    vector[0, :3] = pixels[0].mean(axis=(1, 2))
    return {"fc1": vector}


def test_engine_finds_aligns_and_describes_each_face() -> None:
    """The fake detector's face comes back with its box, score, sharpness, vector."""
    picture = Image.new("RGB", (640, 480), (200, 100, 50))
    faces = FaceEngine(detector, embedder).find(picture)
    assert len(faces) == 1
    face = faces[0]
    assert face.box.side == 32.0
    assert face.score == pytest.approx(0.96)
    assert face.sharpness == 0.0  # a plain picture has no edge
    assert len(face.landmarks) == 10
    assert face.vector()[:3] == pytest.approx(np.array((200, 100, 50)) / 229.13, 1e-3)
