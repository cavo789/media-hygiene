"""The faces of the people set aside: kept, forgotten, compared (TODO 0328)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from media_hygiene.faces.models import EMBEDDING_SIZE, FaceBox, embedding_bytes
from media_hygiene.index.aside_faces import AsideFaces, remember, remembered
from media_hygiene.index.face_rows import FaceStore, StoredFace
from media_hygiene.index.parked import park, unpark
from media_hygiene.index.repository import FactsRepository
from media_hygiene.people.alike import LOOK_ALIKE, AlikeFinder
from media_hygiene.people.board import PeopleBoard
from media_hygiene.people.remembered import AsideMemory, aside_date, new_aside
from media_hygiene.people.views import PageView
from media_hygiene.services.people_groups import PeopleGroups


def at(cosine: float) -> bytes:
    """A unit vector at this cosine from the first axis."""
    vector = np.zeros(EMBEDDING_SIZE, dtype=np.float32)
    vector[0], vector[1] = cosine, np.sqrt(1 - cosine**2)
    return embedding_bytes(vector)


def stored(path: Path, embedding: bytes, width: float = 100.0) -> StoredFace:
    """A face of the index, on a photo written to the disk."""
    path.write_bytes(b"x")
    return StoredFace(path, 0, FaceBox(0, 0, width, width), 0.95, 1.0, embedding)


def test_faces_are_kept_once_per_person_and_forgotten_by_vector(
    tmp_path: Path,
) -> None:
    """Two people, oldest first; a vector kept once; forgetting is by vector."""
    memory = AsideMemory(tmp_path / "index.sqlite")
    assert memory.remember(AsideFaces("20261022-163817", "Ex", (at(1), at(1)))) == 1
    assert memory.remember(AsideFaces("20261020-100000", "", (at(0.5),))) == 1
    assert [one.aside for one in memory.people()] == [
        "20261020-100000",
        "20261022-163817",
    ]
    memory.forget([at(1)])
    assert [one.aside for one in memory.people()] == ["20261020-100000"]


def test_an_unreadable_index_remembers_nothing(tmp_path: Path) -> None:
    """Not an index: nothing kept, nothing read, the page still works."""
    broken = tmp_path / "index.sqlite"
    broken.write_bytes(b"not a database, at all, " * 100)
    memory = AsideMemory(broken)
    assert memory.remember(AsideFaces("1", "", (at(1),))) == 0
    assert not memory.people()
    memory.forget([at(1)])


def test_forgetting_every_face_forgets_the_people_set_aside(tmp_path: Path) -> None:
    """`people --forget` leaves no face behind, theirs included."""
    with FactsRepository.open(tmp_path / "index.sqlite") as index:
        remember(index.connection, AsideFaces("1", "", (at(1),)))
        FaceStore(index.connection, "model").forget()
        assert not remembered(index.connection)


def test_undo_forgets_the_faces_of_a_photo_it_brings_back(tmp_path: Path) -> None:
    """Parked by `clean`, put back by `undo`: its vector is no one's set aside."""
    original, quarantined = str(tmp_path / "a.jpg"), str(tmp_path / "q" / "a.jpg")
    with FactsRepository.open(tmp_path / "index.sqlite") as index:
        connection = index.connection
        connection.execute(
            "INSERT INTO faces VALUES (?, 1, 1, 'm', 0, 0, 0, 9, 9, '', 1, 1, ?)",
            (original, at(1)),
        )
        remember(connection, AsideFaces("1", "", (at(1), at(0.2))))
        park(connection, "run", [(original, quarantined)])
        assert len(remembered(connection)[0].embeddings) == 2  # moved: still kept
        assert unpark(connection, [(quarantined, original)]) == 1
        assert remembered(connection)[0].embeddings == (at(0.2),)


def test_faces_close_to_a_person_set_aside_are_shown_the_closest_first(
    tmp_path: Path,
) -> None:
    """Above the threshold, small ones too; not below, set aside or gone."""
    faces = (
        stored(tmp_path / "far.jpg", at(LOOK_ALIKE - 0.05)),
        stored(tmp_path / "close.jpg", at(LOOK_ALIKE + 0.05)),
        stored(tmp_path / "small.jpg", at(LOOK_ALIKE + 0.1), width=8),
        stored(tmp_path / "aside.jpg", at(0.9)),
        StoredFace(tmp_path / "gone.jpg", 0, FaceBox(0, 0, 1, 1), 1, 1, at(0.9)),
    )
    board = PeopleBoard.of(PeopleGroups((), 0, 0), faces)
    memory = AsideMemory(tmp_path / "index.sqlite")
    memory.remember(AsideFaces("20261022-163817", "Ex", (at(1),)))
    view = PageView(str, frozenset({str(tmp_path / "aside.jpg")}))
    found = AlikeFinder(board, memory).view(view)
    assert len(found) == 1
    assert (found[0]["date"], found[0]["label"], found[0]["photos"]) == (
        "2026-10-22",
        "Ex",
        2,
    )
    photos = [Path(face["photo"]).name for face in found[0]["faces"]]  # type: ignore[attr-defined]
    assert photos == ["small.jpg", "close.jpg"]


def test_a_person_set_aside_is_named_by_the_moment() -> None:
    """The id is the local date and time; the page shows its day."""
    aside = new_aside()
    assert len(aside) == len("YYYYMMDD-HHMMSS")
    assert aside_date("20261022-163817") == "2026-10-22"
    assert aside_date("someone") == "someone"
