"""The faces that look like a person set aside: shown to check, never set aside alone.

Each person set aside is summed up by the mean of their faces (`aside_faces`); every
face of the board comes close to it or not, the faces left out of the groups included
(too small, too blurry, alone). Measured on the maintainer's index (2026-10-24, read
only, 22,000 faces): a face kept by such a group lies at 0.48 or more from the mean of
the others, the closest face left in the index at 0.44, and comparing with the
nearest face of the group instead flags 10,000 faces and more. The faces of photos
already set aside, or no longer on the disk, are left out.
"""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import EMBEDDING_SIZE, vector_of
from media_hygiene.people.remembered import aside_date
from media_hygiene.people.views import faces_view

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from media_hygiene.index.aside_faces import AsideFaces
    from media_hygiene.people.board import PeopleBoard
    from media_hygiene.people.remembered import AsideMemory
    from media_hygiene.people.views import PageView

# Cosine from the mean of a person's faces: every face of their group lies above
# (0.48 at least, measured), a few others close to it (7 of 22,000, measured).
LOOK_ALIKE: Final = 0.40
MOST: Final = 200  # faces shown per person at most, the closest first


def centre(person: AsideFaces) -> NDArray[np.float32]:
    """The mean of a person's faces, of length 1.

    Args:
        person: Their faces.

    Returns:
        The vector.
    """
    mean = np.mean([vector_of(vector) for vector in person.embeddings], axis=0)
    return (mean / max(float(np.linalg.norm(mean)), 1e-9)).astype(np.float32)


class AlikeFinder:
    """Finds, among the faces of the board, those of the people set aside."""

    def __init__(self, board: PeopleBoard, memory: AsideMemory) -> None:
        """Bind the board and the memory of the people set aside.

        Args:
            board: Every face of the page, grouped or not.
            memory: The index keeping their faces.
        """
        self._board = board
        self._memory = memory

    @cached_property
    def _vectors(self) -> NDArray[np.float32]:
        """Every face of the board, one row each.

        Returns:
            The vectors.
        """
        faces = self._board.faces
        if not faces:
            return np.empty((0, EMBEDDING_SIZE), dtype=np.float32)
        return np.stack([vector_of(face.embedding) for face in faces])

    def view(self, view: PageView) -> list[dict[str, object]]:
        """Each person set aside with faces like theirs left, as the page reads them.

        Args:
            view: Host paths, and the files set aside.

        Returns:
            One entry per person, oldest first: when, the label, the photos, the
            faces (the closest first).
        """
        found: list[dict[str, object]] = []
        for person in self._memory.people():
            keys = self._alike(person, view)
            if not keys:
                continue
            board = self._board
            photos = {board.faces[key].path for key in keys}
            found.append(
                {
                    "aside": person.aside,
                    "date": aside_date(person.aside),
                    "label": person.label,
                    "photos": len(photos),
                    "faces": faces_view(board, keys[:MOST], view.host),
                }
            )
        return found

    def _alike(self, person: AsideFaces, view: PageView) -> tuple[int, ...]:
        """The faces close to a person, on photos still there and not set aside.

        Args:
            person: Their faces.
            view: Host paths, and the files set aside.

        Returns:
            Board numbers, the closest first.
        """
        likeness = self._vectors @ centre(person)
        close = np.flatnonzero(likeness >= LOOK_ALIKE)
        ordered = close[np.argsort(-likeness[close], kind="stable")].tolist()
        faces = self._board.faces
        return tuple(
            key
            for key in ordered
            if view.host(faces[key].path) not in view.aside and faces[key].path.exists()
        )
