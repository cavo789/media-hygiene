"""The neighbour search gives the links of the brute force it replaced (0693)."""

from __future__ import annotations

import numpy as np
import pytest

from media_hygiene.faces import cluster
from media_hygiene.faces import neighbours as neighbours_module
from media_hygiene.faces.neighbours import Linkage, neighbours


def _brute_force(
    vectors: np.ndarray, linkage: Linkage, wanted: np.ndarray
) -> np.ndarray:
    """Sort every row (closest, then first column), keep those above the threshold.

    The search before 0693 partitioned every row (`argpartition`): the same links but
    for exact ties at the last place, which it broke arbitrarily.
    """
    keep = min(linkage.neighbours, len(vectors) - 1)
    pairs = [np.empty((0, 3))]
    for start in range(0, len(wanted) if keep > 0 else 0, 256):
        faces = wanted[start : start + 256]
        block = vectors[faces] @ vectors.T
        block[np.arange(len(faces)), faces] = -np.inf
        columns = np.broadcast_to(np.arange(len(vectors)), block.shape)
        nearest = np.lexsort((columns, -block), axis=1)[:, :keep]
        similar = np.take_along_axis(block, nearest, axis=1)
        line, rank = np.nonzero(similar >= linkage.similarity)
        found = (faces[line], nearest[line, rank], similar[line, rank])
        pairs.append(np.column_stack(found).astype(np.float64))
    return np.concatenate(pairs)


def _crowd(seed: int) -> np.ndarray:
    """People of every size (some above 30 faces), exact copies (ties), strays."""
    random = np.random.default_rng(seed)
    rows = []
    for size in random.integers(1, 120, size=25):
        centre = random.normal(size=128)
        rows.append(
            centre + random.normal(scale=random.uniform(0.3, 0.9), size=(size, 128))
        )
    vectors = np.concatenate(rows)
    vectors = np.concatenate((vectors, vectors[:40], random.normal(size=(60, 128))))
    return (vectors / np.linalg.norm(vectors, axis=1, keepdims=True)).astype(np.float32)


def _sorted(links: np.ndarray) -> np.ndarray:
    return links[np.lexsort((links[:, 1], links[:, 0]))]


@pytest.mark.parametrize("case", [(0, 1), (0, 5), (0, 30), (1, 1), (1, 30)])
@pytest.mark.parametrize("sample", [64, 100_000])
def test_same_links_and_groups_as_the_brute_force(
    case: tuple[int, int], sample: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same links (ties at the k-th place included), hence the same groups.

    `case`: the seed and the neighbours wanted; `sample` 64: the floor from the
    first columns is used; 100,000: never.
    """
    seed, wanted = case
    monkeypatch.setattr(neighbours_module, "_SAMPLE", sample)
    vectors = _crowd(seed)
    linkage = Linkage(neighbours=wanted)
    every = np.arange(len(vectors), dtype=np.int64)
    fast = neighbours(vectors, linkage, every)
    np.testing.assert_array_equal(
        _sorted(fast), _sorted(_brute_force(vectors, linkage, every))
    )
    groups = cluster.group_faces(vectors, linkage)
    monkeypatch.setattr(cluster, "neighbours", _brute_force)
    assert cluster.group_faces(vectors, linkage) == groups


def test_only_some_faces_and_tiny_sets() -> None:
    """The new faces alone, one face, two faces: like the brute force."""
    vectors = _crowd(5)
    linkage = Linkage()
    some = np.arange(3, len(vectors), 7, dtype=np.int64)
    np.testing.assert_array_equal(
        _sorted(neighbours(vectors, linkage, some)),
        _sorted(_brute_force(vectors, linkage, some)),
    )
    for count in (1, 2):
        few = vectors[:count]
        rows = np.arange(count, dtype=np.int64)
        np.testing.assert_array_equal(
            neighbours(few, linkage, rows), _brute_force(few, linkage, rows)
        )
