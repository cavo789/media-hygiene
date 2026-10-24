"""The faces of reference: those the user confirmed or ignored, with their vectors.

Gathered once per run from every face of the index (mounted or not: a name stays known
while its photos are elsewhere) and the names of `[people]`, the ids of moved photos
followed (`followed`, TODO 0146). Each reference keeps its id, so that a name given can
be explained by the face that gave it (TODO 0318).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import EMBEDDING_SIZE, vector_of
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.naming import FaceName, How, id_of
from media_hygiene.people.recognisable import Thresholds

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from numpy.typing import NDArray

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.index.face_rows import StoredFace

IGNORED_NAME: Final = ""  # the name of the ignored faces among the references


@dataclass(frozen=True, slots=True)
class Rule:
    """When a face takes its nearest reference's name: likeness, size, sharpness."""

    similarity: float
    thresholds: Thresholds


@dataclass(frozen=True, slots=True)
class Known:
    """The faces of reference: their names, ids and vectors, and who was ruled out."""

    names: tuple[str, ...]  # one per reference row; `IGNORED_NAME` for an ignored face
    ids: tuple[str, ...]  # the face id of each reference row
    vectors: NDArray[np.float32]
    confirmed: dict[str, FaceName]
    rejected: dict[str, frozenset[str]]  # face id → names it is not
    rule: Rule

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
            settings: `[people]`, with the names and the thresholds.
            moves: Where the photos the index followed went (`index.moves`): a name
                confirmed before a `sort` still finds its face.

        Returns:
            The references; a face id no longer in the index is left out.
        """
        present = {str(face.path) for face in every}
        settings = follow_ids(settings, moves or {}, present)
        confirmed = {
            key: FaceName(IGNORED_NAME, How.IGNORED) for key in settings.ignored
        }
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
            names=tuple(name.name for _, name in rows),
            ids=tuple(id_of(face) for face, _ in rows),
            vectors=vectors,
            confirmed=confirmed,
            rejected={key: frozenset(names) for key, names in rejected.items()},
            rule=Rule(settings.similarity, Thresholds.of(settings)),
        )

    @property
    def people(self) -> tuple[str, ...]:
        """The names of the people with at least one face in the index.

        Returns:
            Each name once, in the order of the file.
        """
        return tuple(dict.fromkeys(name for name in self.names if name != IGNORED_NAME))

    def scores(self, key: str, similar: NDArray[np.float32]) -> NDArray[np.float32]:
        """The likeness of a face to each reference, those of names it is not at -1.

        Args:
            key: The face id.
            similar: Its cosine similarity to each reference row.

        Returns:
            A copy, the references of the names ruled out for it at -1.
        """
        scores = similar.copy()
        ruled_out = self.rejected.get(key, frozenset())
        for column, name in enumerate(self.names):
            if name in ruled_out:
                scores[column] = -1.0
        return scores
