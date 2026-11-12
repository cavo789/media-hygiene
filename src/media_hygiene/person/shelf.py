"""The faces the person page knows, by number: the page never sees a path to ask for.

A face of the index keeps its box, cut out of its photo on request; a face found by a
second look (the photo turned, `second_look`) keeps the small picture cut then, in
memory only, never written: its box is in a turned picture. The same face (the same
photo and vector) keeps its number for as long as the page's server runs. The page
sees a face as `face_view` says: its number, its picture, whether it was drawn by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.index.drawn_faces import is_drawn
from media_hygiene.person.routes import FACE_PREFIX, JPEG

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.models import FaceBox


@dataclass(frozen=True, slots=True)
class ShelfFace:
    """A face: its photo, its vector, where it is or its picture already cut."""

    path: Path  # in the container
    embedding: bytes
    box: FaceBox | None = None  # in the upright photo
    crop: bytes | None = None  # JPEG, found turned by a second look
    number: int | None = None  # its number in the photo, in the index: it can be named


class FaceShelf:
    """The faces handed to the page, by number."""

    def __init__(self) -> None:
        """Start with no face."""
        self._faces: list[ShelfFace] = []
        self._numbers: dict[tuple[Path, bytes], int] = {}

    def add(self, face: ShelfFace) -> int:
        """Number a face, or give back the number it has.

        Args:
            face: The face.

        Returns:
            Its number.
        """
        known = (face.path, face.embedding)
        if known not in self._numbers:
            self._numbers[known] = len(self._faces)
            self._faces.append(face)
        return self._numbers[known]

    def face(self, key: str) -> ShelfFace | None:
        """The face a number names.

        Args:
            key: The number, from the page.

        Returns:
            The face, or None for anything else.
        """
        if not key.isdigit() or int(key) >= len(self._faces):
            return None
        return self._faces[int(key)]


def face_view(key: int, number: int | None = None) -> dict[str, object]:
    """A face to choose, as the page reads it.

    Args:
        key: Its number on the shelf.
        number: Its number in its photo, in the index; None for a second look's.

    Returns:
        Its number, its picture, and `drawn` for a face drawn by hand (0715): the
        page offers to forget it.
    """
    drawn = number is not None and is_drawn(number)
    return {"key": key, "face": f"{FACE_PREFIX}{key}{JPEG}", "drawn": drawn}
