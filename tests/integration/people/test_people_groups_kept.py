"""0588: the groups of faces kept in the index; what invalidates them, what does not."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock

import numpy as np
import pytest

from media_hygiene.config.people_settings import PeopleSettings
from media_hygiene.faces import cluster
from media_hygiene.faces.models import FaceBox, embedding_bytes
from media_hygiene.index.face_rows import FaceStore, StoredFace
from media_hygiene.index.schema import prepare
from media_hygiene.services import people_labels
from media_hygiene.services.people_groups import PeopleGroups, group_people

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

_MODEL = "test"


def _faces(sizes: Sequence[int], seed: int = 0) -> list[StoredFace]:
    """Faces of a few people, each on its own photo.

    Args:
        sizes: How many faces per person.
        seed: Which people.

    Returns:
        The faces, by path.
    """
    rng = np.random.default_rng(seed)
    faces: list[StoredFace] = []
    for person, size in enumerate(sizes):
        centre = rng.normal(size=128)
        centre /= np.linalg.norm(centre)
        for shot in range(size):
            vector = (centre + rng.normal(size=128) * 0.03).astype(np.float32)
            faces.append(
                StoredFace(
                    Path(f"/data/{seed}/{person}/{shot}.jpg"),
                    0,
                    FaceBox(0, 0, 100, 100),
                    0.9,
                    500.0,
                    embedding_bytes(vector),
                )
            )
    return faces


@pytest.fixture(name="index")
def _index() -> Iterator[sqlite3.Connection]:
    """A fresh index in memory.

    Yields:
        The connection.
    """
    with closing(sqlite3.connect(":memory:")) as connection:
        prepare(connection)
        yield connection


def _paths(groups: PeopleGroups) -> list[list[str]]:
    """The groups as paths, comparable across two runs.

    Args:
        groups: The groups.

    Returns:
        The paths, group by group.
    """
    return [[str(face.path) for face in group] for group in groups.groups]


def _no_grouping() -> mock.MagicMock:
    """A `face_labels` that fails the test if it runs.

    Returns:
        The mock to install.
    """
    return mock.MagicMock(side_effect=AssertionError("grouped again"))


def test_kept_groups_equal_a_full_grouping_and_are_not_computed_again(
    index: sqlite3.Connection,
) -> None:
    """Same groups as the plain algorithm, at the first opening and at the next."""
    faces = _faces((9, 4, 1, 6))
    settings = PeopleSettings()
    reference = _paths(group_people(faces, settings))
    assert _paths(group_people(faces, settings, index)) == reference
    with mock.patch.object(people_labels, "face_labels", _no_grouping()):
        assert _paths(group_people(faces, settings, index)) == reference


def test_moved_or_renamed_photos_keep_their_group_without_grouping(
    index: sqlite3.Connection,
) -> None:
    """The digest is of the vector: `sort`, `undo`, or Explorer change nothing."""
    faces = _faces((8, 8))
    settings = PeopleSettings()
    before = group_people(faces, settings, index)
    moved = [
        StoredFace(Path("/moved") / f.path.name, *_rest(f)) for f in reversed(faces)
    ]
    with mock.patch.object(people_labels, "face_labels", _no_grouping()):
        after = group_people(moved, settings, index)
    assert sorted(len(group) for group in after.groups) == sorted(
        len(group) for group in before.groups
    )


def _rest(face: StoredFace) -> tuple[int, FaceBox, float, float, bytes]:
    """A face without its path.

    Args:
        face: The face.

    Returns:
        Its other fields.
    """
    return face.number, face.box, face.score, face.sharpness, face.embedding


def test_a_few_new_faces_join_without_grouping_everything(
    index: sqlite3.Connection,
) -> None:
    """Under a tenth: placed by neighbours, and they stay placed at the next opening."""
    faces = _faces((40, 40))
    settings = PeopleSettings()
    group_people(faces[:-3], settings, index)
    with mock.patch.object(people_labels, "face_labels", _no_grouping()):
        joined = group_people(faces, settings, index)
        again = group_people(faces, settings, index)
    assert sorted(len(group) for group in joined.groups) == [40, 40]
    assert _paths(again) == _paths(joined)


def test_past_a_tenth_of_new_faces_everything_is_grouped_again(
    index: sqlite3.Connection,
) -> None:
    """The joined faces add up, across openings: the groups cannot drift for ever."""
    faces = _faces((50, 50))
    settings = PeopleSettings()
    group_people(faces[:80], settings, index)
    spy = mock.MagicMock(wraps=cluster.face_labels)
    with mock.patch.object(people_labels, "face_labels", spy):
        group_people(faces[:85], settings, index)  # 5 of 80: join
        assert spy.call_count == 0
        group_people(faces[:90], settings, index)  # 10 joined of 85: over a tenth
        assert spy.call_count == 1


@pytest.mark.parametrize(
    "changed", [{"similarity": 0.9}, {"min_face": 60}, {"min_sharpness": 40}]
)
def test_other_settings_group_again(
    index: sqlite3.Connection, changed: dict[str, float]
) -> None:
    """Another threshold finds no group kept."""
    faces = _faces((8, 8))
    group_people(faces, PeopleSettings(), index)
    spy = mock.MagicMock(wraps=cluster.face_labels)
    with mock.patch.object(people_labels, "face_labels", spy):
        group_people(faces, PeopleSettings.model_validate(changed), index)
    assert spy.call_count == 1


def test_a_photo_edited_is_a_new_face(index: sqlite3.Connection) -> None:
    """Its vector changed, under the same path: the digest misses, nothing stale."""
    faces = _faces((3,))
    settings = PeopleSettings()
    group_people(faces, settings, index)
    edited = _faces((1,), seed=7)[0]
    faces[0] = StoredFace(faces[0].path, *_rest(edited))
    sizes = sorted(len(group) for group in group_people(faces, settings, index).groups)
    assert sizes == [1, 2]


def test_forgetting_the_faces_forgets_the_groups(index: sqlite3.Connection) -> None:
    """`--forget` leaves nothing of them."""
    group_people(_faces((3,)), PeopleSettings(), index)
    FaceStore(index, _MODEL).forget()
    assert index.execute("SELECT COUNT(*) FROM face_groups").fetchone() == (0,)


def test_a_read_only_index_still_groups(tmp_path: Path) -> None:
    """The cache not kept costs time only."""
    file = tmp_path / "index.db"
    with closing(sqlite3.connect(file)) as connection:
        prepare(connection)
    with closing(sqlite3.connect(f"file:{file}?mode=ro", uri=True)) as read_only:
        grouped = group_people(_faces((4, 4)), PeopleSettings(), read_only)
    assert sorted(len(group) for group in grouped.groups) == [4, 4]


def test_no_face(index: sqlite3.Connection) -> None:
    """Nothing to group, nothing kept."""
    assert not group_people((), PeopleSettings(), index).groups
