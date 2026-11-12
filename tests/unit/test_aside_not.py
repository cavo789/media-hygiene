"""The faces said not to be a person set aside: kept, taken back, forgotten (0713)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import MediaHygieneError
from media_hygiene.index.aside_faces import AsideFaces
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.people.alike import LOOK_ALIKE, AlikeFinder
from media_hygiene.people.aside import AsideAsked, AsideDesk
from media_hygiene.people.board import PeopleBoard
from media_hygiene.people.remembered import AsideMemory
from media_hygiene.people.views import PageView
from media_hygiene.services.people_groups import PeopleGroups
from tests.unit.test_aside_faces import at, stored

if TYPE_CHECKING:
    from pathlib import Path

EX, OTHER = "20261022-163817", "20261023-100000"


def _setup(tmp_path: Path) -> tuple[PeopleBoard, AsideMemory]:
    faces = (
        stored(tmp_path / "daughter.jpg", at(LOOK_ALIKE + 0.05)),
        stored(tmp_path / "ex.jpg", at(LOOK_ALIKE + 0.1)),
    )
    memory = AsideMemory(tmp_path / "index.sqlite")
    memory.remember(AsideFaces(EX, "Ex", (at(1),)))
    return PeopleBoard.of(PeopleGroups((), 0, 0), faces), memory


def _shown(board: PeopleBoard, memory: AsideMemory) -> dict[str, list[str]]:
    found = AlikeFinder(board, memory).view(PageView(str, frozenset()))
    return {
        str(one["aside"]): [str(face["photo"]) for face in one["faces"]]  # type: ignore[attr-defined]
        for one in found
    }


def test_a_face_said_not_them_stays_out_after_a_reload(tmp_path: Path) -> None:
    """Saved in the index, read back by a new finder; ↺ brings it back."""
    board, memory = _setup(tmp_path)
    assert memory.not_them(EX, (at(LOOK_ALIKE + 0.05),), back=False) == 1
    reread = AsideMemory(tmp_path / "index.sqlite")
    assert _shown(board, reread) == {EX: [str(tmp_path / "ex.jpg")]}
    found = AlikeFinder(board, reread).view(PageView(str, frozenset()))
    assert found[0]["photos"] == 1
    assert len(found[0]["ignored"]) == 1  # type: ignore[arg-type]
    assert reread.not_them(EX, (at(LOOK_ALIKE + 0.05),), back=True) == 0
    assert len(_shown(board, reread)[EX]) == 2


def test_an_ignored_face_still_shows_for_another_person(tmp_path: Path) -> None:
    """Not the ex, maybe someone else set aside."""
    board, memory = _setup(tmp_path)
    memory.remember(AsideFaces(OTHER, "", (at(1),)))
    memory.not_them(EX, (at(LOOK_ALIKE + 0.05), at(LOOK_ALIKE + 0.1)), back=False)
    shown = _shown(board, memory)
    assert shown[EX] == []
    assert len(shown[OTHER]) == 2


def test_taking_the_person_back_forgets_their_ignores(tmp_path: Path) -> None:
    """Every face of theirs forgotten: what was said not them goes too."""
    _, memory = _setup(tmp_path)
    memory.not_them(EX, (at(0.5),), back=False)
    memory.forget([at(1)])
    assert memory.ignored() == {}


def test_forgetting_every_face_forgets_the_ignores(tmp_path: Path) -> None:
    """`people --forget` leaves no vector behind."""
    _, memory = _setup(tmp_path)
    memory.not_them(EX, (at(0.5),), back=False)
    with FactsRepository.open(tmp_path / "index.sqlite") as index:
        FaceStore(index.connection, "model").forget()
    assert memory.ignored() == {}


def test_an_unreadable_index_ignores_nothing(tmp_path: Path) -> None:
    """Not an index: -1 said, nothing read."""
    broken = tmp_path / "index.sqlite"
    broken.write_bytes(b"not a database, at all, " * 100)
    memory = AsideMemory(broken)
    assert memory.not_them(EX, (at(1),), back=False) == -1
    assert memory.ignored() == {}


def test_the_desk_keeps_not_them_without_touching_the_decisions(tmp_path: Path) -> None:
    """`not` needs no reports folder; no cache or no person is refused."""
    board, memory = _setup(tmp_path)
    desk = AsideDesk(store=None, ready=lambda: None, memory=memory)  # type: ignore[arg-type]
    said = desk.change(board, AsideAsked(action="not", faces=(0, 1), into=EX))
    assert said["ignored"] == 2
    assert "2" in str(said["message"])
    for refused in (
        AsideDesk(store=None, ready=lambda: None),  # type: ignore[arg-type]
        desk,
    ):
        asked = AsideAsked(action="not", faces=(0,), into="" if refused is desk else EX)
        with pytest.raises(MediaHygieneError):
            refused.change(board, asked)
