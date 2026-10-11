"""The faces of the page, each under a number, and the groups as numbers.

A face is known to the page by its number in this run only: the page never sees a
path it could ask for, only numbers the board hands out. The host path of each photo
is shown as text, to find it again.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.services.people_groups import PeopleGroups


@dataclass(frozen=True, slots=True)
class PeopleBoard:
    """The faces of the page, by number, and the groups as numbers."""

    faces: tuple[StoredFace, ...]
    groups: tuple[tuple[int, ...], ...]
    alone: int

    @classmethod
    def of(cls, grouped: PeopleGroups) -> PeopleBoard:
        """Number the faces of the groups of at least two.

        Args:
            grouped: The groups.

        Returns:
            The board.
        """
        faces: list[StoredFace] = []
        groups: list[tuple[int, ...]] = []
        for group in grouped.people:
            start = len(faces)
            faces.extend(group)
            groups.append(tuple(range(start, len(faces))))
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
