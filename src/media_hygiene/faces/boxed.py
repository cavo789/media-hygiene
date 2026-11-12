"""A face drawn by hand where the detector found none (TODO 0715).

Without a detection there are no landmarks: the box is taken for a face seen from the
front, filling it like SFace's template fills its 112 x 112 crop, and the template's
five points are placed in the box. Only the engine with its embedder can describe it;
another finder (a test's) has nothing to say of a box.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.faces.align import CROP_SIDE, TEMPLATE
from media_hygiene.faces.engine import FaceEngine, Placed

if TYPE_CHECKING:
    from PIL import Image

    from media_hygiene.faces.engine import FaceFinder
    from media_hygiene.faces.models import Face, FaceBox

NO_SCORE: Final = 0.0  # no detector said it was a face


def template_landmarks(box: FaceBox) -> tuple[float, ...]:
    """SFace's five points, placed in a box as in its crop.

    Args:
        box: The box drawn, in the picture's pixels.

    Returns:
        The 10 landmark values (x, y of each point).
    """
    values: list[float] = []
    for x, y in TEMPLATE.tolist():
        values.extend(
            (box.x + x / CROP_SIDE * box.width, box.y + y / CROP_SIDE * box.height)
        )
    return tuple(values)


def boxed_face(finder: FaceFinder, picture: Image.Image, box: FaceBox) -> Face | None:
    """Describe the face a box holds, aligned on the box itself.

    Args:
        finder: The finder of the worker.
        picture: The upright picture, RGB.
        box: The box drawn.

    Returns:
        The face; None when the finder cannot describe a box.
    """
    if not isinstance(finder, FaceEngine):
        return None
    return finder.describe(picture, Placed(box, template_landmarks(box), NO_SCORE))
