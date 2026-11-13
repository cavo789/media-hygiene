"""The names of `/person` kept in memory (0805): every change seen, no growth."""

from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import numpy as np

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.faces.models import EMBEDDING_SIZE
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.naming import id_of
from media_hygiene.person.likeness import FaceRows, kept_rows, likeness, stacked
from media_hygiene.person.names import FaceNames

if TYPE_CHECKING:
    from media_hygiene.person.lookup import FaceIndex
    from media_hygiene.person.shelf import FaceShelf

_PEOPLE = 9
_GROWTH = 10  # 80 times the names, at most this many times the time


class _Faces:
    """A `FaceIndex` of synthetic faces: `every`, `vectors`, `refresh`."""

    def __init__(self, total: int) -> None:
        """Draw the faces.

        Args:
            total: How many.
        """
        rng = np.random.default_rng(1)
        vectors = rng.standard_normal((total, EMBEDDING_SIZE)).astype(np.float32)
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
        self.every = tuple(
            StoredFace(
                Path(f"/data/c/p/{n // 2}.jpg"),
                n % 2,
                cast("object", None),  # type: ignore[arg-type]
                0.9,
                100.0,
                vectors[n].tobytes(),
            )
            for n in range(total)
        )
        self.vectors = stacked(self.every)

    def refresh(self) -> None:
        """A face drawn by hand (0715): the faces read again."""
        self.every = tuple(self.every)[:-1]
        self.vectors = stacked(self.every)

    def of(self, path: Path) -> tuple[StoredFace, ...]:
        """No photo's faces: the desk's numbers are not used here.

        Args:
            path: The photo.

        Returns:
            None of them.
        """
        del path
        return ()


def _desk(tmp_path: Path, total: int, named: int) -> tuple[FaceNames, _Faces]:
    """A desk over `config.toml` naming the first faces.

    Args:
        tmp_path: The test's folder.
        total: The faces of the index.
        named: How many of them are named.

    Returns:
        The desk and its faces.
    """
    faces = _Faces(total)
    ids = [id_of(face) for face in faces.every[:named]]
    config = tmp_path / "config.toml"
    config.write_text("", encoding="utf-8")
    people = tuple(
        Person(name=f"p{n}", faces=tuple(ids[n::_PEOPLE])) for n in range(_PEOPLE)
    )
    save_people(config, PeopleSettings(person=people))
    shelf = SimpleNamespace(face=lambda _key: None)
    desk = FaceNames(
        config, PeopleSettings(), cast("FaceIndex", faces), cast("FaceShelf", shelf)
    )
    return desk, faces


def _rename(desk: FaceNames, name: str) -> None:
    """The first person renamed in their file, as a name given on the page.

    Args:
        desk: The desk.
        name: The new name.
    """
    assert desk.config_file is not None
    now = read_people(desk.config_file)
    first = now.person[0].model_copy(update={"name": name})
    save_people(desk.config_file, now.model_copy(update={"person": (first,)}))


def test_known_built_once_while_nothing_changes(tmp_path: Path) -> None:
    """Two large views: one build."""
    desk, _ = _desk(tmp_path, 40, 20)
    assert desk.known() is desk.known()
    assert desk.kept.builds == 1


def test_a_name_given_or_a_file_edited_is_seen(tmp_path: Path) -> None:
    """A name given, a face rejected, `--forget`, a hand edit: `config` changes."""
    desk, _ = _desk(tmp_path, 40, 20)
    before = desk.known()
    _rename(desk, "Juliette")
    assert "Juliette" in desk.known().people
    assert desk.known() is not before


def test_a_rejection_is_seen(tmp_path: Path) -> None:
    """A face said not to be someone joins `rejected`."""
    desk, faces = _desk(tmp_path, 40, 20)
    assert not desk.known().rejected
    assert desk.config_file is not None
    now = read_people(desk.config_file)
    wanted = id_of(faces.every[30])
    first = now.person[0].model_copy(update={"rejected": (wanted,)})
    people = (first, *now.person[1:])
    save_people(desk.config_file, now.model_copy(update={"person": people}))
    assert desk.known().rejected[wanted] == frozenset({"p0"})


def test_a_face_drawn_or_a_photo_moved_is_seen(tmp_path: Path) -> None:
    """`refresh()` (a face drawn, the faces read again after `sort`): built again."""
    desk, faces = _desk(tmp_path, 40, 40)
    before = len(desk.known().ids)
    faces.refresh()
    assert len(desk.known().ids) == before - 1
    assert desk.kept.builds == 2


def test_likeness_uses_the_rows_of_the_faces_kept(tmp_path: Path) -> None:
    """A face left out of the mean has its row left out of the matrix too."""
    _, faces = _desk(tmp_path, 10, 0)
    every = FaceRows(faces.every, faces.vectors)
    some = faces.every[2:5]
    rows = kept_rows(every, some)
    assert np.array_equal(rows.vectors, faces.vectors[2:5])
    assert kept_rows(every, faces.every).vectors is faces.vectors
    seed = faces.every[3].embedding
    assert likeness(seed, rows, ()).faces[0] == faces.every[3]


def _tags_time(desk: FaceNames) -> float:
    """The best of a few large views' names, after the first.

    Args:
        desk: The desk.

    Returns:
        Seconds.
    """
    desk.tags([1])
    times = []
    for _ in range(5):
        start = time.perf_counter()
        desk.tags([1])
        times.append(time.perf_counter() - start)
    return min(times)


def test_a_large_view_does_not_grow_with_the_names(tmp_path: Path) -> None:
    """Sorting never punished: 1,000 or 80,000 named faces, the same order of time."""
    few, _ = _desk(_folder(tmp_path / "few"), 1_250, 1_000)
    many, _ = _desk(_folder(tmp_path / "many"), 100_000, 80_000)
    assert _tags_time(many) < max(_tags_time(few) * _GROWTH, 0.005)


def _folder(path: Path) -> Path:
    """A new folder.

    Args:
        path: Where.

    Returns:
        It.
    """
    path.mkdir()
    return path
