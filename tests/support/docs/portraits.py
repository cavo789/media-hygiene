"""Faces pasted into some scenes of the demo library: three people and a stranger.

The faces are generated ones, in the public domain (`faces/ATTRIBUTION.md`): never a
real person. A face belongs to a scene (its kind and seed), not to a file, so every
rendering of that scene shows it: the copies, the smaller WhatsApp or e-mail versions.
No burst scene holds one: a series keeps its own subject and its shaken shot.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Final

from PIL import Image, ImageDraw, ImageFilter, ImageOps

if TYPE_CHECKING:
    from collections.abc import Mapping

FACES: Final = Path(__file__).parent / "faces"
_FEATHER: Final = 12.0  # the blurred edge of the oval: the face melts into the scene


class Person(StrEnum):
    """Who a face is, named after its file in `faces/`."""

    WOMAN = "woman"  # the one the documentation names, Chloé
    BOY = "boy"
    MAN = "man"
    STRANGER = "stranger"  # in one photo only: no group of their own


@dataclass(frozen=True, slots=True)
class Placement:
    """A face in a scene: where its top-left corner lies, how wide, mirrored or not."""

    person: Person
    left: int
    top: int
    width: int
    mirrored: bool = False


# (kind, seed) of `pictures.Picture` → its face. Holidays: beach 1-5, sunset 6-9;
# birthday: balloons 10-12 (not the burst); Christmas 1-6; lake: meadow 40-41;
# hike: mountains 22.
_PLACEMENTS: Final[Mapping[tuple[str, int], Placement]] = {
    ("beach", 1): Placement(Person.WOMAN, 600, 330, 300),
    ("beach", 2): Placement(Person.WOMAN, 380, 300, 340, mirrored=True),
    ("beach", 3): Placement(Person.WOMAN, 860, 360, 280),
    ("balloons", 10): Placement(Person.WOMAN, 540, 280, 320),
    ("balloons", 11): Placement(Person.WOMAN, 300, 320, 300, mirrored=True),
    ("balloons", 12): Placement(Person.WOMAN, 820, 300, 340),
    ("christmas", 2): Placement(Person.WOMAN, 640, 340, 290),
    ("beach", 5): Placement(Person.BOY, 520, 400, 260),
    ("sunset", 6): Placement(Person.BOY, 760, 380, 280, mirrored=True),
    ("christmas", 4): Placement(Person.BOY, 420, 360, 300),
    ("christmas", 5): Placement(Person.BOY, 880, 380, 270, mirrored=True),
    ("meadow", 40): Placement(Person.BOY, 600, 420, 290),
    ("sunset", 8): Placement(Person.MAN, 460, 300, 330),
    ("sunset", 9): Placement(Person.MAN, 900, 320, 300, mirrored=True),
    ("christmas", 1): Placement(Person.MAN, 560, 300, 320),
    ("mountains", 22): Placement(Person.MAN, 700, 360, 290),
    ("meadow", 41): Placement(Person.STRANGER, 640, 360, 300),
}


def placement_of(kind: str, seed: int) -> Placement | None:
    """The face of a scene, if it has one.

    Args:
        kind: The kind of the picture (`beach`, …).
        seed: Its seed.

    Returns:
        Where the face goes, or None.
    """
    return _PLACEMENTS.get((kind, seed))


def paste_face(scene: Image.Image, placement: Placement) -> None:
    """Paste a face into a scene, inside a soft oval.

    Args:
        scene: The picture, drawn wider than the frame; changed in place.
        placement: Which face, where, how large.
    """
    with Image.open(FACES / f"{placement.person}.jpg") as source:
        face = source.convert("RGB")
    if placement.mirrored:
        face = ImageOps.mirror(face)
    height = round(face.height * placement.width / face.width)
    face = face.resize((placement.width, height), Image.Resampling.LANCZOS)
    mask = Image.new("L", face.size, 0)
    inset = round(_FEATHER)
    ImageDraw.Draw(mask).ellipse(
        (inset, inset, face.width - inset, face.height - inset), fill=255
    )
    mask = mask.filter(ImageFilter.GaussianBlur(_FEATHER))
    scene.paste(face, (placement.left, placement.top), mask)
