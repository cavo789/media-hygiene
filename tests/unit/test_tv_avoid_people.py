"""0825: the people a phone asks to keep off the TV, for one show."""

from __future__ import annotations

import asyncio
import contextlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np
import pytest

from media_hygiene.faces.models import FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.person.likeness import stacked
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services import slideshow_avoid, slideshow_here
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.slideshow_avoid import Avoided, avoided
from media_hygiene.services.slideshow_here import SlideshowHere
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from media_hygiene.services.runtime import Runtime

_HOST: Final = {"host": "127.0.0.1:8088", "content-type": "application/json"}
_PHOTOS: Final = 4  # IMG_0 named Antoine, IMG_1 looks like him, IMG_2 someone else
_BOX: Final = FaceBox(0, 0, 60, 60)


def _vector(*values: float) -> bytes:
    vector = np.zeros(128, dtype=np.float32)
    vector[: len(values)] = values
    return (vector / np.linalg.norm(vector)).astype("<f4").tobytes()


class _Faces:
    """The faces of the index, without reading one."""

    def __init__(self, every: tuple[StoredFace, ...]) -> None:
        self.every = every
        self.vectors = stacked(every)


def _faces(trip: Path) -> tuple[StoredFace, ...]:
    shapes = ((1.0, 0.0), (0.98, 0.2), (0.0, 1.0))
    return tuple(
        StoredFace(trip / f"IMG_{n}.jpg", 0, _BOX, 0.9, 99.0, _vector(*shape))
        for n, shape in enumerate(shapes)
    )


@pytest.fixture
def runtime(tmp_path: Path) -> Runtime:
    """Antoine named on IMG_0's face; Léa named, her faces not in the index."""
    locations = make_locations(tmp_path)
    trip = locations.data_dir / "c" / "Trip"
    locations.config_file.parent.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text(
        "[[people.person]]\nname = 'Antoine'\n"
        f"faces = ['{trip / 'IMG_0.jpg'}#0']\n"
        "[[people.person]]\nname = 'Léa'\n",
        "utf-8",
    )
    return make_runtime(locations)


@pytest.fixture
def here(
    runtime: Runtime, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[SlideshowHere]:
    """The home slideshow over Trip: four dated camera photos, three with a face."""
    trip = runtime.locations.data_dir / "c" / "Trip"
    index = tmp_path / "index.sqlite"
    indexed_photos(index, trip, _PHOTOS)
    with closing(sqlite3.connect(index)) as connection:
        connection.execute(
            "UPDATE files SET media_date = '2025:11:03 10:00:00', metadata = ?",
            ('{"make": "Canon"}',),
        )
        connection.commit()
    every = _faces(trip)
    monkeypatch.setattr(slideshow_avoid, "FaceIndex", lambda _file: _Faces(every))

    @contextlib.contextmanager
    def opened(_runtime: Runtime, *, words: bool) -> Iterator[SearchIndex]:
        assert not words
        with SearchIndex.open(index) as search:
            yield search

    monkeypatch.setattr(slideshow_here, "open_search", opened)
    with ThreadPoolExecutor(1) as executor:
        built = SlideshowHere(
            FreshRuntime(runtime), HomeServer(None, Ending(), executor)
        )
        yield built
        built.close()


def _ask(here: SlideshowHere, request: Request) -> Response:
    return asyncio.run(here.handle(request))


def _choose(here: SlideshowHere, body: Mapping[str, object]) -> Response:
    payload = json.dumps(body).encode()
    return _ask(here, Request("POST", "/slideshow/choose", _HOST, payload))


def _shown(here: SlideshowHere) -> list[int]:
    answer = _ask(here, Request("GET", "/slideshow/api/slides", _HOST))
    return sorted(slide["key"] for slide in json.loads(answer.body)["slides"])


def test_the_choices_list_the_people_named(here: SlideshowHere) -> None:
    """The phone's block lists every name of `[[people.person]]`."""
    lists = json.loads(_ask(here, Request("GET", "/slideshow/choices", _HOST)).body)
    assert lists["people"] == ["Antoine", "Léa"]


def test_a_random_show_drops_the_named_and_the_look_alike_photos(
    here: SlideshowHere,
) -> None:
    """IMG_0 (named) and IMG_1 (close to his mean) left out; IMG_2, IMG_3 stay."""
    answer = _choose(here, {"random": {"minutes": 30}, "avoid": ["antoine"]})
    assert answer.status is HTTPStatus.OK
    body = json.loads(answer.body)
    assert body["left_out"] == 2  # the stated count is the photos dropped
    assert body["avoided"] == ["Antoine"]
    assert _shown(here) == [3, 4]


@pytest.mark.parametrize(
    "chosen",
    [{"first": "2025-11-01", "last": "2025-11-30"}, {"folder": "C:\\Trip"}],
)
def test_a_folder_or_a_month_drops_them_the_same_way(
    here: SlideshowHere, chosen: dict[str, str]
) -> None:
    """A month or a folder: the same two photos left out, the count stated."""
    if "folder" in chosen:
        lists = json.loads(_ask(here, Request("GET", "/slideshow/choices", _HOST)).body)
        chosen = {"folder": lists["folders"][0]["value"]}
    answer = _choose(here, {**chosen, "avoid": ["Antoine"]})
    assert answer.status is HTTPStatus.OK
    assert json.loads(answer.body)["left_out"] == 2
    assert _shown(here) == [3, 4]


def test_an_unknown_name_is_ignored_and_nothing_is_said(here: SlideshowHere) -> None:
    """Nobody is named Zoé: every photo shown, no count in the answer."""
    answer = _choose(
        here, {"first": "2025-11-01", "last": "2025-11-30", "avoid": ["Zoé"]}
    )
    assert answer.status is HTTPStatus.OK
    assert "left_out" not in json.loads(answer.body)
    assert _shown(here) == [1, 2, 3, 4]


def test_a_person_without_faces_is_stated_with_nothing_left_out(
    runtime: Runtime, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Léa has no face in the index: named, nothing dropped."""
    monkeypatch.setattr(slideshow_avoid, "FaceIndex", lambda _file: _Faces(()))
    assert avoided(runtime, ["Léa"]) == Avoided(names=("Léa",))


def test_no_person_named_shows_no_avoid_block() -> None:
    """The block is drawn only with names; no link to /people from it."""
    script = (
        Path(__file__).resolve().parents[2]
        / "src/media_hygiene/review/templates/home_tv.js.j2"
    ).read_text("utf-8")
    block = script[
        script.index("function tvAvoidBox") : script.index("function tvAvoided")
    ]
    assert 'if (!people.length) return "";' in block
    assert "/people" not in block
    assert "tvAvoidBox(lists.people || [])" in script
    assert "avoid: avoid" in script


def test_the_remote_offers_only_the_people_on_the_show(here: SlideshowHere) -> None:
    """Antoine named on IMG_0, guessed on IMG_1, Léa on none: only Antoine."""
    answer = _choose(here, {"first": "2025-11-01", "last": "2025-11-30"})
    assert answer.status is HTTPStatus.OK
    view = json.loads(_ask(here, Request("GET", "/slideshow/api/avoid", _HOST)).body)
    assert view["people"] == [{"name": "Antoine", "sure": 1, "guessed": 1}]
    payload = json.dumps({"names": ["Antoine"]}).encode()
    ticked = _ask(here, Request("POST", "/slideshow/api/avoid", _HOST, payload))
    assert json.loads(ticked.body)["out"] == 2
