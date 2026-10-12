"""One synthetic picture: a scene drawn wider than the frame, panned, grained.

A burst shot may have a pose: a subject moved across the frame, so that the shots of a
series differ like real ones (another pose), not only by a few pixels of panning.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from PIL import ImageDraw, ImageFilter

from tests.support.docs.festive import balloons, christmas
from tests.support.docs.landscapes import beach, meadow, mountains, sunset
from tests.support.docs.painting import grain
from tests.support.docs.portraits import paste_face, placement_of

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from PIL import Image

    from tests.support.docs.painting import Size

WIDTH: Final = 1500
HEIGHT: Final = 1000
_MARGIN: Final = 80  # drawn wider than the frame: a burst pans across the same scene
_SOFTEN: Final = 0.8
_SHAKEN: Final = 6.0
_GRAIN_SEEDS: Final = 1000
_SUBJECT: Final = 110  # diameter of the posing subject, in pixels
_POSE_STEP: Final = 90  # how far it moves from one pose to the next
_SUBJECT_COLOUR: Final = (40, 45, 60)


class Kind(StrEnum):
    """What a picture shows."""

    BEACH = "beach"
    MOUNTAINS = "mountains"
    SUNSET = "sunset"
    MEADOW = "meadow"
    CHRISTMAS = "christmas"
    BALLOONS = "balloons"


_PAINTERS: Final[Mapping[Kind, Callable[[random.Random, Size], Image.Image]]] = {
    Kind.BEACH: beach,
    Kind.MOUNTAINS: mountains,
    Kind.SUNSET: sunset,
    Kind.MEADOW: meadow,
    Kind.CHRISTMAS: christmas,
    Kind.BALLOONS: balloons,
}


@dataclass(frozen=True, slots=True)
class Picture:
    """A scene: the same kind and seed always draw the same picture."""

    kind: Kind
    seed: int
    pan: int = _MARGIN // 2
    shaken: bool = False
    pose: int | None = None  # burst shots: where the subject stands, None: no subject


def render(picture: Picture) -> Image.Image:
    """Draw a picture.

    Args:
        picture: The scene, how far the camera panned, whether it shook.

    Returns:
        The picture, `WIDTH` by `HEIGHT` pixels.
    """
    # Seeded drawing, not secrets: the same scene on every run.
    rnd = random.Random(f"{picture.kind}-{picture.seed}")  # noqa: S311
    wide = _PAINTERS[picture.kind](rnd, (WIDTH + _MARGIN, HEIGHT))
    if (face := placement_of(picture.kind, picture.seed)) is not None:
        paste_face(wide, face)
    frame = wide.crop((picture.pan, 0, picture.pan + WIDTH, HEIGHT))
    if picture.pose is not None:
        left, top = _SUBJECT + _POSE_STEP * picture.pose, HEIGHT // 3
        ImageDraw.Draw(frame).ellipse(
            (left, top, left + _SUBJECT, top + _SUBJECT), fill=_SUBJECT_COLOUR
        )
    frame = frame.filter(ImageFilter.GaussianBlur(_SOFTEN))
    if picture.shaken:
        frame = frame.filter(ImageFilter.GaussianBlur(_SHAKEN))
    return grain(frame, picture.seed * _GRAIN_SEEDS + picture.pan)
