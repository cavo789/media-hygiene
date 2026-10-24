"""The faces of the page, each under a number, and the groups as numbers.

A face is known to the page by its number in this run only: the page never sees a
path it could ask for, only numbers the board hands out. The host path of each photo
is shown as text, to find it again. The faces of no group come after those of the
groups: a face like someone set aside may be one of them (TODO 0328).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.people.naming import id_of

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.services.people_groups import PeopleGroups


@dataclass(frozen=True, slots=True)
class PeopleBoard:
    """The faces of the page, by number, and the groups as numbers."""

    faces: tuple[StoredFace, ...]
    groups: tuple[tuple[int, ...], ...]
    alone: int

    @classmethod
    def of(cls, grouped: PeopleGroups, every: Iterable[StoredFace] = ()) -> PeopleBoard:
        """Number the faces of the groups of at least two, then the others.

        Args:
            grouped: The groups.
            every: Every face of the index: those of no group are numbered after.

        Returns:
            The board.
        """
        faces: list[StoredFace] = []
        groups: list[tuple[int, ...]] = []
        for group in grouped.people:
            start = len(faces)
            faces.extend(group)
            groups.append(tuple(range(start, len(faces))))
        numbered = {(face.path, face.number) for face in faces}
        faces.extend(face for face in every if (face.path, face.number) not in numbered)
        return cls(tuple(faces), tuple(groups), grouped.alone)

    def face(self, key: str) -> StoredFace | None:
        """The face a number names.

        Args:
            key: The number, from the page.

        Returns:
            The face, or None for anything else.
        """
        if not key.isdigit() or int(key) >= len(self.faces):
            return None
        return self.faces[int(key)]

    def ids(self, keys: tuple[int, ...]) -> tuple[str, ...]:
        """The ids of faces of the board.

        Args:
            keys: Their numbers.

        Returns:
            Their ids; unknown numbers are left out.
        """
        return tuple(
            id_of(face) for key in keys if (face := self.face(str(key))) is not None
        )
