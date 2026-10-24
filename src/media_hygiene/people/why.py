"""Why a face has a name: confirmed by the user, or close to a face they confirmed.

Computed for one face, on demand (TODO 0318): the reference that gave the name (its
id), the likeness and the threshold (`[people] similarity`), and the nearest other
person when they come close too, which is often whom the user expected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import vector_of
from media_hygiene.people.known import IGNORED_NAME
from media_hygiene.people.naming import How, id_of

if TYPE_CHECKING:
    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.known import Known

CLOSE: Final = 0.03  # another person this close to the best is shown too


@dataclass(frozen=True, slots=True)
class Runner:
    """Another person whose face comes close: their name and the likeness."""

    name: str
    score: float


@dataclass(frozen=True, slots=True)
class Why:
    """How a face got its name: confirmed, or the reference, its likeness, the rule."""

    how: How | None
    reference: str = ""  # the face id of the reference that gave the name
    score: float = 0.0
    threshold: float = 0.0
    runner: Runner | None = None


def why_named(face: StoredFace, known: Known) -> Why:
    """Explain the name of one face, as `name_all` gives it.

    Args:
        face: The face.
        known: The references.

    Returns:
        Confirmed (or ignored) without a score; else the nearest reference, the
        likeness, the threshold and, for a face named, the next person when
        within `CLOSE`.
    """
    key = id_of(face)
    if key in known.confirmed:
        return Why(known.confirmed[key].how)
    if not known.names:
        return Why(None)
    scores = known.scores(key, vector_of(face.embedding) @ known.vectors.T)
    best = int(np.argmax(scores))
    name, score = known.names[best], float(scores[best])
    others = [
        (float(value), other)
        for value, other in zip(scores, known.names, strict=True)
        if other not in {name, IGNORED_NAME}
    ]
    near = max(others, default=None)
    named = score >= known.rule.similarity and known.rule.thresholds.recognisable(face)
    close = named and near is not None and score - near[0] <= CLOSE
    runner = Runner(near[1], near[0]) if close and near is not None else None
    how = (How.ASSIGNED if name else How.IGNORED) if named else None
    return Why(how, known.ids[best], score, known.rule.similarity, runner)
