"""`search`: a person's chip: its cross takes the name off, *Put back*, *Why*."""

from __future__ import annotations

import json
import tomllib
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.people_files import linked_section
from media_hygiene.review.http import Request
from media_hygiene.services import search_pages as search_service
from tests.integration.people.test_people_names import keys, post, state
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response
    from media_hygiene.search.app import SearchApp

    Page = Callable[[list[object]], tuple[list[Response], SearchApp]]

CHLOE = {"text": "person:chloe"}


def files_of(folder: Path) -> dict[str, bytes]:
    """Every file of the config folder, by name, as bytes."""
    return {
        str(path.relative_to(folder)): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def person(locations: Locations) -> dict[str, list[str]]:
    """Chloé's lists, read back from her file: `faces` and `rejected`."""
    config = locations.config_dir / "config.toml"
    section = linked_section(tomllib.loads(config.read_text())["people"], config.parent)
    people = section["person"]
    assert isinstance(people, list)
    first = people[0]
    assert isinstance(first, dict)
    return {
        key: [str(one) for one in first.get(key, [])] for key in ("faces", "rejected")
    }


def name_half(cli: CliRunner, apps: list[object]) -> None:
    """Chloé confirmed on two faces of her group: the two others are attributed."""
    assert run(cli, "people").exit_code == 0
    group = keys(state(apps[-1])["sections"][0])  # type: ignore[index]
    post(apps[-1], {"action": "name", "name": "Chloé", "faces": group[:2]})
    assert run(cli, "tags", "--no-describe").exit_code == 0


def serve(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch, calls: list[object]
) -> tuple[list[Response], SearchApp]:
    """Open the search page, send the calls (a route and a body, or a request)."""
    answers: list[Response] = []
    served: list[SearchApp] = []

    async def browse(app: SearchApp) -> None:
        served.append(app)
        for call in calls:
            if callable(call):  # a step of the test, inside the page's life
                call(app)
                continue
            if isinstance(call, Request):
                answers.append(await app.handle(call))
                continue
            assert isinstance(call, tuple)
            route: str = call[0]
            body: object = call[1]
            if callable(body):
                body = body(answers)
            answers.append(await _call(app, route, body))

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(browse))
    result = run(cli, "search")
    assert result.exit_code == 0, result.output
    return answers, served[0]


@pytest.fixture
def page(cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch) -> Page:
    """Chloé half named, tags given: a search page to send calls to.

    Args:
        cli: The runner on the coloured pictures.
        apps: The people pages served.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        A function sending calls to a new search page.
    """
    name_half(cli, apps)
    return partial(serve, cli, monkeypatch)


def hits(answer: Response) -> list[dict[str, object]]:
    """The files a search answer lists."""
    found: list[dict[str, object]] = json.loads(answer.body)["hits"]
    return found


def test_a_name_taken_off_is_rejected_read_back_and_put_back_exactly(
    page: Page, locations: Locations
) -> None:
    """Assigned: into `rejected`; the search drops it; *Put back*: the same bytes."""
    confirmed = set(person(locations)["faces"])
    before = files_of(locations.config_dir)

    def assigned(answers: list[Response]) -> dict[str, object]:
        hit = next(
            one
            for one in hits(answers[0])
            if not any(
                key.split("#")[0].endswith(str(one["name"])) for key in confirmed
            )
        )
        return {"key": hit["key"], "name": "Chloé"}

    def back(answers: list[Response]) -> dict[str, object]:
        return {**assigned(answers), "action": "back"}

    answers, _app = page(
        [
            ("POST /api/search", CHLOE),
            ("POST /api/people/reject", assigned),
            ("POST /api/search", CHLOE),
            ("POST /api/people/reject", back),
            ("POST /api/search", CHLOE),
        ],
    )
    assert json.loads(answers[0].body)["total"] == 4
    taken = json.loads(answers[1].body)
    assert taken == {
        "saved": "Saved in config.toml, read back: 1 face of this photo is not Chloé.",
        "names": [],
    }
    assert json.loads(answers[2].body)["total"] == 3
    again = json.loads(answers[3].body)
    assert again["saved"] == (
        "Saved in config.toml, read back: Chloé is on this photo again."
    )
    assert again["names"] == ["Chloé"]
    assert json.loads(answers[4].body)["total"] == 4
    assert files_of(locations.config_dir) == before


def test_a_confirmed_face_leaves_faces_two_faces_both_go(
    page: Page, locations: Locations
) -> None:
    """A confirmed face: out of `faces`, into `rejected`; every face of the photo."""
    confirmed = list(person(locations)["faces"])
    path, _number = confirmed[0].rsplit("#", 1)
    twin = f"{path}#1"  # a second face of the same photo, given the same name

    def first(answers: list[Response]) -> dict[str, object]:
        hit = next(one for one in hits(answers[0]) if path.endswith(str(one["name"])))
        return {"key": hit["key"], "name": "Chloé"}

    def more(app: SearchApp) -> None:
        named = app.place.names.faces().named
        for names in named.values():
            if confirmed[0] in names.get("Chloé", ()):
                names["Chloé"] = (*names["Chloé"], twin)

    answers, _app = page(
        [("POST /api/search", CHLOE), more, ("POST /api/people/reject", first)],
    )
    taken = answers[1]
    assert taken.status is HTTPStatus.OK, taken.body
    chloe = person(locations)
    assert confirmed[0] not in chloe["faces"]
    assert {confirmed[0], twin} <= set(chloe["rejected"])
    assert "2 faces of this photo are not Chloé" in json.loads(taken.body)["saved"]


