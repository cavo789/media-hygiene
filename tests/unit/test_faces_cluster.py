"""Grouping the faces alike, on synthetic vectors."""

from __future__ import annotations

import numpy as np

from media_hygiene.faces.cluster import Linkage, group_faces


def people(sizes: tuple[int, ...], spread: float = 0.05) -> np.ndarray:
    """Unit vectors scattered around one random centre per person.

    Args:
        sizes: Faces per person.
        spread: How far a face strays from its person.

    Returns:
        The vectors, person after person.
    """
    random = np.random.default_rng(7)
    rows = []
    for size in sizes:
        centre = random.normal(size=128)
        rows.append(centre + random.normal(scale=spread * 10, size=(size, 128)) * 0.1)
    vectors = np.concatenate(rows)
    return (vectors / np.linalg.norm(vectors, axis=1, keepdims=True)).astype(np.float32)


def test_each_person_is_one_group_largest_first() -> None:
    """Three people, three groups, in decreasing size."""
    groups = group_faces(people((5, 12, 3)), Linkage())
    assert [len(group) for group in groups] == [12, 5, 3]
    assert groups[0] == tuple(range(5, 17))


def test_identical_faces_beyond_the_neighbours_stay_together() -> None:
    """Fifty copies of one face, more than the neighbours kept, make one group."""
    vectors = np.tile(people((1,)), (50, 1))
    assert [len(group) for group in group_faces(vectors, Linkage())] == [50]


def test_a_strict_threshold_leaves_each_face_alone() -> None:
    """Above every similarity, no face is linked."""
    groups = group_faces(people((4,), spread=0.5), Linkage(similarity=0.9999))
    assert groups == ((0,), (1,), (2,), (3,))


def test_no_face_and_one_face() -> None:
    """Nothing gives nothing; one face is its own group."""
    assert not group_faces(np.empty((0, 128), dtype=np.float32), Linkage())
    assert group_faces(people((1,)), Linkage()) == ((0,),)


def test_the_same_faces_give_the_same_groups() -> None:
    """The order is drawn from a fixed seed."""
    vectors = people((8, 8, 8), spread=0.3)
    assert group_faces(vectors, Linkage()) == group_faces(vectors, Linkage())
