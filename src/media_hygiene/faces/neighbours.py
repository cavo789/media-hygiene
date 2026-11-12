"""Find each face's closest neighbours above a similarity threshold, block by block.

Each block of faces is compared with every face (one matrix product); only the
faces above the threshold are kept, then sorted to keep the closest of each (ties:
the first row). Partitioning every whole row was the costliest step (0693).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.faces.similarity import SFACE_SIMILARITY

if TYPE_CHECKING:
    from numpy.typing import NDArray

NEIGHBOURS: Final = 30
_BLOCK: Final = 256  # rows compared at once: 256 x faces float32 in memory
_SAMPLE: Final = 8_192  # columns whose k-th closest bounds a row's (0693)


@dataclass(frozen=True, slots=True)
class Linkage:
    """How close two faces must be to be linked, and to how many neighbours."""

    similarity: float = SFACE_SIMILARITY
    neighbours: int = NEIGHBOURS


def neighbours(
    vectors: NDArray[np.float32], linkage: Linkage, wanted: NDArray[np.int64]
) -> NDArray[np.float64]:
    """Find the close neighbours of some faces, block by block.

    Args:
        vectors: The unit vectors.
        linkage: The threshold and the number of neighbours.
        wanted: The faces whose neighbours are looked for.

    Returns:
        One row per link: face, neighbour, similarity.
    """
    keep = min(linkage.neighbours, len(vectors) - 1)
    pairs: list[NDArray[np.float64]] = [np.empty((0, 3))]
    across = np.ascontiguousarray(vectors.T, dtype=np.float32)
    product = np.empty((min(_BLOCK, len(wanted)), len(vectors)), np.float32)
    close = np.empty(product.shape, np.bool_)  # both reused: a third faster (0693)
    for start in range(0, len(wanted) if keep > 0 else 0, _BLOCK):
        faces = wanted[start : start + _BLOCK]
        block = np.matmul(vectors[faces], across, out=product[: len(faces)])
        block[np.arange(len(faces)), faces] = -np.inf  # not its own neighbour
        np.greater_equal(
            block, _floor(block, linkage, keep)[:, None], out=close[: len(faces)]
        )
        # flat then divmod: several times faster than a 2-D nonzero (measured, 0693)
        line, column = np.divmod(np.flatnonzero(close[: len(faces)]), len(vectors))
        similar = block[line, column]
        near = _closest(line, similar, keep)
        pairs.append(_links(faces[line[near]], column[near], similar[near]))
    return np.concatenate(pairs)


def _floor(
    block: NDArray[np.float32], linkage: Linkage, keep: int
) -> NDArray[np.float32]:
    """Tell, per row, a similarity every one of its `keep` closest faces reaches.

    The k-th closest among the first columns is never above the k-th closest of
    the whole row: someone met in thousands of photos then leaves a few hundred
    candidates instead of thousands, and nothing kept is lost.

    Args:
        block: The similarities of a block of faces with every face.
        linkage: The threshold and the number of neighbours.
        keep: How many to keep per row at most.

    Returns:
        One value per row, never below the threshold.
    """
    floor = np.full(len(block), linkage.similarity, np.float32)
    if block.shape[1] <= _SAMPLE:
        return floor
    kth = np.partition(block[:, :_SAMPLE], -keep, axis=1)[:, -keep]
    return np.maximum(kth, floor)


def _closest(
    line: NDArray[np.int64], similar: NDArray[np.float32], keep: int
) -> NDArray[np.bool_]:
    """Tell which close faces are among the `keep` closest of their row.

    Args:
        line: The row of each close face, ascending (then by column).
        similar: Its similarity.
        keep: How many to keep per row at most.

    Returns:
        True for the kept ones; ties at the last place: the first columns.
    """
    if len(line) == 0:
        return np.zeros(0, dtype=np.bool_)
    counts = np.bincount(line)
    first = (np.cumsum(counts) - counts)[line]  # where each row starts
    rank = np.arange(len(line)) - first
    padded = np.full((int(line[-1]) + 1, int(rank.max()) + 1), -np.inf, np.float32)
    padded[line, rank] = similar
    if padded.shape[1] <= keep:
        return np.ones(len(line), dtype=np.bool_)
    last = -np.partition(-padded, keep - 1, axis=1)[:, keep - 1]  # k-th closest
    near = np.flatnonzero(similar >= last[line])  # a few per row: ties are left
    line, similar = line[near], similar[near]
    tied = similar == last[line]
    room = keep - np.bincount(line[~tied], minlength=len(last))  # per row, for ties
    ties_before = np.cumsum(tied) - tied
    counts = np.bincount(line, minlength=len(last))
    tie_rank = ties_before - ties_before[(np.cumsum(counts) - counts)[line]]
    kept = np.zeros(len(rank), dtype=np.bool_)
    kept[near[~tied | (tie_rank < room[line])]] = True
    return kept


def _links(
    faces: NDArray[np.int64], others: NDArray[np.int64], similar: NDArray[np.float32]
) -> NDArray[np.float64]:
    """Stack links as rows of face, neighbour, similarity."""
    return np.column_stack((faces, others, similar)).astype(np.float64)
