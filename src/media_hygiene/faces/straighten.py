"""Guess the turn a sideways photo needs, from the faces found in its four turns (0711).

Only camera photos are guessed: a screenshot, a games console's capture or a picture
without any camera in its EXIF (a collage, a drawing, a scan) is left out — two of the
three wrong turns measured on the maintainer's collection were not photos. Only photos
whose orientation tag says nothing (none, `0` or `1`) are guessed: a tagged one is
already shown as its camera meant. The guess is a proposal, never applied blindly: a
person lying down on an upright photo is its blind spot (1 in 22 measured).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Final

from PIL import Image

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

# Makes that are not cameras (measured, step 48: 820 `Nintendo 3DS` captures).
NOT_CAMERAS: Final = ("nintendo",)
_SILENT_TAGS: Final = frozenset({None, 0, 1})
_HALF_TURN_FACES: Final = 2  # an upside-down guess needs this many faces to agree


class Turn(IntEnum):
    """Degrees a photo is turned clockwise to stand upright."""

    NONE = 0
    QUARTER = 90
    HALF = 180
    THREE_QUARTERS = 270


_TRANSPOSE: Final = {
    Turn.QUARTER: Image.Transpose.ROTATE_270,  # PIL turns counter-clockwise
    Turn.HALF: Image.Transpose.ROTATE_180,
    Turn.THREE_QUARTERS: Image.Transpose.ROTATE_90,
}
# The EXIF orientation that shows the stored pixels turned clockwise by so much.
ORIENTATION_OF: Final = {Turn.QUARTER: 6, Turn.HALF: 3, Turn.THREE_QUARTERS: 8}


@dataclass(frozen=True, slots=True)
class Candidate:
    """What the index knows of a photo before its pixels are looked at."""

    camera: str | None  # make and model, from the EXIF
    orientation: int | None  # its EXIF orientation tag, as stored
    screenshot: bool  # `classify`'s screenshot test


def worth_guessing(candidate: Candidate) -> bool:
    """Whether a photo's turn is worth guessing.

    Args:
        candidate: The photo's facts.

    Returns:
        True for a camera photo whose orientation tag says nothing.
    """
    if candidate.screenshot or candidate.orientation not in _SILENT_TAGS:
        return False
    make = (candidate.camera or "").strip().casefold()
    return bool(make) and not make.startswith(NOT_CAMERAS)


def turned(picture: Image.Image, turn: Turn) -> Image.Image:
    """The picture turned clockwise.

    Args:
        picture: The picture as stored.
        turn: The turn.

    Returns:
        The picture turned (the same picture for `Turn.NONE`).
    """
    return picture if turn is Turn.NONE else picture.transpose(_TRANSPOSE[turn])


def proposed_turn(faces: Mapping[Turn, int]) -> Turn | None:
    """The turn to propose, from the faces found in each turn.

    Proposed when the stored picture has no face and a turn has some (measured: every
    right turn had none as stored, so no score margin helps); upside down only when two
    faces or more agree.

    Args:
        faces: The number of faces found in each turn.

    Returns:
        The turn with the most faces, or None to leave the photo as it is.
    """
    if faces.get(Turn.NONE, 0) > 0:
        return None
    best = max(
        (Turn.QUARTER, Turn.THREE_QUARTERS, Turn.HALF), key=lambda t: faces.get(t, 0)
    )
    found = faces.get(best, 0)
    if found == 0 or (best is Turn.HALF and found < _HALF_TURN_FACES):
        return None
    return best


def guess_turn(
    picture: Image.Image, count: Callable[[Image.Image], int]
) -> Turn | None:
    """Guess the turn a picture needs.

    Args:
        picture: The picture as stored (no orientation applied), RGB.
        count: The number of faces found in a picture (YuNet in the app).

    Returns:
        The turn to propose, or None.
    """
    return proposed_turn({turn: count(turned(picture, turn)) for turn in Turn})
