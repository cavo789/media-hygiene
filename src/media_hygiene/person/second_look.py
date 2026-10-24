"""A second look at one photo whose faces the audit missed: turned, and less strict.

The audit looks at each photo upright, with the detector's usual score (0.9): a face
tilted, lying, or blurred is not found. Asked for one photo, the page looks again at
the picture turned by `ANGLES`, keeping the faces down to `LOOSE_SCORE`. Measured
2026-10-24 on 9 real photos of one person, none with a face in the index: 6 show his
face at one of these angles (0.50 to 0.71 from the mean of his faces set aside), one at
the threshold (0.40), two not; the other faces found lie at 0.35 or less. What is found
is shown to pick from, never stored as the photo's faces: the regular analysis stays
the same for every photo. Runs in a worker process.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image

from media_hygiene.faces.models import vector_of
from media_hygiene.faces.worker import finder_of
from media_hygiene.people.crops import crop_jpeg
from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.image_check import prepare_image_worker

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.models import Face
    from media_hygiene.faces.worker import FinderRecipe

# Degrees, counterclockwise: upright first, then a little, then lying on a side.
ANGLES: Final = (0, -15, 15, -30, 30, -45, 45, -90, 90)
# The lowest detector score kept: the faces measured above were found from 0.68 to 0.92.
LOOSE_SCORE: Final = 0.6
# Two faces this close are the same face, found at two angles: the best score stays.
SAME_FACE: Final = 0.5


@dataclass(frozen=True, slots=True)
class LookJob:
    """One photo, and the recipe of a finder less strict than the audit's."""

    path: Path
    recipe: FinderRecipe


@dataclass(frozen=True, slots=True)
class LookedFace:
    """A face found by the second look: its vector, its score, its picture cut out."""

    embedding: bytes
    score: float
    crop: bytes


def second_look(job: LookJob) -> tuple[LookedFace, ...]:
    """Look for the faces of a photo, turned by each angle.

    Args:
        job: The photo and the recipe.

    Returns:
        Each face once, the best score first; none when the photo cannot be read.
    """
    prepare_image_worker()
    finder = finder_of(job.recipe)
    try:
        picture = upright_picture(job.path)
    except unreadable_errors():
        return ()
    found: list[tuple[Face, Image.Image]] = []
    for angle in ANGLES:
        turned = picture.rotate(angle, Image.Resampling.BILINEAR, expand=True)
        found.extend((face, turned) for face in finder.find(turned))
    found.sort(key=lambda pair: -pair[0].score)
    kept: list[LookedFace] = []
    for face, turned in found:
        vector = vector_of(face.embedding)
        if any(
            float(np.dot(vector, vector_of(one.embedding))) >= SAME_FACE for one in kept
        ):
            continue
        kept.append(LookedFace(face.embedding, face.score, crop_jpeg(turned, face.box)))
    return tuple(kept)
