"""Grouping the faces alike, on synthetic vectors."""

from __future__ import annotations

import numpy as np

from media_hygiene.faces.cluster import (
    Linkage,
    face_labels,
    group_faces,
    groups_of,
    join_labels,
)


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


def _partition(groups: tuple[tuple[int, ...], ...]) -> set[tuple[int, ...]]:
    """The groups, whatever their order.

    Args:
        groups: The groups.

    Returns:
        The same as a set.
    """
    return set(groups)


def test_the_labels_give_the_same_groups_as_group_faces() -> None:
    """`face_labels` then `groups_of` is `group_faces`."""
    vectors = people((5, 12, 3))
    assert groups_of(face_labels(vectors, Linkage())) == group_faces(vectors, Linkage())


def test_a_new_face_joins_its_person_and_the_others_do_not_move() -> None:
    """One more face of the second person: only that face gets a group."""
    vectors = people((6, 6))
    known = face_labels(vectors[:-1], Linkage())
    labels = join_labels(vectors, np.append(known, -1), Linkage())
    assert (labels[:-1] == known).all()
    assert labels[-1] == labels[6]
    assert _partition(groups_of(labels)) == _partition(group_faces(vectors, Linkage()))


def test_new_faces_of_someone_new_make_a_group_of_their_own() -> None:
    """A person seen for the first time, and nobody merged."""
    vectors = people((6, 4))
    labels = np.full(10, -1, dtype=np.int64)
    labels[:6] = 3
    joined = join_labels(vectors, labels, Linkage())
    assert (joined[:6] == 3).all()
    assert len({int(label) for label in joined[6:]}) == 1
    assert joined[6] != 3


def test_a_new_face_like_nobody_stays_alone() -> None:
    """Above every similarity, the new face links to nothing, and the input is kept."""
    vectors = people((3,), spread=0.5)
    labels = np.array([0, 1, -1], dtype=np.int64)
    joined = join_labels(vectors, labels, Linkage(similarity=0.9999))
    assert joined.tolist()[:2] == [0, 1]
    assert joined[2] not in {0, 1}
    assert labels[2] == -1
