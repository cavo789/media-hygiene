"""YuNet's input and output, around a model that never runs: synthetic tensors only."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from media_hygiene.faces.detect import (
    DETECT_SIDE,
    SCORE,
    STRIDES,
    decode,
    letterbox,
    suppress,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray


def silent_outputs() -> dict[str, NDArray[np.float32]]:
    """The detector's answer for a picture without any face.

    Returns:
        Every output at zero.
    """
    outputs: dict[str, NDArray[np.float32]] = {}
    for stride in STRIDES:
        cells = (DETECT_SIDE // stride) ** 2
        outputs[f"cls_{stride}"] = np.zeros((1, cells, 1), dtype=np.float32)
        outputs[f"obj_{stride}"] = np.zeros((1, cells, 1), dtype=np.float32)
        outputs[f"bbox_{stride}"] = np.zeros((1, cells, 4), dtype=np.float32)
        outputs[f"kps_{stride}"] = np.zeros((1, cells, 10), dtype=np.float32)
    return outputs


def with_face(
    outputs: dict[str, NDArray[np.float32]], cell: tuple[int, int], score: float
) -> None:
    """Put a face of 32 x 32 pixels in one cell of stride 32.

    Args:
        outputs: The answer, changed in place.
        cell: Column and line of the cell.
        score: Its class and objectness score.
    """
    column, line = cell
    index = line * (DETECT_SIDE // 32) + column
    outputs["cls_32"][0, index, 0] = score
    outputs["obj_32"][0, index, 0] = score
    outputs["bbox_32"][0, index] = (0.5, 0.5, 0.0, 0.0)  # centred, exp(0) * 32 wide
    outputs["kps_32"][0, index] = np.tile((0.25, 0.25), 5)


def test_letterbox_scales_the_longer_side_and_turns_rgb_into_bgr() -> None:
    """A 320 x 160 red picture fills the top half of the square, red in channel 2."""
    picture = Image.new("RGB", (320, 160), (255, 0, 0))
    box = letterbox(picture)
    assert box.scale == 2.0
    assert box.pixels.shape == (1, 3, DETECT_SIDE, DETECT_SIDE)
    assert box.pixels[0, 2, 10, 10] == 255.0
    assert box.pixels[0, 0, 10, 10] == 0.0
    assert box.pixels[0, 2, 400, 10] == 0.0  # below the picture: black


def test_decode_places_a_face_in_the_picture_pixels() -> None:
    """A cell's box and landmarks come back in the picture's pixels, scaled back."""
    outputs = silent_outputs()
    with_face(outputs, (3, 2), 0.95)
    rows = decode(outputs, scale=2.0)
    assert rows.shape == (1, 15)
    x, y, width, height = rows[0, :4]
    assert (x, y, width, height) == (48.0, 32.0, 16.0, 16.0)
    assert rows[0, 4] == (3 + 0.25) * 32 / 2
    assert round(float(rows[0, SCORE]), 3) == 0.95


def test_decode_drops_unsure_faces_and_keeps_none_without_any() -> None:
    """Below 0.9 a detection is not a face; a silent answer gives no row."""
    outputs = silent_outputs()
    with_face(outputs, (1, 1), 0.5)
    assert decode(outputs, 1.0).shape == (0, 15)
    assert decode(silent_outputs(), 1.0).shape == (0, 15)


def test_suppress_keeps_the_best_of_overlapping_boxes() -> None:
    """Two boxes of one face give one; a box apart is kept."""
    rows = np.zeros((3, 15))
    rows[0, :4], rows[0, SCORE] = (0, 0, 10, 10), 0.91
    rows[1, :4], rows[1, SCORE] = (1, 1, 10, 10), 0.97
    rows[2, :4], rows[2, SCORE] = (50, 50, 10, 10), 0.92
    kept = suppress(rows)
    assert [float(score) for score in kept[:, SCORE]] == [0.97, 0.92]


def test_suppress_ignores_boxes_without_area() -> None:
    """Two empty boxes never overlap: both are kept."""
    rows = np.zeros((2, 15))
    rows[:, SCORE] = 0.95
    assert len(suppress(rows)) == 2
