"""Turn a face upright and to scale, as SFace expects it: 112 x 112, eyes in place.

The five landmarks are mapped onto SFace's template by a similarity (rotation, one
scale, translation) fitted by least squares (Umeyama), as OpenCV's
`FaceRecognizerSF.alignCrop` does; the picture is then resampled through it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

CROP_SIDE: Final = 112
# Where SFace wants the eyes, the nose tip and the mouth corners, in the crop's pixels.
TEMPLATE: Final = np.array(
    (
        (38.2946, 51.6963),
        (73.5318, 51.5014),
        (56.0252, 71.7366),
        (41.5493, 92.3655),
        (70.7299, 92.2041),
    )
)


def similarity(points: NDArray[np.float64]) -> NDArray[np.float64]:
    """Fit the similarity taking the landmarks onto the template.

    Args:
        points: 5 x 2 landmarks, in the picture's pixels.

    Returns:
        The 2 x 3 matrix, picture → crop.
    """
    source_mean = points.mean(axis=0)
    target_mean = TEMPLATE.mean(axis=0)
    source = points - source_mean
    target = TEMPLATE - target_mean
    covariance = target.T @ source / len(points)
    left, singular, right = np.linalg.svd(covariance)
    sign = np.ones(2)
    if np.linalg.det(covariance) < 0:
        sign[-1] = -1
    rotation = left @ np.diag(sign) @ right
    spread = float((source**2).sum()) / len(points)
    scale = float((singular * sign).sum()) / spread if spread > 0 else 1.0
    shift = target_mean - scale * rotation @ source_mean
    return np.hstack((scale * rotation, shift[:, np.newaxis]))


def aligned_face(picture: Image.Image, landmarks: Sequence[float]) -> Image.Image:
    """Cut the face out of the picture, upright, at SFace's size.

    Args:
        picture: The upright picture, RGB.
        landmarks: The 10 landmark values (x, y of each point).

    Returns:
        A 112 x 112 RGB picture.
    """
    forward = np.vstack((similarity(np.asarray(landmarks).reshape(5, 2)), (0, 0, 1)))
    backward = np.linalg.inv(forward)[:2]
    # PIL measures from pixel edges, OpenCV from pixel centres: half a pixel apart.
    half = np.array((0.5, 0.5))
    shift = backward[:, 2] + half - backward[:, :2] @ half
    data = (*backward[0, :2], shift[0], *backward[1, :2], shift[1])
    return picture.transform(
        (CROP_SIDE, CROP_SIDE),
        Image.Transform.AFFINE,
        tuple(float(value) for value in data),
        resample=Image.Resampling.BILINEAR,
    )


def embedder_input(face: Image.Image) -> NDArray[np.float32]:
    """SFace's input: the RGB pixels as they are, channels first.

    Args:
        face: The aligned face.

    Returns:
        1 x 3 x 112 x 112 values.
    """
    pixels = np.asarray(face.convert("RGB"), dtype=np.float32)
    return pixels.transpose(2, 0, 1)[np.newaxis].copy()
