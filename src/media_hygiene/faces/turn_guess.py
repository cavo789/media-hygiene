"""Guess a photo's turn in the `people` worker, from the picture it decoded (0725).

The faces found as stored are counted once, by the face run itself; only a photo worth
guessing (`straighten.worth_guessing`) is looked at in its three other turns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import Image

from media_hygiene.classify.rules.matchers import screenshot_name
from media_hygiene.faces.straighten import (
    Candidate,
    Turn,
    proposed_turn,
    turned,
    worth_guessing,
)
from media_hygiene.report.thumbnails import unreadable_errors

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.engine import FaceFinder

_MAKE: Final = 0x010F
_ORIENTATION: Final = 0x0112
NO_TURN: Final = 0


def candidate_of(path: Path) -> Candidate | None:
    """Read what the guess needs from a picture's header.

    Args:
        path: The picture.

    Returns:
        Its camera make, orientation tag and screenshot name; None when unreadable
        by Pillow (a RAW file).
    """
    try:
        with Image.open(path) as image:
            exif = image.getexif()
    except unreadable_errors():
        return None
    make = exif.get(_MAKE)
    orientation = exif.get(_ORIENTATION)
    return Candidate(
        str(make) if make else None,
        orientation if isinstance(orientation, int) else None,
        screenshot_name(path.stem),
    )


@dataclass(frozen=True, slots=True)
class Seen:
    """A photo as the face run saw it: its picture and the faces found in it."""

    path: Path
    picture: Image.Image  # decoded upright: as stored, for a photo worth guessing
    faces: int


def turn_of(seen: Seen, finder: FaceFinder) -> int:
    """The turn to propose for a photo, in degrees clockwise.

    Args:
        seen: The photo, its picture and the faces found as stored.
        finder: The face finder.

    Returns:
        90, 180 or 270; `NO_TURN` when none is proposed or the photo is not guessed.
    """
    candidate = candidate_of(seen.path)
    if seen.faces or candidate is None or not worth_guessing(candidate):
        return NO_TURN
    faces = {Turn.NONE: seen.faces} | {
        turn: len(finder.find(turned(seen.picture, turn)))
        for turn in (Turn.QUARTER, Turn.HALF, Turn.THREE_QUARTERS)
    }
    turn = proposed_turn(faces)
    return NO_TURN if turn is None else int(turn)
