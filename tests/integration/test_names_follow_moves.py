"""Names confirmed in `people` follow the photos `sort` and `undo` move (TODO 0146)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.faces.models import FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.index.moves import load_moves
from media_hygiene.index.repository import FactsRepository
from media_hygiene.people.board import PeopleBoard
from media_hygiene.people.changes import Naming
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.known import Known
from media_hygiene.people.naming import face_id
from media_hygiene.people.roster import Change, NamesFile, Roster
from media_hygiene.services.people_groups import PeopleGroups

if TYPE_CHECKING:
    import sqlite3

OLD: Final = Path("/data/c/Photos/2019/IMG_0001.jpg")
NEW: Final = Path("/data/c/Photos/Tri/2019/Noel/IMG_0001.jpg")
LATER: Final = Path("/data/c/Photos/Tri/2019/Noël/IMG_0001.jpg")
CHLOE: Final = PeopleSettings(person=(Person(name="Chloé", faces=(face_id(OLD, 0),)),))


def stored(path: Path, number: int = 0) -> StoredFace:
    """A face with a unit vector, as the index gives it back."""
    vector = np.ones(128, dtype=np.float32)
    vector /= np.linalg.norm(vector)
    return StoredFace(path, number, FaceBox(0, 0, 10, 10), 0.9, 50.0, vector.tobytes())


def people_at(path: Path, connection: sqlite3.Connection) -> tuple[str, ...]:
    """Who is named, the face stored at `path`, with the moves of the index."""
    return Known.of([stored(path)], CHLOE, load_moves(connection)).people


def test_a_name_follows_one_move_then_two() -> None:
    """`sort` moves the photo: its face is still Chloé's, after a second sort too."""
    with FactsRepository.open(None) as repository:
        assert people_at(OLD, repository.connection) == ("Chloé",)
        assert not Known.of([stored(NEW)], CHLOE).people  # the bug, without moves
        repository.move([(str(OLD), str(NEW))])
        assert people_at(NEW, repository.connection) == ("Chloé",)
        repository.move([(str(NEW), str(LATER))])
        assert people_at(LATER, repository.connection) == ("Chloé",)


def test_sort_then_undo_leaves_no_loop() -> None:
    """Back at its first path, the photo is named, and the moves hold no loop."""
    with FactsRepository.open(None) as repository:
        repository.move([(str(OLD), str(NEW))])
        repository.move([(str(NEW), str(OLD))])
        assert people_at(OLD, repository.connection) == ("Chloé",)
        assert load_moves(repository.connection) == {str(NEW): str(OLD)}


def test_the_next_save_writes_the_new_ids(tmp_path: Path) -> None:
    """Naming someone else on the page rewrites Chloé's face with its new path."""
    config = tmp_path / "config.toml"
    config.write_text("# my settings\n", encoding="utf-8")
    save_people(config, CHLOE)
    other = stored(NEW, 1)
    board = PeopleBoard.of(
        PeopleGroups(((stored(NEW), other),), too_small=0, too_blurry=0)
    )
    names = NamesFile(config, read_people(config), {str(OLD): str(NEW)})
    roster = Roster(board, board.faces, names)
    said = roster.change(Change("name", Naming("Léa", (face_id(NEW, 1),))))
    assert "1 face follows a photo that sort moved" in said
    back = {person.name: person.faces for person in read_people(config).person}
    assert back == {"Chloé": (face_id(NEW, 0),), "Léa": (face_id(NEW, 1),)}
    assert config.read_text(encoding="utf-8").startswith("# my settings")
