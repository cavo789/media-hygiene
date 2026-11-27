"""A second look at one photo whose faces the audit missed: turned, and less strict.

The audit looks at each photo upright, from the score `MIN_SCORE`: a face tilted,
lying, or far away scores less and is not kept. Asked for one photo, the page looks
again at the picture turned by `ANGLES`, keeping the faces down to `LOOSE_SCORE`.
Measured 2026-11-15 on "Communion Manon" (215 real photos, upright only): 497 faces at
0.6, 524 at 0.5, 557 at 0.4, of which 488, 508 and 536 close to a person named: below
the audit's score, 3 to 5 faces in 6 are still people, so the user picks. Each face
found is placed back on the upright photo (`upright_box`), the same face found at two
angles is kept once, by its place (`OVERLAP`), and a face the photo has already is not
returned (`beside`). A large photo is also looked at upright on overlapping tiles
(`faces.tiles`, 0840): the small faces of a group photo. What comes back is new,
and kept in the index by the page (`scan_route.looked_again`), named and searched
like any other (0841). Runs in a worker process.
"""

from __future__ import annotations

import dataclasses
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import Image

from media_hygiene.faces.detect import OVERLAP
from media_hygiene.faces.models import FaceBox
from media_hygiene.faces.tiles import find_on_tiles
from media_hygiene.faces.worker import finder_of
from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.image_check import prepare_image_worker

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.models import Face
    from media_hygiene.faces.worker import FinderRecipe

# Degrees, counterclockwise: upright first, then a little, then lying on a side.
ANGLES: Final = (0, -15, 15, -30, 30, -45, 45, -90, 90)
# The lowest detector score kept, the user picking from what is found (measured above).
LOOSE_SCORE: Final = 0.4


@dataclass(frozen=True, slots=True)
class LookJob:
    """One photo, the recipe of a finder less strict than the audit's, its boxes."""

    path: Path
    recipe: FinderRecipe
    beside: tuple[FaceBox, ...] = ()  # the faces the photo has: not returned again


def second_look(job: LookJob) -> tuple[Face, ...]:
    """Look for the faces of a photo, turned by each angle.

    Args:
        job: The photo, the recipe and the boxes it has.

    Returns:
        Each new face once, placed on the upright photo, the best score first; none
        when the photo cannot be read.
    """
    prepare_image_worker()
    finder = finder_of(job.recipe)
    try:
        picture = upright_picture(job.path)
    except unreadable_errors():
        return ()
    found: list[Face] = []
    for angle in ANGLES:
        turned = picture.rotate(angle, Image.Resampling.BILINEAR, expand=True)
        turn = Turn(angle, picture.size, turned.size)
        found.extend(
            dataclasses.replace(face, box=upright_box(face.box, turn), landmarks=())
            for face in finder.find(turned)
        )
    found.extend(find_on_tiles(finder, picture))
    found.sort(key=lambda face: -face.score)
    kept: list[Face] = []
    for face in found:
        boxes = (*job.beside, *(one.box for one in kept))
        if all(face.box.overlap(box) <= OVERLAP for box in boxes):
            kept.append(face)
    return tuple(kept)


@dataclass(frozen=True, slots=True)
class Turn:
    """A turn of the picture: its angle, its size before and after (`expand`)."""

    angle: float
    before: tuple[int, int]
    after: tuple[int, int]


def upright_box(box: FaceBox, turn: Turn) -> FaceBox:
    """Place a box found on the turned picture back on the upright one.

    Its centre turns back around the picture's centre; its sides stay (a face turned
    by 90° swaps them back).

    Args:
        box: The box on the turned picture.
        turn: The turn.

    Returns:
        The box on the upright picture.
    """
    radians = math.radians(turn.angle)
    cos, sin = math.cos(radians), math.sin(radians)
    dx = box.x + box.width / 2 - turn.after[0] / 2
    dy = box.y + box.height / 2 - turn.after[1] / 2
    x = cos * dx - sin * dy + turn.before[0] / 2
    y = sin * dx + cos * dy + turn.before[1] / 2
    wide, high = (
        (box.height, box.width) if abs(sin) > abs(cos) else (box.width, box.height)
    )
    return FaceBox(x - wide / 2, y - high / 2, wide, high)
