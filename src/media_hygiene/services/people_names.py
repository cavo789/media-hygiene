"""What a `people` run ends with: the groups, the counts, and who is on how many photos.

A person's photos are those with a face confirmed as theirs, or close enough to one
(`people.naming`): the same faces `search` finds by name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.people.naming import name_all

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.index.face_rows import FaceTally, StoredFace
    from media_hygiene.people.naming import Known
    from media_hygiene.services.people_groups import PeopleGroups


@dataclass(frozen=True, slots=True)
class PeopleResult:
    """The groups of a run, its counts, every face of the index, the people named."""

    groups: PeopleGroups
    tally: FaceTally
    every: tuple[StoredFace, ...]
    named: tuple[tuple[str, int], ...]  # name, photos of the run; most photos first


def named_photos(
    faces: Sequence[StoredFace], known: Known
) -> tuple[tuple[str, int], ...]:
    """Count the photos of each person named.

    Args:
        faces: The faces of the run.
        known: The faces of reference.

    Returns:
        Each person with at least one photo, and how many; most photos first.
    """
    photos: dict[str, set[Path]] = {}
    for face, name in zip(faces, name_all(faces, known), strict=True):
        if name.named:
            photos.setdefault(name.name, set()).add(face.path)
    counted = ((name, len(paths)) for name, paths in photos.items())
    return tuple(sorted(counted, key=lambda item: (-item[1], item[0].casefold())))
