"""0836: a person's actions menu: set aside their photos, drop the name, album."""

from __future__ import annotations

import asyncio
import json
from collections import Counter
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.file_history import versions_of
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.person_actions import RENAME_PATH
from media_hygiene.people.person_aside import (
    PersonAside,
    PersonAsideAsked,
    PersonPhotos,
)
from media_hygiene.people.sections import Section, Sections
from media_hygiene.people.views import PageView
from media_hygiene.review.http import Request
from media_hygiene.services.people_actions import ALBUMS_PATH, with_actions
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from media_hygiene.people.app import PeopleApp
    from media_hygiene.people.aside import AsideAsked, AsideDesk, FaceNumbers
    from media_hygiene.people.board import PeopleBoard

_TEMPLATES = Path(__file__).parents[2] / "src" / "media_hygiene"
_LOCAL = {"host": "127.0.0.1:8088", "content-type": "application/json"}
EX = Person(name="Ex", faces=("/a.jpg#0", "/b.jpg#0", "/c.jpg#0"))


@dataclass(frozen=True)
class _Face:
    path: Path
    number: int = 0


@dataclass
class _Desk:
    """The people page's desk: records what is set aside."""

    asked: list[AsideAsked] = field(default_factory=list)

    def change(self, _board: FaceNumbers, asked: AsideAsked) -> dict[str, object]:
        """Record, and say."""
        self.asked.append(asked)
        return {"message": f"{len(asked.faces)} set aside"}


def _photos() -> PersonPhotos:
    """Ex on a.jpg and b.jpg alone, on c.jpg with someone (face 3)."""
    faces = tuple(_Face(Path(p)) for p in ("/a.jpg", "/b.jpg", "/c.jpg", "/c.jpg"))
    board = cast("PeopleBoard", type("B", (), {})())
    object.__setattr__(board, "faces", faces)
    object.__setattr__(board, "crowd", Counter(face.path for face in faces))
    sections = Sections((Section((0, 1, 2), "Ex", verified=True), Section((3,))), 0)
    return PersonPhotos(board, sections, PageView(str))


def _aside(tmp_path: Path) -> tuple[PersonAside, _Desk, Path]:
    config = tmp_path / "config.toml"
    config.write_text("# mine\n")
    save_people(config, PeopleSettings(person=(EX,)))
    desk = _Desk()
    adopted: list[PeopleSettings] = []
    aside = PersonAside(cast("AsideDesk", desk), config, adopted.append)
    return aside, desk, config


def test_the_photos_alone_are_offered_the_others_listed(tmp_path: Path) -> None:
    """Seeing first: alone ticked by default, with others listed, untouched."""
    aside, desk, _config = _aside(tmp_path)
    said = aside.answer(PersonAsideAsked(name="ex", check=True), _photos())
    assert said == {
        "alone": [{"face": 0, "where": "/a.jpg"}, {"face": 1, "where": "/b.jpg"}],
        "others": [{"face": 2, "where": "/c.jpg"}],
    }
    assert not desk.asked


def test_only_the_ticked_photos_go_and_the_name_with_them(tmp_path: Path) -> None:
    """An unticked photo stays; a photo with others is never sent; name dropped."""
    aside, desk, config = _aside(tmp_path)
    asked = PersonAsideAsked(name="Ex", keys=(0, 2), drop=True)
    said = aside.answer(asked, _photos())
    assert [a.faces for a in desk.asked] == [(0,)]
    assert said["set"] == [0]
    assert read_people(config).person == ()
    assert "nobody is named Ex" in str(said["saved"])
    file = tmp_path / "people" / "Ex.toml"
    assert not file.exists()
    assert versions_of(file)
    assert versions_of(config)


