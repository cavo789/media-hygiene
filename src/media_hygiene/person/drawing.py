"""A face drawn by hand on a photo (TODO 0715): detected in the box, or the box itself.

The user drags a box where they see a face the audit did not keep. The detector looks
again in that part of the photo, enlarged (a small face becomes one it can find), less
strict (the recipe of the second look); the best face whose centre lies in the box is
kept, measured in the photo. Without one, the box itself is aligned and described
(`faces.boxed`). Either way the face must be large and sharp enough to stand for a
person: below `DRAWN_SIDE` or `DRAWN_SHARPNESS`, its vector is noise and nothing is
kept. Runs in a worker process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import Image

from media_hygiene.faces.boxed import boxed_face
from media_hygiene.faces.models import Face, FaceBox
from media_hygiene.faces.worker import finder_of
from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.image_check import prepare_image_worker

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.engine import FaceFinder
    from media_hygiene.faces.worker import FinderRecipe

# Provisional, not measured yet (0715, `tests/measure/mh-measure.ps1` step 49): half
# the people page's `min_face` (40 px) and `min_sharpness` (30). A named constant, not
# a setting, until photos of two collections say otherwise.
DRAWN_SIDE: Final = 20.0
DRAWN_SHARPNESS: Final = 15.0
_MARGIN: Final = 0.5  # of the box's side, around it: the detector needs some context
_LOOK_SIDE: Final = 320  # the part looked at is enlarged to this side at least
_MOST_ENLARGED: Final = 8.0


@dataclass(frozen=True, slots=True)
class DrawJob:
    """A photo, the box drawn on it (fractions of the upright photo), the recipe."""

    path: Path
    box: tuple[float, float, float, float]  # x, y, width, height, from 0 to 1
    recipe: FinderRecipe


def usable(face: Face) -> bool:
    """Tell whether a face drawn is large and sharp enough to find others.

    Args:
        face: The face.

    Returns:
        True from `DRAWN_SIDE` and `DRAWN_SHARPNESS` on.
    """
    return face.box.side >= DRAWN_SIDE and face.sharpness >= DRAWN_SHARPNESS


def draw_face(job: DrawJob) -> Face | None:
    """The face of a box drawn on a photo, in the upright photo's pixels.

    Args:
        job: The photo, the box and the recipe.

    Returns:
        The face; None when the photo cannot be read or nothing usable is there.
    """
    prepare_image_worker()
    finder = finder_of(job.recipe)
    try:
        picture = upright_picture(job.path).convert("RGB")
    except unreadable_errors():
        return None
    width, height = picture.size
    x, y, wide, high = job.box
    box = FaceBox(x * width, y * height, wide * width, high * height)
    face = detected(finder, picture, box) or boxed_face(finder, picture, box)
    return face if face is not None and usable(face) else None


def detected(finder: FaceFinder, picture: Image.Image, box: FaceBox) -> Face | None:
    """The best face the detector finds around a box, its centre in the box.

    Args:
        finder: The finder.
        picture: The upright picture.
        box: The box drawn.

    Returns:
        The face, measured in the picture; None when there is none.
    """
    part = _part(picture, box)
    if part is None:
        return None
    enlarged, scale, shift = part
    for face in sorted(finder.find(enlarged), key=lambda one: -one.score):
        placed = _back(face, scale, shift)
        centre_x = placed.box.x + placed.box.width / 2
        centre_y = placed.box.y + placed.box.height / 2
        if (
            box.x <= centre_x <= box.x + box.width
            and box.y <= centre_y <= box.y + box.height
        ):
            return placed
    return None


def _part(
    picture: Image.Image, box: FaceBox
) -> tuple[Image.Image, float, tuple[int, int]] | None:
    """The part of the picture around a box, enlarged for the detector.

    Args:
        picture: The upright picture.
        box: The box drawn.

    Returns:
        The part, how much it was enlarged, where it starts; None when empty.
    """
    margin = box.side * _MARGIN
    left, top = max(0.0, box.x - margin), max(0.0, box.y - margin)
    right = min(float(picture.width), box.x + box.width + margin)
    bottom = min(float(picture.height), box.y + box.height + margin)
    if right - left < 1 or bottom - top < 1:
        return None
    part = picture.crop((int(left), int(top), int(right), int(bottom)))
    scale = min(_MOST_ENLARGED, max(1.0, _LOOK_SIDE / max(part.size)))
    size = (round(part.width * scale), round(part.height * scale))
    return part.resize(size, Image.Resampling.BICUBIC), scale, (int(left), int(top))


def _back(face: Face, scale: float, shift: tuple[int, int]) -> Face:
    """A face found in the enlarged part, measured in the picture again.

    Args:
        face: The face.
        scale: How much the part was enlarged.
        shift: Where the part starts in the picture.

    Returns:
        The same face, its box and landmarks in the picture's pixels.
    """
    left, top = shift
    box = face.box
    landmarks = tuple(
        value / scale + (left if index % 2 == 0 else top)
        for index, value in enumerate(face.landmarks)
    )
    return Face(
        box=FaceBox(
            box.x / scale + left,
            box.y / scale + top,
            box.width / scale,
            box.height / scale,
        ),
        landmarks=landmarks,
        score=face.score,
        sharpness=face.sharpness,
        embedding=face.embedding,
    )
