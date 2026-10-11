"""Group the faces that look alike: the same person, probably, until someone names it.

Each face is linked to its closest neighbours whose cosine similarity reaches the
threshold (a nearest-neighbour graph, both directions). The groups come from Chinese
whispers on that graph (Biemann, 2006; dlib's face clustering): each face takes, in
turn, the group its links weigh most for, until nothing changes. Unlike plain
connected faces, one face that looks a bit like two people does not merge them.
Computed from the index in blocks, never stored: a later threshold regroups in
seconds. The order is drawn from a fixed seed: the same faces give the same groups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

type Groups = tuple[tuple[int, ...], ...]

# SFace's documented cosine threshold for "same person".
SFACE_SIMILARITY: Final = 0.363
NEIGHBOURS: Final = 30
ROUNDS: Final = 20  # at most; it usually settles in a few
_BLOCK: Final = 256  # rows compared at once: 256 x faces float32 in memory
_SEED: Final = 0


@dataclass(frozen=True, slots=True)
class Linkage:
    """How close two faces must be to be linked, and to how many neighbours."""

    similarity: float = SFACE_SIMILARITY
    neighbours: int = NEIGHBOURS


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
    labels = _whispers(_graph(vectors, linkage))
    members: dict[int, list[int]] = {}
    for index, label in enumerate(labels.tolist()):
        members.setdefault(label, []).append(index)
    ordered = sorted(members.values(), key=lambda group: (-len(group), group[0]))
    return tuple(tuple(group) for group in ordered)


def _graph(vectors: NDArray[np.float32], linkage: Linkage) -> _Graph:
    """Link each face to its close neighbours, in both directions.

    Args:
        vectors: The unit vectors.
        linkage: The threshold and the number of neighbours.

    Returns:
        The links, each pair once per direction, grouped by face.
    """
    count = len(vectors)
    links = _neighbours(vectors, linkage)
    both = np.concatenate((links, links[:, (1, 0, 2)]))
    codes = both[:, 0].astype(np.int64) * count + both[:, 1].astype(np.int64)
    _, first = np.unique(codes, return_index=True)  # sorted by source, then target
    kept = both[first]
    per_face = np.bincount(kept[:, 0].astype(np.int64), minlength=count)
    starts = np.concatenate(([0], np.cumsum(per_face))).astype(np.int64)
    return _Graph(starts, kept[:, 1].astype(np.int64), kept[:, 2])


def _neighbours(vectors: NDArray[np.float32], linkage: Linkage) -> NDArray[np.float64]:
    """Find each face's close neighbours, block by block.

    Args:
        vectors: The unit vectors.
        linkage: The threshold and the number of neighbours.

    Returns:
        One row per link: face, neighbour, similarity.
    """
    count = len(vectors)
    keep = min(linkage.neighbours, count - 1)
    pairs: list[NDArray[np.float64]] = [np.empty((0, 3))]
    for start in range(0, count if keep > 0 else 0, _BLOCK):
        block = vectors[start : start + _BLOCK] @ vectors.T
        rows = np.arange(len(block))
        block[rows, rows + start] = -np.inf  # a face is not its own neighbour
        nearest = np.argpartition(-block, keep - 1, axis=1)[:, :keep]
        similar = np.take_along_axis(block, nearest, axis=1)
        line, rank = np.nonzero(similar >= linkage.similarity)
        found = (line + start, nearest[line, rank], similar[line, rank])
        pairs.append(np.column_stack(found).astype(np.float64))
    return np.concatenate(pairs)


def _whispers(graph: _Graph) -> NDArray[np.int64]:
    """Spread the groups along the links until they settle.

    Args:
        graph: The links.

    Returns:
        The group of each face (the number of one of its members).
    """
    count = len(graph.starts) - 1
    labels = np.arange(count, dtype=np.int64)
    order = np.random.default_rng(_SEED)
    for _ in range(ROUNDS):
        changed = False
        for node in order.permutation(count).tolist():
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