def test_undo_puts_the_name_its_file_and_its_link_back(tmp_path: Path) -> None:
    """The page's Undo: the .toml and the link of config.toml again, read back."""
    aside, _desk, config = _aside(tmp_path)
    aside.answer(PersonAsideAsked(name="Ex", keys=(0,), drop=True), _photos())
    said = aside.answer(PersonAsideAsked(name="Ex", restore=True), _photos())
    back = read_people(config).person
    assert [(p.name, p.faces, p.file) for p in back] == [
        ("Ex", EX.faces, "people/Ex.toml")
    ]
    assert (tmp_path / "people" / "Ex.toml").is_file()
    assert "Ex is named again" in str(said["saved"])


def test_nothing_ticked_is_refused(tmp_path: Path) -> None:
    """Only a photo where they are alone can be sent."""
    aside, desk, _config = _aside(tmp_path)
    with pytest.raises(ValueError, match="no photo"):
        aside.answer(PersonAsideAsked(name="Ex", keys=(2,)), _photos())
    assert not desk.asked


def test_the_menu_is_the_same_on_people_and_person() -> None:
    """One shared menu, included by both pages, with their paths."""
    people = (_TEMPLATES / "people/templates/people.html.j2").read_text()
    person = (_TEMPLATES / "person/templates/person.html.j2").read_text()
    for page in (people, person):
        assert '{% include "person_menu.html.j2" %}' in page
    menu = (_TEMPLATES / "review/templates/person_menu.html.j2").read_text()
    for action in ('"rename"', '"aside"', '"albums"'):
        assert action in menu
    assert (
        "mhPersonMenu.menu"
        in (_TEMPLATES / "people/templates/people_guide.js.j2").read_text()
    )
    assert (
        "mhPersonMenu.menu"
        in (_TEMPLATES / "person/templates/person_names.js.j2").read_text()
    )


def test_the_album_in_memory_holds_every_photo_of_the_person(tmp_path: Path) -> None:
    """The board's face numbers name their photos: the album has each, read back."""
    runtime = make_runtime(make_locations(tmp_path))
    folder = tmp_path / "photos"
    indexed_photos(runtime.locations.index_file, folder, 2)
    photos = sorted(folder.iterdir())
    board = cast("PeopleBoard", type("B", (), {})())
    object.__setattr__(board, "faces", tuple(_Face(p) for p in photos))
    faces = tuple(_Face(p) for p in photos)
    object.__setattr__(board, "face", lambda key: faces[int(key)])
    roster = type("R", (), {"board": board, "adopt": lambda _self, _back: None})()
    app = cast("PeopleApp", type("A", (), {"roster": roster})())
    door = with_actions(app, runtime, (None, cast("AsideDesk", _Desk())))
    body = json.dumps({"action": "add", "album": "Ex", "keys": ["0", "1"]}).encode()
    answer = asyncio.run(door.handle(Request("POST", ALBUMS_PATH, _LOCAL, body)))
    assert answer.status is HTTPStatus.OK
    assert "Ex" in json.loads(answer.body)["message"]
    saved = (runtime.locations.reports_dir / "albums.json").read_text()
    assert all(photo.name in saved for photo in photos)


def test_rename_answers_the_loopback_only(tmp_path: Path) -> None:
    """Another host: 403; GET: 405; a rename without config.toml: refused."""
    runtime = make_runtime(make_locations(tmp_path))
    roster = type("R", (), {"board": type("B", (), {"faces": ()})(), "adopt": None})()
    app = cast("PeopleApp", type("A", (), {"roster": roster})())
    door = with_actions(app, runtime, (None, cast("AsideDesk", _Desk())))
    far = {**_LOCAL, "host": "evil.example"}
    body = json.dumps({"name": "Ex", "to": "Y"}).encode()
    assert (
        asyncio.run(door.handle(Request("POST", RENAME_PATH, far, body))).status
        is HTTPStatus.FORBIDDEN
    )
    assert (
        asyncio.run(door.handle(Request("GET", RENAME_PATH, _LOCAL))).status
        is HTTPStatus.METHOD_NOT_ALLOWED
    )
    refused = asyncio.run(door.handle(Request("POST", RENAME_PATH, _LOCAL, body)))
    assert refused.status is HTTPStatus.UNPROCESSABLE_ENTITY
