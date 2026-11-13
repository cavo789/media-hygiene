"""From one face, the photos of that person: the faces of the index close to them.

One face alone is a poor summary of someone: the faces close to it (`LOOK_ALIKE`, the
threshold of the people page) give a mean, closer to that person than any one face;
the photos are those with a face close to that mean, the closest first. A person set
aside before (`aside_faces`) whose mean comes that close is the same person: their
faces join the mean, and the photos set aside now join them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.models import vector_of
from media_hygiene.people.alike import LOOK_ALIKE, MOST, centre

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from media_hygiene.index.aside_faces import AsideFaces
    from media_hygiene.index.face_rows import StoredFace

_ROUNDS: Final = 2  # the mean, then the mean of what it finds


@dataclass(frozen=True, slots=True)
class FaceRows:
    """Faces, and their vectors stacked: one row per face, in the same order."""

    faces: tuple[StoredFace, ...]
    vectors: NDArray[np.float32]


def stacked(faces: Sequence[StoredFace]) -> NDArray[np.float32]:
    """The vectors of faces, one per row.

    Args:
        faces: The faces.

    Returns:
        The matrix; an empty one without faces.
    """
    if not faces:
        return np.empty((0, 0), dtype=np.float32)
    return np.stack([vector_of(face.embedding) for face in faces])


def kept_rows(every: FaceRows, kept: tuple[StoredFace, ...]) -> FaceRows:
    """The rows of some faces of `every`, the matrix not stacked again (0805).

    Args:
        every: Every face and the matrix of their vectors.
        kept: Some of them, in their order.

    Returns:
        Those faces and their rows.
    """
    if len(kept) == len(every.faces):
        return FaceRows(kept, every.vectors)
    wanted = {id(face) for face in kept}
    mask = np.fromiter(
        (id(face) in wanted for face in every.faces), dtype=bool, count=len(every.faces)
    )
    return FaceRows(kept, every.vectors[mask])


@dataclass(frozen=True, slots=True)
class Likeness:
    """The faces of a person, one per photo, the closest first, and who they were."""

    faces: tuple[StoredFace, ...]
    known: AsideFaces | None  # the person set aside before they look like


def unit(vectors: NDArray[np.float32]) -> NDArray[np.float32]:
    """The mean of vectors, of length 1.

    Args:
        vectors: One per row.

    Returns:
        The vector.
    """
    mean = vectors.mean(axis=0)
    return (mean / max(float(np.linalg.norm(mean)), 1e-9)).astype(np.float32)


def known_person(seed: bytes, people: Sequence[AsideFaces]) -> AsideFaces | None:
    """The person set aside a face looks like most, if close enough.

    Args:
        seed: The face's vector.
        people: The people set aside.

    Returns:
        Them; None when nobody comes to `LOOK_ALIKE`.
    """
    vector = vector_of(seed)
    scored = [(float(np.dot(vector, centre(one))), one) for one in people]
    best = max(scored, default=(0.0, None), key=lambda pair: pair[0])
    return best[1] if best[0] >= LOOK_ALIKE else None


def likeness(seed: bytes, rows: FaceRows, people: Sequence[AsideFaces]) -> Likeness:
    """The photos of the person a face shows.

    Args:
        seed: The face's vector.
        rows: The faces of the index to look in, and their vectors.
        people: The people set aside.

    Returns:
        One face per photo, the closest first (`MOST` at most), and the person set
        aside they are, if any.
    """
    known = known_person(seed, people)
    before = known.embeddings if known is not None else ()
    starting = [vector_of(seed), *(vector_of(one) for one in before)]
    every, vectors = rows.faces, rows.vectors
    if not every:
        return Likeness((), known)
    mean = unit(np.stack(starting))
    close = np.empty(0, dtype=np.int64)
    likeness_of = np.zeros(len(every), dtype=np.float32)
    for _ in range(_ROUNDS):
        likeness_of = vectors @ mean
        close = np.flatnonzero(likeness_of >= LOOK_ALIKE)
        mean = unit(np.concatenate((np.stack(starting), vectors[close])))
    return Likeness(_one_per_photo(every, close, likeness_of), known)


def _one_per_photo(
    every: Sequence[StoredFace], close: NDArray[np.int64], score: NDArray[np.float32]
) -> tuple[StoredFace, ...]:
    """The closest face of each photo, the closest first.

    Args:
        every: Every face of the index.
        close: The rows close enough.
        score: The likeness of every row.

    Returns:
        At most `MOST` faces.
    """
    best: dict[object, int] = {}
    for row in close[np.argsort(-score[close], kind="stable")].tolist():
        best.setdefault(every[row].path, row)
    return tuple(every[row] for row in best.values())[:MOST]
