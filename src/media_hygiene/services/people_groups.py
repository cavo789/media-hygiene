"""Group the faces of the index: small and blurry ones apart, the rest by likeness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from media_hygiene.faces.cluster import Linkage, group_faces
from media_hygiene.faces.models import EMBEDDING_SIZE, vector_of

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace


@dataclass(frozen=True, slots=True)
class PeopleGroups:
    """The faces grouped, and those left out (too small first, then too blurry)."""

    groups: tuple[tuple[StoredFace, ...], ...]  # largest first
    too_small: int
    too_blurry: int

    @property
    def people(self) -> tuple[tuple[StoredFace, ...], ...]:
        """The groups of at least two faces: someone seen more than once.

        Returns:
            Those groups, largest first.
        """
        return tuple(group for group in self.groups if len(group) > 1)

    @property
    def alone(self) -> int:
        """How many faces look like no other.

        Returns:
            The number of groups of one face.
        """
        return sum(1 for group in self.groups if len(group) == 1)


def group_people(faces: Sequence[StoredFace], settings: PeopleSettings) -> PeopleGroups:
    """Leave out the faces too small or too blurry, then group the others.

    Args:
        faces: Every face of the index.
        settings: `[people]`.

    Returns:
        The groups and what was left out.
    """
    small = [face for face in faces if face.box.side < settings.min_face]
    sized = [face for face in faces if face.box.side >= settings.min_face]
    kept = [face for face in sized if face.sharpness >= settings.min_sharpness]
    vectors = (
        np.stack([vector_of(face.embedding) for face in kept])
        if kept
        else np.empty((0, EMBEDDING_SIZE), dtype=np.float32)
    )
    rows = group_faces(vectors, Linkage(settings.similarity))
    return PeopleGroups(
        groups=tuple(tuple(kept[row] for row in group) for group in rows),
        too_small=len(small),
        too_blurry=len(sized) - len(kept),
    )
