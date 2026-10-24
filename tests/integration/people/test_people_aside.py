"""The people page: every face of a group, its photos set aside, moved by `clean`."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING

from media_hygiene.people.app import PeopleApp
from media_hygiene.report.decisions import read_decisions
from tests.support.cli import run
from tests.support.faces import coloured
from tests.support.json_calls import answer, call

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def largest(app: object) -> dict[str, object]:
    """The first group of the page."""
    sections = answer(app, "GET /api/groups")["sections"]
    assert isinstance(sections, list)
    first = sections[0]
    assert isinstance(first, dict)
    return first


def every_face(app: object, section: dict[str, object]) -> list[int]:
    """The numbers of every face of a group, as the page asks for them."""
    shown = section["shown"]
    assert isinstance(shown, list)
    faces = answer(app, f"GET /api/section/{shown[0]['key']}")["faces"]
    assert isinstance(faces, list)
    return [face["key"] for face in faces]


def test_every_face_of_a_group_beyond_its_sample(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page shows a sample; the group's route lists every face of it."""
    monkeypatch.setattr("media_hygiene.people.views.SHOWN", 2)
    assert run(cli, "people").exit_code == 0
    section = largest(apps[-1])
    assert section["faces"] == 4
    assert len(section["shown"]) == 2  # type: ignore[arg-type]
    assert len(every_face(apps[-1], section)) == 4
    for unknown in ("99", "x"):
        assert answer(apps[-1], f"GET /api/section/{unknown}") == {"faces": []}


