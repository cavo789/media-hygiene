"""`/person` (TODO 0351): one photo, its faces, the photos of a face, set aside."""

from __future__ import annotations

import asyncio
import dataclasses
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING

import pytest

from media_hygiene.person.app import PersonApp
from media_hygiene.person.door import with_person
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.apply_api import ApplyOffer, ApplyStep, applying_door
from media_hygiene.review.http import Request, Response
from media_hygiene.services import people_models
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.share.album_route import WithAlbums
from tests.support.cli import run
from tests.support.faces import FakeRecipe, face_of
from tests.support.json_calls import JSON, answer, call
from tests.support.pick_pages import PICK_PARTS
from tests.support.runtime import make_runtime, thread_pool

if TYPE_CHECKING:
    from collections.abc import Iterator

    from PIL import Image
    from typer.testing import CliRunner

    from media_hygiene.faces.models import Face
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.ending import EndingDoor


@dataclass(frozen=True, slots=True)
class TurnedFinder:
    """Sees person 0 on a picture taller than wide only: a photo lying on its side."""

    def find(self, picture: Image.Image) -> tuple[Face, ...]:
        """Find the face of a picture turned upright.

        Args:
            picture: The picture.

        Returns:
            One face when it stands, none otherwise.
        """
        width, height = picture.size
        return (face_of(0, picture.size),) if height > width else ()


@dataclass(frozen=True, slots=True)
class TurnedRecipe:
    """Builds the finder of lying photos."""

    def build(self) -> TurnedFinder:
        """Build it.

        Returns:
            The finder.
        """
        return TurnedFinder()


@dataclass(frozen=True, slots=True)
class Nothing:
    """A page that answers nothing: only its door matters here."""

    async def handle(self, _request: Request) -> Response:
        """Answer every request with 404.

        Returns:
            Not found.
        """
        return Response(HTTPStatus.NOT_FOUND)


@pytest.fixture
def person(
    cli: CliRunner, apps: list[object], doors: list[EndingDoor]
) -> Iterator[PersonApp]:
    """The `/person` of the people page, with a worker pool of its own."""
    assert run(cli, "people").exit_code == 0
    assert apps
    found = _unwrapped(doors[-1].person)
    assert isinstance(found, PersonApp)
    with ThreadPoolExecutor(2) as executor:
        yield dataclasses.replace(found, executor=executor)


def _unwrapped(person: object) -> object:
    """The person page inside its albums route (0657)."""
    return person.app if isinstance(person, WithAlbums) else person


def photo(app: PersonApp, typed: str) -> dict[str, object]:
    """The faces of a photo, by its path."""
    return answer(app, "POST /person/api/photo", {"path": typed})


def names(files: object) -> list[str]:
    """The names of the files of the grid."""
    assert isinstance(files, list)
    return [file["name"] for file in files]


def test_a_typed_path_finds_the_photo_its_face_and_that_persons_photos(
    person: PersonApp,
) -> None:
    r"""`C:\\...` → its one face → the four photos of person 0, that one first."""
    found = photo(person, '"C:\\Holidays\\IMG_2.png"')
    assert (found["photo"], found["scanned"]) == ("C:\\Holidays\\IMG_2.png", True)
    faces = found["faces"]
    assert isinstance(faces, list)
    assert len(faces) == 1
    key = faces[0]["key"]
    assert call(person, f"GET {faces[0]['face']}").status is HTTPStatus.OK
    liked = answer(person, "POST /person/api/like", {"key": key})
    files = liked["files"]
    assert names(files)[0] == "IMG_2.png"
    assert sorted(names(files)) == ["IMG_0.png", "IMG_1.png", "IMG_2.png", "IMG_3.png"]
    assert liked["known"] is None
    assert call(person, f"GET {files[1]['thumb']}").status is HTTPStatus.OK  # type: ignore[index]


@pytest.mark.parametrize(
    "typed", ["C:\\Holidays\\nope.png", "C:\\..\\..\\etc\\passwd", "C:\\Holidays"]
)
def test_a_path_that_is_not_a_photo_here_is_said_in_one_sentence(
    person: PersonApp, typed: str
) -> None:
    """Missing, outside the photo folders, a folder: a sentence, never an error."""
    found = photo(person, typed)
    assert found["faces"] == []
    assert "is not a photo of the folders this page shows" in str(found["said"])


