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
from tests.support.cli import run
from tests.support.faces import face_of
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
    found = doors[-1].person
    assert isinstance(found, PersonApp)
    with ThreadPoolExecutor(2) as executor:
        yield dataclasses.replace(found, executor=executor)


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
    person = door.person
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
    assert isinstance(alone.person, PersonApp)
    assert b'id="applyNow"' not in call(alone.person, "GET /person").body
    assert (
        call(alone.person, "POST /person/api/apply", {}).status is HTTPStatus.NOT_FOUND
    )


def test_each_photo_found_opens_the_page_again_on_itself(person: PersonApp) -> None:
    """Its host path rides with it: the 👤 of the card and of the large view."""
    key = photo(person, "C:\\Holidays\\IMG_0.png")["faces"][0]["key"]  # type: ignore[index]
    files = answer(person, "POST /person/api/like", {"key": key})["files"]
    assert isinstance(files, list)
    assert {file["path"] for file in files} == {file["where"] for file in files}
    assert "C:\\Family\\IMG_1.png" in {file["path"] for file in files}
    page = call(person, "GET /person").body.decode()
    assert '"/person?path=" + encodeURIComponent(file.path)' in page