def test_the_photos_of_a_group_are_set_aside_read_back_and_taken_back(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Every photo of the faces kept, once each; read back; taken out again."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    section = largest(app)
    assert section["aside"] == 0
    faces = every_face(app, section)
    kept = faces[1:]  # the first one is somebody else's: its cross took it out
    added = answer(
        app, "POST /api/aside", {"action": "add", "faces": kept, "label": "Ex"}
    )
    said = added["aside"]
    assert isinstance(said, dict)
    assert said["count"] == len(kept)
    assert "clean --decisions" in said["message"]
    assert added["chosen"] == len(kept)
    assert largest(app)["aside"] == len(kept)
    chosen = read_decisions(locations.reports_dir / "decisions.json").chosen
    assert len(chosen) == len(kept)
    assert {file.found_by for file in chosen} == {"Ex"}
    back = answer(app, "POST /api/aside", {"action": "remove", "faces": faces})
    assert back["aside"] == {"count": 0, "size": "0", "message": "Nothing set aside."}
    assert largest(app)["aside"] == 0


def test_a_wrong_body_or_no_reports_folder_saves_nothing(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """400 for a body that is not a choice; 409, said, without /reports."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    faces = every_face(app, largest(app))
    for wrong in ({"action": "delete", "faces": faces}, {"action": "add", "faces": []}):
        assert call(app, "POST /api/aside", wrong).status is HTTPStatus.BAD_REQUEST
    monkeypatch.delenv("MEDIA_HYGIENE_REPORTS_DIR")
    assert run(cli, "people").exit_code == 0
    refused = call(apps[-1], "POST /api/aside", {"action": "add", "faces": faces})
    assert refused.status is HTTPStatus.CONFLICT
    assert "/reports" in json.loads(refused.body)["error"]


def test_clean_moves_the_photos_set_aside_and_undo_brings_them_back(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """The command proposes `clean --decisions`; it moves exactly those photos."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    faces = every_face(app, largest(app))
    answer(app, "POST /api/aside", {"action": "add", "faces": faces})
    shown = run(cli, "people")  # a new page: the console proposes the clean
    assert "clean --decisions" in shown.output.split("What next")[-1]
    photos = set(locations.data_dir.rglob("IMG_*.png"))
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    left = set(locations.data_dir.rglob("IMG_*.png"))
    assert isinstance(app, PeopleApp)
    aside = {app.roster.board.faces[key].path for key in faces}
    assert len(aside) == len(faces)
    assert not aside & left  # their duplicates may go too: the same clean
    assert run(cli, "undo").exit_code == 0
    assert set(locations.data_dir.rglob("IMG_*.png")) == photos


def test_photos_set_aside_are_hidden_from_their_section_until_taken_back(
    cli: CliRunner, apps: list[object]
) -> None:
    """Not drawn, not counted, never confirmed; listed apart; back once taken back."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    faces = every_face(app, largest(app))
    aside, kept = faces[:2], faces[2:]
    answer(app, "POST /api/aside", {"action": "add", "faces": aside, "label": "Ex"})
    section = largest(app)
    assert [face["key"] for face in section["shown"]] == kept  # type: ignore[attr-defined]
    assert (section["faces"], section["photos"], section["aside"]) == (2, 2, 2)
    assert [face["key"] for face in section["hidden"]] == aside  # type: ignore[attr-defined]
    assert every_face(app, section) == kept
    named = answer(
        app, "POST /api/people", {"action": "name", "name": "Chloé", "faces": faces}
    )
    assert (
        named["saved"] == "Saved in config.toml, read back: Chloé, 2 confirmed faces."
    )
    answer(app, "POST /api/aside", {"action": "remove", "faces": aside})
    back = largest(app)
    assert (back["faces"], back["aside"], back["hidden"]) == (2, 0, [])
    attributed = answer(app, "GET /api/groups")["sections"][1]  # type: ignore[index]
    assert sorted(face["key"] for face in attributed["shown"]) == aside


def test_a_section_whose_photos_are_all_set_aside_still_offers_them_back(
    cli: CliRunner, apps: list[object]
) -> None:
    """Every face hidden: the section stays, empty, its faces listed to take back."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    faces = every_face(app, largest(app))
    answer(app, "POST /api/aside", {"action": "add", "faces": faces})
    sections = answer(app, "GET /api/groups")["sections"]
    assert isinstance(sections, list)
    empty = next(one for one in sections if one["hidden"])
    assert (empty["faces"], empty["shown"], empty["aside"]) == (0, [], 4)


def alike(app: object) -> list[dict[str, object]]:
    """The look-alike sections of the page (TODO 0328)."""
    found = answer(app, "GET /api/groups")["alike"]
    assert isinstance(found, list)
    return found


def alike_photos(app: object) -> set[str]:
    """The photos of every look-alike section."""
    return {
        str(face["photo"])
        for person in alike(app)
        for face in person["faces"]  # type: ignore[attr-defined]
    }


def new_photo(cli: CliRunner, locations: Locations, person: int) -> str:
    """A photo of someone added later, audited: its name."""
    later = locations.data_dir / "c" / "Later" / f"NEW_{person}.png"
    coloured(later, person, (80, 60))  # not a copy of an older photo
    assert run(cli, "audit").exit_code == 0
    return f"NEW_{person}.png"


def test_a_group_set_aside_is_remembered_and_photos_like_it_are_shown(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Its faces are kept; a new photo of that person shows on top, another not."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    faces = every_face(app, largest(app))
    added = answer(
        app, "POST /api/aside", {"action": "add", "faces": faces, "label": "Ex"}
    )
    # The fake gives one vector per person: kept once, as copies of a photo are.
    assert added["aside"]["remembered"] == 1  # type: ignore[index]
    assert alike(app) == []  # every photo like them is set aside already
    name = new_photo(cli, locations, 0)
    new_photo(cli, locations, 1)
    assert run(cli, "people").exit_code == 0
    shown = alike(apps[-1])
    assert len(shown) == 1
    assert (shown[0]["label"], shown[0]["photos"]) == ("Ex", 1)
    assert [PureWindowsPath(photo).name for photo in alike_photos(apps[-1])] == [name]


def test_faces_set_aside_too_join_the_person_and_taking_back_forgets_them(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """`into` adds to the same person; taken back, the faces are forgotten."""
    assert run(cli, "people").exit_code == 0
    faces = every_face(apps[-1], largest(apps[-1]))
    answer(apps[-1], "POST /api/aside", {"action": "add", "faces": faces})
    new_photo(cli, locations, 0)
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    person = alike(app)[0]
    keys = [face["key"] for face in person["faces"]]  # type: ignore[attr-defined]
    body = {"action": "add", "faces": keys, "into": person["aside"]}
    joined = answer(app, "POST /api/aside", body)
    assert joined["aside"]["remembered"] == 1  # type: ignore[index]
    assert joined["alike"] == []
    every = [*faces, *keys]
    answer(app, "POST /api/aside", {"action": "remove", "faces": every})
    assert alike(app) == []  # nobody remembered any more: nothing looks like them


def test_clean_and_purge_keep_the_faces_of_the_person_set_aside(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """The photos go, then are erased: their faces still find a new photo."""
    assert run(cli, "people").exit_code == 0
    faces = every_face(apps[-1], largest(apps[-1]))
    answer(apps[-1], "POST /api/aside", {"action": "add", "faces": faces})
    cleaned = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert cleaned.exit_code == 0, cleaned.output
    assert run(cli, "purge", "--yes").exit_code == 0
    for size in ((70, 50), (60, 40)):  # a group left for the page to show
        coloured(locations.data_dir / "c" / "Later" / f"P1_{size[0]}.png", 1, size)
    name = new_photo(cli, locations, 0)
    assert run(cli, "people").exit_code == 0
    assert [PureWindowsPath(photo).name for photo in alike_photos(apps[-1])] == [name]


def test_undo_forgets_the_faces_of_the_photos_it_brings_back(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Moved by `clean`, back by `undo`: that person is not remembered any more."""
    assert run(cli, "people").exit_code == 0
    faces = every_face(apps[-1], largest(apps[-1]))
    answer(apps[-1], "POST /api/aside", {"action": "add", "faces": faces})
    assert run(cli, "clean", "--yes", "--decisions", "decisions.json").exit_code == 0
    assert run(cli, "undo").exit_code == 0
    new_photo(cli, locations, 0)
    assert run(cli, "people").exit_code == 0
    assert alike(apps[-1]) == []


def test_one_photo_set_aside_from_the_large_view_leaves_its_section(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """TODO 0329: in `chosen`, hidden from its section, its face not remembered."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    first = every_face(app, largest(app))[0]
    body = {"action": "add", "faces": [first], "remember": False}
    said = answer(app, "POST /api/aside", body)["aside"]
    assert isinstance(said, dict)
    assert said["count"] == 1
    assert "remembered" not in said
    assert len(read_decisions(locations.reports_dir / "decisions.json").chosen) == 1
    section = largest(app)
    assert [face["key"] for face in section["hidden"]] == [first]  # type: ignore[attr-defined]
    assert alike(app) == []
