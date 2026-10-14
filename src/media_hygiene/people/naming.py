"""Who is on each face: the faces the user confirmed, then the nearest of them.

A face is known by its photo and its number in it (`face_id`), never by its group: a
new grouping keeps every name. A face confirmed on the page keeps its name; any other
takes the name of the nearest confirmed face when they are similar enough
(`[people] similarity`), never one the user removed it from. Faces near those the
user ignored are ignored too: the same stranger is not shown again.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import EMBEDDING_SIZE, vector_of
from media_hygiene.people.followed import follow_ids

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from numpy.typing import NDArray

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace

_SEPARATOR: Final = "#"
_BLOCK: Final = 4096  # faces compared at once: a few MB of similarities
_IGNORED: Final = ""  # the name of the ignored faces among the references


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


@dataclass(frozen=True, slots=True)
class Known:
    """The faces of reference: their names, their vectors, and who was ruled out."""

    names: tuple[str, ...]  # one per reference row; `_IGNORED` for an ignored face
    vectors: NDArray[np.float32]
    confirmed: dict[str, FaceName]
    rejected: dict[str, frozenset[str]]  # face id → names it is not
    similarity: float

    @classmethod
    def of(
        cls,
        every: Sequence[StoredFace],
        settings: PeopleSettings,
        moves: Mapping[str, str] | None = None,
    ) -> Known:
        """Gather the references among every face of the index.

        Args:
            every: The faces of the index, mounted or not: a name stays known while
                its photos are elsewhere.
            settings: `[people]`, with the names.
            moves: Where the photos the index followed went (`index.moves`): a name
                confirmed before a `sort` still finds its face.

        Returns:
            The references; a face id no longer in the index is left out.
        """
        present = {str(face.path) for face in every}
        settings = follow_ids(settings, moves or {}, present)
        confirmed = {key: FaceName(_IGNORED, How.IGNORED) for key in settings.ignored}
        rejected: dict[str, set[str]] = {}
        for person in settings.person:
            confirmed.update(
                {key: FaceName(person.name, How.CONFIRMED) for key in person.faces}
            )
            for key in person.rejected:
                rejected.setdefault(key, set()).add(person.name)
        rows = [
            (face, confirmed[id_of(face)]) for face in every if id_of(face) in confirmed
        ]
        vectors = (
            np.stack([vector_of(face.embedding) for face, _ in rows])
            if rows
            else np.empty((0, EMBEDDING_SIZE), dtype=np.float32)
        )
        return cls(
            tuple(name.name for _, name in rows),
            vectors,
            confirmed,
            {key: frozenset(names) for key, names in rejected.items()},
            settings.similarity,
        )

    @property
    def people(self) -> tuple[str, ...]:
        """The names of the people with at least one face in the index.

        Returns:
            Each name once, in the order of the file.
        """
        return tuple(dict.fromkeys(name for name in self.names if name != _IGNORED))


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
        scores = similar[row].copy()
        for column, name in enumerate(known.names):
            if name in known.rejected.get(key, ()):
                scores[column] = -1.0
        best = int(np.argmax(scores))
        if scores[best] < known.similarity:
            names.append(NOBODY)
            continue
        name = known.names[best]
        how = How.IGNORED if name == _IGNORED else How.ASSIGNED
        names.append(FaceName(name, how))
    return names