def test_a_second_look_finds_a_face_on_a_photo_lying_on_its_side(
    person: PersonApp, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No face upright; turned by 90°, one: shown with its picture, never stored."""
    lying = locations.data_dir / "c" / "Holidays" / "IMG_0.png"
    found = photo(person, "C:\\Family\\IMG_9.png")  # nobody on it, upright
    assert (found["faces"], found["scanned"]) == ([], True)
    assert lying.is_file()
    monkeypatch.setattr(people_models, "models_present", lambda _runtime: False)
    absent = answer(person, "POST /person/api/look", {"path": "C:\\Family\\IMG_9.png"})
    assert "audit --people" in str(absent["said"])
    monkeypatch.setattr(people_models, "models_present", lambda _runtime: True)
    monkeypatch.setattr(people_models, "face_recipe", lambda _runtime: TurnedRecipe())
    looked = answer(person, "POST /person/api/look", {"path": "C:\\Family\\IMG_9.png"})
    faces = looked["faces"]
    assert isinstance(faces, list)
    assert len(faces) == 1  # found at -90° and 90°: the same face, once
    picture = call(person, f"GET {faces[0]['face']}")
    assert (picture.status, picture.content_type.value) == (HTTPStatus.OK, "image/jpeg")
    liked = answer(person, "POST /person/api/like", {"key": faces[0]["key"]})
    assert names(liked["files"])[0] == "IMG_9.png"
    assert len(names(liked["files"])) == 5  # its photo, then person 0's four


def test_the_photos_set_aside_are_saved_read_back_and_the_person_remembered(
    person: PersonApp, locations: Locations
) -> None:
    """In `chosen`; the face remembered: the same face then names that person."""
    key = photo(person, "C:\\Holidays\\IMG_0.png")["faces"][0]["key"]  # type: ignore[index]
    files = answer(person, "POST /person/api/like", {"key": key})["files"]
    keys = [file["key"] for file in files]  # type: ignore[attr-defined]
    body = {"action": "add", "faces": keys, "label": "Person of IMG_0.png"}
    said = answer(person, "POST /person/api/aside", body)["aside"]
    assert isinstance(said, dict)
    assert (said["count"], said["remembered"]) == (4, 1)
    chosen = read_decisions(locations.reports_dir / "decisions.json").chosen
    assert {PureWindowsPath(file.path).name for file in chosen} == {
        "IMG_0.png",
        "IMG_1.png",
        "IMG_2.png",
        "IMG_3.png",
    }
    again = answer(person, "POST /person/api/like", {"key": key})
    assert all(file["chosen"] for file in again["files"])  # type: ignore[attr-defined]
    known = again["known"]
    assert isinstance(known, dict)
    assert (known["aside"], known["label"]) == (said["person"], "Person of IMG_0.png")
    back = {"action": "remove", "faces": keys}
    assert answer(person, "POST /person/api/aside", back)["aside"]["count"] == 0  # type: ignore[index]
    assert answer(person, "POST /person/api/like", {"key": key})["known"] is None


def test_the_page_answers_on_the_loopback_only_and_from_any_page(
    person: PersonApp, doors: list[EndingDoor]
) -> None:
    """The page, its query; another host refused; the people page's door routes it."""
    for path in ("/person", "/person?path=C%3A%5Cx.jpg"):
        page = call(person, f"GET {path}")
        assert page.status is HTTPStatus.OK
        # The naming combo reaches the page's script, not only the album bar's.
        assert page.body.decode().count("function comboAttach(") == 2
        assert 'id="confirmGuesses"' in page.body.decode()  # one click: the ≈ names
        assert '<option value="todo" selected>' in page.body.decode()
        assert 'data-size="xl"' in page.body.decode()  # tiles big enough for children
        assert "function pathNames(" in page.body.decode()  # 📁 the names of the path
        for part in PICK_PARTS:  # the shared parts of a page of photos to pick
            assert page.body.decode().count(part) == 1, part
    far = Request("GET", "/person", {"host": "example.com"}, b"")
    assert asyncio.run(person.handle(far)).status is HTTPStatus.FORBIDDEN
    assert call(person, "POST /person/api/like", {"key": "x"}).status is (
        HTTPStatus.BAD_REQUEST
    )
    door = doors[-1]
    routed = asyncio.run(door.handle(Request("GET", "/person", JSON, b"")))
    assert b'id="grid"' in routed.body


def test_apply_now_shows_when_the_page_serving_it_was_opened_from_home(
    locations: Locations,
) -> None:
    """The host's step, ended the same way; refused while nothing is set aside."""
    offer = ApplyOffer(lambda: ApplyStep(7, "mh clean"), lambda: True)
    door = with_person(
        applying_door(Nothing(), offer), make_runtime(locations), thread_pool()
    )
    person = _unwrapped(door.person)
    assert isinstance(person, PersonApp)
    assert b'id="applyNow"' in call(person, "GET /person").body
    refused = call(person, "POST /person/api/apply", {})
    assert refused.status is HTTPStatus.CONFLICT  # the host had something, not /person
    assert "Nothing set aside." in refused.body.decode()
    assert door.ending.asked is None
    alone = with_person(
        applying_door(Nothing(), ApplyOffer(None, lambda: True)),
        make_runtime(locations),
        thread_pool(),
    )
    bare = _unwrapped(alone.person)
    assert isinstance(bare, PersonApp)
    assert b'id="applyNow"' not in call(bare, "GET /person").body
    assert call(bare, "POST /person/api/apply", {}).status is HTTPStatus.NOT_FOUND


def test_the_person_page_undoes_the_run_of_its_host(locations: Locations) -> None:
    """A host that stays open: toast and route; no Undo given: neither (0621)."""
    runtime = make_runtime(locations)
    offer = ApplyOffer(
        lambda: ApplyStep(7, "mh clean"), lambda: True, PageUndo(runtime)
    )
    door = with_person(applying_door(Nothing(), offer), runtime, thread_pool())
    person = _unwrapped(door.person)
    assert isinstance(person, PersonApp)
    page = call(person, "GET /person").body
    assert b'id="mhUndoToast"' in page
    assert b'"/person/api/undo-run"' in page
    latest = call(person, "GET /person/api/undo-run")
    assert latest.status is HTTPStatus.OK
    assert b'"run_id"' in latest.body


def test_each_photo_found_opens_the_page_again_on_itself(person: PersonApp) -> None:
    """Its host path rides with it: the 👤 of the card and of the large view."""
    key = photo(person, "C:\\Holidays\\IMG_0.png")["faces"][0]["key"]  # type: ignore[index]
    files = answer(person, "POST /person/api/like", {"key": key})["files"]
    assert isinstance(files, list)
    assert {file["path"] for file in files} == {file["where"] for file in files}
    assert "C:\\Family\\IMG_1.png" in {file["path"] for file in files}
    page = call(person, "GET /person").body.decode()
    assert '"/person?path=" + encodeURIComponent(file.path)' in page


def _named(item: object) -> object:
    """The name tag of a face or a tile."""
    assert isinstance(item, dict)
    return item["named"]


def test_a_face_named_on_person_is_saved_read_back_and_shown_named(
    person: PersonApp, locations: Locations
) -> None:
    """0714: "This is Juliette" → config.toml; the face then says ✓ Juliette."""
    found = photo(person, "C:\\Holidays\\IMG_0.png")
    assert found["writable"] is True
    face = found["faces"][0]  # type: ignore[index]
    assert _named(face) is None
    body = {"action": "name", "name": "Juliette", "faces": [face["key"]]}
    saved = answer(person, "POST /person/api/names", body)
    assert "Juliette, 1 confirmed face" in str(saved["saved"])
    assert saved["people"] == ["Juliette"]
    assert "Juliette" in locations.config_file.read_text(encoding="utf-8") or any(
        (locations.config_file.parent / "people").glob("*.toml")
    )
    again = photo(person, "C:\\Holidays\\IMG_0.png")["faces"][0]  # type: ignore[index]
    assert _named(again) == {"name": "Juliette", "how": "confirmed", "not": []}


def test_confirming_n_tiles_records_exactly_those_and_not_someone_elses(
    person: PersonApp,
) -> None:
    """Two tiles confirmed: 3 faces; "not Ann" then drops a tile."""
    key = photo(person, "C:\\Holidays\\IMG_0.png")["faces"][0]["key"]  # type: ignore[index]
    answer(
        person,
        "POST /person/api/names",
        {"action": "name", "name": "Ann", "faces": [key]},
    )
    files = answer(person, "POST /person/api/like", {"key": key})["files"]
    assert isinstance(files, list)
    two = [file["key"] for file in files[1:3]]
    body = {"action": "name", "name": "Ann", "faces": two}
    assert "Ann, 3 confirmed faces" in str(
        answer(person, "POST /person/api/names", body)["saved"]
    )
    last = files[3]["key"]
    body = {"action": "reject", "name": "Ann", "faces": [last]}
    assert "is not Ann" in str(answer(person, "POST /person/api/names", body)["saved"])
    after = answer(person, "POST /person/api/like", {"key": key})["files"]
    assert isinstance(after, list)
    assert last not in [file["key"] for file in after]
    assert [_named(file)["how"] for file in after] == ["confirmed"] * 3  # type: ignore[index]


def test_a_face_of_a_second_look_or_without_config_cannot_be_named(
    person: PersonApp,
) -> None:
    """An unknown shelf number names no face: said, nothing written."""
    body = {"action": "name", "name": "Ann", "faces": [999]}
    assert "error" in answer(person, "POST /person/api/names", body)
    assert call(person, "POST /person/api/names", {"action": "x"}).status is (
        HTTPStatus.BAD_REQUEST
    )


def test_a_face_said_not_to_be_the_name_leaves_the_likeness_too(
    person: PersonApp,
) -> None:
    """0714 step 6: the cross "not Ann" takes that face out of the mean too."""
    key = photo(person, "C:\\Holidays\\IMG_0.png")["faces"][0]["key"]  # type: ignore[index]
    every = len(person.finder.kept(str(key)))
    answer(
        person,
        "POST /person/api/names",
        {"action": "name", "name": "Ann", "faces": [key]},
    )
    files = answer(person, "POST /person/api/like", {"key": key})["files"]
    assert isinstance(files, list)
    body = {"action": "reject", "name": "Ann", "faces": [files[-1]["key"]]}
    answer(person, "POST /person/api/names", body)
    assert len(person.finder.kept(str(key))) == every - 1


def test_the_large_view_and_the_people_page_lead_to_person(
    person: PersonApp, doors: list[EndingDoor]
) -> None:
    """Who is on the photo (`#viewerWho`, asked when opened), the people page's link."""
    page = call(person, "GET /person").body.decode()
    assert 'id="viewerWho"' in page
    assert "/person/api/photo" in page  # pick_who.js.j2: one request per photo opened
    assert "&face=" in page
    home = asyncio.run(doors[-1].handle(Request("GET", "/", JSON, b"")))
    assert b'id="personPage" href="/person"' in home.body


def test_the_person_verb_refuses_a_path_that_is_not_a_photo(cli: CliRunner) -> None:
    """`mh person` on a path outside the photo folders: said, exit 2, nothing served."""
    result = run(cli, "person", "C:\\nowhere\\x.jpg")
    assert result.exit_code == 2
    assert "is not a photo" in result.output


def test_a_face_drawn_by_hand_is_kept_searched_and_a_blank_box_writes_nothing(
    person: PersonApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0715: the photo to draw on; a box on a face → that person's photos."""
    monkeypatch.setattr(people_models, "models_present", lambda _runtime: True)
    monkeypatch.setattr(people_models, "face_recipe", lambda _runtime: FakeRecipe())
    draw = "POST /person/api/draw"
    picture = answer(person, draw, {"path": "C:\\Family\\IMG_9.png"})["picture"]
    assert call(person, f"GET {picture}").status is HTTPStatus.OK
    shown = int(str(picture).rsplit("/", maxsplit=1)[-1].removesuffix(".jpg"))
    assert answer(person, "POST /person/api/like", {"key": shown})["files"] == []
    blank = {"path": "C:\\Family\\IMG_9.png", "box": [0.1, 0.1, 0.8, 0.8]}
    said = answer(person, draw, blank)
    assert (said["faces"], "Too small or blurred" in str(said["said"])) == ([], True)
    assert photo(person, "C:\\Family\\IMG_9.png")["faces"] == []  # nothing written
    empty = {"path": "C:\\Family\\IMG_9.png", "box": [0.5, 0.5, 0.0, 0.0]}
    assert answer(person, draw, empty)["faces"] == []
    before = len(photo(person, "C:\\Holidays\\IMG_2.png")["faces"])  # type: ignore[arg-type]
    box = {"path": "C:\\Holidays\\IMG_2.png", "box": [0.2, 0.2, 0.6, 0.6]}
    kept = answer(person, draw, box)
    assert kept.get("drawn") is True, kept
    key = kept["faces"][0]["key"]  # type: ignore[index]
    assert len(photo(person, "C:\\Holidays\\IMG_2.png")["faces"]) == before + 1  # type: ignore[arg-type]
    liked = answer(person, "POST /person/api/like", {"key": key})
    assert names(liked["files"])[0] == "IMG_2.png"
    assert sorted(names(liked["files"])) == [
        "IMG_0.png",
        "IMG_1.png",
        "IMG_2.png",
        "IMG_3.png",
    ]