def test_a_wrong_request_changes_nothing(page: Page, locations: Locations) -> None:
    """Not JSON, a foreign host, an unknown photo, a name not on it: refused."""
    before = files_of(locations.config_dir)
    body = json.dumps({"key": 0, "name": "Chloé"}).encode()
    text = Request(
        "POST",
        "/api/people/reject",
        {"host": "127.0.0.1", "content-type": "text/plain"},
        body,
    )
    foreign = Request(
        "POST",
        "/api/people/reject",
        {"host": "evil.example", "content-type": "application/json"},
        body,
    )
    answers, _app = page(
        [
            text,
            foreign,
            ("POST /api/people/reject", {"key": 99999, "name": "Chloé"}),
            ("POST /api/people/reject", {"key": 1, "name": "Nobody"}),
            ("POST /api/people/reject", {"key": 1, "name": "Chloé", "action": "back"}),
        ],
    )
    statuses = [answer.status for answer in answers]
    assert statuses[0] in {HTTPStatus.UNSUPPORTED_MEDIA_TYPE, HTTPStatus.BAD_REQUEST}
    assert statuses[1] is HTTPStatus.FORBIDDEN
    assert statuses[2] is HTTPStatus.NOT_FOUND
    assert statuses[3:] == [HTTPStatus.UNPROCESSABLE_ENTITY] * 2
    assert files_of(locations.config_dir) == before


def test_why_this_name_then_yes_or_not_for_one_face(
    page: Page, locations: Locations
) -> None:
    """Assigned: its reference and the score; confirmed: no score; Yes / Not saved."""
    confirmed = set(person(locations)["faces"])

    def is_confirmed(hit: dict[str, object]) -> bool:
        return any(key.split("#")[0].endswith(str(hit["name"])) for key in confirmed)

    def ask(*, confirmed_one: bool) -> object:
        def body(answers: list[Response]) -> dict[str, object]:
            found = hits(answers[0])
            hit = next(one for one in found if is_confirmed(one) is confirmed_one)
            return {"key": hit["key"], "name": "Chloé"}

        return body

    def face_of(answers: list[Response]) -> int:
        face: int = json.loads(answers[1].body)["faces"][0]["face"]
        return face

    answers, _app = page(
        [
            ("POST /api/search", CHLOE),
            ("POST /api/people/why", ask(confirmed_one=False)),
            ("POST /api/people/why", ask(confirmed_one=True)),
            ("POST /api/people/why", {"key": 1, "name": "Nobody"}),
            ("GET /api/people/face/99999.jpg", None),
            (
                "POST /api/people/reject",
                lambda answers: {
                    **ask(confirmed_one=False)(answers),  # type: ignore[operator]
                    "action": "confirm",
                    "face": face_of(answers),
                },
            ),
        ],
    )
    assigned = json.loads(answers[1].body)["faces"]
    assert len(assigned) == 1
    assert assigned[0]["how"] == "assigned"
    assert "a name is given from 0.36 ([people] similarity)" in assigned[0]["said"]
    reference = assigned[0]["reference"]
    assert any(key.split("#")[0].endswith(reference["file"]) for key in confirmed)
    assert reference["preview"].startswith("/preview/")
    mine = json.loads(answers[2].body)["faces"][0]
    assert mine["how"] == "confirmed"
    assert "reference" not in mine
    assert answers[3].status is HTTPStatus.UNPROCESSABLE_ENTITY
    assert answers[4].status is HTTPStatus.NOT_FOUND
    yes = json.loads(answers[5].body)
    assert yes["saved"] == "Saved in config.toml, read back: Chloé, 3 confirmed faces."
    assert len(person(locations)["faces"]) == 3


def test_a_face_is_cut_out_for_the_panel(page: Page) -> None:
    """`/api/people/face/<n>.jpg`: a JPEG of the face, from the worker pool."""
    answers, _app = page(
        [
            ("POST /api/search", CHLOE),
            (
                "POST /api/people/why",
                lambda answers: {"key": hits(answers[0])[0]["key"], "name": "Chloé"},
            ),
            (
                "GET /api/people/face/0.jpg",
                None,
            ),
        ],
    )
    crop = json.loads(answers[1].body)["faces"][0]["crop"]
    assert crop.startswith("/api/people/face/")
    assert answers[2].status is HTTPStatus.OK
    assert answers[2].body[:2] == b"\xff\xd8"
