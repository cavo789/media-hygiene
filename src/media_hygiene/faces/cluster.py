"""Group the faces that look alike: the same person, probably, until someone names it.

Each face is linked to its closest neighbours whose cosine similarity reaches the
threshold (a nearest-neighbour graph, both directions). The groups come from Chinese
whispers on that graph (Biemann, 2006; dlib's face clustering): each face takes, in
turn, the group its links weigh most for, until nothing changes. Unlike plain
connected faces, one face that looks a bit like two people does not merge them.
Computed from the index in blocks; `services.people_labels` keeps the result, and new
faces join it without moving the others (`join_labels`): a later threshold regroups in
seconds. The order is drawn from a fixed seed: the same faces give the same groups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.neighbours import NEIGHBOURS, Linkage, neighbours

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = [
    "NEIGHBOURS",
    "Linkage",
    "face_labels",
    "group_faces",
    "groups_of",
    "join_labels",
]

type Groups = tuple[tuple[int, ...], ...]

ROUNDS: Final = 20  # at most; it usually settles in a few
_SEED: Final = 0


@dataclass(frozen=True, slots=True)
class _Graph:
    """The links of every face, compressed: face i's are `targets[starts[i]:...]`."""

    starts: NDArray[np.int64]
    targets: NDArray[np.int64]
    weights: NDArray[np.float64]


def group_faces(vectors: NDArray[np.float32], linkage: Linkage) -> Groups:
    """Group the faces whose vectors are close.

    Args:
        vectors: One unit vector per face, one row each.
        linkage: The threshold and the number of neighbours.

    Returns:
        The groups, as row numbers, largest first (then by first row); a face
        linked to no other is a group of its own.
    """
    return groups_of(face_labels(vectors, linkage))


def face_labels(vectors: NDArray[np.float32], linkage: Linkage) -> NDArray[np.int64]:
    """Tell the group of each face, from all of them.

    Args:
        vectors: One unit vector per face, one row each.
        linkage: The threshold and the number of neighbours.

    Returns:
        The group of each face (the number of one of its members).
    """
    count = len(vectors)
    every = np.arange(count, dtype=np.int64)
    return _whispers(_graph(vectors, linkage, every), every.copy(), every)


def join_labels(
    vectors: NDArray[np.float32], labels: NDArray[np.int64], linkage: Linkage
) -> NDArray[np.int64]:
    """Give the new faces a group; the groups of the others do not move.

    Each new face takes the group its closest neighbours weigh most for: a known
    one, or a new one with the other new faces it looks like.

    Args:
        vectors: One unit vector per face, one row each.
        labels: The group of each face; negative for a new face.
        linkage: The threshold and the number of neighbours.

    Returns:
        The group of each face.
    """
    fresh = np.flatnonzero(labels < 0)
    start = int(labels.max(initial=-1)) + 1
    joined = labels.astype(np.int64)
    joined[fresh] = start + fresh
    return _whispers(_graph(vectors, linkage, fresh), joined, fresh)


def groups_of(labels: NDArray[np.int64]) -> Groups:
    """Gather the faces of each group.

    Args:
        labels: The group of each face.

    Returns:
        The groups, as row numbers, largest first (then by first row).
    """
    members: dict[int, list[int]] = {}
    for index, label in enumerate(labels.tolist()):
        members.setdefault(label, []).append(index)
    ordered = sorted(members.values(), key=lambda group: (-len(group), group[0]))
    return tuple(tuple(group) for group in ordered)


def _graph(
    vectors: NDArray[np.float32], linkage: Linkage, rows: NDArray[np.int64]
) -> _Graph:
    """Link some faces to their close neighbours, in both directions.

    Args:
        vectors: The unit vectors.
        linkage: The threshold and the number of neighbours.
        rows: The faces whose neighbours are looked for.

    Returns:
        The links, each pair once per direction, grouped by face.
    """
    count = len(vectors)
    links = neighbours(vectors, linkage, rows)
    both = np.concatenate((links, links[:, (1, 0, 2)]))
    codes = both[:, 0].astype(np.int64) * count + both[:, 1].astype(np.int64)
    _, first = np.unique(codes, return_index=True)  # sorted by source, then target
    kept = both[first]
    per_face = np.bincount(kept[:, 0].astype(np.int64), minlength=count)
    starts = np.concatenate(([0], np.cumsum(per_face))).astype(np.int64)
    return _Graph(starts, kept[:, 1].astype(np.int64), kept[:, 2])


def _whispers(
    graph: _Graph, labels: NDArray[np.int64], moving: NDArray[np.int64]
) -> NDArray[np.int64]:
    """Spread the groups along the links until they settle.

    Args:
        graph: The links.
        labels: The group each face starts in; changed in place.
        moving: The faces that may change group.

    Returns:
        The group of each face.
    """
    order = np.random.default_rng(_SEED)
    for _ in range(ROUNDS):
        changed = False
        for node in order.permutation(moving).tolist():
            begin, end = graph.starts[node], graph.starts[node + 1]
            if begin == end:
                continue
            around, where = np.unique(
                labels[graph.targets[begin:end]], return_inverse=True
            )
            best = int(around[np.argmax(np.bincount(where, graph.weights[begin:end]))])
            if best != labels[node]:
                labels[node] = best
                changed = True
        if not changed:
            break
    return labels
