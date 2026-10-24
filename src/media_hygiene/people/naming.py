"""Who is on each face: the faces the user confirmed, then the nearest of them.

A face is known by its photo and its number in it (`face_id`), never by its group: a
new grouping keeps every name. A face confirmed on the page keeps its name; any other
takes the name of the nearest confirmed face when they are similar enough
(`[people] similarity`), never one the user removed it from, and only when it is
large and sharp enough to be shown on the people page (`min_face`, `min_sharpness`,
TODO 0316). Faces near those the user ignored are ignored too: the same stranger is
not shown again. The references are gathered by `known.Known`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import vector_of

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.known import Known

_SEPARATOR: Final = "#"
_BLOCK: Final = 4096  # faces compared at once: a few MB of similarities


class How(StrEnum):
    """How a face got its name."""

    CONFIRMED = "confirmed"  # the user said so on the page
    ASSIGNED = "assigned"  # close enough to a confirmed face
    IGNORED = "ignored"  # a stranger, a poster: never named


@dataclass(frozen=True, slots=True)
class FaceName:
    """The name of one face, and how it got it; no name: nobody known."""

    name: str = ""
    how: How | None = None

    @property
    def named(self) -> bool:
        """Tell whether the face is someone's.

        Returns:
            True when confirmed or assigned.
        """
        return self.how in {How.CONFIRMED, How.ASSIGNED}


NOBODY: Final = FaceName()


def face_id(path: Path, number: int) -> str:
    """The id of a face, as `config.toml` keeps it.

    Args:
        path: Its photo, in the container.
        number: Its number in the photo.

    Returns:
        `<path>#<number>`.
    """
    return f"{path}{_SEPARATOR}{number}"


def id_of(face: StoredFace) -> str:
    """The id of a stored face.

    Args:
        face: The face.

    Returns:
        Its id.
    """
    return face_id(face.path, face.number)


def name_all(faces: Sequence[StoredFace], known: Known) -> tuple[FaceName, ...]:
    """Name each face: confirmed, or the nearest reference close enough.

    Args:
        faces: The faces to name.
        known: The references.

    Returns:
        One name per face, in order.
    """
    names: list[FaceName] = []
    for start in range(0, len(faces), _BLOCK):
        names.extend(_block(faces[start : start + _BLOCK], known))
    return tuple(names)


def _block(faces: Sequence[StoredFace], known: Known) -> list[FaceName]:
    """Name a block of faces.

    Args:
        faces: The block.
        known: The references.

    Returns:
        Their names.
    """
    if not known.names:
        return [known.confirmed.get(id_of(face), NOBODY) for face in faces]
    vectors = np.stack([vector_of(face.embedding) for face in faces])
    similar = vectors @ known.vectors.T
    names: list[FaceName] = []
    for row, face in enumerate(faces):
        key = id_of(face)
        if key in known.confirmed:
            names.append(known.confirmed[key])
            continue
        if not known.rule.thresholds.recognisable(face):  # never shown: never named
            names.append(NOBODY)
            continue
        scores = known.scores(key, similar[row])
        best = int(np.argmax(scores))
        if scores[best] < known.rule.similarity:
            names.append(NOBODY)
            continue
        name = known.names[best]
        how = How.ASSIGNED if name else How.IGNORED
        names.append(FaceName(name, how))
    return names
