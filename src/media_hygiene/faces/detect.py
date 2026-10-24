"""YuNet's input and output: the picture as it expects it, its answer as face boxes.

The model takes a fixed 640 x 640 BGR picture, pixel values as they are: the photo is
shrunk (or enlarged) to fit, its longer side 640 pixels, the rest left black. Its
answer has, for each of three strides (8, 16, 32 pixels), one row per grid cell: two
scores, a box relative to the cell and five landmarks. Decoding follows OpenCV's
`FaceDetectorYN`: score = sqrt(class x objectness), then non-maximum suppression.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Mapping

    from numpy.typing import NDArray

DETECT_SIDE: Final = 640
STRIDES: Final = (8, 16, 32)
MIN_SCORE: Final = 0.9  # OpenCV's default: below, mostly not a face
OVERLAP: Final = 0.3  # a box overlapping a better one more than this is the same face
# Columns of a decoded row: box (x, y, width, height), 10 landmark values, score.
BOX: Final = slice(0, 4)
LANDMARKS: Final = slice(4, 14)
SCORE: Final = 14
_ROW: Final = 15
type Rows = NDArray[np.float64]
type Outputs = Mapping[str, NDArray[np.float32]]


@dataclass(frozen=True, slots=True)
class Letterbox:
    """The detector's input, and the scale from the picture to it."""

    pixels: NDArray[np.float32]  # 1 x 3 x 640 x 640, BGR
    scale: float


def letterbox(picture: Image.Image) -> Letterbox:
    """Fit an RGB picture into the detector's square, top left, rest black.

    Args:
        picture: The upright picture, RGB.

    Returns:
        The input tensor and the scale applied.
    """
    width, height = picture.size
    scale = DETECT_SIDE / max(width, height, 1)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    resized = np.asarray(picture.resize(size, Image.Resampling.BILINEAR))
    canvas = np.zeros((DETECT_SIDE, DETECT_SIDE, 3), dtype=np.float32)
    canvas[: size[1], : size[0]] = resized[..., ::-1]  # RGB to BGR
    return Letterbox(canvas.transpose(2, 0, 1)[np.newaxis].copy(), scale)


def decode(outputs: Outputs, scale: float, least: float = MIN_SCORE) -> Rows:
    """Read the detector's answer as faces, in the picture's pixels.

    Args:
        outputs: Output name (`cls_8`, `obj_8`, `bbox_8`, `kps_8`, ...) → values.
        scale: The scale of the letterbox.
        least: The lowest score kept (`MIN_SCORE`, lower for a second look).

    Returns:
        One row per face kept (see `BOX`, `LANDMARKS`, `SCORE`), best first.
    """
    rows = [_stride_rows(outputs, stride) for stride in STRIDES]
    found = np.concatenate(rows) if rows else np.empty((0, _ROW))
    found = found[found[:, SCORE] >= least]
    found[:, :SCORE] /= scale
    return suppress(found)


def _stride_rows(outputs: Outputs, stride: int) -> Rows:
    """Decode the cells of one stride.

    Args:
        outputs: The detector's outputs.
        stride: 8, 16 or 32.

    Returns:
        One row per cell, in the letterbox's pixels.
    """
    cells = DETECT_SIDE // stride
    score_class = np.clip(outputs[f"cls_{stride}"].reshape(-1), 0, 1)
    score_object = np.clip(outputs[f"obj_{stride}"].reshape(-1), 0, 1)
    box = outputs[f"bbox_{stride}"].reshape(-1, 4).astype(np.float64)
    points = outputs[f"kps_{stride}"].reshape(-1, 10).astype(np.float64)
    index = np.arange(cells * cells)
    column = (index % cells).astype(np.float64)
    line = (index // cells).astype(np.float64)
    width = np.exp(box[:, 2]) * stride
    height = np.exp(box[:, 3]) * stride
    centre_x = (column + box[:, 0]) * stride
    centre_y = (line + box[:, 1]) * stride
    rows = np.empty((cells * cells, _ROW))
    rows[:, 0] = centre_x - width / 2
    rows[:, 1] = centre_y - height / 2
    rows[:, 2] = width
    rows[:, 3] = height
    rows[:, 4:14:2] = (points[:, 0::2] + column[:, np.newaxis]) * stride
    rows[:, 5:14:2] = (points[:, 1::2] + line[:, np.newaxis]) * stride
    rows[:, SCORE] = np.sqrt(score_class * score_object)
    return rows


def suppress(rows: Rows) -> Rows:
    """Keep the best box of each face: drop those overlapping a better one.

    Args:
        rows: Decoded rows.

    Returns:
        The rows kept, best score first.
    """
    ordered = rows[np.argsort(-rows[:, SCORE], kind="stable")]
    kept: list[int] = []
    for index in range(len(ordered)):
        if all(_overlap(ordered[index], ordered[other]) <= OVERLAP for other in kept):
            kept.append(index)
    return ordered[kept]


def _overlap(first: Rows, second: Rows) -> float:
    """Intersection over union of two boxes.

    Args:
        first: A row.
        second: Another row.

    Returns:
        From 0 (apart) to 1 (the same box).
    """
    left = max(first[0], second[0])
    top = max(first[1], second[1])
    right = min(first[0] + first[2], second[0] + second[2])
    bottom = min(first[1] + first[3], second[1] + second[3])
    inter = max(0.0, right - left) * max(0.0, bottom - top)
    union = first[2] * first[3] + second[2] * second[3] - inter
    return float(inter / union) if union > 0 else 0.0
